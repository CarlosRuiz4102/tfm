# Sistema LLM para analisis financiero historico con generacion automatica de codigo

## Resumen

Este repositorio contiene la implementacion del prototipo desarrollado para el Trabajo Fin de Master. El sistema estudia si una arquitectura multiagente basada en LLM puede transformar una consulta financiera en lenguaje natural en una respuesta historica trazable, apoyada en datos descargados, calculos observables, codigo ejecutado y una interpretacion final prudente.

El objetivo del proyecto no es predecir el mercado ni recomendar inversiones. El foco esta en el analisis historico descriptivo y en el control del flujo: validacion de entradas, planificacion estructurada, generacion de codigo Python, validacion previa a la ejecucion, ejecucion controlada y trazabilidad completa por corrida.

## Alcance

El sistema esta pensado para:

- recibir una consulta financiera en lenguaje natural;
- resolver tickers y contexto temporal;
- descargar datos historicos mediante `yfinance`;
- planificar el analisis con un LLM;
- generar y validar codigo Python antes de ejecutarlo;
- redactar una respuesta final basada solo en los resultados obtenidos.

Queda fuera del alcance:

- prediccion de precios futuros;
- recomendaciones de compra o venta;
- uso de noticias, macroeconomia o analisis fundamental como parte del flujo principal;
- sustitucion del criterio profesional de un analista financiero.

## Arquitectura del workflow

El workflow principal se construye en [src/graph/build_graph.py](/C:/Users/usuario/Desktop/tfm/src/graph/build_graph.py) y recorre estas etapas:

1. `ingest_node`: valida la consulta de entrada.
2. `data_request_planning_node`: convierte la consulta en un `FinancialDataRequest`.
3. `data_request_structural_validation_node`: comprueba que la peticion de datos tiene una forma valida antes de tocar el proveedor.
4. `data_download_node`: descarga, normaliza y valida operativamente los datos historicos.
5. `llm_analysis_node`: elabora el plan analitico.
6. `code_generation_node`: genera el script Python.
7. `code_validation_node`: revisa el codigo antes de ejecutarlo.
8. `code_execution_node`: ejecuta el script en un entorno controlado y valida el resultado.
9. `interpretation_node`: redacta la respuesta final para el usuario.

El flujo incorpora rutas terminales para estados `invalid`, `blocked`, `error`, `code_rejected` y `execution_failed`, de forma que incluso una ejecucion no completada deje una salida coherente y trazable.

## Estructura del repositorio

```text
tfm/
  README.md
  requirements.txt
  .env.example
  run_mvp.py
  data/
    catalog/
  docs/
  results/
  scripts/
  src/
  tests/
```

Directorios y ficheros clave:

- [run_mvp.py](/C:/Users/usuario/Desktop/tfm/run_mvp.py): punto de entrada principal del MVP.
- [src](/C:/Users/usuario/Desktop/tfm/src): implementacion del workflow, esquemas, cliente LLM, descarga de datos y ejecucion.
- [tests](/C:/Users/usuario/Desktop/tfm/tests): pruebas unitarias e integracion del flujo.
- [scripts/evaluate_bateria_50.py](/C:/Users/usuario/Desktop/tfm/scripts/evaluate_bateria_50.py): ejecuta la bateria de 50 ejemplos y actualiza el informe de evaluacion.
- [data/catalog/bateria_50_ejemplos_v2.json](/C:/Users/usuario/Desktop/tfm/data/catalog/bateria_50_ejemplos_v2.json): catalogo base de la bateria.
- [results](/C:/Users/usuario/Desktop/tfm/results): artefactos generados durante ejecuciones y evaluaciones.
- [docs](/C:/Users/usuario/Desktop/tfm/docs): memoria, presentacion, guias y material complementario del TFM.

## Requisitos

- Python `3.10` o superior.
- Acceso a un endpoint compatible con OpenAI Chat Completions para ejecutar las fases LLM reales.
- Conectividad a `yfinance` para descargar datos historicos en ejecuciones completas.

Las dependencias del proyecto se recogen en [requirements.txt](/C:/Users/usuario/Desktop/tfm/requirements.txt). El fichero se mantiene porque sigue siendo la via directa de reproduccion del MVP.

## Instalacion

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuracion del LLM

La configuracion se centraliza en [src/config.py](/C:/Users/usuario/Desktop/tfm/src/config.py) y puede cargarse automaticamente desde un fichero `.env`.

Hay una plantilla lista para copiar en [.env.example](/C:/Users/usuario/Desktop/tfm/.env.example):

```env
LLM_PROVIDER=openai-compatible

VLLM_BASE_URL=https://servidor-vllm.example/v1
VLLM_API_KEY=your_vllm_key_here
VLLM_MODEL=openai/gpt-oss-20b

OPENAI_BASE_URL=
OPENAI_API_KEY=
OPENAI_MODEL=openai/gpt-oss-20b

LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=

LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_TIMEOUT_SECONDS=120

# OPENAI_VERIFY_SSL=false
```

Orden de prioridad de variables soportadas por el codigo:

1. familia `VLLM_*`
2. familia `UNIVERSITY_*` cuando exista en el entorno
3. familia generica `LLM_*`
4. familia `OPENAI_*`

Si no hay credenciales validas, el sistema no completa las fases LLM reales y devuelve un error controlado. Esto esta cubierto por la logica de [src/llm/client.py](/C:/Users/usuario/Desktop/tfm/src/llm/client.py) y por las pruebas de configuracion.

## Ejecucion del MVP

### Ejecutar un ejemplo interno

```powershell
python run_mvp.py --example overview_aapl
```

### Ejecutar una consulta desde JSON

```powershell
python run_mvp.py --input-json .\mi_consulta.json
```

Ejemplo minimo de entrada:

```json
{
  "query": "Analiza AAPL en 3 meses y explica que se puede concluir solo con estos datos historicos."
}
```

La salida del programa es el `WorkflowState` final serializado como JSON.

### Ver ejemplos disponibles

Los ejemplos embebidos viven en [src/examples/sample_inputs.py](/C:/Users/usuario/Desktop/tfm/src/examples/sample_inputs.py). Se usan para pruebas manuales y demostraciones. Algunos campos auxiliares como `csv_paths` se conservan por compatibilidad con material de evaluacion previo, pero la ejecucion normal del flujo parte de la `query`.

### Ayuda del ejecutable

```powershell
python run_mvp.py --help
```

## Evaluacion de la bateria de 50 ejemplos

El repositorio incluye una bateria de 50 consultas en [data/catalog/bateria_50_ejemplos_v2.json](/C:/Users/usuario/Desktop/tfm/data/catalog/bateria_50_ejemplos_v2.json) y un script de ejecucion en [scripts/evaluate_bateria_50.py](/C:/Users/usuario/Desktop/tfm/scripts/evaluate_bateria_50.py).

Ejemplo de uso:

```powershell
python scripts/evaluate_bateria_50.py --start 1 --count 5
```

Este proceso actualiza:

- `results/evaluations/bateria_50_ejemplos_v2_results.json`
- `docs/evaluacion_bateria_50_ejemplos_v2.md`

## Artefactos generados

Durante las ejecuciones el sistema puede crear o actualizar estas carpetas:

- `results/data_requests/`: peticiones de datos construidas por el workflow.
- `results/data_raw/`: descargas brutas del proveedor.
- `results/data_normalized/`: datos normalizados para analisis.
- `results/code/`: scripts Python generados.
- `results/logs/`: logs de ejecucion del codigo generado.
- `results/traces/`: trazas estructuradas por corrida.
- `results/evaluations/`: resultados agregados de la bateria de evaluacion.

La logica de trazabilidad esta en [src/tracing/workflow_trace.py](/C:/Users/usuario/Desktop/tfm/src/tracing/workflow_trace.py). Cada corrida puede guardar `manifest.json`, `events.jsonl` y snapshots completos del estado por nodo.

## Pruebas

El proyecto incluye pruebas en [tests](/C:/Users/usuario/Desktop/tfm/tests) para configuracion del LLM, prompts, trazabilidad y distintas fases del flujo.

Suite completa:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Estado actual de la suite:

- varias pruebas de integracion usan rutas `csv_paths` heredadas en [src/examples/sample_inputs.py](/C:/Users/usuario/Desktop/tfm/src/examples/sample_inputs.py);
- esas rutas apuntan a ficheros historicos bajo `data/raw/`;
- en el estado actual del repositorio esos CSV no estan presentes, por lo que la suite completa falla si no se restauran esos fixtures.

Comprobacion minima sin depender de esos CSV:

```powershell
python -m unittest tests.test_llm_config tests.test_prompts tests.test_phase5
```

Comprobacion rapida de compilacion:

```powershell
python -m compileall -q src run_mvp.py scripts
```

## Documentacion adicional

Material relevante del TFM:

- memoria en [docs/memoria_latex/main.tex](/C:/Users/usuario/Desktop/tfm/docs/memoria_latex/main.tex);
- PDF compilado en [docs/memoria_latex/main.pdf](/C:/Users/usuario/Desktop/tfm/docs/memoria_latex/main.pdf);
- capitulo metodologico en [docs/memoria_latex/chapters/04_metodologia_compacta.tex](/C:/Users/usuario/Desktop/tfm/docs/memoria_latex/chapters/04_metodologia_compacta.tex);
- capitulo del flujo multiagente en [docs/memoria_latex/chapters/05_flujo_multiagente.tex](/C:/Users/usuario/Desktop/tfm/docs/memoria_latex/chapters/05_flujo_multiagente.tex);
- capitulo de resultados en [docs/memoria_latex/chapters/06_resultados_evaluacion_compacta.tex](/C:/Users/usuario/Desktop/tfm/docs/memoria_latex/chapters/06_resultados_evaluacion_compacta.tex);
- presentacion en [docs/presentacion_tfm_15min_v4.pptx](/C:/Users/usuario/Desktop/tfm/docs/presentacion_tfm_15min_v4.pptx).

## Limitaciones

Las conclusiones del proyecto deben leerse dentro de su alcance experimental:

- la evaluacion se apoya en una arquitectura concreta y una configuracion LLM determinada;
- la disponibilidad de datos depende de `yfinance` y de las limitaciones del proveedor;
- el sistema trabaja sobre analisis historico, no sobre prediccion;
- la calidad final puede variar segun la consulta, el endpoint LLM y los datos accesibles en cada momento;
- una parte de la evaluacion sigue requiriendo revision humana.

## Autoria

Autor: **Carlos Ruiz Oyarzun**.
