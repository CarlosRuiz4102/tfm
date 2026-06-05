# Entrada del ejemplo A

La entrada se toma de `src/examples/sample_inputs.py`.

Entrada conceptual:

```json
{
  "query": "Cuanto ha crecido Nvidia en 5 años",
  "tickers": ["NVDA"],
  "start": null,
  "end": null,
  "period": "5y",
  "interval": "1d",
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\data\\raw\\cunto_ha_crecido_nvidia_en_5_aos.csv"
  ],
  "warnings": []
}
```

Qué debes entender:

- `query` es lo que pregunta el usuario.
- `tickers` indica los activos financieros que se esperan en los CSV.
- `period` e `interval` describen la ventana temporal usada al descargar los datos.
- `csv_paths` apunta a los datos congelados. En este MVP, la ejecución no descarga datos nuevos durante el cálculo.

## Paso 0: run_mvp.py

Archivo: `run_mvp.py`.

Hace tres cosas:

1. Lee argumentos con `argparse`.
2. Si se usa `--example growth_nvda`, carga `SAMPLE_INPUTS["growth_nvda"]`.
3. Construye el workflow con `build_workflow()` y lo invoca.

Fragmento clave:

```python
query_input = load_input(args)
workflow = build_workflow()
result = workflow.invoke(query_input)
```

Salida final:

```python
print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
```

Esto significa que el programa imprime todo el estado final del workflow, no solo la respuesta para el usuario.

## Paso 1: FinancialQueryInput

Archivo: `src/schemas.py`.

La entrada se convierte en un objeto `FinancialQueryInput`.

Campos importantes:

```text
query
tickers
csv_paths
start
end
period
interval
needs_clarification
warnings
```

Función relevante:

```python
FinancialQueryInput.from_dict(...)
```

Esta función normaliza listas y convierte rutas a texto.

Qué debes poder explicar:

`FinancialQueryInput` es el contrato de entrada. Evita pasar diccionarios sueltos sin estructura por todo el sistema.

## Paso 2: WorkflowState

Archivo: `src/schemas.py`.

Antes de ejecutar los nodos, se crea un `WorkflowState`.

Contiene:

```text
user_query
normalized_query
csv_paths
analysis_plan
generated_code
execution_stdout
execution_stderr
execution_returncode
execution_output
execution_artifacts
final_answer
warnings
error_message
status
```

Estado inicial:

```text
status = "created"
analysis_plan = None
generated_code = None
execution_output = None
final_answer = ""
```

Qué debes poder explicar:

`WorkflowState` es la memoria compartida del flujo. Cada nodo lee parte del estado, escribe nuevos campos y cambia `status`.

## Paso 3: ingest_node

Archivo: `src/graph/nodes.py`.

Función:

```python
ingest_node(state)
```

Llama a:

```python
validate_input(query_input)
```

Archivo de validación:

```text
src/graph/validation.py
```

Comprueba:

- Que la query no esté vacía.
- Que exista al menos un ticker.
- Que exista al menos una ruta CSV.
- Que `start` y `end`, si existen, tengan formato `YYYY-MM-DD`.
- Que cada CSV exista realmente.

Para este caso, la validación real fue:

```json
{
  "status": "valid",
  "errors": []
}
```

Cambio de estado:

```text
created -> ingested
```

Qué se genera:

Nada en disco. Solo se actualiza el estado en memoria.

## Paso 4: llm_analysis_node

Archivo: `src/graph/nodes.py`.

Función:

```python
llm_analysis_node(state)
```

Llama a:

```python
build_llm_analysis(query_input)
```

Archivo:

```text
src/llm/pipeline.py
```

Este paso llama al Agente 1.

Objetivo del Agente 1:

Convertir la pregunta del usuario en un plan analítico. No calcula cifras. No redacta la respuesta final.

Prompt construido en:

```text
src/llm/prompts.py
```

El prompt obliga al LLM a devolver JSON con:

```text
analysis_level
analytical_goal
analysis_type
metrics
required_columns
data_requirements
output_requirements
presentation_preferences
reasoning
```

Salida real del Agente 1 en la traza:

```json
{
  "analysis_level": "A",
  "analytical_goal": "Calcular el crecimiento total y la tasa de crecimiento anual compuesta (CAGR) de Nvidia (NVDA) durante los últimos 5 años.",
  "analysis_type": "historical_financial_analysis",
  "metrics": ["retorno_total", "cagr"],
  "required_columns": ["Close"],
  "data_requirements": [
    "Periodo: 5 años completos desde la fecha más antigua disponible hasta la fecha más reciente en el CSV.",
    "Intervalo: diario (1d).",
    "Activo: NVDA.",
    "Validación mínima: al menos 5 años de datos continuos sin periodos de datos faltantes mayores a 5 días consecutivos."
  ],
  "output_requirements": [
    "JSON con los valores numéricos de retorno_total y CAGR.",
    "Formato: {\"retorno_total\": <float>, \"cagr\": <float>}"
  ],
  "presentation_preferences": [
    "Tono: breve y directo.",
    "Estructura: solo los valores numéricos sin texto adicional."
  ],
  "reasoning": "La consulta solicita únicamente el crecimiento de un activo en un periodo fijo, sin comparaciones ni métricas adicionales. Por lo tanto, se asigna nivel A y se incluyen solo las métricas esenciales."
}
```

Cambio de estado:

```text
ingested -> planned
```

Qué se genera:

Nada en disco. Se rellena `state.analysis_plan`.

Qué debes poder defender:

El nivel A se justifica porque la pregunta es directa: un activo, una ventana temporal, métricas básicas. No pide tabla, gráfica ni análisis multicriterio.

## Paso 5: code_generation_node

Archivo: `src/graph/nodes.py`.

Función:

```python
code_generation_node(state)
```

Llama a:

```python
build_llm_code(query_input, plan)
```

Este paso llama al Agente 2.

Objetivo del Agente 2:

Generar un script Python completo que lea un payload desde `argv[1]`, calcule con los CSV indicados y escriba un único JSON por stdout.

Restricciones importantes del prompt:

- Debe definir `main()`.
- Debe usar `Path(sys.argv[1]).read_text(...)`.
- No debe usar `open()`.
- Debe usar `load_close_prices` o `load_market_data`.
- No debe usar red, rutas externas, `os`, `subprocess`, `eval` ni `exec`.
- Debe devolver `analysis_type`, `analysis_level`, `metrics`, `summary` y `limitations`.
- Debe pasar la salida por `make_json_safe`.

En la traza real hubo un primer intento inválido:

```json
{
  "attempt": "1",
  "error": "Expecting value: line 1 column 1 (char 0)",
  "raw_response_start": ""
}
```

Eso significa que el LLM devolvió algo que no se pudo interpretar como JSON válido. El pipeline vuelve a pedir una respuesta válida hasta un máximo de 3 intentos.

Código generado finalmente:

```python
import json, sys
from pathlib import Path
import pandas as pd
import numpy as np
from src.execution.market_data import load_close_prices, make_json_safe

def main():
    payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    csv_paths = payload.get('csv_paths', [])
    tickers = payload.get('tickers', [])
    close = load_close_prices(csv_paths, tickers)
    close.index = pd.to_datetime(close.index)
    close = close.sort_index()
    ticker = tickers[0] if tickers else None
    if ticker is None or ticker not in close.columns:
        output = {
            "analysis_type": "price_growth",
            "analysis_level": "A",
            "metrics": {"retorno_total": null, "cagr": null},
            "summary": "",
            "limitations": ["Ticker not found in data"]
        }
        print(json.dumps(make_json_safe(output), ensure_ascii=False))
        return
    series = close[ticker].dropna()
    if series.empty:
        output = {
            "analysis_type": "price_growth",
            "analysis_level": "A",
            "metrics": {"retorno_total": null, "cagr": null},
            "summary": "",
            "limitations": ["No price data available"]
        }
        print(json.dumps(make_json_safe(output), ensure_ascii=False))
        return
    first_price = series.iloc[0]
    last_price = series.iloc[-1]
    if first_price == 0:
        retorno_total = None
    else:
        retorno_total = (last_price / first_price) - 1
    days = (series.index[-1] - series.index[0]).days
    years = days / 365.25 if days > 0 else None
    if years and years > 0 and first_price != 0:
        cagr = (last_price / first_price) ** (1 / years) - 1
    else:
        cagr = None
    summary = f"Nvidia ha crecido un {retorno_total*100:.2f}% en total y un CAGR de {cagr*100:.2f}% durante los últimos {years:.2f} años." if retorno_total is not None and cagr is not None else ""
    limitations = []
    if retorno_total is None:
        limitations.append("No se pudo calcular retorno_total debido a precio inicial cero o datos insuficientes.")
    if cagr is None:
        limitations.append("No se pudo calcular CAGR debido a datos insuficientes o division por cero.")
    output = {
        "analysis_type": "price_growth",
        "analysis_level": "A",
        "metrics": {"retorno_total": retorno_total, "cagr": cagr},
        "summary": summary,
        "limitations": limitations
    }
    print(json.dumps(make_json_safe(output), ensure_ascii=False))

if __name__ == "__main__":
    main()
```

Cambio de estado:

```text
planned -> code_generated
```

Qué se genera:

Todavía nada en disco. Se rellena `state.generated_code`.

Observación importante:

El código generado tiene un problema latente: usa `null` en ramas de error. En Python deberia ser `None`. En está ejecución no falla porque esas ramas no se ejecutan, pero es una limitación clara del sistema y conviene conocerla.

## Paso 6: code_security_node

Archivo:

```text
src/graph/nodes.py
```

Llama a:

```python
validate_generated_code(state.generated_code)
```

Archivo:

```text
src/execution/code_security.py
```

La validación analiza el código con `ast.parse`.

Comprueba:

- Que exista `def main(`.
- Que aparezca `json.dumps`.
- Que los imports estén en una lista permitida.
- Que no se llamen funciones bloqueadas como `eval`, `exec`, `compile`, `open`, `input`, `__import__`.
- Que no se usen módulos bloqueados como `os`, `subprocess`, `shutil`, `socket`, `requests`, `urllib`, `httpx`.

Lista de imports permitidos:

```text
__future__
json
sys
pathlib
math
statistics
pandas
numpy
src
```

Resultado real:

```json
{
  "is_valid": true,
  "errors": [],
  "warnings": []
}
```

Cambio de estado:

```text
code_generated -> code_validated
```

Qué se genera:

Nada en disco.

Limitación que debes saber:

Esta validación no garantiza que el código sea correcto. Solo bloquea ciertos riesgos básicos. Por ejemplo, no detecta que `null` no existe en Python si esa rama no se ejecuta durante el test.

## Paso 7: code_execution_node

Archivo:

```text
src/graph/nodes.py
```

Función:

```python
code_execution_node(state)
```

Crea un payload para el script generado:

```json
{
  "query": "Cuanto ha crecido Nvidia en los últimos 5 años",
  "tickers": ["NVDA"],
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\data\\raw\\cunto_ha_crecido_nvidia_en_5_aos.csv"
  ],
  "start": null,
  "end": null,
  "period": "5y",
  "interval": "1d",
  "input": {
    "query": "Cuanto ha crecido Nvidia en los últimos 5 años",
    "tickers": ["NVDA"],
    "csv_paths": [
      "C:\\Users\\usuario\\Desktop\\tfm\\data\\raw\\cunto_ha_crecido_nvidia_en_5_aos.csv"
    ],
    "start": null,
    "end": null,
    "period": "5y",
    "interval": "1d",
    "needs_clarification": false,
    "warnings": []
  },
  "analysis_plan": {
    "analysis_level": "A",
    "analytical_goal": "Calcular el crecimiento total de Nvidia en los últimos 5 años",
    "analysis_type": "price_growth",
    "metrics": ["retorno_total", "cagr"],
    "required_columns": ["Close"],
    "data_requirements": [
      "ticker: NVDA",
      "period: 5y",
      "interval: 1d"
    ],
    "output_requirements": [
      "JSON con valores numéricos de retorno_total y cagr"
    ],
    "presentation_preferences": [
      "Respuesta breve, sin formato adicional, solo valores numéricos"
    ],
    "reasoning": "Nivel A porque la consulta solicita únicamente el crecimiento total de un solo activo."
  }
}
```

Después llama a:

```python
run_generated_code(state.generated_code, payload)
```

Archivo:

```text
src/execution/code_runner.py
```

Este archivo genera un identificador temporal:

```python
run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```

Con ese `run_id` escribe cuatro artefactos:

```text
results/code/generated_<run_id>.py
results/logs/payload_<run_id>.json
results/logs/stdout_<run_id>.json
results/logs/stderr_<run_id>.log
```

Artefactos reales de la traza:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260604_185136_820615.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260604_185136_820615.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260604_185136_820615.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260604_185136_820615.log"
}
```

El script generado se ejecuta con `subprocess.run`.

Esto es importante:

El proyecto bloquea `subprocess` dentro del código generado, pero el sistema principal si usa `subprocess` para lanzar ese código en un proceso separado.

## Paso 8: carga de datos dentro del script generado

El script generado llama a:

```python
load_close_prices(csv_paths, tickers)
```

Archivo:

```text
src/execution/market_data.py
```

`load_close_prices` hace:

1. Llama a `load_market_data`.
2. Carga el CSV.
3. Detecta si es formato ancho de yfinance.
4. Normaliza a tabla larga con columnas como `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`.
5. Crea una tabla de cierres en formato ancho:

```text
índice: Date
columnas: una por ticker
valores: Close
```

Para este caso, queda una columna:

```text
NVDA
```

Luego el script:

```python
series = close["NVDA"].dropna()
first_price = series.iloc[0]
last_price = series.iloc[-1]
```

Cálculos:

```python
retorno_total = (last_price / first_price) - 1
days = (series.index[-1] - series.index[0]).days
years = days / 365.25
cagr = (last_price / first_price) ** (1 / years) - 1
```

Interpretación de métricas:

- `retorno_total`: crecimiento acumulado durante toda la ventana.
- `cagr`: tasa anual compuesta aproximada.

## Paso 9: salida estructurada del script

El stdout real fue:

```json
{
  "analysis_level": "A",
  "metrics": {
    "retorno_total": 12.733345485465156,
    "cagr": 0.689316908211292
  },
  "summary": "Crecimiento total y CAGR calculados.",
  "limitations": []
}
```

Conversion a porcentajes:

```text
retorno_total = 12.733345485465156 -> 1273.33%
cagr = 0.689316908211292 -> 68.93%
```

Return code:

```text
0
```

stderr:

```text
vacío
```

Cambio de estado:

```text
code_validated -> executed
```

Campos del estado actualizados:

```text
execution_stdout
execution_stderr
execution_returncode
execution_output
execution_artifacts
```

## Paso 10: interpretation_node

Archivo:

```text
src/graph/nodes.py
```

Función:

```python
interpretation_node(state)
```

Este nodo llama al Agente 3:

```python
build_llm_interpretation(output_for_llm, plan)
```

Archivo:

```text
src/llm/pipeline.py
```

Prompt construido en:

```text
src/llm/prompts.py
```

El Agente 3 recibe:

1. `execution_output`, es decir, los resultados ya calculados.
2. `analysis_plan`, es decir, el plan que explica qué se quería calcular.

Reglas del Agente 3:

- No recalcular.
- No completar cifras ausentes.
- No usar informacion externa.
- Ajustar extension al nivel A/B/C.
- No dar recomendaciones de compra o venta.
- Explicar en espanol claro.

Entrada conceptual al Agente 3:

```json
{
  "execution_output": {
    "analysis_level": "A",
    "metrics": {
      "retorno_total": 12.733345485465156,
      "cagr": 0.689316908211292
    },
    "summary": "Crecimiento total y CAGR calculados.",
    "limitations": []
  },
  "analysis_plan": {
    "analysis_level": "A",
    "analysis_type": "historical_financial_analysis",
    "metrics": ["retorno_total", "cagr"]
  }
}
```

En la traza real, la salida final del Agente 3 fue:

```text
El retorno total durante los últimos 5 años es 12.7333 y la tasa de crecimiento anual compuesta (CAGR) es 0.6893.
```

Cambio de estado:

```text
executed -> completed
```

## Valor literal de `state.final_answer` en este caso

La salida final del `interpretation_node` se guarda en:

```text
state.final_answer
```

En la traza real de este caso, el valor literal de `state.final_answer` fue:

```text
El retorno total durante los últimos 5 años es 12.7333 y la tasa de crecimiento anual compuesta (CAGR) es 0.6893.
```

Es decir, para está ejecución concreta:

```text
state.final_answer = "El retorno total durante los últimos 5 años es 12.7333 y la tasa de crecimiento anual compuesta (CAGR) es 0.6893."
```

Este valor sale del Agente 3, que recibió:

```text
execution_output + analysis_plan
```

No es un cálculo nuevo. Es la respuesta final que el Agente 3 devolvió a partir de los resultados ya calculados.

## Salida real completa del ejemplo A

En está traza concreta, la ejecución genero estos artefactos:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260604_185136_820615.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260604_185136_820615.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260604_185136_820615.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260604_185136_820615.log"
}
```

La salida real del script generado, guardada en `stdout_path` y parseada como `state.execution_output`, fue:

```json
{
  "analysis_level": "A",
  "metrics": {
    "retorno_total": 12.733345485465156,
    "cagr": 0.689316908211292
  },
  "summary": "Crecimiento total y CAGR calculados.",
  "limitations": []
}
```

El `stderr_path` de está ejecución estaba vacío:

```text

```

Por tanto, la ejecución del script termino correctamente:

```text
execution_returncode = 0
status tras code_execution_node = executed
```

Después, el Agente 3 recibió ese `execution_output` junto con el `analysis_plan`. La salida real final guardada en `state.final_answer` fue:

```text
El retorno total durante los últimos 5 años es 12.7333 y la tasa de crecimiento anual compuesta (CAGR) es 0.6893.
```

Así, el resultado final de está traza fue:

```text
status = completed
state.execution_output = JSON estructurado con analysis_level, metrics, summary y limitations
state.final_answer = "El retorno total durante los últimos 5 años es 12.7333 y la tasa de crecimiento anual compuesta (CAGR) es 0.6893."
```

Esta es la salida real observada en la traza `generated_20260604_185136_820615`.

## Evaluación subjetiva del ejemplo A

La siguiente evaluación aplica la rúbrica subjetiva definida para el sistema sobre la traza real del caso `growth_nvda`.

| Criterio | Puntuación | Motivo breve |
|---|---:|---|
| Completitud del flujo | Sí | Se entiende bien la ejecución. |
| Comprensión de la consulta | 2 / 2 | Se entiende bien la ejecución. |
| Pertinencia de métricas | 2 / 2 | Métricas adecuadas. |
| Calidad de ejecución analítica | 2 / 2 | Se ejecuta bien. |
| Fidelidad de la interpretación | 2 / 2 | No se inventa datos. |
| Claridad, utilidad y prudencia | 1 / 2 | No es clara del todo, ya que en porcentaje quedaría más claro. |
| **Total subjetivo** | **9 / 10** | Resultado bueno para el objetivo del MVP. |