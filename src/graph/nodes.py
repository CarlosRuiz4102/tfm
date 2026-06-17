from __future__ import annotations

from src.data.provider_yfinance import download_market_data, normalize_downloaded_data, persist_download_artifacts
from src.data.validation import validate_financial_data_request_structure, validate_operational_download
from src.execution.code_runner import run_generated_code
from src.execution.validation import validate_execution_result
from src.graph.validation import validate_input
from src.llm.client import LLMClientError
from src.llm.pipeline import (
    build_llm_analysis,
    build_llm_code,
    build_llm_code_validation,
    build_llm_data_request,
    build_llm_interpretation,
    repair_llm_code,
    repair_llm_execution_code,
    repair_llm_data_request,
)
from src.schemas.analysis import Phase2DataContext, Phase2PromptContext, TemporalContext
from src.schemas.data import FinancialDataRequest
from src.schemas.execution import ExecutionValidationDecision
from src.schemas.input import FinancialQueryInput
from src.schemas.workflow import WorkflowState


# Limites de reintento por fase. Mantenerlos aqui ayuda a localizar de un
# vistazo cuantas oportunidades de reparacion tiene cada parte del flujo.
MAX_STRUCTURAL_REPAIR_ATTEMPTS = 2
MAX_OPERATIONAL_REPAIR_ATTEMPTS = 2
MAX_CODE_REPAIR_ATTEMPTS = 2
MAX_EXECUTION_ATTEMPTS = 3
# Estas claves representan pistas internas que no deben contaminar al
# interpretador final. La respuesta debe apoyarse en resultados reales, no en
# etiquetas del flujo o en metadatos de planificacion.
INTERPRETATION_HINT_KEYS = {
    "analysis_plan",
    "analysis_type",
    "analysis_level",
    "level",
    "presentation_preferences",
    "output_requirements",
}


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


def _strip_interpretation_hints(value):
    """
    El Agente 5 no debe ver pistas del plan analitico ni etiquetas de nivel.

    Esta limpieza se aplica sobre la carga que llega al interprete para que
    infiera la elaboracion de la respuesta desde la query y los resultados
    reales, no desde metadatos internos del flujo.
    """
    if isinstance(value, dict):
        return {
            key: _strip_interpretation_hints(item)
            for key, item in value.items()
            if key not in INTERPRETATION_HINT_KEYS
        }
    if isinstance(value, list):
        return [_strip_interpretation_hints(item) for item in value]
    return value


def _build_interpretation_payload(state: WorkflowState) -> dict:
    """
    Construye un payload limpio para el Agente 5.

    El interpretador solo debe recibir la consulta original, contexto resuelto,
    resultados de ejecucion y avisos relevantes. No debe depender de
    analysis_plan ni de pistas equivalentes.
    """
    resolved_context = {
        "tickers": list(state.normalized_query.tickers),
        "temporal_context": {
            "start": state.normalized_query.start,
            "end": state.normalized_query.end,
            "period": state.normalized_query.period,
            "interval": state.normalized_query.interval,
        },
    }
    # La salida de la parte 4 puede contener metricas, tablas o series utiles
    # para el usuario, pero no debe arrastrar pistas que le digan al Agente 5
    # como "deberia" interpretar o estructurar la respuesta.
    execution_output = _strip_interpretation_hints(state.execution_output or {})
    return {
        "user_query": state.user_query,
        "resolved_context": resolved_context,
        "execution_output": _compact_for_interpretation(execution_output),
        "warnings": list(state.warnings),
    }


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
        download_summary=summary.to_dict() if summary else None,
    )


def _build_code_validation_feedback(state: WorkflowState) -> str:
    """
    Compacta la decision del Agente 4 para pasarsela al subagente.

    El objetivo es que la correccion trabaje con errores, avisos y fixes
    pedidos por el validador sin arrastrar logica adicional al prompt.
    """
    decision = state.code_validation_decision
    if decision is None:
        return "El Agente 4 marco el codigo como reparable, pero no se conservo detalle adicional."

    lines = [f"decision={decision.decision}", f"reasoning={decision.reasoning}"]
    if decision.errors:
        lines.append("errors=" + " | ".join(decision.errors))
    if decision.required_fixes:
        lines.append("required_fixes=" + " | ".join(decision.required_fixes))
    if decision.warnings:
        lines.append("warnings=" + " | ".join(decision.warnings))
    return "\n".join(lines)


def _compact_runtime_text(value: str, max_chars: int = 2000) -> str:
    """Recorta stdout y stderr largos para no saturar el prompt del subagente."""
    cleaned = value.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + "... [texto truncado]"


def _build_execution_repair_feedback(state: WorkflowState) -> str:
    """
    Compacta la evidencia del fallo real para el Subagente 4.

    La idea es pasarle al subagente el contexto minimo que necesita:
    que intento acaba de fallar, con que error observable y que contrato de
    salida seguia incumpliendo el script.
    """
    decision = state.execution_validation_decision
    lines = [f"execution_attempt={state.execution_attempts}"]
    if decision is not None:
        lines.append(f"decision={decision.decision}")
        lines.append(f"reasoning={decision.reasoning}")
        if decision.errors:
            lines.append("errors=" + " | ".join(decision.errors))
        if decision.warnings:
            lines.append("warnings=" + " | ".join(decision.warnings))
    if state.execution_returncode is not None:
        lines.append(f"returncode={state.execution_returncode}")
    if state.execution_stdout.strip():
        lines.append("stdout=" + _compact_runtime_text(state.execution_stdout))
    if state.execution_stderr.strip():
        lines.append("stderr=" + _compact_runtime_text(state.execution_stderr))
    return "\n".join(lines)


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

    # Si el request es reparable, el subagente reescribe la peticion y se
    # vuelve a validar sobre la nueva version, no sobre la original.
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

    # Este bucle solo termina cuando la descarga se valida, se bloquea de forma
    # definitiva o se agotan los reintentos operativos permitidos.
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

    state.warnings.extend(warnings)
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


def code_validation_node(state: WorkflowState) -> WorkflowState:
    """
    Agente 4: decide si el codigo es valido, reparable o bloqueado.

    Esta fase sigue la misma filosofia que las partes anteriores:
    salida LLM estructurada, reintentos acotados y un subagente propio cuando
    el fallo todavia parece corregible.
    """
    if not state.generated_code or not state.analysis_plan:
        state.status = "error"
        state.error_message = "Faltan generated_code o analysis_plan para validar codigo."
        return state

    query_input = state.normalized_query.to_query_input()
    phase2_input_payload = _build_phase2_input_payload(state)
    state.status = "code_validating"

    # El Agente 4 puede aceptar, bloquear o pedir una reparacion. Si la salida
    # es reparable, el mismo bucle reenvia el codigo corregido para una nueva
    # decision antes de permitir la ejecucion.
    while True:
        try:
            decision, warnings = build_llm_code_validation(
                query_input,
                state.analysis_plan,
                state.generated_code,
                input_payload=phase2_input_payload.to_dict(),
            )
        except LLMClientError as exc:
            state.status = "error"
            state.error_message = str(exc)
            return state

        state.code_validation_decision = decision
        state.warnings.extend(warnings)
        state.warnings.extend(decision.warnings)

        if decision.decision == "valid":
            state.status = "code_validated"
            return state

        if decision.decision == "blocked":
            state.status = "code_rejected"
            detail = " | ".join(decision.errors) if decision.errors else decision.reasoning
            state.error_message = "Codigo bloqueado por el Agente 4: " + detail
            return state

        if state.code_repair_attempts >= MAX_CODE_REPAIR_ATTEMPTS:
            state.status = "code_rejected"
            detail = " | ".join(decision.errors) if decision.errors else decision.reasoning
            state.error_message = (
                "Se supero el numero maximo de intentos de reparacion de codigo. "
                + detail
            )
            return state

        try:
            state.status = "code_repairing"
            repaired_code, repair_warnings = repair_llm_code(
                query_input,
                state.analysis_plan,
                state.generated_code,
                _build_code_validation_feedback(state),
                input_payload=phase2_input_payload.to_dict(),
            )
        except LLMClientError as exc:
            state.status = "error"
            state.error_message = str(exc)
            return state

        state.generated_code = repaired_code
        state.code_repair_attempts += 1
        state.warnings.extend(repair_warnings)


def code_execution_node(state: WorkflowState) -> WorkflowState:
    """
    Parte 4: ejecutar, validar la salida y reparar si el fallo es recuperable.

    Esta fase ya no usa analysis_plan dentro del payload de ejecucion. El
    contrato analitico se resolvio antes; aqui solo importa si el script corre
    y si deja una salida util para la siguiente fase.
    """
    if not state.generated_code:
        state.status = "error"
        state.error_message = "Falta generated_code para ejecutar."
        return state

    phase2_input_payload = _build_phase2_input_payload(state)
    # El payload de ejecucion reutiliza el mismo contrato compacto que ya vio
    # el Agente 3. Asi evitamos duplicidades entre codegen y runtime.
    execution_payload = phase2_input_payload.to_dict()
    query_input = state.normalized_query.to_query_input()

    # Cada intento persiste su propia evidencia de runtime. Eso permite separar
    # despues errores de codigo, errores de entorno y salidas mal formadas.
    while state.execution_attempts < MAX_EXECUTION_ATTEMPTS:
        state.status = "executing"
        execution = run_generated_code(state.generated_code, execution_payload)
        state.execution_attempts += 1
        state.execution_stdout = execution.stdout
        state.execution_stderr = execution.stderr
        state.execution_returncode = execution.returncode
        state.execution_output = execution.parsed_output
        state.execution_artifacts = execution.artifacts

        state.status = "execution_validating"
        decision = validate_execution_result(execution)
        state.execution_validation_decision = decision
        state.warnings.extend(decision.warnings)

        if decision.decision == "valid":
            state.status = "executed"
            return state

        if state.execution_attempts >= MAX_EXECUTION_ATTEMPTS:
            state.execution_validation_decision = ExecutionValidationDecision(
                decision="blocked",
                errors=list(decision.errors),
                warnings=list(decision.warnings),
                reasoning="Se agotaron los intentos maximos de ejecucion sin obtener una salida valida.",
            )
            state.status = "execution_failed"
            detail = " | ".join(decision.errors) if decision.errors else decision.reasoning
            state.error_message = (
                "Se agotaron los intentos maximos de ejecucion. "
                + detail
            )
            return state

        try:
            state.status = "execution_repairing"
            repaired_code, repair_warnings = repair_llm_execution_code(
                query_input,
                state.generated_code,
                _build_execution_repair_feedback(state),
                input_payload=execution_payload,
            )
        except LLMClientError as exc:
            state.status = "error"
            state.error_message = str(exc)
            return state

        # El Subagente 4 no certifica que el codigo ya este bien: solo propone
        # una nueva version. La validacion real llega en la siguiente
        # reejecucion del bucle.
        state.generated_code = repaired_code
        state.execution_repair_attempts += 1
        state.warnings.extend(repair_warnings)

    state.status = "execution_failed"
    state.error_message = "La parte 4 termino en un estado inconsistente."
    return state


def interpretation_node(state: WorkflowState) -> WorkflowState:
    """Agente 5: transforma los resultados ejecutados en una respuesta final."""
    if state.execution_returncode != 0:
        return execution_error_node(state)
    state.status = "interpretation_preparing"
    interpretation_payload = _build_interpretation_payload(state)
    # Conservamos la carga exacta que vio el interpretador para poder trazar
    # despues como se conectan la parte 4 y la parte 5.
    state.interpretation_payload = interpretation_payload
    try:
        state.status = "interpreting"
        final_answer, warnings = build_llm_interpretation(interpretation_payload)
    except LLMClientError as exc:
        state.status = "completed_with_error"
        state.error_message = str(exc)
        state.final_answer = (
            "No se pudo generar una respuesta final con LLM. "
            f"Detalle: {exc}"
        )
        return state

    # No validamos semanticamente la interpretacion aqui. Esta parte acepta la
    # respuesta textual del agente tal como venga, salvo los controles minimos
    # de formato que ya viven en build_llm_interpretation(...).
    state.warnings.extend(warnings)
    state.final_answer = final_answer
    state.status = "interpreted"
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
