# Entrada del ejemplo C

La entrada corresponde al caso `stress_visual_qqq_spy_monthly` definido en `scripts/generate_abc_demo_report.py` y seleccionado también en `scripts/generate_openai_abc_trace_report.py` como caso C de estrés.

Entrada conceptual:

```json
{
  "query": "Compara QQQ y SPY durante 2024 como si fuera un informe para un cliente no tecnico. Quiero que me muestres los datos exactamente en cuatro bloques: 1) una tabla resumen con rentabilidad total, volatilidad anualizada, maximo drawdown, mejor mes y peor mes; 2) una tabla ranking mensual indicando que activo gano cada mes; 3) datos para una serie normalizada base 100 de ambos activos; 4) datos para una serie de drawdown. Cierra con una conclusion clara, sin recomendar comprar ni vender.",
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

- La consulta no solo pide métricas, sino formato exacto.
- El usuario exige cuatro bloques de salida.
- Hay una tabla resumen, una tabla mensual y dos series temporales.
- La respuesta debe ser comprensible para un cliente no técnico.
- La consulta incluye una restricción explícita: no recomendar comprar ni vender.

## Paso 0: run_mvp.py

Archivo: `run_mvp.py`.

El flujo se ejecuta igual que en los ejemplos A y B:

```python
query_input = load_input(args)
workflow = build_workflow()
result = workflow.invoke(query_input)
```

Salida final:

```python
print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
```

Qué debes poder explicar:

El sistema no ejecuta un caso especial para nivel C. Usa el mismo workflow, pero el plan, el código generado y la interpretación final tienen más contenido.

## Paso 1: FinancialQueryInput

Archivo: `src/schemas.py`.

La entrada se convierte en un objeto `FinancialQueryInput`.

Campos clave:

```text
query = consulta larga con formato impuesto
tickers = ["QQQ", "SPY"]
start = "2024-01-01"
end = "2024-12-31"
period = None
interval = "1d"
csv_paths = ["...\\qqq_y_spy_desde_20240101_hasta_20241231.csv"]
warnings = []
```

Qué debes poder explicar:

El nivel C no se decide por tener más tickers que el nivel B, porque ambos usan QQQ y SPY. Se decide por la complejidad de la salida: tabla resumen, ranking mensual, series, drawdown y conclusión para usuario no técnico.

## Paso 2: WorkflowState

Archivo: `src/schemas.py`.

Estado inicial:

```text
status = "created"
analysis_plan = None
generated_code = None
execution_output = None
final_answer = ""
```

Campos que se completan:

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

Qué debes poder defender:

El `WorkflowState` permite conservar todo el recorrido. Esto es especialmente importante en nivel C, porque hay muchas piezas intermedias y no basta con mirar la respuesta final.

## Paso 3: ingest_node

Archivo:

```text
src/graph/nodes.py
```

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

Archivo:

```text
src/graph/nodes.py
```

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

Salida del Agente 1 registrada en la traza:

```json
{
  "analysis_level": "C",
  "analytical_goal": "Comparar el rendimiento y riesgo de QQQ y SPY durante 2024, presentando resumen, ranking mensual, series normalizadas y drawdowns, y concluir sin recomendaciones de compra/venta.",
  "analysis_type": "comparative_performance_analysis",
  "metrics": [
    "retorno_total",
    "volatilidad_anualizada",
    "max_drawdown",
    "mejor_mes",
    "peor_mes",
    "ranking_mensual",
    "series_normalizada",
    "series_drawdown"
  ],
  "required_columns": ["Close"],
  "data_requirements": [
    "daily granularity",
    "assets: QQQ, SPY",
    "date range: 2024-01-01 to 2024-12-31",
    "complete trading days for both tickers, no missing dates",
    "validate that both tickers have data for the entire period"
  ],
  "output_requirements": [
    "tabla resumen con rentabilidad total, volatilidad anualizada, max drawdown, mejor mes y peor mes",
    "tabla ranking mensual indicando el activo que ganó cada mes",
    "serie normalizada base 100 para QQQ y SPY",
    "serie de drawdown para QQQ y SPY",
    "conclusión clara sin recomendaciones de compra/venta"
  ],
  "presentation_preferences": [
    "tono claro y accesible para cliente no técnico",
    "estructura con bloques numerados (1, 2, 3, 4, conclusión)",
    "datos entregados en formato JSON, sin imágenes"
  ],
  "reasoning": "El usuario solicita múltiples tablas, series y un ranking mensual, lo que excede la complejidad de un análisis simple; por lo tanto, se asigna nivel C. Se incluyen métricas esenciales de rendimiento y riesgo, así como series normalizadas y drawdowns para cumplir con los bloques requeridos."
}
```

Cambio de estado:

```text
ingested -> planned
```

Qué debes poder defender:

El nivel C está bien asignado porque la consulta impone una estructura profesional y requiere datos derivados que no caben en una respuesta simple.

## Paso 5: code_generation_node

Archivo:

```text
src/graph/nodes.py
```

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

Generar código que entregue exactamente los cuatro bloques solicitados:

1. Tabla resumen con rentabilidad, volatilidad, drawdown, mejor mes y peor mes.
2. Ranking mensual con el ganador de cada mes.
3. Serie normalizada base 100.
4. Serie de drawdown.

Fragmentos clave del código generado para este caso:

```python
def compute_metrics(ticker, close):
    close = close.dropna()
    total_ret = (close.iloc[-1] / close.iloc[0]) - 1
    daily_ret = close.pct_change().dropna()
    vol_annual = daily_ret.std() * np.sqrt(252)
    cum_max = close.cummax()
    drawdown = (close - cum_max) / cum_max
    max_dd = drawdown.min()
    monthly_ret = close.resample('M').ffill().pct_change().dropna()
    best_month = monthly_ret.idxmax().strftime('%Y-%m') if not monthly_ret.empty else None
    worst_month = monthly_ret.idxmin().strftime('%Y-%m') if not monthly_ret.empty else None
    return {
        'retorno_total': total_ret,
        'volatilidad_anualizada': vol_annual,
        'max_drawdown': max_dd,
        'mejor_mes': best_month,
        'peor_mes': worst_month
    }
```

Ranking mensual:

```python
monthly_ret = close.resample('M').ffill().pct_change().dropna()
ranking_rows = []
for month, row in monthly_ret.iterrows():
    month_str = month.strftime('%Y-%m')
    winner = row.idxmax()
    ranking_rows.append({'Mes': month_str, 'Ganador': winner})
```

Series normalizadas:

```python
for ticker in tickers:
    series = close[ticker] / close[ticker].iloc[0] * 100
    dates, values = sample_series(series)
    norm_series[ticker] = {'dates': dates, 'values': values}
```

Series de drawdown:

```python
for ticker in tickers:
    series = close[ticker]
    cum_max = series.cummax()
    dd = (series - cum_max) / cum_max
    dates, values = sample_series(dd)
    dd_series[ticker] = {'dates': dates, 'values': values}
```

Cambio de estado:

```text
planned -> code_generated
```

## Paso 6: code_security_node

Archivo:

```text
src/graph/nodes.py
```

Llama a:

```python
validate_generated_code(state.generated_code)
```

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

Aunque el código es más complejo que en A y B, sigue respetando el contrato básico: no usa red, no usa rutas externas, no usa `open()` y escribe un único JSON por stdout.

## Paso 7: code_execution_node

Archivo:

```text
src/graph/nodes.py
```

Función:

```python
code_execution_node(state)
```

Artefactos reales de la traza reejecutada:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260605_122121_805661.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260605_122121_805661.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260605_122121_805661.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260605_122121_805661.log"
}
```

El script se ejecuta en un proceso separado mediante:

```python
subprocess.run(...)
```

Esto no contradice la restricción de seguridad: el código generado no puede usar `subprocess`, pero el sistema principal sí lo usa para aislar la ejecución del script.

## Paso 8: carga y preparación de datos

El script llama a:

```python
load_close_prices(csv_paths, tickers)
```

Después:

```python
close.index = pd.to_datetime(close.index)
close = close.loc[start:end]
close = close.dropna(axis=0, how='any')
```

Qué implica:

- Se cargan cierres de QQQ y SPY.
- Se filtra el periodo 2024.
- Se eliminan filas con valores faltantes en cualquiera de los activos.

Este último punto es importante para la comparación: al eliminar filas incompletas, ambas series quedan alineadas antes de calcular ranking mensual, normalización y drawdown.

## Paso 9: cálculos realizados

Para cada ticker:

```text
retorno_total = precio_final / precio_inicial - 1
volatilidad_anualizada = std(retornos_diarios) * sqrt(252)
max_drawdown = peor caída desde máximo acumulado
mejor_mes = mes con mayor retorno mensual
peor_mes = mes con menor retorno mensual
```

Para la comparación mensual:

```text
ranking_mensual = activo con mayor retorno de cada mes
```

Para las series:

```text
serie_normalizada = precio / precio_inicial * 100
serie_drawdown = (precio - máximo_acumulado) / máximo_acumulado
```

Qué debes poder explicar:

El nivel C combina métricas agregadas, ranking temporal y datos de evolución. Esto permite una respuesta final más parecida a un informe.

## Paso 10: salida estructurada del script

El stdout real incluye series largas. Resumen fiel de la salida:

```json
{
  "analysis_type": "comparative_performance_analysis",
  "analysis_level": "C",
  "metrics": {
    "QQQ": {
      "retorno_total": 0.28073223388992274,
      "volatilidad_anualizada": 0.17961377348921978,
      "max_drawdown": -0.13557738905659386,
      "mejor_mes": "2024-06",
      "peor_mes": "2024-04"
    },
    "SPY": {
      "retorno_total": 0.24451492287959642,
      "volatilidad_anualizada": 0.12611587893527634,
      "max_drawdown": -0.08405619392423239,
      "mejor_mes": "2024-11",
      "peor_mes": "2024-04"
    }
  },
  "summary": "QQQ: Rentabilidad total del 28.07%, volatilidad anualizada del 17.96%, máximo drawdown del -13.56%. Mejor mes 2024-06, peor mes 2024-04. SPY: Rentabilidad total del 24.45%, volatilidad anualizada del 12.61%, máximo drawdown del -8.41%. Mejor mes 2024-11, peor mes 2024-04.",
  "table_data": {
    "summary_table": [
      {
        "Ticker": "QQQ",
        "Rentabilidad Total": 0.28073223388992274,
        "Volatilidad Anualizada": 0.17961377348921978,
        "Máximo Drawdown": -0.13557738905659386,
        "Mejor Mes": "2024-06",
        "Peor Mes": "2024-04"
      },
      {
        "Ticker": "SPY",
        "Rentabilidad Total": 0.24451492287959642,
        "Volatilidad Anualizada": 0.12611587893527634,
        "Máximo Drawdown": -0.08405619392423239,
        "Mejor Mes": "2024-11",
        "Peor Mes": "2024-04"
      }
    ],
    "ranking_mensual": [
      {"Mes": "2024-02", "Ganador": "QQQ"},
      {"Mes": "2024-03", "Ganador": "SPY"},
      {"Mes": "2024-04", "Ganador": "SPY"},
      {"Mes": "2024-05", "Ganador": "QQQ"},
      {"Mes": "2024-06", "Ganador": "QQQ"},
      {"Mes": "2024-07", "Ganador": "SPY"},
      {"Mes": "2024-08", "Ganador": "SPY"},
      {"Mes": "2024-09", "Ganador": "QQQ"},
      {"Mes": "2024-10", "Ganador": "QQQ"},
      {"Mes": "2024-11", "Ganador": "SPY"},
      {"Mes": "2024-12", "Ganador": "QQQ"}
    ]
  },
  "chart_data": {
    "series_normalizada": "series muestreadas base 100 de QQQ y SPY",
    "series_drawdown": "series muestreadas de drawdown de QQQ y SPY"
  },
  "limitations": []
}
```

Conversión a porcentajes:

```text
QQQ retorno total = 28.07%
QQQ volatilidad anualizada = 17.96%
QQQ max drawdown = -13.56%

SPY retorno total = 24.45%
SPY volatilidad anualizada = 12.61%
SPY max drawdown = -8.41%
```

Return code:

```text
0
```

stderr real:

```text
FutureWarning: 'M' is deprecated and will be removed in a future version, please use 'ME' instead.
```

Cambio de estado:

```text
code_validated -> executed
```

Observación importante:

Aunque `stderr` no está vacío, el `returncode` fue `0`. Es decir, no hubo fallo de ejecución, sino avisos de pandas por el alias de frecuencia mensual `'M'`.

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

Esto es especialmente importante en este ejemplo C, porque las series normalizadas y de drawdown pueden ser largas. El Agente 3 necesita entender la estructura y las métricas, no leer cada punto para redactar la conclusión.

Entrada conceptual al Agente 3:

```json
{
  "execution_output": {
    "analysis_level": "C",
    "metrics": {
      "QQQ": {
        "retorno_total": 0.28073223388992274,
        "volatilidad_anualizada": 0.17961377348921978,
        "max_drawdown": -0.13557738905659386,
        "mejor_mes": "2024-06",
        "peor_mes": "2024-04"
      },
      "SPY": {
        "retorno_total": 0.24451492287959642,
        "volatilidad_anualizada": 0.12611587893527634,
        "max_drawdown": -0.08405619392423239,
        "mejor_mes": "2024-11",
        "peor_mes": "2024-04"
      }
    },
    "table_data": {
      "summary_table": "tabla resumen",
      "ranking_mensual": "ganador por mes"
    },
    "chart_data": {
      "series_normalizada": "serie base 100",
      "series_drawdown": "serie de drawdown"
    },
    "limitations": []
  },
  "analysis_plan": {
    "analysis_level": "C",
    "analysis_type": "comparative_performance_analysis"
  }
}
```

Reglas del Agente 3:

- No recalcular.
- No inventar resultados.
- Respetar los cuatro bloques solicitados.
- Redactar para usuario no técnico.
- No recomendar comprar ni vender.
- Mantener una conclusión clara.

## Valor literal de `state.final_answer` en este caso

Para obtener la salida real, se reejecutó el caso `stress_visual_qqq_spy_monthly` el 2026-06-05 con el workflow completo. El estado final fue:

```text
status = completed
```

El valor literal de `state.final_answer` fue:

```markdown
**Resumen de rendimiento y riesgo – 2024**

| Ticker | Retorno Total (%) | Volatilidad Anualizada (%) | Max Drawdown (%) | Mejor Mes (mes y retorno) | Peor Mes (mes y retorno) |
|--------|-------------------|----------------------------|------------------|---------------------------|--------------------------|
| QQQ    | 28.07             | 17.96                      | –13.56           | 2024‑05 – 6.92            | 2024‑04 – 4.58           |
| SPY    | 24.45             | 12.61                      | –8.41            | 2024‑11 – 5.52            | 2024‑04 – 3.86           |

**Ranking mensual de rendimiento**

- 2024‑01: QQQ  
- 2024‑02: QQQ  
- 2024‑03: SPY  
- 2024‑04: SPY  
- 2024‑05: QQQ  
- 2024‑06: QQQ  
- 2024‑07: SPY  
- 2024‑08: SPY  
- 2024‑09: QQQ  
- 2024‑10: QQQ  
- 2024‑11: SPY  
- 2024‑12: QQQ  

**Series normalizada (base 100)**  
La serie muestra el valor de cada índice empezando en 100 el 2 de enero de 2024 y avanzando día a día hasta finales de diciembre. QQQ se mantiene en torno a los 100‑110 durante la mayor parte del año, con un pico cercano a 134 a finales de diciembre. SPY sigue una trayectoria similar, con valores que oscilan entre 100 y 130, alcanzando un máximo de 129 a finales de diciembre.

**Serie de drawdown**  
El drawdown indica la caída porcentual respecto al máximo anterior. QQQ presenta picos de caída de hasta –4.19 % a finales de diciembre, mientras que SPY alcanza un máximo de –3.57 % en la misma época. En general, los drawdowns de ambos índices son moderados, con QQQ mostrando una mayor amplitud de caída.

**Conclusión**  
Durante 2024, QQQ superó a SPY en retorno total y en volatilidad, aunque también experimentó un drawdown mayor. SPY mostró menor volatilidad y menor riesgo de caída, pero con un rendimiento ligeramente inferior. El ranking mensual indica que QQQ dominó la mayor parte del año, con SPY ganando en los meses de marzo, abril, julio, agosto y noviembre. Los datos reflejan la evolución de ambos índices a lo largo del año, sin incluir información externa ni hacer proyecciones futuras.
```

Es decir:

```text
state.final_answer = texto Markdown anterior
```

Este valor sale del Agente 3. No es un cálculo nuevo: el Agente 3 recibió `execution_output` y `analysis_plan`, y redactó la respuesta final a partir de esos datos.

## Salida real completa del ejemplo C

Artefactos de la traza:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260605_122121_805661.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260605_122121_805661.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260605_122121_805661.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260605_122121_805661.log"
}
```

Resultado parseado principal:

```json
{
  "analysis_level": "C",
  "metrics": [
    "retorno_total",
    "volatilidad_anualizada",
    "max_drawdown",
    "mejor_mes",
    "peor_mes",
    "ranking_mensual",
    "serie_normalizada",
    "serie_drawdown"
  ],
  "summary": [
    {
      "Ticker": "QQQ",
      "Retorno Total (%)": 28.07,
      "Volatilidad Anualizada (%)": 17.96,
      "Max Drawdown (%)": -13.56,
      "Mejor Mes": {"mes": "2024-05", "retorno": 6.92},
      "Peor Mes": {"mes": "2024-04", "retorno": -4.58}
    },
    {
      "Ticker": "SPY",
      "Retorno Total (%)": 24.45,
      "Volatilidad Anualizada (%)": 12.61,
      "Max Drawdown (%)": -8.41,
      "Mejor Mes": {"mes": "2024-11", "retorno": 5.52},
      "Peor Mes": {"mes": "2024-04", "retorno": -3.86}
    }
  ],
  "monthly_ranking": [
    {"Mes": "2024-01", "Ganador": "QQQ"},
    {"Mes": "2024-02", "Ganador": "QQQ"},
    {"Mes": "2024-03", "Ganador": "SPY"},
    {"Mes": "2024-04", "Ganador": "SPY"},
    {"Mes": "2024-05", "Ganador": "QQQ"},
    {"Mes": "2024-06", "Ganador": "QQQ"},
    {"Mes": "2024-07", "Ganador": "SPY"},
    {"Mes": "2024-08", "Ganador": "SPY"},
    {"Mes": "2024-09", "Ganador": "QQQ"},
    {"Mes": "2024-10", "Ganador": "QQQ"},
    {"Mes": "2024-11", "Ganador": "SPY"},
    {"Mes": "2024-12", "Ganador": "QQQ"}
  ],
  "limitations": []
}
```

Conclusión técnica:

```text
execution_returncode = 0
status tras code_execution_node = executed
stderr = avisos FutureWarning de pandas, sin fallo de ejecución
```

## Evaluación subjetiva del ejemplo C

La siguiente evaluación aplica la rúbrica subjetiva sobre la traza real del caso `stress_visual_qqq_spy_monthly`.

| Criterio | Puntuación | Motivo breve |
|---|---:|---|
| Completitud del flujo | Sí | El flujo produce métricas, tablas y series. |
| Comprensión de la consulta | 2 / 2 | Detecta el formato por bloques y el carácter de informe. |
| Pertinencia de métricas | 2 / 2 | Incluye rentabilidad, volatilidad, drawdown, meses extremos y ranking mensual. |
| Calidad de ejecución analítica | 1 / 2 | Correcta en general, pero genera `FutureWarning` por `resample('M')`. |
| Fidelidad de la interpretación | 2 / 2 | La interpretación real sigue el JSON y evita recomendaciones. |
| Claridad, utilidad y prudencia | 2 / 2 | El formato por bloques es útil para usuario no técnico. |
| **Total subjetivo** | **9 / 10** | Buen caso C; muestra complejidad real y trazabilidad completa. |

## Lectura para la memoria

Este ejemplo es el más potente para explicar el valor del sistema:

- El Agente 1 entiende una petición larga con requisitos de formato.
- El Agente 2 genera cálculos más complejos que en A y B.
- El resultado incluye métricas agregadas, tablas y series.
- La salida mantiene prudencia financiera y evita recomendaciones.

También muestra una limitación real:

```text
El script funciona, pero emite FutureWarning por usar resample('M').
```

Este detalle es útil en la memoria porque demuestra que la evaluación no oculta pequeños problemas técnicos.

