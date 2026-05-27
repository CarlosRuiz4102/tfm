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

    completed = subprocess.run(
        [EXECUTION_CONFIG.python_executable, str(script_path), str(payload_path)],
        capture_output=True,
        cwd=ROOT_DIR,
        env=env,
        text=True,
        timeout=EXECUTION_CONFIG.timeout_seconds,
        check=False,
    )

    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    parsed_output = None
    if completed.stdout.strip():
        try:
            parsed_output = json.loads(completed.stdout)
        except json.JSONDecodeError:
            parsed_output = {"raw_stdout": completed.stdout}

    artifacts = ExecutionArtifacts(
        script_path=str(script_path),
        payload_path=str(payload_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
    )
    return ExecutionResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
        parsed_output=parsed_output,
        artifacts=artifacts,
    )
