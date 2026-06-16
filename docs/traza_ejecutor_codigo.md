# Trazabilidad de la parte del ejecutor de codigo

## Objetivo

Este documento no resume la parte 4 de forma general.
La idea aqui es seguir una ejecucion comentada de esta fase para entender:

- como se conecta la parte 3 con la parte 4;
- que recibe realmente el ejecutor;
- que funciones participan;
- como se decide si un intento es `valid`, `repairable` o `blocked`;
- como actua el Subagente 4;
- y que artefactos quedan escritos en disco.

## Como se conectan la parte 3 y la parte 4

La conexion entre ambas partes debe entenderse asi:

1. La parte 3 entrega un script ya aceptado por el Agente 4.
2. La parte 4 no vuelve a validarlo de forma estatica.
3. La parte 4 lo ejecuta de verdad y observa el resultado.
4. Si falla, el Subagente 4 corrige ese fallo usando la evidencia real de runtime.
5. La unica forma de confirmar que la correccion funciona es volver a pasar por el ejecutor.

La conexion esta bien hecha cuando se cumplen estas reglas:

- la parte 3 entrega `state.generated_code` en estado `code_validated`;
- la parte 4 recibe ese script y el contexto operativo ya resuelto;
- la parte 4 no mete `analysis_plan` dentro del payload de ejecucion;
- la parte 4 decide por evidencia observable, no por una opinion adicional del workflow;
- el Subagente 4 solo propone una nueva version del script;
- el ejecutor confirma o desmiente esa reparacion en el siguiente intento.

## Caso trazado

Consulta usada:

```text
Dame una vision general de AAPL en 3 meses
```

La traza se ha construido de forma controlada para ver bien la logica de la parte 4:

- la fase de datos se simulo con un `FinancialDataRequest` correcto;
- el analista y el generador se simularon para producir un script;
- la validacion estatica de la parte 3 acepto el codigo;
- el primer intento de ejecucion fallo;
- el Subagente 4 devolvio una version corregida;
- el segundo intento de ejecucion ya fue valido.

Esto permite ver la conexion real entre parte 3 y parte 4 sin depender de LLM real ni de red.

## Flujo exacto que se ejecuta

Desde que termina bien la parte 3 hasta que la parte 4 deja una salida valida, el recorrido es este:

1. `code_validation_node(...)`
2. `code_execution_node(...)`
3. `_build_phase2_input_payload(...)`
4. `run_generated_code(...)`
5. `validate_execution_result(...)`
6. `_build_execution_repair_feedback(...)`
7. `repair_llm_execution_code(...)`
8. `run_generated_code(...)` otra vez
9. `validate_execution_result(...)` otra vez

## Punto de entrada real a la parte 4

Cuando la parte 3 termina bien, el estado ya contiene como minimo:

- `state.generated_code`
- `state.code_validation_decision`
- `state.csv_paths`
- `state.normalized_query`
- `state.download_summary`

Lo importante aqui es esto:

- la parte 4 si recibe `generated_code`;
- la parte 4 no usa `analysis_plan` dentro del payload que se lanza al script.

## Paso 0. Salida correcta de la parte 3

La parte 3 deja el workflow en este tipo de estado:

```json
{
  "status": "code_validated",
  "generated_code": "script Python completo",
  "code_validation_decision": {
    "decision": "valid",
    "errors": [],
    "warnings": [],
    "required_fixes": [],
    "reasoning": "El codigo puede continuar."
  }
}
```

Que significa:

- el Agente 4 ya acepto el script;
- la parte 4 puede ejecutarlo;
- si falla, el problema ya no es estatico sino de runtime.

## Paso 1. Construccion del payload operativo

Dentro de `code_execution_node(...)` se construye un payload como este:

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
  "warnings": [],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["AAPL"],
    "tickers_found": ["AAPL"]
  }
}
```

Punto importante:

- la parte 4 solo trabaja con contexto operativo real de ejecucion.

## Paso 2. Primer intento de ejecucion

Funcion usada:

```python
execution = run_generated_code(state.generated_code, execution_payload)
```

En esta traza, el primer script falla a proposito con un `KeyError`.

Salida observada del runner en este primer intento:

```json
{
  "stdout": "",
  "stderr": "Traceback ... KeyError: 'AAPL'",
  "returncode": 1,
  "parsed_output": null,
  "timed_out": false,
  "launch_error": null
}
```

Artefactos que se escriben:

- `results/code/generated_<run_id>.py`
- `results/logs/payload_<run_id>.json`
- `results/logs/stdout_<run_id>.json`
- `results/logs/stderr_<run_id>.log`

## Paso 3. Validacion del primer intento

Funcion usada:

```python
decision = validate_execution_result(execution)
```

La parte 4 responde aqui a dos preguntas:

1. El script se ejecuto correctamente como proceso?
2. La salida generada esta en una forma correcta para que la parte 5 pueda trabajar bien con ella?

Como el proceso fallo con `returncode != 0`, la decision es:

```json
{
  "decision": "repairable",
  "errors": [
    "La ejecucion termino con returncode=1. stderr: Traceback ... KeyError: 'AAPL'"
  ],
  "warnings": [],
  "reasoning": "El script fallo durante la ejecucion real y necesita una correccion antes de reintentarse."
}
```

Interpretacion:

- la parte 4 no puede continuar;
- pero la decision sigue dentro de la rama `repairable`;
- por tanto entra el Subagente 4.

## Paso 4. Construccion del feedback para el Subagente 4

Funcion usada:

```python
_build_execution_repair_feedback(state)
```

Esta funcion compacta la evidencia del fallo real en un texto como este:

```text
execution_attempt=1
decision=repairable
reasoning=El script fallo durante la ejecucion real y necesita una correccion antes de reintentarse.
errors=La ejecucion termino con returncode=1. stderr: Traceback ... KeyError: 'AAPL'
returncode=1
stderr=Traceback ... KeyError: 'AAPL'
```

La idea es importante:

- el Subagente 4 no recibe una orden vaga de "arregla el codigo";
- recibe el error exacto que ha ocurrido en runtime.

## Paso 5. Subagente 4

Funcion usada:

```python
repair_llm_execution_code(
    query_input,
    state.generated_code,
    _build_execution_repair_feedback(state),
    input_payload=execution_payload,
)
```

El Subagente 4 recibe:

- la consulta original;
- el contexto operativo de ejecucion;
- el codigo anterior;
- el error real observado;
- el contrato de salida del workflow.

Y devuelve:

```json
{
  "code": "script Python completo corregido"
}
```

Punto clave de arquitectura:

- el Subagente 4 no certifica que el codigo ya este bien;
- solo propone una nueva version;
- la validacion real vendra al volver al ejecutor.

## Paso 6. Segundo intento de ejecucion

El workflow sustituye:

```python
state.generated_code = repaired_code
```

Y vuelve a entrar en:

```python
execution = run_generated_code(state.generated_code, execution_payload)
```

En esta traza, el segundo script ya produce una salida correcta:

```json
{
  "metrics": {
    "tickers": ["AAPL"],
    "csv_count": 1
  },
  "summary": "reparado",
  "limitations": []
}
```

Salida observada del runner en este segundo intento:

```json
{
  "stdout": "{\"metrics\": {\"tickers\": [\"AAPL\"], \"csv_count\": 1}, \"summary\": \"reparado\", \"limitations\": []}",
  "stderr": "",
  "returncode": 0,
  "parsed_output": {
    "metrics": {
      "tickers": ["AAPL"],
      "csv_count": 1
    },
    "summary": "reparado",
    "limitations": []
  }
}
```

## Paso 7. Validacion del segundo intento

`validate_execution_result(...)` revisa ahora:

- que el proceso termino bien;
- que `stdout` es JSON parseable;
- que existen `metrics`, `summary` y `limitations`;
- que `summary` no viene vacio;
- que la salida ya sirve para la siguiente fase.

La decision resultante es:

```json
{
  "decision": "valid",
  "errors": [],
  "warnings": [],
  "reasoning": "El script se ejecuto correctamente y dejo una salida estructurada util para la siguiente fase."
}
```

## Estado final de la parte 4

Al terminar esta traza, el estado relevante del workflow queda asi:

```json
{
  "status": "executed",
  "execution_attempts": 2,
  "execution_repair_attempts": 1,
  "execution_returncode": 0,
  "execution_output": {
    "metrics": {
      "tickers": ["AAPL"],
      "csv_count": 1
    },
    "summary": "reparado",
    "limitations": []
  },
  "execution_validation_decision": {
    "decision": "valid",
    "errors": [],
    "warnings": [],
    "reasoning": "El script se ejecuto correctamente y dejo una salida estructurada util para la siguiente fase."
  }
}
```

Interpretacion:

- la parte 3 entrego un script estaticamente aceptado;
- la parte 4 detecto un fallo real de ejecucion;
- el Subagente 4 corrigio ese fallo;
- el ejecutor confirmo en el siguiente intento que la salida ya era valida.

## Que demuestra esta traza

Esta traza demuestra varias cosas importantes sobre la conexion entre parte 3 y parte 4:

1. La parte 3 y la parte 4 no hacen lo mismo.
2. Un script aceptado estaticamente todavia puede fallar en runtime.
3. La parte 4 no necesita `analysis_plan` dentro del payload de ejecucion.
4. El Subagente 4 trabaja con evidencia real de ejecucion, no con una evaluacion separada del workflow.
5. La unica confirmacion fuerte de una reparacion es volver a ejecutar.

## Resumen operativo final

Si lo bajamos a lenguaje muy directo, esta parte hace esto:

1. recibe un script ya aceptado por la parte 3;
2. le construye un payload operativo;
3. lo ejecuta y guarda la evidencia;
4. decide si la ejecucion sirve o no;
5. si falla de forma reparable, activa al Subagente 4;
6. vuelve a ejecutar el nuevo script;
7. solo continua cuando el propio ejecutor confirma una salida valida.

Esa es precisamente la razon de ser de la parte 4:

- no volver a pensar el analisis;
- sino comprobar si el codigo realmente funciona dentro del workflow.
