from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import EXECUTION_CONFIG, RESULTS_CODE_DIR, RESULTS_LOGS_DIR, ROOT_DIR
from src.schemas import ExecutionArtifacts, ExecutionResult


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def run_generated_code(code: str, payload: dict[str, Any]) -> ExecutionResult:
    """
    Ejecuta el script generado y persiste la evidencia del intento.

    Esta funcion solo lanza el proceso y recoge artefactos. La decision de si el intento fue valido, reparable 
    o bloqueado pertenece a la validacion de la parte 4, no al runner.
    """
    RESULTS_CODE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    run_id = _timestamp()
    script_path = RESULTS_CODE_DIR / f"generated_{run_id}.py"
    payload_path = RESULTS_LOGS_DIR / f"payload_{run_id}.json"
    stdout_path = RESULTS_LOGS_DIR / f"stdout_{run_id}.json"
    stderr_path = RESULTS_LOGS_DIR / f"stderr_{run_id}.log"

    script_path.write_text(code, encoding="utf-8")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT_DIR) if not existing_pythonpath else f"{ROOT_DIR}{os.pathsep}{existing_pythonpath}"

    stdout = ""
    stderr = ""
    returncode: int | None = None
    timed_out = False
    launch_error: str | None = None

    try:
        completed = subprocess.run(
            [EXECUTION_CONFIG.python_executable, str(script_path), str(payload_path)],
            capture_output=True,
            cwd=ROOT_DIR,
            env=env,
            text=True,
            timeout=EXECUTION_CONFIG.timeout_seconds,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        # Guardamos la evidencia del timeout igual que cualquier otro intento
        # para que el subagente pueda repararlo con trazas reales.
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if stderr and not stderr.endswith("\n"):
            stderr += "\n"
        stderr += f"Tiempo maximo de ejecucion superado ({EXECUTION_CONFIG.timeout_seconds}s)."
    except OSError as exc:
        # Si el proceso ni siquiera puede lanzarse, lo tratamos como error
        # observable de infraestructura para que el workflow pueda bloquear o
        # reparar con un mensaje entendible.
        launch_error = f"No se pudo lanzar el script generado: {exc}"
        stderr = launch_error

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    parsed_output = None
    if stdout.strip():
        try:
            parsed_output = json.loads(stdout)
        except json.JSONDecodeError:
            parsed_output = None

    artifacts = ExecutionArtifacts(
        script_path=str(script_path),
        payload_path=str(payload_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )
    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        parsed_output=parsed_output,
        artifacts=artifacts,
        timed_out=timed_out,
        launch_error=launch_error,
    )
