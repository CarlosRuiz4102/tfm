from __future__ import annotations

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
from src.schemas import AnalysisPlan, FinancialDataRequest, FinancialQueryInput, WorkflowState


MAX_STRUCTURAL_REPAIR_ATTEMPTS = 2
MAX_OPERATIONAL_REPAIR_ATTEMPTS = 2


def _compact_for_interpretation(value, max_list_items: int = 40, max_string_chars: int = 2000):
    # La interpretación final debe recibir una salida manejable por el LLM.
    # Este helper evita enviar listas enormes o strings excesivamente largos.
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
    Sincroniza el request de datos con el workflowstate.

    Esto evita que cada nodo tenga que reconstruir manualmente tickers,
    fechas e intervalo antes de pasar al siguiente bloque.
    """
    state.financial_data_request = request.to_dict()
    state.normalized_query["tickers"] = request.tickers
    state.normalized_query["start"] = request.start
    state.normalized_query["end"] = request.end
    state.normalized_query["period"] = request.period
    state.normalized_query["interval"] = request.interval
    state.normalized_query["needs_clarification"] = request.needs_clarification
    state.normalized_query["warnings"] = list(state.warnings)


def ingest_node(state: WorkflowState) -> WorkflowState:
    """Valida la consulta original antes de entrar en la planificación de datos."""
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    errors = validate_input(query_input)
    if errors:
        state.status = "invalid"
        state.error_message = " | ".join(errors)
        return state
    state.status = "ingested"
    return state


def data_request_planning_node(state: WorkflowState) -> WorkflowState:
    """Agente 1: convierte la consulta libre en un FinancialDataRequest."""
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    try:
        request, warnings = build_llm_data_request(query_input)
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    _apply_data_request_to_state(state, request)
    # Este status deja claro que ya existe un request de datos, aunque todavía
    # no se ha demostrado que esté bien ni que descargue correctamente.
    state.status = "data_request_planned"
    return state


def data_request_structural_validation_node(state: WorkflowState) -> WorkflowState:
    """
    Valida la estructura del FinancialDataRequest y activa el Subagente 1 si procede.

    Esta etapa aún no descarga nada: solo comprueba que la petición a yfinance
    está bien planteada.
    """
    if not state.financial_data_request:
        state.status = "error"
        state.error_message = "No existe FinancialDataRequest para validar."
        return state

    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    request = FinancialDataRequest.from_dict(state.financial_data_request)
    decision = validate_financial_data_request_structure(request)

    while decision.status == "repairable" and state.structural_repair_attempts < MAX_STRUCTURAL_REPAIR_ATTEMPTS:
        # El subagente reescribe el request con el feedback explícito del validador.
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
        # Solo ahora consideramos que el request está listo para probarse contra
        # la fuente real de datos.
        state.status = "data_request_validated"
        return state

    state.status = "blocked"
    if decision.status == "repairable":
        # Llegar aquí implica que el problema era corregible en teoría, pero se
        # agotó el número máximo de intentos permitidos.
        state.error_message = (
            "Se supero el numero maximo de intentos de reparacion estructural. "
            + " | ".join(decision.errors)
        )
    else:
        state.error_message = " | ".join(decision.errors) or "La fase de datos se bloqueo por falta de aclaracion."
    return state


def data_download_node(state: WorkflowState) -> WorkflowState:
    """
    Ejecuta la validación operativa: descargar de verdad y verificar que sirve.

    Si la descarga falla de forma reparable, activa el Subagente 2 para ajustar
    el request desde un punto de vista operativo.
    """
    if not state.financial_data_request:
        state.status = "error"
        state.error_message = "No existe FinancialDataRequest para descargar datos."
        return state

    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    request = FinancialDataRequest.from_dict(state.financial_data_request)

    while True:
        try:
            downloaded = download_market_data(request)
            normalized = normalize_downloaded_data(downloaded, request.tickers)
            decision = validate_operational_download(request, normalized)
        except Exception as exc:  # pragma: no cover - depende de yfinance y entorno externo
            # Un fallo aquí significa que el request parecía correcto, pero no ha
            # funcionado bien contra la fuente real o el resultado no es usable.
            decision_errors = [f"Fallo operativo al descargar datos: {exc}"]
            decision_status = "repairable" if state.operational_repair_attempts < MAX_OPERATIONAL_REPAIR_ATTEMPTS else "blocked"
            if decision_status == "blocked":
                state.status = "blocked"
                state.error_message = " | ".join(decision_errors)
                return state
            decision = type("Decision", (), {"status": decision_status, "errors": decision_errors})()

        if decision.status == "valid":
            # La propia descarga que valida operativamente el request se reutiliza
            # como entrada para el resto del flujo; no se vuelve a descargar.
            artifacts, summary = persist_download_artifacts(request, downloaded, normalized)
            state.download_artifacts = artifacts.to_dict()
            state.download_summary = summary.to_dict()
            # Mantenemos compatibilidad con el resto del pipeline actual
            # alimentándolo con el CSV normalizado que acabamos de generar.
            state.csv_paths = [artifacts.normalized_data_path]
            state.normalized_query["csv_paths"] = [artifacts.normalized_data_path]
            state.normalized_query["tickers"] = request.tickers
            state.normalized_query["warnings"] = list(state.warnings)
            _apply_data_request_to_state(state, request)
            state.status = "data_downloaded"
            return state

        if decision.status != "repairable":
            state.status = "blocked"
            state.error_message = " | ".join(decision.errors) or "La descarga operativa no pudo completarse."
            return state

        if state.operational_repair_attempts >= MAX_OPERATIONAL_REPAIR_ATTEMPTS:
            # Igual que en la ruta estructural, el bloqueo aquí significa que ya
            # no seguimos corrigiendo esta ejecución.
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
            # El subagente operativo solo puede ajustar un request que siga
            # siendo estructuralmente correcto; si rompe el contrato, bloqueamos.
            state.status = "blocked"
            state.error_message = (
                "El subagente operativo devolvio un FinancialDataRequest estructuralmente invalido. "
                + " | ".join(structural_decision.errors)
            )
            return state
        request = repaired_request
        _apply_data_request_to_state(state, request)


def llm_analysis_node(state: WorkflowState) -> WorkflowState:
    """Agente 2: transforma consulta y datos descargados en un plan analítico."""
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    try:
        # El agente 2 necesita más contexto que la query libre, así que le
        # pasamos también la versión enriquecida acumulada en el estado.
        plan, warnings = build_llm_analysis(query_input, input_payload=state.normalized_query)
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    state.analysis_plan = plan.to_dict()
    # A partir de aquí el problema deja de ser "qué datos necesito" y pasa a
    # ser "qué cálculos necesito hacer con esos datos".
    state.status = "planned"
    return state


def code_generation_node(state: WorkflowState) -> WorkflowState:
    """Agente 3: genera el script Python que materializa el análisis."""
    if not state.analysis_plan:
        state.status = "error"
        state.error_message = "No existe analysis_plan para generar codigo."
        return state

    plan = AnalysisPlan(**state.analysis_plan)
    query_input = FinancialQueryInput.from_dict(state.normalized_query)
    try:
        code_output, warnings = build_llm_code(query_input, plan, input_payload=state.normalized_query)
    except LLMClientError as exc:
        state.status = "error"
        state.error_message = str(exc)
        return state
    state.warnings.extend(warnings)
    state.generated_code = code_output
    state.status = "code_generated"
    return state


def code_security_node(state: WorkflowState) -> WorkflowState:
    """Agente 4: validación estática del código antes de ejecutarlo."""
    if not state.generated_code:
        state.status = "error"
        state.error_message = "No existe generated_code para validar."
        return state

    result = validate_generated_code(state.generated_code)
    if not result.is_valid:
        if state.analysis_plan:
            plan = AnalysisPlan(**state.analysis_plan)
            query_input = FinancialQueryInput.from_dict(state.normalized_query)
            error_detail = "Codigo rechazado por seguridad: " + " | ".join(result.errors)
            try:
                repaired_code, warnings = repair_llm_code(
                    query_input,
                    plan,
                    state.generated_code,
                    error_detail,
                    input_payload=state.normalized_query,
                )
                repaired_result = validate_generated_code(repaired_code)
                if repaired_result.is_valid:
                    state.generated_code = repaired_code
                    state.warnings.extend(warnings)
                    # Si la reparación consigue un script seguro, no hace falta
                    # exponer el rechazo inicial al resto del pipeline.
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
    """Ejecutor: lanza el script generado y recoge artefactos y salida estructurada."""
    if not state.generated_code or not state.analysis_plan:
        state.status = "error"
        state.error_message = "Faltan generated_code o analysis_plan."
        return state

    payload = {
        "query": state.user_query,
        "tickers": state.normalized_query["tickers"],
        "csv_paths": state.csv_paths,
        "start": state.normalized_query.get("start"),
        "end": state.normalized_query.get("end"),
        "period": state.normalized_query.get("period"),
        "interval": state.normalized_query.get("interval"),
        "input": state.normalized_query,
        "analysis_plan": state.analysis_plan,
        "download_artifacts": state.download_artifacts,
        "download_summary": state.download_summary,
    }
    # El payload concentra todo lo que el script necesita sin depender de estado global.
    execution = run_generated_code(state.generated_code, payload)
    if execution.returncode != 0:
        # Si el script falla en tiempo de ejecución, intentamos una reparación
        # apoyándonos en stderr o en el detalle observable del fallo.
        plan = AnalysisPlan(**state.analysis_plan)
        query_input = FinancialQueryInput.from_dict(state.normalized_query)
        error_detail = execution.stderr.strip() or "El script fallo sin stderr."
        try:
            repaired_code, warnings = repair_llm_code(
                query_input,
                plan,
                state.generated_code,
                error_detail,
                input_payload=state.normalized_query,
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
    state.execution_artifacts = execution.artifacts.to_dict()
    state.status = "executed" if execution.returncode == 0 else "execution_failed"
    return state


def interpretation_node(state: WorkflowState) -> WorkflowState:
    """Agente 5: convierte la salida ejecutada en una respuesta legible para el usuario."""
    output = state.execution_output or {}
    if state.execution_returncode != 0:
        return execution_error_node(state)
    if not state.analysis_plan:
        state.status = "completed_with_error"
        state.error_message = "No existe analysis_plan para interpretar resultados."
        state.final_answer = state.error_message
        return state

    plan = AnalysisPlan(**state.analysis_plan)
    output_for_llm = _compact_for_interpretation(output)
    try:
        final_answer, warnings = build_llm_interpretation(output_for_llm, plan)
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
    # El flujo solo se considera completo cuando ya existe una respuesta final
    # basada en resultados ejecutados y no en inferencias intermedias.
    state.status = "completed"
    return state


def invalid_request_node(state: WorkflowState) -> WorkflowState:
    """Salida controlada para errores de entrada o bloqueos de la fase de datos."""
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
