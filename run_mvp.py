from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.examples.sample_inputs import SAMPLE_INPUTS
from src.graph.build_graph import build_workflow
from src.schemas import FinancialQueryInput


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def load_input(args: argparse.Namespace) -> FinancialQueryInput:
    if args.example:
        return FinancialQueryInput.from_dict(SAMPLE_INPUTS[args.example])
    if args.input_json:
        payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
        return FinancialQueryInput.from_dict(payload)
    raise ValueError("Debes usar --example o --input-json.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta el MVP financiero multiagente.")
    parser.add_argument("--example", choices=sorted(SAMPLE_INPUTS))
    parser.add_argument("--input-json")
    args = parser.parse_args()

    query_input = load_input(args)
    workflow = build_workflow()
    result = workflow.invoke(query_input)

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
