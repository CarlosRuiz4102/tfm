# Trazabilidad de la parte del validador de codigo

## Objetivo

Este documento no resume la parte 3 de forma general.
La idea aqui es ver una ejecucion controlada de esta fase para entender:

- como se conecta la parte 2 con la parte 3;
- que entra exactamente al Agente 4;
- que decision devuelve;
- como actua el Subagente 3 cuando el caso es reparable;
- que estado queda listo antes de la ejecucion.

## Como se conectan la parte 2 y la parte 3

La conexion entre ambas partes se considera buena cuando la parte 3 no recibe
solo un script aislado, sino un bloque coherente formado por:

- `state.analysis_plan`
- `state.generated_code`
- el mismo `input` compacto que ya conocian Agente 2 y Agente 3
- el contexto de descarga heredado de la fase de datos

Esto es importante porque el Agente 4 no valida codigo "en vacio".
Lo valida contra:

- la consulta original;
- el contexto de datos ya resuelto;
- el contrato analitico decidido en la parte 2;
- el script que el Agente 3 ha generado a partir de ese contrato.

Si esa cadena se conserva bien, la parte 3 puede decidir con bastante claridad
si el codigo encaja con el plan o no.

## Caso trazado

Consulta usada:

```text
Dame una vision general de AAPL en 3 meses
```

Tipo de traza:

- la fase de datos se simulo reutilizando un CSV congelado del proyecto;
- el Agente 2 se simulo con un `AnalysisPlan` valido;
- el Agente 3 se simulo primero con un script defectuoso;
- el Agente 4 se simulo con una decision `repairable`;
- el Subagente 3 devolvio un script corregido;
- el Agente 4 valido de nuevo y marco `valid`.

Esto permite ver la logica real de la parte 3 sin depender del LLM ni de red.

## Flujo exacto que se ejecuta

Desde que termina la parte 2 hasta dejar el codigo validado, el recorrido es:

1. `llm_analysis_node(...)`
2. `code_generation_node(...)`
3. `code_validation_node(...)`

Dentro de esos nodos, las funciones relevantes que participan son:

1. `_build_phase2_input_payload(...)`
2. `build_llm_analysis(...)`
3. `build_llm_code(...)`
4. `build_llm_code_validation(...)`
5. `_build_code_validation_feedback(...)`
6. `repair_llm_code(...)`

## Entrada real a la parte 3

Cuando termina la parte 2, el estado ya contiene:

```json
{
  "status": "code_generated",
  "analysis_plan": {
    "analytical_goal": "Describir AAPL en 3 meses.",
    "analysis_type": "historical_overview",
    "metrics": ["ultimo_cierre"],
    "required_columns": ["Date", "Close"],
    "data_requirements": ["CSV historico normalizado"],
    "output_requirements": ["JSON con metrics, summary y limitations"],
    "presentation_preferences": ["respuesta breve"],
    "reasoning": "La consulta pide una vision general simple."
  },
  "generated_code": "print('mal')"
}
```

Interpretacion:

- la parte 2 ya ha fijado el contrato analitico;
- el Agente 3 ya ha producido un script;
- la parte 3 todavia no sabe si ese script puede aceptarse.

## Paso 1. Reutilizacion del handoff de la parte 2

Funcion usada:

```python
_build_phase2_input_payload(state)
```

La parte 3 no construye un contexto nuevo desde cero.
Reutiliza el mismo handoff compacto que ya venia de la parte 2.

Salida real del handoff compartido:

```json
{
  "query": "Dame una vision general de AAPL en 3 meses",
  "tickers": ["AAPL"],
  "temporal_context": {
    "start": null,
    "end": null,
    "period": "3mo",
    "interval": "1d"
  },
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_id.csv"
  ],
  "data_context": {
    "row_count": 60,
    "available_columns": [
      "Date",
      "Ticker",
      "Open",
      "High",
      "Low",
      "Close",
      "Adj Close",
      "Volume"
    ]
  },
  "warnings": []
}
```

Que significa:

- el Agente 4 ve el mismo contexto operativo que Agente 2 y Agente 3;
- la validacion se hace sobre la misma base que la generacion;
- no aparece una reinterpretacion oculta entre fases.

## Paso 2. `code_validation_node`

Funcion del nodo:

```python
code_validation_node(state)
```

Que hace internamente:

1. comprueba que existen `analysis_plan` y `generated_code`;
2. marca el estado como `code_validating`;
3. llama a `build_llm_code_validation(...)`;
4. guarda la decision en `state.code_validation_decision`;
5. decide si continuar, reparar o bloquear.

## Decision observada del Agente 4

Primera salida observada en esta traza controlada:

```json
{
  "decision": "repairable",
  "errors": [
    "La salida no sigue el formato esperado."
  ],
  "warnings": [],
  "required_fixes": [
    "Devolver metrics, summary y limitations."
  ],
  "reasoning": "El script puede corregirse sin rehacer el plan analitico."
}
```

Interpretacion:

- el Agente 4 no acepta el script tal como esta;
- tampoco bloquea directamente la ejecucion;
- describe una correccion concreta y activa al Subagente 3.

## Paso 3. Construccion del feedback para el subagente

Funcion usada:

```python
_build_code_validation_feedback(state)
```

Esta funcion compacta la decision del Agente 4 para pasarla al subagente sin
meter logica extra en el prompt.

Feedback generado para el subagente:

```text
decision=repairable
reasoning=El script puede corregirse sin rehacer el plan analitico.
errors=La salida no sigue el formato esperado.
required_fixes=Devolver metrics, summary y limitations.
```

## Paso 4. `repair_llm_code(...)`

El Subagente 3 recibe:

- la consulta original;
- el contexto de entrada;
- el `AnalysisPlan`;
- el script anterior;
- el feedback compacto del Agente 4.

Y devuelve un script completo nuevo.

Script corregido observado en esta traza:

```python
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = {
        "metrics": {"tickers": payload["tickers"]},
        "summary": "ok",
        "limitations": [],
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

## Paso 5. Segunda validacion del Agente 4

Despues de la correccion, `code_validation_node(...)` vuelve a llamar a
`build_llm_code_validation(...)`.

Segunda salida observada:

```json
{
  "decision": "valid",
  "errors": [],
  "warnings": [],
  "required_fixes": [],
  "reasoning": "La version corregida ya puede continuar."
}
```

Cambio de estado:

```text
code_generated
-> code_validating
-> code_repairing
-> code_validated
```

## Estado final al salir de la parte 3

Estado al salir del nodo:

```json
{
  "status": "code_validated",
  "code_repair_attempts": 1,
  "code_validation_decision": {
    "decision": "valid",
    "errors": [],
    "warnings": [],
    "required_fixes": [],
    "reasoning": "La version corregida ya puede continuar."
  },
  "generated_code": "script corregido y aceptado"
}
```

Interpretacion:

- el codigo no se ejecuto directamente tras generarse;
- el Agente 4 emitio una decision estructurada;
- el Subagente 3 corrigio el script;
- el Agente 4 revalido esa correccion;
- la parte 3 dejo el codigo listo para pasar al ejecutor.

## Que recibe despues la ejecucion

Cuando la parte 3 termina bien, la siguiente fase recibe:

- `state.generated_code`
- `state.analysis_plan`
- `state.code_validation_decision`
- el payload de ejecucion compacto con `query`, `tickers`, `temporal_context`,
  `csv_paths`, `data_context`, `warnings` y `download_summary`

Por eso puede decirse que la conexion parte 2 -> parte 3 esta bien resuelta:

1. la parte 2 entrega plan y codigo;
2. la parte 3 valida ese codigo contra el mismo contexto compartido;
3. solo despues se permite avanzar a ejecucion.
