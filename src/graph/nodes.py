from __future__ import annotations

from src.analysis.validation import validate_analysis_plan
from src.data.provider_yfinance import download_market_data, normalize_downloaded_data, persist_download_artifacts
from src.data.validation import validate_financial_data_request_structure, validate_operational_download
from src.execution.code_runner import run_generated_code
from src.execution.code_security import validate_generated_code
from src.graph.validation import validate_input
from src.llm.client import LLMClientError
from src.llm.pipeline import (
    build_llm_analysis,
    build_llm_code,
    build_llm_data_request,
    build_llm_interpretation,
    repair_llm_code,
    repair_llm_data_request,
)
from src.schemas.analysis import AnalysisPlan, Phase2DataContext, Phase2PromptContext, TemporalContext
from src.schemas.data import FinancialDataRequest
from src.schemas.input import FinancialQueryInput
from src.schemas.workflow import WorkflowState


MAX_STRUCTURAL_REPAIR_ATTEMPTS = 2
MAX_OPERATIONAL_REPAIR_ATTEMPTS = 2


def _compact_for_interpretation(value, max_list_items: int = 40, max_string_chars: int = 2000):
    # El interprete final debe recibir una carga compacta en vez de listas muy
    # grandes o cadenas enormes que solo meten ruido y no informacion util.
    if isinstance(value, dict):
        return {
            key: _compact_for_interpretation(item, max_list_items=max_list_items, max_string_chars=max_string_chars)
            for key, item in value.items()
        }
    if isinstance(value, list):
        if len(value) <= max_list_items:
            return [
                _compact_for_interpretation(item, max_list_items=max_list_items, max_string_chars=max_string_chars)
                for item in value
            ]
        head_size = max_list_items // 2
        tail_size = max_list_items - head_size
        compacted_items = value[:head_size] + value[-tail_size:]
        return {
            "truncated": True,
            "original_length": len(value),
            "items": [
                _compact_for_interpretation(item, max_list_items=max_list_items, max_string_chars=max_string_chars)
                for item in compacted_items
            ],
        }
    if isinstance(value, str) and len(value) > max_string_chars:
        return value[:max_string_chars] + "... [texto truncado para interpretacion]"
    return value


def _apply_data_request_to_state(state: WorkflowState, request: FinancialDataRequest) -> None:
    """
    Sincroniza el request de datos con el estado compartido.

    Este paso actualiza el contexto resuelto con tickers y parametros
    temporales sin perder la traza de que todo eso procede del request
    validado de la fase de datos.
    """
    state.financial_data_request = request
    state.normalized_query.tickers = request.tickers
    state.normalized_query.start = request.start
    state.normalized_query.end = request.end
    state.normalized_query.period = request.period
    state.normalized_query.interval = request.interval
    state.normalized_query.needs_clarification = request.needs_clarification
    state.normalized_query.warnings = list(state.warnings)


def _build_phase2_input_payload(state: WorkflowState) -> Phase2PromptContext:
    """
    Construye el traspaso compacto entre fase 1 y fase 2.

    La trazabilidad completa sigue viviendo en WorkflowState. El LLM de la
    parte 2 recibe solo el contexto operativo minimo que necesita para
    planificar e implementar el analisis.
    """
    summary = state.download_summary
    data_context = Phase2DataContext(
        row_count=summary.row_count if summary else None,
        available_columns=list(summary.columns) if summary else [],
    )
    temporal_context = TemporalContext(
        start=state.normalized_query.start,
        end=state.normalized_query.end,
        period=state.normalized_query.period,
        interval=state.normalized_query.interval,
    )
    return Phase2PromptContext(
        query=state.user_query,
        tickers=list(state.normalized_query.tickers),
        temporal_context=temporal_context,
        csv_paths=list(state.csv_paths),
        data_context=data_context,
        warnings=list(state.warnings),
    )


def ingest_node(state: WorkflowState) -> WorkflowState:
    """Valida la consulta original antes de que empiece cualquier planificacion."""
    query_input = state.normalized_query.to_query_input()
    errors = validate_input(query_input)
    if errors:
        state.status = "invalid"
        state.error_message = " | ".join(errors)
        return state
    state.status = "ingested"
    return state


def data_request_planning_node(state: WorkflowState) -> WorkflowState:
    """Agente 1: transforma la consulta del usuario en un FinancialDataRequest."""
    query_input = state.normalized_query.to_query_input()
    try:
        request, warnings = build_llm_data_request(query_input)
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    _apply_data_request_to_state(state, request)
    state.status = "data_request_planned"
    return state


def data_request_structural_validation_node(state: WorkflowState) -> WorkflowState:
    """
    Valida la estructura del FinancialDataRequest.

    Esta etapa todavia no descarga nada. Solo comprueba que el request sea lo
    bastante coherente como para merecer un intento real contra yfinance.
    """
    if not state.financial_data_request:
        state.status = "error"
        state.error_message = "No existe FinancialDataRequest para validar."
        return state

    query_input = state.normalized_query.to_query_input()
    request = state.financial_data_request
    decision = validate_financial_data_request_structure(request)

    while decision.status == "repairable" and state.structural_repair_attempts < MAX_STRUCTURAL_REPAIR_ATTEMPTS:
        try:
            repaired_request, warnings = repair_llm_data_request(query_input, request, decision.errors, stage="structural")
        except LLMClientError as exc:
            state.status = "error"
            state.error_message = str(exc)
            return state
        state.structural_repair_attempts += 1
        state.warnings.extend(warnings)
        request = repaired_request
        _apply_data_request_to_state(state, request)
        decision = validate_financial_data_request_structure(request)

    if decision.status == "valid":
        _apply_data_request_to_state(state, request)
        state.status = "data_request_validated"
        return state

    state.status = "blocked"
    if decision.status == "repairable":
        state.error_message = (
            "Se supero el numero maximo de intentos de reparacion estructural. "
            + " | ".join(decision.errors)
        )
    else:
        state.error_message = " | ".join(decision.errors) or "La fase de datos se bloqueo por falta de aclaracion."
    return state


def data_download_node(state: WorkflowState) -> WorkflowState:
    """
    Ejecuta la validacion operativa: descarga real mas comprobaciones de uso.

    Si la descarga falla de forma reparable, el subagente operativo puede
    ajustar el request y reintentar preservando la intencion original.
    """
    if not state.financial_data_request:
        state.status = "error"
        state.error_message = "No existe FinancialDataRequest para descargar datos."
        return state

    query_input = state.normalized_query.to_query_input()
    request = state.financial_data_request

    while True:
        try:
            downloaded = download_market_data(request)
            normalized = normalize_downloaded_data(downloaded, request.tickers)
            decision = validate_operational_download(request, normalized)
        except Exception as exc:  # pragma: no cover - depende de yfinance y entorno externo
            decision_errors = [f"Fallo operativo al descargar datos: {exc}"]
            decision_status = "repairable" if state.operational_repair_attempts < MAX_OPERATIONAL_REPAIR_ATTEMPTS else "blocked"
            if decision_status == "blocked":
                state.status = "blocked"
                state.error_message = " | ".join(decision_errors)
                return state
            decision = type("Decision", (), {"status": decision_status, "errors": decision_errors})()

        if decision.status == "valid":
            artifacts, summary = persist_download_artifacts(request, downloaded, normalized)
            state.download_artifacts = artifacts
            state.download_summary = summary
            state.csv_paths = [artifacts.normalized_data_path]
            state.normalized_query.csv_paths = [artifacts.normalized_data_path]
            state.normalized_query.tickers = request.tickers
            state.normalized_query.warnings = list(state.warnings)
            _apply_data_request_to_state(state, request)
            state.status = "data_downloaded"
            return state

        if decision.status != "repairable":
            state.status = "blocked"
            state.error_message = " | ".join(decision.errors) or "La descarga operativa no pudo completarse."
            return state

        if state.operational_repair_attempts >= MAX_OPERATIONAL_REPAIR_ATTEMPTS:
            state.status = "blocked"
            state.error_message = (
                "Se supero el numero maximo de intentos de reparacion operativa. "
                + " | ".join(decision.errors)
            )
            return state

        try:
            repaired_request, warnings = repair_llm_data_request(query_input, request, decision.errors, stage="operational")
        except LLMClientError as exc:
            state.status = "error"
            state.error_message = str(exc)
            return state
        state.operational_repair_attempts += 1
        state.warnings.extend(warnings)
        structural_decision = validate_financial_data_request_structure(repaired_request)
        if structural_decision.status != "valid":
            state.status = "blocked"
            state.error_message = (
                "El subagente operativo devolvio un FinancialDataRequest estructuralmente invalido. "
                + " | ".join(structural_decision.errors)
            )
            return state
        request = repaired_request
        _apply_data_request_to_state(state, request)


def llm_analysis_node(state: WorkflowState) -> WorkflowState:
    """Agente 2: transforma el contexto validado de datos en un AnalysisPlan."""
    query_input = state.normalized_query.to_query_input()
    phase2_input_payload = _build_phase2_input_payload(state)
    try:
        plan, warnings = build_llm_analysis(query_input, input_payload=phase2_input_payload.to_dict())
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state

    available_columns = state.download_summary.columns if state.download_summary else None
    validation = validate_analysis_plan(plan, available_columns=available_columns)
    if not validation.is_valid:
        state.status = "error"
        state.error_message = "AnalysisPlan invalido: " + " | ".join(validation.errors)
        return state

    state.warnings.extend(warnings)
    state.warnings.extend(validation.warnings)
    state.analysis_plan = plan
    state.status = "planned"
    return state


def code_generation_node(state: WorkflowState) -> WorkflowState:
    """Agente 3: genera el script Python que materializa el plan."""
    if not state.analysis_plan:
        state.status = "error"
        state.error_message = "No existe analysis_plan para generar codigo."
        return state

    query_input = state.normalized_query.to_query_input()
    phase2_input_payload = _build_phase2_input_payload(state)
    try:
        code_output, warnings = build_llm_code(query_input, state.analysis_plan, input_payload=phase2_input_payload.to_dict())
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    state.generated_code = code_output
    state.status = "code_generated"
    return state


def code_security_node(state: WorkflowState) -> WorkflowState:
    """Agente 4: valida el codigo generado antes de ejecutarlo."""
    if not state.generated_code:
        state.status = "error"
        state.error_message = "No existe generated_code para validar."
        return state

    result = validate_generated_code(state.generated_code)
    if not result.is_valid:
        if state.analysis_plan:
            query_input = state.normalized_query.to_query_input()
            error_detail = "Codigo rechazado por seguridad: " + " | ".join(result.errors)
            try:
                repaired_code, warnings = repair_llm_code(
                    query_input,
                    state.analysis_plan,
                    state.generated_code,
                    error_detail,
                    input_payload=_build_phase2_input_payload(state).to_dict(),
                )
                repaired_result = validate_generated_code(repaired_code)
                if repaired_result.is_valid:
                    state.generated_code = repaired_code
                    state.warnings.extend(warnings)
                    state.status = "code_validated"
                    return state
                result = repaired_result
            except LLMClientError as exc:
                state.warnings.append(str(exc))
        state.status = "code_rejected"
        state.error_message = "Codigo rechazado por seguridad: " + " | ".join(result.errors)
        return state
    state.status = "code_validated"
    return state


def code_execution_node(state: WorkflowState) -> WorkflowState:
    """Ejecuta el script generado y recoge artefactos mas salida estructurada."""
    if not state.generated_code or not state.analysis_plan:
        state.status = "error"
        state.error_message = "Faltan generated_code o analysis_plan."
        return state

    phase2_input_payload = _build_phase2_input_payload(state)
    temporal_context = phase2_input_payload.temporal_context
    payload = {
        "query": state.user_query,
        "tickers": list(state.normalized_query.tickers),
        "csv_paths": list(state.csv_paths),
        "start": temporal_context.start,
        "end": temporal_context.end,
        "period": temporal_context.period,
        "interval": temporal_context.interval,
        "input": phase2_input_payload.to_dict(),
        "analysis_plan": state.analysis_plan.to_dict(),
        "download_artifacts": state.download_artifacts.to_dict() if state.download_artifacts else None,
        "download_summary": state.download_summary.to_dict() if state.download_summary else None,
    }
    execution = run_generated_code(state.generated_code, payload)
    if execution.returncode != 0:
        query_input = state.normalized_query.to_query_input()
        error_detail = execution.stderr.strip() or "El script fallo sin stderr."
        try:
            repaired_code, warnings = repair_llm_code(
                query_input,
                state.analysis_plan,
                state.generated_code,
                error_detail,
                input_payload=phase2_input_payload.to_dict(),
            )
            repaired_result = validate_generated_code(repaired_code)
            if repaired_result.is_valid:
                state.generated_code = repaired_code
                state.warnings.extend(warnings)
                execution = run_generated_code(repaired_code, payload)
            else:
                state.warnings.append("La reparacion no supero seguridad: " + " | ".join(repaired_result.errors))
        except LLMClientError as exc:
            state.warnings.append(str(exc))
    state.execution_stdout = execution.stdout
    state.execution_stderr = execution.stderr
    state.execution_returncode = execution.returncode
    state.execution_output = execution.parsed_output
    state.execution_artifacts = execution.artifacts
    state.status = "executed" if execution.returncode == 0 else "execution_failed"
    return state


def interpretation_node(state: WorkflowState) -> WorkflowState:
    """Agente 5: transforma los resultados ejecutados en una respuesta final."""
    output = state.execution_output or {}
    if state.execution_returncode != 0:
        return execution_error_node(state)
    if not state.analysis_plan:
        state.status = "completed_with_error"
        state.error_message = "No existe analysis_plan para interpretar resultados."
        state.final_answer = state.error_message
        return state

    output_for_llm = _compact_for_interpretation(output)
    try:
        final_answer, warnings = build_llm_interpretation(output_for_llm, state.analysis_plan)
    except LLMClientError as exc:
        state.status = "completed_with_error"
        state.error_message = str(exc)
        state.final_answer = (
            "No se pudo generar una respuesta final con LLM. "
            f"Detalle: {exc}"
        )
        return state

    state.warnings.extend(warnings)
    state.final_answer = final_answer
    state.status = "completed"
    return state


def invalid_request_node(state: WorkflowState) -> WorkflowState:
    """Salida controlada para entradas invalidas o bloqueos de la fase de datos."""
    state.final_answer = state.error_message or "La peticion es invalida."
    state.status = "completed_with_error"
    return state


def execution_error_node(state: WorkflowState) -> WorkflowState:
    """Salida controlada para fallos posteriores a la fase de datos."""
    if state.error_message:
        state.final_answer = state.error_message
        state.status = "completed_with_error"
        return state

    state.final_answer = (
        "El script generado fallo durante la ejecucion. "
        f"stderr: {state.execution_stderr.strip() or 'sin detalle adicional'}"
    )
    state.status = "completed_with_error"
    return state
