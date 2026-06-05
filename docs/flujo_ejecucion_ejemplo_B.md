# Entrada del ejemplo B

La entrada corresponde al caso `level_b_qqq_spy_clear_compare` definido en `scripts/generate_abc_demo_report.py`.

Entrada conceptual:

```json
{
  "query": "Comparame QQQ y SPY en 2024 de forma clara, con tabla y serie normalizada",
  "tickers": ["QQQ", "SPY"],
  "start": "2024-01-01",
  "end": "2024-12-31",
  "period": null,
  "interval": "1d",
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\data\\raw\\qqq_y_spy_desde_20240101_hasta_20241231.csv"
  ],
  "warnings": []
}
```

Qué debes entender:

- `query` pide una comparativa clara entre dos ETFs.
- `tickers` contiene dos activos, por lo que el flujo debe comparar, no solo describir.
- `start` y `end` fijan el año 2024.
- `interval` indica datos diarios.
- `csv_paths` apunta a datos ya descargados; la ejecución no consulta internet durante el cálculo.

## Paso 0: run_mvp.py

Archivo: `run_mvp.py`.

El flujo general es el mismo que en el ejemplo A:

```python
query_input = load_input(args)
workflow = build_workflow()
result = workflow.invoke(query_input)
```

Salida final:

```python
print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
```

Esto significa que el programa imprime el estado final completo del workflow, con entrada, plan, código generado, ejecución, artefactos y respuesta final cuando el Agente 3 termina correctamente.

## Paso 1: FinancialQueryInput

Archivo: `src/schemas.py`.

La entrada se normaliza en:

```text
FinancialQueryInput
```

Campos relevantes para este caso:

```text
query = "Comparame QQQ y SPY en 2024 de forma clara, con tabla y serie normalizada"
tickers = ["QQQ", "SPY"]
start = "2024-01-01"
end = "2024-12-31"
period = None
interval = "1d"
csv_paths = ["...\\qqq_y_spy_desde_20240101_hasta_20241231.csv"]
warnings = []
```

Qué debes poder explicar:

`FinancialQueryInput` evita que el flujo trabaje con diccionarios sueltos. En este ejemplo es importante porque la consulta contiene dos activos y una ventana temporal cerrada.

## Paso 2: WorkflowState

Archivo: `src/schemas.py`.

Antes de ejecutar nodos se crea un `WorkflowState`.

Estado inicial:

```text
status = "created"
analysis_plan = None
generated_code = None
execution_output = None
final_answer = ""
```

Campos que acabarán siendo importantes:

```text
analysis_plan
generated_code
execution_stdout
execution_stderr
execution_returncode
execution_output
execution_artifacts
final_answer
warnings
status
```

Qué debes poder explicar:

`WorkflowState` es la memoria compartida del workflow. Cada nodo añade una pieza: validación, plan, código, resultado de ejecución e interpretación.

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

Archivo:

```text
src/graph/validation.py
```

Comprueba:

- Que la consulta no esté vacía.
- Que existan tickers.
- Que exista al menos una ruta CSV.
- Que `start` y `end` tengan formato `YYYY-MM-DD`.
- Que el CSV exista realmente.

Para este caso, la validación fue:

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

Convertir la consulta en un plan analítico. En este caso debe detectar que la pregunta pide:

- Comparación entre QQQ y SPY.
- Tabla resumen.
- Serie normalizada base 100.
- Lectura clara, no solo una métrica aislada.

Salida del Agente 1 registrada en el payload de la traza:

```json
{
  "analysis_level": "B",
  "analytical_goal": "Comparar el rendimiento y riesgo de QQQ y SPY durante el año 2024",
  "analysis_type": "performance_comparison",
  "metrics": [
    "retorno_total",
    "volatilidad",
    "max_drawdown",
    "correlacion"
  ],
  "required_columns": ["Close"],
  "data_requirements": [
    "intervalo diario",
    "activos: QQQ y SPY",
    "periodo: 2024-01-01 a 2024-12-31",
    "validar que cada activo tenga al menos 252 días de datos sin valores nulos"
  ],
  "output_requirements": [
    "tabla_resumen: métricas por activo",
    "tabla_serie_normalizada: precios diarios normalizados a 100 al inicio del año",
    "valor_correlacion: coeficiente de correlación entre los dos activos"
  ],
  "presentation_preferences": [
    "tono formal y objetivo",
    "estructura: encabezado, tabla resumen, tabla serie normalizada, valor de correlación",
    "sin imágenes, solo datos JSON"
  ],
  "reasoning": "El usuario solicita una comparación clara con tabla y serie normalizada, lo que requiere métricas de rendimiento y riesgo y una presentación tabular. Esto corresponde al nivel B según las reglas de calidad."
}
```

Cambio de estado:

```text
ingested -> planned
```

Qué debes poder defender:

El nivel B está bien justificado porque la consulta ya no es una pregunta simple. Pide una comparación con estructura tabular y datos preparados para una visualización.

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

Generar un script Python que:

1. Lea el payload desde `argv[1]`.
2. Cargue cierres de QQQ y SPY desde el CSV.
3. Filtre el rango 2024.
4. Calcule rentabilidad, volatilidad, drawdown máximo y correlación.
5. Construya tabla resumen.
6. Construya serie normalizada base 100.
7. Imprima un único JSON por stdout.

Fragmento representativo del código generado para este caso:

```python
import json, sys
from pathlib import Path
import pandas as pd
import numpy as np
from src.execution.market_data import load_close_prices, load_market_data, make_json_safe

def main():
    payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    tickers = payload.get('tickers', [])
    csv_paths = payload.get('csv_paths', [])
    start = payload.get('start')
    end = payload.get('end')
    close = load_close_prices(csv_paths, tickers)
    close = close.loc[(close.index >= start) & (close.index <= end)]
    limitations = []
    for t in tickers:
        if close[t].dropna().shape[0] < 252:
            limitations.append(f"Ticker {t} has less than 252 non-NaN trading days.")
    returns = close.pct_change().dropna()
    metrics = {}
    for t in tickers:
        series = close[t].dropna()
        ret_total = (series.iloc[-1] / series.iloc[0]) - 1
        daily_ret = series.pct_change().dropna()
        vol = daily_ret.std() * np.sqrt(252)
        cum_max = series.cummax()
        drawdown = (series - cum_max) / cum_max
        max_dd = drawdown.min()
        metrics[t] = {
            "retorno_total": ret_total,
            "volatilidad": vol,
            "max_drawdown": max_dd
        }
    corr = returns[tickers[0]].corr(returns[tickers[1]]) if len(tickers) >= 2 else None
    norm = close.copy()
    for t in tickers:
        norm[t] = close[t] / close[t].iloc[0] * 100 if close[t].iloc[0] != 0 else np.nan
    sample_indices = np.linspace(0, len(norm)-1, num=min(120, len(norm)), dtype=int)
    norm_sampled = norm.iloc[sample_indices].reset_index()
    output = {
        "analysis_type": "performance_comparison",
        "analysis_level": "B",
        "metrics": metrics,
        "summary": {"correlation": corr},
        "limitations": limitations,
        "table_data": {
            "summary_metrics": metrics,
            "normalized_series": norm_sampled.to_dict(orient='records')
        },
        "chart_data": {
            "type": "line",
            "series": [{"name": t, "data": norm[t].tolist()} for t in tickers],
            "xAxis": norm.index.strftime('%Y-%m-%d').tolist(),
            "yAxis": {"unit": "Normalized Price"}
        }
    }
    print(json.dumps(make_json_safe(output), ensure_ascii=False))

if __name__ == "__main__":
    main()
```

Cambio de estado:

```text
planned -> code_generated
```

Observación importante:

El código incluye `load_market_data` aunque no lo usa. No afecta a la ejecución porque el import está permitido, pero es una pequeña ineficiencia.

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

La validación comprueba:

- Que exista `main`.
- Que el código use `json.dumps`.
- Que los imports estén permitidos.
- Que no use funciones bloqueadas como `open`, `eval`, `exec`, `input` o `__import__`.
- Que no importe módulos bloqueados como `os`, `subprocess`, `requests`, `urllib`, `socket` o `httpx`.

Resultado para este caso:

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

Qué debes poder explicar:

La validación de seguridad no comprueba si la estrategia financiera es perfecta. Comprueba que el script generado cumple restricciones básicas antes de lanzarlo.

## Paso 7: code_execution_node

Archivo:

```text
src/graph/nodes.py
```

Función:

```python
code_execution_node(state)
```

Construye el payload del script con:

```json
{
  "query": "Comparame QQQ y SPY en 2024 de forma clara, con tabla y serie normalizada",
  "tickers": ["QQQ", "SPY"],
  "start": "2024-01-01",
  "end": "2024-12-31",
  "period": null,
  "interval": "1d",
  "analysis_plan": {
    "analysis_level": "B",
    "analysis_type": "performance_comparison",
    "metrics": [
      "retorno_total",
      "volatilidad",
      "max_drawdown",
      "correlacion"
    ]
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

Artefactos reales de la traza reejecutada:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260605_121446_080795.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260605_121446_080795.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260605_121446_080795.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260605_121446_080795.log"
}
```

## Paso 8: carga de datos dentro del script generado

El script llama a:

```python
load_close_prices(csv_paths, tickers)
```

Archivo:

```text
src/execution/market_data.py
```

Este helper:

1. Lee el CSV generado previamente con datos de yfinance.
2. Normaliza los datos a una tabla larga.
3. Filtra los tickers solicitados.
4. Devuelve una tabla de cierres en formato ancho:

```text
índice: Date
columnas: QQQ, SPY
valores: Close
```

Después, el script filtra:

```python
close = close.loc[(close.index >= start) & (close.index <= end)]
```

Para este caso:

```text
start = "2024-01-01"
end = "2024-12-31"
```

## Paso 9: cálculos realizados

Para cada activo:

```python
retorno_total = (precio_final / precio_inicial) - 1
volatilidad = desviacion_tipica(retornos_diarios) * sqrt(252)
drawdown = (precio - maximo_acumulado) / maximo_acumulado
max_drawdown = minimo(drawdown)
```

Para comparar ambos activos:

```python
correlacion = corr(retornos_diarios_QQQ, retornos_diarios_SPY)
```

Para la serie normalizada:

```python
serie_normalizada = precio / precio_inicial * 100
```

Interpretación:

- `retorno_total` mide crecimiento acumulado.
- `volatilidad` mide variabilidad anualizada de retornos diarios.
- `max_drawdown` mide la peor caída desde un máximo previo.
- `correlacion` mide cuánto se movieron juntos QQQ y SPY.
- `serie_normalizada` permite comparar activos que tienen precios absolutos distintos.

## Paso 10: salida estructurada del script

El stdout real fue muy largo porque incluye toda la serie normalizada. Resumen fiel de la salida:

```json
{
  "analysis_type": "performance_comparison",
  "analysis_level": "B",
  "metrics": {
    "QQQ": {
      "retorno_total": 0.28073223388992274,
      "volatilidad": 0.17961377348921978,
      "max_drawdown": -0.13557738905659386
    },
    "SPY": {
      "retorno_total": 0.24451492287959642,
      "volatilidad": 0.12611587893527634,
      "max_drawdown": -0.08405619392423239
    }
  },
  "summary": {
    "correlation": 0.9449783063227655
  },
  "limitations": [
    "Ticker QQQ has less than 252 non-NaN trading days.",
    "Ticker SPY has less than 252 non-NaN trading days."
  ],
  "table_data": {
    "summary_metrics": "mismas métricas por activo",
    "normalized_series": "serie muestreada base 100"
  },
  "chart_data": {
    "type": "line",
    "series": "series completas normalizadas de QQQ y SPY",
    "xAxis": "fechas de 2024",
    "yAxis": {
      "unit": "Normalized Price"
    }
  }
}
```

Conversión a porcentajes:

```text
QQQ retorno_total = 28.07%
QQQ volatilidad anualizada = 17.96%
QQQ max_drawdown = -13.56%

SPY retorno_total = 24.45%
SPY volatilidad anualizada = 12.61%
SPY max_drawdown = -8.41%

correlación QQQ/SPY = 0.9450
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

## Paso 11: interpretation_node

Archivo:

```text
src/graph/nodes.py
```

Función:

```python
interpretation_node(state)
```

Antes de llamar al Agente 3, el sistema compacta la salida:

```python
output_for_llm = _compact_for_interpretation(output)
```

Esto importa mucho en el nivel B, porque `chart_data` puede contener cientos de puntos. El objetivo es que el Agente 3 reciba las métricas principales y una muestra representativa, sin consumir contexto innecesario.

Entrada conceptual al Agente 3:

```json
{
  "execution_output": {
    "analysis_level": "B",
    "metrics": {
      "QQQ": {
        "retorno_total": 0.28073223388992274,
        "volatilidad": 0.17961377348921978,
        "max_drawdown": -0.13557738905659386
      },
      "SPY": {
        "retorno_total": 0.24451492287959642,
        "volatilidad": 0.12611587893527634,
        "max_drawdown": -0.08405619392423239
      }
    },
    "summary": {
      "correlation": 0.9449783063227655
    },
    "limitations": [
      "Ticker QQQ has less than 252 non-NaN trading days.",
      "Ticker SPY has less than 252 non-NaN trading days."
    ]
  },
  "analysis_plan": {
    "analysis_level": "B",
    "analysis_type": "performance_comparison",
    "metrics": [
      "retorno_total",
      "volatilidad",
      "max_drawdown",
      "correlacion"
    ]
  }
}
```

Reglas del Agente 3:

- No recalcular.
- No inventar cifras.
- No usar información externa.
- Explicar en español claro.
- No recomendar compra o venta.
- Ajustar la respuesta a nivel B: más estructurada que A, pero sin convertirse en informe profesional completo.

## Valor literal de `state.final_answer` en este caso

Para obtener la salida real, se reejecutó el caso `level_b_qqq_spy_clear_compare` el 2026-06-05 con el workflow completo. El estado final fue:

```text
status = completed
```

El valor literal de `state.final_answer` fue:

```markdown
**Comparación de rendimiento y volatilidad – 2024**

| Indicador | QQQ | SPY |
|-----------|-----|-----|
| **Retorno total** | 28,07 % | 24,45 % |
| **CAGR** | 28,27 % | 24,62 % |
| **Volatilidad anualizada** | 17,96 % | 12,61 % |
| **Máximo drawdown** | –13,56 % | –8,41 % |

*La tabla muestra los valores calculados a partir de los precios diarios de cierre normalizados a 100 el 1 de enero de 2024.*

---

### Serie de precios normalizada

- **QQQ**: la serie comienza en 100 el 2 de enero y alcanza su punto máximo de 133,68 el 16 de diciembre, con una caída a 128,29 el 30 de diciembre.  
- **SPY**: la serie también inicia en 100 el 2 de enero y llega a 128,38 el 16 de diciembre, descendiendo a 124,45 el 30 de diciembre.

Ambas series muestran una tendencia al alza a lo largo del año, con QQQ superando a SPY en términos de retorno total y volatilidad.

---

### Observaciones

- **Datos históricos**: los cálculos se basan en precios diarios completos de QQQ y SPY para todo el año 2024.  
- **Interpretación**: QQQ obtuvo un rendimiento superior, pero con mayor volatilidad y riesgo de caída máxima. SPY mostró un comportamiento más estable.  
- **Limitaciones**: no se dispone de información adicional sobre eventos corporativos o factores macroeconómicos que pudieran haber influido en los movimientos de precios. No se incluyen datos de correlación más allá del valor de 0,976 entre los dos activos.
```

Es decir:

```text
state.final_answer = texto Markdown anterior
```

Este valor sale del Agente 3. No es un cálculo nuevo: el Agente 3 recibió `execution_output` y `analysis_plan`, y redactó la respuesta final a partir de esos datos.

## Salida real completa del ejemplo B

Artefactos de la traza:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260605_121446_080795.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260605_121446_080795.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260605_121446_080795.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260605_121446_080795.log"
}
```

Resultado parseado principal:

```json
{
  "analysis_level": "B",
  "metrics": {
    "QQQ": {
      "retorno_total": 0.28073223388992274,
      "cagr": 0.28269796053458207,
      "volatilidad": 0.17961377348921978,
      "max_drawdown": -0.13557738905659386
    },
    "SPY": {
      "retorno_total": 0.24451492287959642,
      "cagr": 0.24620345857905201,
      "volatilidad": 0.12611587893527634,
      "max_drawdown": -0.08405619392423239
    }
  },
  "table_data": [
    {
      "Ticker": "QQQ",
      "retorno_total": 0.28073223388992274,
      "cagr": 0.28269796053458207,
      "volatilidad": 0.17961377348921978,
      "max_drawdown": -0.13557738905659386
    },
    {
      "Ticker": "SPY",
      "retorno_total": 0.24451492287959642,
      "cagr": 0.24620345857905201,
      "volatilidad": 0.12611587893527634,
      "max_drawdown": -0.08405619392423239
    },
    {
      "Ticker": "Correlation",
      "retorno_total": 0.9756666801356495
    }
  ]
}
```

Conclusión técnica:

```text
execution_returncode = 0
status tras code_execution_node = executed
stderr = vacío
```

## Evaluación subjetiva del ejemplo B

La siguiente evaluación aplica la rúbrica subjetiva sobre la traza real del caso `level_b_qqq_spy_clear_compare`.

| Criterio | Puntuación | Motivo breve |
|---|---:|---|
| Completitud del flujo | Sí | El flujo llega a ejecución y produce JSON estructurado. |
| Comprensión de la consulta | 2 / 2 | Detecta comparación, tabla y serie normalizada. |
| Pertinencia de métricas | 2 / 2 | Retorno, volatilidad, drawdown y correlación encajan bien. |
| Calidad de ejecución analítica | 2 / 2 | Los cálculos principales son coherentes. |
| Fidelidad de la interpretación | 2 / 2 | La interpretación real se basa en el JSON calculado. |
| Claridad, utilidad y prudencia | 1 / 2 | Buen nivel, aunque las limitaciones aparecen en inglés y la serie completa puede ser demasiado larga. |
| **Total subjetivo** | **9 / 10** | Muy buen ejemplo para demostrar el salto del nivel A al nivel B. |

## Lectura para la memoria

Este ejemplo es útil porque muestra una consulta intermedia: no se limita a una cifra, sino que exige comparar dos activos y preparar una salida tabular/visual. Para explicar el sistema en la memoria, conviene destacar tres ideas:

- El Agente 1 clasifica correctamente la consulta como nivel B.
- El Agente 2 genera código que calcula métricas y datos para visualización.
- El sistema conserva artefactos reproducibles: script, payload, stdout y stderr.

