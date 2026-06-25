# Sistema LLM para análisis financiero histórico mediante generación automática de código

## Descripción

Este repositorio contiene el desarrollo del prototipo implementado para el Trabajo Fin de Máster centrado en el uso de modelos de lenguaje para análisis financiero histórico a partir de consultas en lenguaje natural.

El objetivo del proyecto no es predecir el mercado ni recomendar inversiones, sino estudiar si un sistema multiagente basado en LLM puede integrarse en un flujo más controlado que transforme una consulta abierta en una respuesta sustentada por datos descargados, cálculos observables, código ejecutado y una interpretación final legible para el usuario.

La aportación principal del proyecto reside en la arquitectura del flujo: resolución y validación de datos, planificación analítica, generación de código Python, validación previa a la ejecución, ejecución controlada e interpretación final, todo ello acompañado de trazabilidad estructurada y mecanismos de reparación acotados.

## Objetivo del proyecto

El sistema se ha diseñado para ayudar a interpretar mejor datos históricos de mercado mediante una arquitectura más explicativa y revisable que una respuesta generativa directa de una sola etapa.

En términos funcionales, el flujo persigue:

- recibir una consulta financiera en lenguaje natural;
- resolver los activos, el contexto temporal y la descarga de datos históricos;
- planificar qué métricas y qué estructura de salida hacen falta;
- generar el código Python necesario para ejecutar el análisis;
- validar y ejecutar ese código dentro de un entorno controlado;
- redactar una respuesta final apoyada exclusivamente en los resultados obtenidos.

## Alcance

El proyecto se limita al análisis histórico y descriptivo de activos financieros. No pretende:

- predecir precios futuros;
- emitir recomendaciones de inversión;
- incorporar noticias, macroeconomía o análisis fundamental como parte del flujo principal;
- sustituir el juicio experto de un analista financiero.

La finalidad del sistema es servir como herramienta de apoyo para interpretar datos históricos de una forma trazable y metodológicamente defendible.

## Arquitectura general

La implementación actual sigue un flujo multiagente lineal con validaciones y salidas terminales controladas. El núcleo del workflow se construye en [src/graph/build_graph.py](src/graph/build_graph.py) y recorre estas fases:

1. `ingest_node`: validación inicial de la consulta.
2. `data_request_planning_node`: construcción del `FinancialDataRequest`.
3. `data_request_structural_validation_node`: validación estructural de la petición de datos.
4. `data_download_node`: descarga, normalización y validación operativa de datos históricos.
5. `llm_analysis_node`: planificación analítica.
6. `code_generation_node`: generación del script Python.
7. `code_validation_node`: validación previa del código.
8. `code_execution_node`: ejecución controlada y validación de runtime.
9. `interpretation_node`: elaboración de la respuesta final.

Además, el sistema incorpora rutas terminales para estados bloqueados o erróneos, de forma que incluso una ejecución fallida deje una salida trazable y coherente para el usuario.

## Estructura del repositorio

```text
tfm-trabajo/
  README.md
  requirements.txt
  run_mvp.py
  .env.example
  data/
  docs/
  results/
  scripts/
  src/
  tests/
```

### Directorios más relevantes

- [src](src): implementación principal del sistema.
- [tests](tests): pruebas unitarias y de integración del flujo.
- [docs](docs): memoria, materiales de apoyo, evaluación y presentación.
- [results](results): artefactos generados por las ejecuciones, incluidas trazas y salidas intermedias.

Dentro de `src`, los módulos más relevantes son:

- [src/config.py](src/config.py): configuración global de rutas, ejecución y proveedor LLM.
- [src/graph](src/graph): orquestación del workflow.
- [src/data](src/data): descarga, validación y normalización de datos históricos.
- [src/execution](src/execution): ejecución y validación del código generado.
- [src/llm](src/llm): cliente, prompts y utilidades de interacción con el modelo.
- [src/schemas](src/schemas): contratos tipados del flujo.
- [src/tracing](src/tracing): trazabilidad estructurada por ejecución.

## Requisitos

- Python `3.10` o superior.
- Dependencias declaradas en [requirements.txt](requirements.txt):
  - `numpy`
  - `pandas`
  - `matplotlib`
  - `yfinance`
  - `langchain`
  - `langchain-openai`
  - `openai`
  - `pydantic`
  - `python-dotenv`

## Instalación

Se recomienda crear y activar un entorno virtual antes de instalar dependencias.

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuración del LLM

La configuración del proveedor LLM se centraliza en [src/config.py](src/config.py) y puede cargarse automáticamente desde un fichero `.env`.

Existe una plantilla de ejemplo en [.env.example](.env.example):

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
```

### Variables más importantes

- `VLLM_BASE_URL`, `VLLM_API_KEY`, `VLLM_MODEL`: configuración recomendada cuando el modelo se sirve sobre vLLM.
- `OPENAI_API_KEY`, `OPENAI_MODEL`: alias compatibles con el SDK de OpenAI.
- `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`: alias genéricos soportados por el proyecto.
- `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT_SECONDS`: parámetros globales de generación.

Si no hay credenciales válidas, el flujo no fuerza una caída abrupta: el sistema está preparado para devolver una salida controlada cuando el LLM no está configurado.

## Ejecución básica

El punto de entrada principal del MVP es [run_mvp.py](run_mvp.py).

### Ejecución con ejemplo interno

```powershell
python run_mvp.py --example overview_aapl
```

### Ejecución con JSON de entrada

```powershell
python run_mvp.py --input-json ruta\al\input.json
```

La entrada mínima esperada tiene esta forma:

```json
{
  "query": "Analiza AAPL en 3 meses y explica qué se puede concluir solo con estos datos históricos."
}
```

El programa imprime por salida estándar el estado final del workflow serializado como JSON.

### Ayuda del ejecutable

```powershell
python run_mvp.py --help
```

## Ejemplos disponibles

Los ejemplos de prueba y demostración se definen en [src/examples/sample_inputs.py](src/examples/sample_inputs.py). Entre ellos se incluyen casos como:

- `growth_nvda`
- `compare_nvda_amd`
- `overview_aapl`
- `returns_qqq_spy`
- `technical_aapl`
- `complex_btc_2024_profile`
- `complex_eurusd_intraday`

Estos ejemplos resultan útiles tanto para pruebas manuales como para reproducir parte del comportamiento descrito en la memoria.

## Artefactos generados

Las rutas de salida se centralizan en [src/config.py](src/config.py). Durante una ejecución pueden generarse artefactos en:

- `results/data_requests/`: peticiones de datos construidas por el flujo.
- `results/data_raw/`: descargas brutas de datos.
- `results/data_normalized/`: datos normalizados y listos para análisis.
- `results/code/`: scripts generados.
- `results/logs/`: logs de ejecución.
- `results/traces/`: trazas completas por ejecución.

Algunos de estos directorios pueden no existir en un clon recién descargado y crearse durante la primera ejecución.

## Trazabilidad

Uno de los elementos clave del proyecto es la persistencia de trazas estructuradas. La lógica de trazabilidad está implementada en [src/tracing/workflow_trace.py](src/tracing/workflow_trace.py).

Cada ejecución puede dejar, entre otros, estos artefactos:

- `manifest.json`: resumen global del recorrido.
- `events.jsonl`: eventos cronológicos por nodo.
- `snapshots/`: instantáneas completas del estado tras cada fase.

Esto permite reconstruir de forma detallada qué ocurrió en cada ejecución, qué artefactos se generaron y en qué punto apareció un fallo si el caso no se completó.

## Pruebas

El proyecto incluye pruebas unitarias y de integración en [tests](tests). Cubren, entre otros aspectos:

- configuración del LLM;
- conexión entre la fase de datos y la planificación analítica;
- validación y reparación del código generado;
- payload de interpretación final;
- recorridos de extremo a extremo del MVP.

### Ejecución de pruebas

Con `unittest`:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Comprobación rápida de compilación

```powershell
python -m compileall -q src run_mvp.py
```

## Documentación adicional

El repositorio incluye material complementario relevante para el TFM:

- memoria principal en [docs/memoria_latex/main.tex](docs/memoria_latex/main.tex);
- capítulo del flujo multiagente en [docs/memoria_latex/chapters/05_flujo_multiagente.tex](docs/memoria_latex/chapters/05_flujo_multiagente.tex);
- capítulo de metodología en [docs/memoria_latex/chapters/04_metodologia_compacta.tex](docs/memoria_latex/chapters/04_metodologia_compacta.tex);
- capítulo de resultados en [docs/memoria_latex/chapters/06_resultados_evaluacion_compacta.tex](docs/memoria_latex/chapters/06_resultados_evaluacion_compacta.tex);
- presentación de defensa en [docs/presentacion_tfm_15min_v4.pptx](docs/presentacion_tfm_15min_v4.pptx).

## Limitaciones

Las conclusiones del proyecto deben leerse dentro de su alcance experimental. Entre las limitaciones principales:

- la evaluación se realiza con una configuración concreta del sistema y un modelo específico;
- el sistema depende de un proveedor de datos históricos;
- el alcance se restringe al análisis histórico;
- la revisión cualitativa de resultados completados se apoya en evaluación humana.

Por tanto, el repositorio no debe interpretarse como una solución universal de análisis financiero, sino como la implementación evaluable de una arquitectura LLM más controlada y trazable.

## Autoría

Autor: **Carlos Ruiz Oyarzun**.
