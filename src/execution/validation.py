from __future__ import annotations

from src.schemas.execution import ExecutionResult, ExecutionValidationDecision


REQUIRED_EXECUTION_OUTPUT_KEYS = {"metrics", "summary", "limitations"}


def validate_execution_result(result: ExecutionResult) -> ExecutionValidationDecision:
    """
    Decide si un intento de ejecucion deja una salida util para el workflow.

    Esta validacion no vuelve a pensar el problema analitico. Solo observa si
    el script se ejecuto bien y si su salida sirve para que la siguiente fase
    pueda trabajar con ella sin ambiguedades.
    """
    warnings: list[str] = []

    if result.launch_error:
        return ExecutionValidationDecision(
            decision="repairable",
            errors=[result.launch_error],
            warnings=[],
            reasoning="El proceso no pudo lanzarse correctamente y hace falta corregir el script o su comportamiento de arranque.",
        )

    if result.timed_out:
        return ExecutionValidationDecision(
            decision="repairable",
            errors=["La ejecucion supero el tiempo maximo permitido."],
            warnings=[],
            reasoning="El script no termino a tiempo. El caso parece recuperable si se simplifica o corrige la implementacion.",
        )

    if result.returncode is None:
        return ExecutionValidationDecision(
            decision="repairable",
            errors=["La ejecucion no devolvio un codigo de retorno interpretable."],
            warnings=[],
            reasoning="No existe una confirmacion util del proceso y conviene tratar el caso como fallo reparable.",
        )

    if result.returncode != 0:
        stderr = result.stderr.strip() or "sin detalle adicional en stderr"
        return ExecutionValidationDecision(
            decision="repairable",
            errors=[f"La ejecucion termino con returncode={result.returncode}. stderr: {stderr}"],
            warnings=[],
            reasoning="El script fallo durante la ejecucion real y necesita una correccion antes de reintentarse.",
        )

    if not result.stdout.strip():
        return ExecutionValidationDecision(
            decision="repairable",
            errors=["El script termino sin error, pero stdout vino vacio."],
            warnings=[],
            reasoning="La salida no sirve todavia para el workflow porque no existe un JSON utilizable.",
        )

    if result.parsed_output is None:
        return ExecutionValidationDecision(
            decision="repairable",
            errors=["stdout no es JSON parseable."],
            warnings=[],
            reasoning="El proceso ha corrido, pero la salida no respeta el contrato estructurado que necesita la siguiente fase.",
        )

    if not isinstance(result.parsed_output, dict):
        return ExecutionValidationDecision(
            decision="repairable",
            errors=["El JSON de salida no es un objeto con claves de primer nivel."],
            warnings=[],
            reasoning="La siguiente fase espera un artefacto estructurado por claves, no una lista ni un valor escalar.",
        )

    output = result.parsed_output
    errors: list[str] = []
    missing_keys = sorted(REQUIRED_EXECUTION_OUTPUT_KEYS.difference(output.keys()))
    if missing_keys:
        errors.append(
            "Faltan claves obligatorias en la salida: " + ", ".join(missing_keys) + "."
        )

    summary = output.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary debe existir como texto no vacio.")

    if "limitations" in output and not isinstance(output.get("limitations"), list):
        errors.append("limitations debe existir como lista.")

    if "metrics" in output and output.get("metrics") is None:
        errors.append("metrics no puede ser null.")

    if errors:
        return ExecutionValidationDecision(
            decision="repairable",
            errors=errors,
            warnings=[],
            reasoning="La salida existe, pero todavia no cumple el contrato minimo que necesita la siguiente fase.",
        )

    if result.stderr.strip():
        # Conservamos el aviso porque stderr no vacio puede ser una pista util
        # de fragilidad aunque el contrato principal se haya cumplido.
        warnings.append(
            "La ejecucion produjo stderr no vacio pese a terminar con returncode 0."
        )

    return ExecutionValidationDecision(
        decision="valid",
        errors=[],
        warnings=warnings,
        reasoning="El script se ejecuto correctamente y dejo una salida estructurada util para la siguiente fase.",
    )
