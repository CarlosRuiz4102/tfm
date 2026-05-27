from __future__ import annotations

import ast
from dataclasses import dataclass, field


ALLOWED_IMPORTS = {"__future__", "json", "sys", "pathlib", "math", "statistics", "pandas", "numpy", "src"}
BLOCKED_CALLS = {"eval", "exec", "compile", "open", "input", "__import__"}
BLOCKED_MODULES = {"os", "subprocess", "shutil", "socket", "requests", "urllib", "httpx"}


@dataclass
class CodeSecurityResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_generated_code(code: str) -> CodeSecurityResult:
    errors: list[str] = []
    if "def main(" not in code:
        errors.append("El script debe definir una funcion main().")
    if "json.dumps" not in code:
        errors.append("El script debe escribir JSON con json.dumps.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return CodeSecurityResult(False, [f"Codigo Python no valido: {exc}"])

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module not in ALLOWED_IMPORTS:
                    errors.append(f"Import no permitido: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            if module not in ALLOWED_IMPORTS:
                errors.append(f"Import no permitido: {node.module}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                errors.append(f"Llamada no permitida: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in BLOCKED_MODULES:
                    errors.append(f"Uso de modulo no permitido: {node.func.value.id}")

    return CodeSecurityResult(not errors, errors)
