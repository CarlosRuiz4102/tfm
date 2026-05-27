# Plan de Pruebas con Queries LLM Complejas

Este documento recoge el nuevo banco de consultas para evaluar el flujo LLM + codegen sin descargar datos nuevos. Todas las pruebas reutilizan los CSV existentes en `data/raw` y aumentan la dificultad del mensaje qué recibe el LLM.

## Objetivo

El objetivo ya no es probar solo consultas simples, sino comprobar si el sistema puede:

- interpretar peticiones financieras más ricas;
- generar código Python con varias métricas;
- leer correctamente los CSV históricos ya disponibles;
- superar validación de seguridad;
- ejecutar el script en entorno controlado;
- redactar una respuesta final clara sin recomendaciones de inversión.

## Que Significa LLM Real

En esta documentacion se usa la expresion `LLM real` para distinguir las pruebas que llaman a una API de modelo de lenguaje de las pruebas unitarias con mocks.

En los tests automatizados de `tests/`, las funciones LLM se simulan para comprobar que el workflow funciona sin gastar cuota ni depender de red. En cambio, las evaluaciones descritas aquí se ejecutaron con un modelo real:

- modelo evaluado: `openai/gpt-oss-20b`, modelo abierto de la familia gpt-oss con capacidad de razonamiento, seguimiento de instrucciones y generación de código;
- infraestructura: servidor vLLM universitario;
- perfil técnico de configuración: `university`;
- endpoint compatible con OpenAI: `https://w1.etsisi.upm.es/vllm/v1`;
- script de evaluación: `scripts/evaluate_llm_profiles.py`;
- entorno Python: `venv\Scripts\python.exe`.

Por tanto, cuando se indica que una query completó con `LLM real`, significa que el sistema hizo llamadas efectivas a `openai/gpt-oss-20b` servido mediante vLLM universitario, modelo elegido por su capacidad de razonamiento, seguimiento de instrucciones y generación de código para análisis de consulta, generación de código y/o interpretación final. No se trata de una respuesta simulada por los tests.

Además, se han realizado pruebas adicionales con los otros perfiles preparados:

- Groq con `llama-3.3-70b-versatile`, modelo Llama 3.3 70B Instruct orientado a razonamiento general y baja latencia;
- Gemini con `gemini-2.5-flash`, modelo Flash de Gemini 2.5 orientado a rapidez y razonamiento.

Los resultados principales de robustez se construyeron primero con `openai/gpt-oss-20b`, modelo abierto de la familia gpt-oss servido por vLLM universitario. Posteriormente se comprobó que Groq con `llama-3.3-70b-versatile` completa la batería compleja y que Gemini con `gemini-2.5-flash` completa consultas puntuales, aunque su evaluación completa queda limitada por cuota.

## Queries Nuevas

| ID | Datos usados | Que evalua |
|---|---|---|
| `complex_nvda_growth_report` | NVDA 5 años | crecimiento, máximo, mínimo, volatilidad y conclusión |
| `complex_nvda_amd_ranking` | NVDA/AMD 2 años | ranking, rentabilidad, volatilidad y drawdown |
| `complex_aapl_overview_volume` | AAPL 3 meses | tendencia, rango de precios y dias de mayor volumen |
| `complex_aapl_technical_context` | AAPL 3 meses | medias moviles 20/50, volatilidad y contexto técnico |
| `complex_qqq_spy_risk_return` | QQQ/SPY 2024 | rentabilidad, volatilidad y correlacion |
| `complex_qqq_spy_drawdown` | QQQ/SPY 2024 | drawdown, mejor/peor día y riesgo relativo |
| `complex_btc_2024_profile` | BTC-USD 2024 | perfil histórico de cripto con volatilidad y extremos |
| `complex_sp500_since_2020` | S&P 500 desde 2020 | crecimiento, volatilidad y drawdown de indice amplió |
| `complex_eurusd_intraday` | EUR/USD 10 dias 1h | análisis intradía con rango y volatilidad horaria |
| `complex_gold_intraday` | Oro 1 semana 1h | commodity intradía, rango, volumen y volatilidad |

## Cambios Para Que Funcionen

Se añadió `src/execution/market_data.py` con helpers reutilizables:

- `load_market_data`: normaliza CSV anchos de yfinance a formato largo con columnas `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`.
- `load_close_prices`: devuelve una matriz de cierres con indice `Date` y una columna por ticker.
- `ticker_summary`: calcula resumen básico por activo.
- `make_json_safe`: convierte valores de pandas/numpy a tipos serializables antes de `json.dumps`.

También se reforzó el prompt de codegen:

- usar `Path(sys.argv[1]).read_text` para leer el payload;
- no usar `open`;
- no usar `pd.read_csv` directamente;
- usar `load_close_prices` para cierres;
- usar `load_market_data` para OHLCV;
- convertir `Series` a escalares antes de compararlas;
- aplicar `make_json_safe` antes de imprimir JSON.

## Tratamiento De Errores

Se incorporaron medidas para reducir fallos observados durante la evaluación:

- reintentos LLM cuando la respuesta de análisis o codegen no es JSON válido;
- reintentos LLM ante errores transitorios de llamada, como timeout;
- reparación LLM del código si no supera la capa de seguridad;
- reparación LLM del código si falla durante la ejecución;
- aumento de `LLM_MAX_TOKENS` a `4096`;
- aumento de `LLM_TIMEOUT_SECONDS` a `120`;
- ejecución del script generado con `PYTHONPATH` apuntando a la raíz del proyecto.

## Errores Observados Durante El Desarrollo

La evaluación no fue lineal ni salio bien desde el primer intento. Esto es importante para la memoria porque muestra el proceso real de construccion del sistema y justifica las decisiones tecnicas posteriores.

### Primera Evaluación Del Flujo Nuevo

Al probar las seis queries base con `openai/gpt-oss-20b` servido por vLLM universitario, modelo abierto de la familia gpt-oss usado por su capacidad de razonamiento y generación de código, todas terminaron inicialmente en `completed_with_error`.

Los problemas observados fueron:

- respuestas de codegen que no eran JSON válido;
- código Python con errores de sintaxis, por ejemplo f-strings mal cerradas;
- uso de `open()`, bloqueado por la capa de seguridad;
- lectura incorrecta de CSV con `pd.read_csv`, porque los CSV de yfinance tienen cabeceras anchas;
- scripts que esperaban una columna `Date` directa cuando el fichero tenía estructura `Ticker/Price/Date`;
- respuestas vacías o no parseables del proveedor.

Este resultado mostró que la interpretación de intención era razonable, pero la generación de código era el cuello de botella.

### Incoherencia Del Contrato Inicial

También aparecio una incoherencia del propio sistema: el prompt pedia al script leer el payload desde `argv[1]`, pero la capa de seguridad bloqueaba `open()`. Algunos codigos generados intentaban leer el fichero de entrada con `open`, lo que producia rechazo de seguridad.

La solucion fue fijar una forma permitida y explícita:

```python
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
```

### Problemas Con El Formato De Datos

Los CSV descargados con yfinance no siempre son tablas simples con columnas `Date`, `Close`, etc. En varios casos son tablas anchas con dos filas de cabecera:

- fila `Ticker`: ticker repetido por cada campo;
- fila `Price`: `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`;
- fila `Date`;
- datos históricos.

El LLM tendía a asumir un CSV simple. Para evitar que tuviera que adivinar el formato, se incorporo `src/execution/market_data.py`.

### Problemas Tipicos De Pandas Y JSON

También aparecieron errores normales cuando se genera código con pandas:

- comparaciones ambiguas de `Series`, por ejemplo `if hourly_vol < 0.5`;
- objetos `numpy.bool_` no serializables por `json.dumps`;
- `Timestamp` de pandas no serializable;
- valores `NaN` o infinitos;
- resultados con Series o arrays en vez de escalares.

Para tratarlo se añadió `make_json_safe` y se reforzó el prompt para pedir conversión explícita a escalares.

### Timeouts Y Respuestas No Parseables

Algunas queries complejas producen prompts largos y código más extenso. En una pasada completa, `complex_nvda_growth_report` fallo por timeout durante codegen. La query no fallo por datos ni por ejecución, sino por una incidencia transitoria del proveedor.

Para reducir este problema se aumento:

- `LLM_MAX_TOKENS`: de `2048` a `4096`;
- `LLM_TIMEOUT_SECONDS`: de `60` a `120`;
- número de intentos LLM: de `2` a `3`.

Después de este ajuste, la query completo correctamente en ejecución individual.

## Evolución De La Robustez

La evolución experimental puede resumirse así:

| Fase | Resultado | Lectura |
|---|---:|---|
| Seis queries base con flujo LLM/codegen inicial | 0/6 completadas | El diseño era correcto, pero codegen era fragil |
| Dos queries tras helper de carga y PYTHONPATH | 1/2 completadas | La lectura de datos empezó a estabilizarse |
| Query compleja QQQ/SPY tras reintento de JSON | 1/1 completada | Los reintentos recuperaron respuestas no parseables |
| Diez queries complejas antes de ultimos ajustes | 5/10 completadas | Persistian errores pandas, JSON y timeout |
| Cinco queries fallidas tras `make_json_safe` y prompt reforzado | 4/5 completadas | Se corrigieron errores de serialización y Series |
| S&P 500 con reparación de código | 1/1 completada | La reparación LLM recuperó código con sintaxis inválida |
| Diez queries complejas tras ajustes | 9/10 completadas | Solo quedo un timeout transitorio |
| Reejecucion de NVDA tras timeout/reintentos | 1/1 completada | El caso pendiente completo |

Esta progresión es relevante porque demuestra que el sistema no se limito a ejecutar queries exitosas, sino que se fue endureciendo a partir de errores reales.

## Estado De Pruebas

Con `openai/gpt-oss-20b` servido por vLLM universitario, la pasada completa de las diez queries complejas dejó 9 de 10 completadas. La única query pendiente en esa pasada fue `complex_nvda_growth_report`, que fallo por timeout del proveedor en codegen.

Tras subir timeout y activar reintentos ante errores de llamada LLM, `complex_nvda_growth_report` completo correctamente en una ejecución individual con el mismo modelo.

Resultados relevantes:

- `results/evaluations/llm_profile_evaluation_20260526_182710.json`: pasada completa de diez queries complejas, 9/10 completadas.
- `results/evaluations/llm_profile_evaluation_20260526_182948.json`: reejecucion de `complex_nvda_growth_report`, completada.
- `results/evaluations/llm_profile_evaluation_20260526_184630.json`: Groq con `llama-3.3-70b-versatile`, modelo Llama 3.3 70B Instruct, diez queries complejas completadas.
- `results/evaluations/llm_profile_evaluation_20260526_184727.json`: Gemini con `gemini-2.5-flash`, modelo Flash de Gemini 2.5, query compleja QQQ/SPY completada tras un fallo previo por cuota.

## Resultados Observados

La siguiente tabla resume los resultados principales de la pasada completa `llm_profile_evaluation_20260526_182710.json` y la reejecucion posterior de NVDA.

Modelo usado en estos resultados: `openai/gpt-oss-20b` sobre servidor vLLM universitario, elegido por su capacidad de razonamiento, seguimiento de instrucciones y generación de código. Groq con `llama-3.3-70b-versatile` y Gemini con `gemini-2.5-flash` se documentan como modelos comparativos.

## Comparativa Inicial Entre Modelos

Después de validar el flujo con `openai/gpt-oss-20b` sobre vLLM universitario, se probaron Groq con `llama-3.3-70b-versatile` y Gemini con `gemini-2.5-flash`.

| Modelo / proveedor | Prueba realizada | Resultado | Observación |
|---|---:|---:|---|
| `openai/gpt-oss-20b` sobre vLLM universitario | 10 queries complejas | 9/10 en pasada completa; 10/10 tras reejecutar el timeout | Modelo abierto de la familia gpt-oss, principal para depuración por razonamiento, seguimiento de instrucciones y generación de código |
| `llama-3.3-70b-versatile` en Groq | 10 queries complejas | 10/10 completadas | Modelo Llama 3.3 70B Instruct; muy rápido en esta prueba y con una reparación automática de código |
| `gemini-2.5-flash` en Gemini | 2 queries puntuales | 2/2 completadas tras reintento | Modelo Flash de Gemini 2.5; rápido, pero con una ejecución intermedia fallida por cuota `429` |

Lectura:

- Groq con `llama-3.3-70b-versatile` funciona con las queries complejas actuales y, en esta ejecución, fue el perfil más rápido.
- Gemini con `gemini-2.5-flash` también funciona en consultas individuales, pero la cuota gratuita puede interrumpir la evaluación si se lanzan varias llamadas seguidas.
- `openai/gpt-oss-20b` sobre vLLM universitario queda como modelo principal documentado en el proceso de depuración, porque con él se observaron y corrigieron los errores iniciales del flujo y se aprovechó su capacidad de razonamiento y generación de código.

| Query | Estado | Tiempo | Resultado principal |
|---|---:|---:|---|
| `complex_nvda_growth_report` | fallo por timeout en pasada completa | 204.21 s | El plan LLM fue correcto, pero codegen excedio el tiempo de espera |
| `complex_nvda_growth_report` reejecutada | completada | 85.22 s | NVDA paso de 13.34 a 183.22; crecimiento 1273.33%; máximo 207.04; mínimo 11.23 |
| `complex_nvda_amd_ranking` | completada | 65.66 s | NVDA rentabilidad 107.13%, AMD 3.11%; NVDA queda primera |
| `complex_aapl_overview_volume` | completada | 55.70 s | AAPL muestra tendencia bajista; rango 246.70-278.12; mayor volumen el 2025-12-19 |
| `complex_aapl_technical_context` | completada | 62.08 s | SMA20 262.60, SMA50 262.33, ultimo cierre 252.82 por debajo de ambas medias |
| `complex_qqq_spy_risk_return` | completada | 49.58 s | QQQ retorno 28.07%, SPY 24.45%; QQQ más volatil; correlacion 0.945 |
| `complex_qqq_spy_drawdown` | completada | 51.98 s | QQQ drawdown aprox. -13.85%, SPY -8.54%; QQQ presenta más riesgo histórico |
| `complex_btc_2024_profile` | completada | 86.66 s | BTC retorno 109.76%, mínimo 39507.37, máximo 106140.60 |
| `complex_sp500_since_2020` | completada | 52.40 s | S&P 500 crecimiento 105.64%, volatilidad anualizada 20.71%, drawdown -33.92% |
| `complex_eurusd_intraday` | completada | 52.82 s | EUR/USD cambio -0.87%, rango intradía medio 0.0088, volatilidad horaria 0.00117 |
| `complex_gold_intraday` | completada | 52.86 s | Oro cambio total -183.30, rango max-min 278.60, volatilidad horaria 0.00299 |

### Lectura De Resultados

Los resultados muestran que el sistema puede resolver consultas más complejas que las seis queries base iniciales. Las respuestas finales no solo devuelven un número, sino que combinan varias métricas y explican su significado.

Ejemplos:

- En `complex_qqq_spy_risk_return`, el sistema no solo calcula rentabilidad, sino también volatilidad y correlacion.
- En `complex_aapl_technical_context`, combina medias moviles y posicion del ultimo cierre.
- En `complex_sp500_since_2020`, resume crecimiento, extremos, volatilidad y drawdown.
- En `complex_eurusd_intraday` y `complex_gold_intraday`, el flujo trabaja con datos horarios, no solo diarios.

También se observa que el sistema conserva trazabilidad: cada evaluación guarda plan, código generado, salida de ejecución, respuesta final y tiempos.

## Donde Encaja En La Memoria

Este material puede encajar especialmente en:

- metodología: para explicar la evaluación iterativa y la revisión humana;
- diseño del sistema: para justificar helpers de carga, capa de seguridad y reparación;
- implementación: para describir `market_data.py`, reintentos y contrato de codegen;
- resultados: para presentar la progresión de fallos a completitud;
- limitaciones: para reconocer dependencia del proveedor LLM, timeouts y variabilidad;
- trabajo futuro: para proponer más proveedores, más repeticiones por query y métricas estadísticas.

Una posible redacción para memoria sería:

> La evaluación del MVP no consistió únicamente en ejecutar casos exitosos. Durante las pruebas con LLM real se observaron fallos de formato JSON, errores de sintaxis en código generado, lecturas incorrectas de CSV, problemas de serialización con pandas/numpy y timeouts del proveedor. Estos fallos motivaron la incorporación de helpers de carga de datos, validación de seguridad, conversión de salidas a JSON seguro, reintentos de llamadas LLM y reparación automática de código. Como resultado, el sistema pasó de no completar las consultas base con el flujo inicial a resolver la mayoría de las consultas complejas sobre los mismos datos históricos.

## Comandos De Evaluación

```powershell
venv\Scripts\python.exe scripts\evaluate_llm_profiles.py --profiles university --examples complex_nvda_growth_report complex_nvda_amd_ranking complex_aapl_overview_volume complex_aapl_technical_context complex_qqq_spy_risk_return complex_qqq_spy_drawdown complex_btc_2024_profile complex_sp500_since_2020 complex_eurusd_intraday complex_gold_intraday
```

Para probar una query concreta:

```powershell
venv\Scripts\python.exe run_mvp.py --example complex_qqq_spy_risk_return
```

## Lectura Para La Memoria

Estas pruebas muestran que el cuello de botella principal no es la interpretación de la consulta, sino la estabilidad del código generado. Al introducir helpers de carga de datos, validación, reparación y reintentos, el sistema pasa de fallos frecuentes por formato CSV, JSON inválido o errores de pandas a una ejecución mayoritariamente correcta sobre consultas más complejas.
