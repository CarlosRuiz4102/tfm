# Detalle completo de una iteracion del workflow

Este documento explica una iteracion real del proyecto de extremo a extremo. El objetivo es mostrar que ocurre desde que una query entra en el evaluador hasta que quedan guardados el codigo generado, el payload, la salida estructurada y la respuesta final.

## Iteracion seleccionada

La iteracion usada como ejemplo pertenece a la evaluacion ejecutada el `2026-06-02`.

| Campo | Valor |
|---|---|
| Perfil LLM | `groq` |
| Modelo | `llama-3.3-70b-versatile` |
| Query ID | `level_b_qqq_spy_clear_compare` |
| Nivel | `B` |
| Estado final | `completed` |
| Tiempo total | `23.52 s` |
| Avisos | Ninguno |

Consulta:

> Comparame QQQ y SPY en 2024 de forma clara, con tabla y grafica normalizada

Esta query es util como ejemplo porque obliga al sistema a generar texto, una tabla comparativa y datos para una visualizacion.

## Como se lanza

La matriz completa de evaluacion se lanza con:

```powershell
python scripts\evaluate_progressive_llm_scope.py --profiles groq gemini university
```

Para repetir solo la iteracion descrita en este documento:

```powershell
python scripts\evaluate_progressive_llm_scope.py --profiles groq --cases level_b_qqq_spy_clear_compare
```

El script principal de evaluacion es:

```text
scripts/evaluate_progressive_llm_scope.py
```

La bateria de consultas se importa desde:

```text
scripts/generate_qualitative_demo_report.py
```

La constante `DEMO_CASES` contiene el ID, nivel, objetivo esperado y entrada estructurada de cada query.

## Entrada definida para el caso

El caso `level_b_qqq_spy_clear_compare` se define con:

```json
{
  "query": "Comparame QQQ y SPY en 2024 de forma clara, con tabla y grafica normalizada",
  "intent": "improved_asset_comparison",
  "tickers": ["QQQ", "SPY"],
  "start": "2024-01-01",
  "end": "2024-12-31",
  "interval": "1d",
  "csv_paths": [
    "data/raw/qqq_y_spy_desde_20240101_hasta_20241231.csv"
  ],
  "warnings": []
}
```

No se descargan datos durante la iteracion. El workflow usa el CSV local:

```text
data/raw/qqq_y_spy_desde_20240101_hasta_20241231.csv
```

## Secuencia general

```text
scripts/evaluate_progressive_llm_scope.py
  -> selecciona perfil y query
  -> src.config.LLMConfig.from_env()
  -> src.graph.build_graph.build_workflow()
  -> ingest_node
  -> llm_analysis_node
  -> code_generation_node
  -> code_security_node
  -> code_execution_node
  -> interpretation_node
  -> evaluador calcula indicadores de cobertura
  -> evaluador guarda JSON global e informe Markdown
```

## Paso 1: seleccion del perfil

La funcion `_run_case` de `scripts/evaluate_progressive_llm_scope.py` asigna:

```python
os.environ["LLM_PROFILE"] = profile
config = LLMConfig.from_env()
```

Para este caso, `profile` vale `groq`. La clase `LLMConfig` se encuentra en:

```text
src/config.py
```

El perfil resuelve:

| Campo | Valor |
|---|---|
| API compatible | `https://api.groq.com/openai/v1` |
| Variable de clave | `GROQ_API_KEY` |
| Variable de modelo | `GROQ_MODEL` |
| Modelo usado | `llama-3.3-70b-versatile` |

La clave se lee desde el entorno local. No se copia a informes ni artefactos.

## Paso 2: construccion del workflow

El evaluador llama:

```python
workflow = build_workflow()
```

La funcion se define en:

```text
src/graph/build_graph.py
```

El orden de nodos es:

```text
ingest
-> llm_analysis
-> code_generation
-> code_security
-> code_execution
-> interpretation
```

Si `langgraph` esta instalado, se construye un grafo con transiciones condicionales. Si no esta disponible, se usa `SimpleFinancialWorkflow`, que ejecuta la misma secuencia.

## Paso 3: validacion de entrada

El primer nodo es:

```text
src/graph/nodes.py -> ingest_node
```

Este nodo reconstruye `FinancialQueryInput` y llama:

```text
src/graph/validation.py -> validate_input
```

La validacion comprueba:

- que la query no este vacia;
- que exista al menos un ticker;
- que exista al menos una ruta CSV;
- que `start` y `end` tengan formato ISO `YYYY-MM-DD`;
- que el CSV exista en disco.

Como la entrada es valida, el estado pasa de `created` a `ingested`.

## Paso 4: plan de analisis generado por LLM

El segundo nodo es:

```text
src/graph/nodes.py -> llm_analysis_node
```

Este nodo llama:

```text
src/llm/pipeline.py -> build_llm_analysis
```

Los mensajes enviados al modelo se construyen en:

```text
src/llm/prompts.py -> build_analysis_messages
```

El prompt exige un JSON con intencionalidad, tipo de analisis, metricas, columnas necesarias, requisitos de datos, requisitos de salida, preferencias de presentacion y razonamiento.

Plan real devuelto para esta iteracion:

```json
{
  "interpreted_intent": "Comparar el rendimiento de QQQ y SPY en 2024",
  "analysis_type": "Comparativa de activos financieros",
  "metrics": [
    "Precio de cierre",
    "Retorno diario",
    "Volatilidad",
    "Media movil de 50 dias"
  ],
  "required_columns": [
    "Fecha",
    "Ticker",
    "Precio de cierre"
  ],
  "data_requirements": [
    "Datos historicos de QQQ y SPY en 2024"
  ],
  "output_requirements": [
    "Tabla comparativa de rendimiento",
    "Grafica normalizada de precios de cierre"
  ],
  "presentation_preferences": [
    "Nivel B: Analisis mas completo con tabla y grafica principal"
  ]
}
```

El estado pasa a `planned`.

## Paso 5: generacion de codigo Python

El tercer nodo es:

```text
src/graph/nodes.py -> code_generation_node
```

Este nodo llama:

```text
src/llm/pipeline.py -> build_llm_code
```

Los mensajes se construyen en:

```text
src/llm/prompts.py -> build_codegen_messages
```

El contrato obliga al modelo a:

- devolver JSON estricto con un campo `code`;
- crear una funcion `main()`;
- leer el payload desde `Path(sys.argv[1]).read_text`;
- usar helpers de `src.execution.market_data`;
- evitar `open()` y `pd.read_csv`;
- imprimir un unico JSON mediante `json.dumps`;
- pasar la salida por `make_json_safe`;
- devolver tabla y datos visuales cuando la query los pide;
- limitar series visuales largas a un maximo de 120 puntos.

El codigo real generado se guarda despues en:

```text
results/code/generated_20260602_170216_529949.py
```

En esta iteracion el script:

- carga cierres con `load_close_prices`;
- filtra el periodo 2024;
- calcula retornos diarios;
- calcula volatilidad anualizada sobre ventana movil;
- calcula media movil de 50 dias;
- normaliza las series;
- crea `table_data`;
- crea `chart_data` con 120 puntos por ticker;
- escribe el JSON por `stdout`.

El estado pasa a `code_generated`.

## Paso 6: control de seguridad

El cuarto nodo es:

```text
src/graph/nodes.py -> code_security_node
```

La validacion se implementa en:

```text
src/execution/code_security.py -> validate_generated_code
```

El codigo se parsea mediante AST. La capa comprueba:

- presencia de `main()`;
- presencia de `json.dumps`;
- imports permitidos;
- ausencia de llamadas bloqueadas como `eval`, `exec`, `compile`, `open`, `input` o `__import__`;
- ausencia de modulos bloqueados como `os`, `subprocess`, `socket`, `requests` o `httpx`.

El codigo de esta iteracion supera la validacion. El estado pasa a `code_validated`.

Si el codigo fuese rechazado, el nodo intentaria una reparacion mediante:

```text
src/llm/pipeline.py -> repair_llm_code
src/llm/prompts.py -> build_code_repair_messages
```

La version reparada vuelve a pasar por seguridad antes de ejecutarse.

## Paso 7: preparacion del payload de ejecucion

El quinto nodo es:

```text
src/graph/nodes.py -> code_execution_node
```

Antes de ejecutar el script se construye un payload con:

- query original;
- tickers;
- rutas CSV;
- fechas o periodo;
- intervalo;
- entrada completa;
- plan de analisis.

El payload real queda guardado en:

```text
results/logs/payload_20260602_170216_529949.json
```

Este fichero permite reconstruir exactamente con que entrada y plan se ejecuto el codigo.

## Paso 8: ejecucion controlada

La ejecucion se delega a:

```text
src/execution/code_runner.py -> run_generated_code
```

Esta funcion:

1. Crea `results/code/` y `results/logs/` si no existen.
2. Genera un identificador temporal.
3. Escribe el script Python generado.
4. Escribe el payload JSON.
5. Anade la raiz del proyecto a `PYTHONPATH`.
6. Ejecuta un proceso separado con `subprocess.run`.
7. Captura `stdout`, `stderr` y `returncode`.
8. Intenta parsear `stdout` como JSON.
9. Devuelve rutas de artefactos auditables.

La orden equivalente es:

```text
python results/code/generated_20260602_170216_529949.py results/logs/payload_20260602_170216_529949.json
```

Artefactos reales:

| Tipo | Ruta | Tamano |
|---|---|---:|
| Script generado | `results/code/generated_20260602_170216_529949.py` | 2302 bytes |
| Payload | `results/logs/payload_20260602_170216_529949.json` | 1774 bytes |
| Stdout | `results/logs/stdout_20260602_170216_529949.json` | 5624 bytes |
| Stderr | `results/logs/stderr_20260602_170216_529949.log` | 0 bytes |

El `returncode` es `0`, por lo que el estado pasa a `executed`.

## Paso 9: salida estructurada

El JSON completo esta en:

```text
results/logs/stdout_20260602_170216_529949.json
```

Resumen de la tabla producida:

| Ticker | Precio de cierre | Retorno diario medio | Volatilidad | Media movil 50 dias |
|---|---:|---:|---:|---:|
| QQQ | 515.61 | 0.001054 | 0.1745 | 510.13 |
| SPY | 588.22 | 0.000907 | 0.1215 | 592.79 |

La salida incluye tambien `chart_data` con:

- tipo sugerido: `line`;
- serie QQQ: 120 puntos;
- serie SPY: 120 puntos.

## Paso 10: compactacion antes de interpretar

Antes de enviar la salida al segundo agente se llama:

```text
src/graph/nodes.py -> _compact_for_interpretation
```

Esta funcion limita listas extensas y textos largos. La salida completa permanece en `results/logs/stdout_*.json`, pero el segundo agente recibe una version adecuada para el contexto disponible.

## Paso 11: interpretacion final

El sexto nodo es:

```text
src/graph/nodes.py -> interpretation_node
```

El nodo llama:

```text
src/llm/pipeline.py -> build_llm_interpretation
src/llm/prompts.py -> build_interpretation_messages
```

El segundo agente debe explicar las metricas, respetar el nivel solicitado, distinguir datos historicos y limitaciones, y evitar predicciones o recomendaciones de inversion.

Para esta iteracion se genero una respuesta final de `1777` caracteres con:

- tabla comparativa;
- explicacion de retornos;
- comparacion de volatilidad;
- lectura de la grafica normalizada;
- limitaciones del analisis historico.

El estado final pasa a `completed`.

## Paso 12: indicadores del evaluador

Cuando termina el workflow, `scripts/evaluate_progressive_llm_scope.py` calcula indicadores simples:

```json
{
  "completed": true,
  "has_analysis_plan": true,
  "has_execution_output": true,
  "has_final_answer": true,
  "has_table_data": true,
  "has_visual_data_when_expected": true,
  "forbidden_terms": [],
  "answer_length_chars": 1777
}
```

Estos indicadores no sustituyen a la revision humana. Sirven para localizar rapidamente casos completos, parciales o sospechosos.

## Paso 13: informe global de la matriz

Al terminar las 45 iteraciones, el evaluador genera:

```text
results/reports/evaluacion_15_queries_llms.md
```

Este Markdown contiene:

- resumen global;
- cobertura por perfil y nivel;
- matriz de 45 resultados;
- detalle por perfil;
- plan, salida estructurada y respuesta final de cada ejecucion;
- avisos y errores registrados.

Tambien genera el JSON completo:

```text
results/evaluations/progressive_llm_scope_20260602_174049.json
```

El JSON es la fuente mas completa para auditoria automatica. El Markdown es la version comoda para revision humana.

## Carpetas de resultados

| Carpeta | Contenido |
|---|---|
| `results/code/` | Scripts Python generados por el primer agente |
| `results/logs/` | Payloads, stdout y stderr de cada ejecucion controlada |
| `results/evaluations/` | JSON global con todas las iteraciones |
| `results/reports/` | Informe Markdown y graficas auxiliares de cobertura |

Estas carpetas estan ignoradas por Git porque contienen artefactos regenerables de ejecucion.

## Que revisar manualmente

Para auditar una iteracion:

1. Abrir el caso en `results/reports/evaluacion_15_queries_llms.md`.
2. Leer el plan del primer agente.
3. Abrir el script correspondiente en `results/code/`.
4. Confirmar que solo usa CSV locales y helpers permitidos.
5. Abrir el payload en `results/logs/payload_*.json`.
6. Comparar el JSON de `stdout` con la respuesta final.
7. Revisar `stderr`.
8. Aplicar la rubrica de `docs/evaluacion_cualitativa_llm.md`.

## Limitacion importante

Que una iteracion termine con `completed` no demuestra por si solo que el analisis sea perfecto. En este ejemplo, la respuesta es util y trazable, pero la revision humana debe valorar si la seleccion de metricas y la interpretacion son las mas adecuadas para la query.
