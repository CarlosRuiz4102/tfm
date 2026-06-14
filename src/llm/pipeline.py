from __future__ import annotations

import json
from typing import Any

from src.config import LLMConfig
from src.llm.client import LLMClientError, create_llm_client
from src.llm.prompts import (
    build_analysis_messages,
    build_code_validation_messages,
    build_code_repair_messages,
    build_codegen_messages,
    build_data_request_messages,
    build_data_request_repair_messages,
    build_execution_repair_messages,
    build_interpretation_messages,
)
from src.schemas import AnalysisPlan, CodeValidationDecision, FinancialDataRequest, FinancialQueryInput


MAX_LLM_ATTEMPTS = 3


def _as_str_list(value: object, default: list[str]) -> list[str]:
    # El LLM puede mezclar tipos o devolver listas con elementos vacíos; este
    # helper deja una lista limpia y consistente.
    if not isinstance(value, list):
        return default
    items = [str(item) for item in value if str(item).strip()]
    return items or default


def _json_from_text(text: str) -> dict:
    # Aceptamos tanto JSON puro como respuestas encapsuladas en markdown para
    # hacer el pipeline más robusto frente a pequeñas desviaciones del modelo.
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Ultimo intento de tolerancia: algunos modelos envuelven el JSON con
        # texto antes o despues. Si detectamos un objeto claro, lo extraemos.
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _code_from_text(text: str) -> str:
    # En generación de código preferimos recuperar el campo "code", pero
    # mantenemos una ruta de tolerancia si el modelo devuelve el script crudo.
    try:
        payload = _json_from_text(text)
        code = str(payload.get("code") or "").strip()
        # Algunos modelos devuelven un segundo wrapper JSON dentro del propio
        # campo code. Si ocurre, lo desanidamos para recuperar el script real.
        for _ in range(2):
            if not code.startswith("{"):
                break
            try:
                nested_payload = _json_from_text(code)
            except json.JSONDecodeError:
                break
            nested_code = str(nested_payload.get("code") or "").strip()
            if not nested_code:
                break
            code = nested_code
        return code
    except json.JSONDecodeError:
        # Ruta de compatibilidad por si el modelo devuelve el script directamente
        # en vez de cumplir exactamente el wrapper JSON pedido.
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        if "def main(" in cleaned and "json.dumps" in cleaned:
            return cleaned
        raise


def _is_json_only_answer(text: str) -> bool:
    # Se usa para detectar cuando el intérprete final ha devuelto JSON en vez de
    # una respuesta textual, y forzar una regeneración más adecuada.
    cleaned = text.strip()
    if not cleaned or cleaned[0] not in "{[":
        return False
    try:
        json.loads(cleaned)
    except json.JSONDecodeError:
        return False
    return True


def _normalize_code_validation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Rellena campos minimos del Agente 4 cuando el LLM omite algun detalle menor.

    La parte 3 sigue exigiendo una decision estructurada, pero no conviene que
    toda la ejecucion se rompa solo porque falte `reasoning` si ya tenemos una
    decision util y errores observables.
    """
    normalized = dict(payload)
    decision = str(normalized.get("decision") or "").strip().lower()
    reasoning = str(normalized.get("reasoning") or "").strip()
    if reasoning:
        return normalized

    errors = _as_str_list(normalized.get("errors"), [])
    required_fixes = _as_str_list(normalized.get("required_fixes"), [])

    if errors:
        normalized["reasoning"] = "El Agente 4 detecto problemas en el script: " + " | ".join(errors)
        return normalized
    if required_fixes:
        normalized["reasoning"] = "El Agente 4 pidio correcciones concretas: " + " | ".join(required_fixes)
        return normalized
    if decision == "valid":
        normalized["reasoning"] = "El Agente 4 considera que el codigo puede continuar."
    elif decision == "repairable":
        normalized["reasoning"] = "El Agente 4 considera que el codigo es corregible."
    elif decision == "blocked":
        normalized["reasoning"] = "El Agente 4 considera que el codigo debe bloquearse."
    return normalized


def _build_data_request_from_payload(payload: dict, query_input: FinancialQueryInput) -> FinancialDataRequest:
    """Normaliza la respuesta del LLM a un FinancialDataRequest robusto."""
    # Este punto es clave: aunque el LLM "acierte", no dejamos pasar su salida
    # cruda al sistema. Primero la convertimos a nuestro contrato interno.
    #
    # Aqui se decide la forma final con la que el validador estructural va a
    # trabajar. Es, por tanto, la frontera entre "respuesta del LLM" y
    # "objeto de dominio del sistema".
    request_payload = {
        "user_query": str(payload.get("user_query") or query_input.query),
        "provider": str(payload.get("provider") or "yfinance"),
        "instruments": payload.get("instruments") or [],
        "interval": str(payload.get("interval") or ""),
        "start": payload.get("start"),
        "end": payload.get("end"),
        "period": payload.get("period"),
        "required_fields": _as_str_list(
            payload.get("required_fields"),
            ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
        ),
        "needs_clarification": bool(payload.get("needs_clarification", False)),
        "clarification_reason": payload.get("clarification_reason"),
    }
    return FinancialDataRequest.from_dict(request_payload)


def build_llm_data_request(query_input: FinancialQueryInput) -> tuple[FinancialDataRequest, list[str]]:
    """Llama al Agente 1 y obliga a devolver un FinancialDataRequest parseable."""
    # Esta funcion se usa en data_request_planning_node.
    #
    # Su responsabilidad no es validar si el request es correcto, sino:
    # 1. hablar con el Agente 1,
    # 2. exigir una salida JSON,
    # 3. parsearla,
    # 4. convertirla a FinancialDataRequest.
    #
    # La validacion fuerte viene despues, en validation.py.
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para construir el FinancialDataRequest.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para planificacion de datos.")
        messages = build_data_request_messages(query_input)
        last_error: Exception | None = None
        payload = None
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                # Esperamos JSON porque el Agente 1 no debe redactar texto
                # libre, sino un contrato estructurado de datos.
                response = client.complete_json(messages)
                payload = _json_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                # Si el modelo rompe el formato, no abandonamos al primer fallo:
                # le devolvemos feedback explicito y reintentamos.
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Devuelve de nuevo exclusivamente un FinancialDataRequest JSON valido.",
                    )
                ]
        if payload is None:
            raise LLMClientError(str(last_error))
        # El contrato final siempre pasa por nuestra normalización local antes
        # de entrar al validador estructural.
        return _build_data_request_from_payload(payload, query_input), []
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo construir el FinancialDataRequest con LLM: {exc}") from exc


def repair_llm_data_request(
    query_input: FinancialQueryInput,
    previous_request: FinancialDataRequest,
    validation_errors: list[str],
    stage: str,
) -> tuple[FinancialDataRequest, list[str]]:
    """Llama a los subagentes de datos usando los errores del validador como feedback."""
    # Esta funcion la usan dos rutas distintas:
    # - stage="structural": Subagente 1
    # - stage="operational": Subagente 2
    #
    # Ambas comparten una misma mecanica:
    # 1. tomar el request anterior,
    # 2. pasarle al LLM los errores observados por el validador,
    # 3. pedir un nuevo FinancialDataRequest JSON,
    # 4. volver a normalizarlo localmente.
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para reparar el FinancialDataRequest.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para reparar la fase de datos.")
        messages = build_data_request_repair_messages(query_input, previous_request, validation_errors, stage)
        last_error: Exception | None = None
        payload = None
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                # El subagente no devuelve un parche textual: devuelve un request
                # completo nuevo, ya corregido.
                response = client.complete_json(messages)
                payload = _json_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Devuelve de nuevo exclusivamente un FinancialDataRequest JSON valido.",
                    )
                ]
        if payload is None:
            raise LLMClientError(str(last_error))
        # Distinguimos el warning según la ruta de reparación para poder auditar
        # después si el problema fue formal u operativo.
        warning = "Se reparo el FinancialDataRequest." if stage == "structural" else "Se reparo operativamente el FinancialDataRequest."
        return _build_data_request_from_payload(payload, query_input), [warning]
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo reparar el FinancialDataRequest con LLM: {exc}") from exc


def build_llm_analysis(
    query_input: FinancialQueryInput,
    input_payload: dict[str, Any] | None = None,
) -> tuple[AnalysisPlan, list[str]]:
    """Llama al Agente 2 y transforma su JSON en un AnalysisPlan tipado."""
    # Aunque query_input ya solo contiene la consulta libre, esta funcion puede
    # recibir input_payload enriquecido desde WorkflowState.
    #
    # Ese detalle permite que el Agente 2 vea tickers, rango, csv_paths y
    # metadata de la fase de datos sin volver a ensuciar FinancialQueryInput.
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para usar openai/gpt-oss-20b sobre vLLM.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para analisis.")
        messages = build_analysis_messages(query_input, input_payload=input_payload)
        last_error: Exception | None = None
        payload = None
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                # Igual que en el Agente 1, exigimos contrato JSON porque el
                # resultado esperado es un plan, no una respuesta narrativa.
                response = client.complete_json(messages)
                payload = _json_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Devuelve de nuevo exclusivamente un objeto JSON valido.",
                    )
                ]
        if payload is None:
            raise LLMClientError(str(last_error))
        # Aqui el JSON del LLM se convierte en AnalysisPlan tipado, que sera la
        # entrada formal del generador de codigo.
        return (
            AnalysisPlan(
                analytical_goal=str(payload.get("analytical_goal") or query_input.query).strip(),
                analysis_type=str(payload.get("analysis_type") or "historical_overview").strip(),
                metrics=_as_str_list(payload.get("metrics"), []),
                required_columns=_as_str_list(payload.get("required_columns"), []),
                data_requirements=_as_str_list(payload.get("data_requirements"), []),
                output_requirements=_as_str_list(payload.get("output_requirements"), []),
                presentation_preferences=_as_str_list(payload.get("presentation_preferences"), []),
                reasoning=str(payload.get("reasoning") or "").strip(),
            ),
            [],
        )
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo interpretar la consulta con LLM: {exc}") from exc


def build_llm_code(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    input_payload: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    """Llama al Agente 3 y extrae el script Python de su respuesta."""
    # Esta funcion ya no devuelve un objeto de dominio, sino codigo ejecutable.
    # Aun asi mantenemos la misma disciplina:
    # - pedimos JSON
    # - parseamos
    # - extraemos el campo "code"
    # - extraemos el script que el workflow tratara despues como artefacto
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para usar openai/gpt-oss-20b sobre vLLM.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para generacion de codigo.")
        messages = build_codegen_messages(query_input, plan, input_payload=input_payload)
        last_error: Exception | None = None
        code = ""
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                code = _code_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Devuelve de nuevo un objeto JSON estricto con un unico campo code.",
                    )
                ]
        if not code:
            raise LLMClientError(str(last_error))
        return code, []
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo generar codigo con LLM: {exc}") from exc


def build_llm_code_validation(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    generated_code: str,
    input_payload: dict[str, Any] | None = None,
) -> tuple[CodeValidationDecision, list[str]]:
    """Llama al Agente 4 y devuelve su decision estructurada."""
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para validar codigo con LLM.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para validacion de codigo.")
        messages = build_code_validation_messages(
            query_input,
            plan,
            generated_code,
            input_payload=input_payload,
        )
        last_error: Exception | None = None
        payload = None
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                payload = _json_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La respuesta anterior no fue JSON valido. Devuelve de nuevo exclusivamente un objeto JSON valido con decision, errors, warnings, required_fixes y reasoning.",
                    )
                ]
        if payload is None:
            raise LLMClientError(str(last_error))
        normalized_payload = _normalize_code_validation_payload(payload)
        return CodeValidationDecision.from_dict(normalized_payload), []
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo validar codigo con LLM: {exc}") from exc


def repair_llm_code(
    query_input: FinancialQueryInput,
    plan: AnalysisPlan,
    previous_code: str,
    error_detail: str,
    input_payload: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    """Llama a la reparación de código usando el detalle observable del fallo."""
    # Esta funcion se activa cuando el flujo detecta un problema reparable:
    # - rechazo del validador de codigo
    # - error real al ejecutar el script
    #
    # El patron es siempre el mismo: error observable -> feedback al LLM ->
    # script completo corregido -> nueva validacion en el flujo.
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para usar openai/gpt-oss-20b sobre vLLM.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para reparar codigo.")
        messages = build_code_repair_messages(
            query_input,
            plan,
            previous_code,
            error_detail,
            input_payload=input_payload,
        )
        last_error: Exception | None = None
        code = ""
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                code = _code_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La reparacion anterior no fue JSON valido. Devuelve de nuevo un objeto JSON estricto con un unico campo code.",
                    )
                ]
        if not code:
            raise LLMClientError(str(last_error))
        return code, ["Se reparo codigo generado tras un error previo."]
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo reparar codigo con LLM: {exc}") from exc


def repair_llm_execution_code(
    query_input: FinancialQueryInput,
    previous_code: str,
    error_detail: str,
    input_payload: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    """Llama al Subagente 4 usando el error real observado al ejecutar."""
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError(
            "Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para reparar errores de ejecucion con LLM."
        )

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para reparar errores de ejecucion.")
        messages = build_execution_repair_messages(
            query_input,
            previous_code,
            error_detail,
            input_payload=input_payload,
        )
        last_error: Exception | None = None
        code = ""
        for _attempt in range(MAX_LLM_ATTEMPTS):
            try:
                response = client.complete_json(messages)
                code = _code_from_text(response.content)
                break
            except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
                messages = messages + [
                    messages[-1].__class__(
                        "user",
                        "La reparacion anterior no fue JSON valido. Devuelve de nuevo un objeto JSON estricto con un unico campo code.",
                    )
                ]
        if not code:
            raise LLMClientError(str(last_error))
        return code, ["Se reparo codigo tras un error de ejecucion."]
    except (LLMClientError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise LLMClientError(f"No se pudo reparar el codigo tras un error de ejecucion: {exc}") from exc


def build_llm_interpretation(interpretation_payload: dict[str, Any]) -> tuple[str, list[str]]:
    """Llama al Agente 5 y fuerza una salida textual utilizable como respuesta final."""
    # A diferencia de Agente 1, 2 y 3, aqui si queremos texto natural.
    # Por eso esta funcion usa complete_text y luego comprueba que el modelo no
    # haya devuelto JSON puro por error.
    #
    # Importante: esta capa no valida si la lectura financiera es "buena" o
    # "mala". Solo impone controles minimos para que la salida sea texto
    # utilizable por el workflow y no un blob JSON crudo o una respuesta vacia.
    llm_config = LLMConfig.from_env()
    if not llm_config.is_configured:
        raise LLMClientError("Falta configurar VLLM_API_KEY/OPENAI_API_KEY o LLM_API_KEY para usar openai/gpt-oss-20b sobre vLLM.")

    try:
        client = create_llm_client(llm_config)
        if client is None:
            raise LLMClientError("No se pudo crear el cliente LLM para interpretacion.")
        messages = build_interpretation_messages(interpretation_payload)
        last_answer = ""
        for attempt in range(MAX_LLM_ATTEMPTS):
            response = client.complete_text(messages)
            answer = response.content.strip()
            if not answer:
                raise LLMClientError("El LLM devolvio una respuesta vacia.")
            if not _is_json_only_answer(answer):
                warnings = []
                if attempt:
                    # Si llega aqui con attempt>0, significa que el primer intento
                    # devolvio JSON y hubo que pedir una reformulacion textual.
                    warnings.append("Se regenero la interpretacion porque la respuesta anterior era JSON puro.")
                return answer, warnings
            last_answer = answer
            messages = messages + [
                messages[-1].__class__(
                    "user",
                    "La respuesta anterior fue JSON puro. Devuelve una interpretacion textual en espanol, "
                    "con frases completas, basada solo en user_query, resolved_context, execution_output y warnings.",
                )
            ]
        raise LLMClientError(
            "El LLM devolvio JSON puro en vez de una interpretacion textual. "
            f"Ultima respuesta: {last_answer[:300]}"
        )
    except LLMClientError as exc:
        raise LLMClientError(f"No se pudo obtener interpretacion LLM: {exc}") from exc
