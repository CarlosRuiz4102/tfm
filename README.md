# TFM Financial LLM Codegen MVP

Este repositorio contiene el MVP del TFM para análisis financiero histórico con LLMs. La arquitectura implementada actualmente se centra en interpretar la consulta con un LLM, generar código Python, validar ese código, ejecutarlo de forma controlada e interpretar los resultados.

La evolución propuesta para el flujo principal se documenta en `docs/flujo_completo_proyecto_borrador.md`: dos agentes LLM comunicados mediante una capa analítica Python determinista y contratos JSON explícitos.

La entrada parte de datos estructurados:

- `query`
- `tickers`
- `start` / `end` o `period`
- `interval`
- `csv_paths`
- `intent` opcional, solo como pista inicial si existe

## Flujo actual implementado

1. `ingest`: validación mínima de formato, fechas y CSV.
2. `llm_analysis`: interpreta la intencionalidad de la consulta y diseña el análisis.
3. `code_generation`: genera código Python a partir del plan y del mensaje original.
4. `code_security`: valida contrato del script, imports permitidos y salida JSON.
5. `code_execution`: ejecuta el script en un proceso controlado.
6. `interpretation`: usa el LLM para explicar las métricas y redactar la respuesta final.

Si falta configuración LLM, el proveedor falla, el código no cumple el contrato o la ejecución devuelve error, el workflow informa el problema de forma explícita.

## Estructura del repositorio

La estructura separa código fuente, datos, documentación, experimentación y artefactos generados. Esta separación permite aplicar prácticas MLOps básicas: reproducibilidad, trazabilidad de ejecuciones, pruebas automatizadas y distinción entre ficheros versionables y resultados regenerables.

```text
tfm/
|-- data/                              # Datos financieros y catálogos del proyecto
|   |-- catalog/                       # Definición de casos de consulta y tickers relevantes
|   |-- processed/                     # Tablas derivadas y resúmenes generados durante el EDA
|   `-- raw/                           # CSV históricos congelados y metadatos de descarga
|-- docs/                              # Documentación técnica, metodología y memoria
|   |-- memoria_latex/                 # Fuentes LaTeX, bibliografía y figuras de la memoria principal
|   `-- PLANTILLA_MASTER_DEEP_LEARNING/ # Plantilla académica de referencia, no usada por el MVP
|-- notebooks/                         # Cuadernos exploratorios de datos y experimentos iniciales
|-- results/                           # Artefactos locales regenerables; excluidos de Git
|   |-- code/                          # Scripts Python generados por el flujo experimental
|   |-- evaluations/                   # Resultados completos de baterías de evaluación en JSON
|   |-- logs/                          # Payloads, stdout y stderr de cada ejecución
|   `-- reports/                       # Informes Markdown y figuras generadas
|-- scripts/                           # Automatizaciones reproducibles de EDA y evaluación
|-- src/                               # Código fuente reutilizable del MVP
|   |-- examples/                      # Entradas de ejemplo para ejecuciones manuales
|   |-- execution/                     # Datos, seguridad y ejecución controlada
|   |-- graph/                         # Estado, validaciones y orquestación del workflow
|   |-- io/                            # Utilidades auxiliares de entrada y salida
|   `-- llm/                           # Cliente, prompts y pipeline de modelos de lenguaje
|-- tests/                             # Pruebas unitarias y de integración básica
|-- .env.example                       # Plantilla de variables de entorno sin secretos
|-- requirements.txt                   # Dependencias Python del proyecto
`-- run_mvp.py                         # Punto de entrada para ejecutar el MVP
```

### Carpetas principales

| Carpeta | Contenido | Papel dentro del proyecto |
|---|---|---|
| `data/raw/` | CSV históricos y metadatos descargados previamente | Datos de entrada inmutables para las ejecuciones del MVP |
| `data/catalog/` | Catálogo de queries y lista de tickers relevantes | Inventario de casos de uso y referencia para preparar datos |
| `data/processed/` | Resúmenes y tablas derivadas durante el EDA | Datos transformados para análisis exploratorio y documentación |
| `docs/` | Documentación técnica, metodología, planificación y materiales de la memoria | Conocimiento versionable del proyecto |
| `docs/memoria_latex/` | Fuente LaTeX y figuras de la memoria principal | Documento académico que se entrega |
| `notebooks/` | EDA, preparación de datos y experimentos iniciales | Entorno exploratorio; no contiene la lógica de producción del MVP |
| `scripts/` | Evaluaciones, generación de informes y utilidades reproducibles | Automatizaciones para validar el sistema y generar evidencias |
| `src/` | Código fuente del MVP | Implementación reutilizable del workflow |
| `src/llm/` | Prompts, cliente compatible con OpenAI y pipeline LLM | Integración con modelos y definición de sus roles |
| `src/graph/` | Estado compartido, nodos, validación y construcción del workflow | Orquestación de la ejecución de principio a fin |
| `src/execution/` | Carga normalizada de datos, seguridad AST y ejecución controlada | Capa determinista que ejecuta y audita el código generado |
| `src/examples/` | Entradas de demostración | Casos rápidos para ejecutar el MVP manualmente |
| `tests/` | Pruebas unitarias y de integración básica | Verificación automatizada del comportamiento esperado |
| `results/` | Código generado, logs, evaluaciones e informes locales | Artefactos regenerables de cada ejecución |

### Artefactos generados

`results/` no se versiona en Git porque contiene resultados locales regenerables:

| Carpeta | Artefactos |
|---|---|
| `results/code/` | Scripts Python generados por el LLM |
| `results/logs/` | Payloads JSON, `stdout` y `stderr` de cada ejecución |
| `results/evaluations/` | Resultados completos de baterías de evaluación en JSON |
| `results/reports/` | Informes Markdown y figuras generadas |

También existen carpetas locales que no forman parte del producto versionable: `venv/` contiene el entorno virtual, `.codex_tmp/` se usa para ficheros temporales y `etica/` conserva materiales auxiliares de otra asignatura.

## Documentación del flujo

- `docs/flujo_completo_proyecto_borrador.md`: arquitectura objetivo acordada y guía para la siguiente iteración del MVP.
- `docs/detalle_iteracion_workflow.md`: recorrido exhaustivo de una ejecución real con sus artefactos.
- `docs/arquitectura_llm_codegen.md`: explicación técnica del flujo experimental que todavía está implementado.
- `docs/control_tamano_salidas_visualizacion.md`: criterio de compactación de series antes de llamar al agente 2.
- `docs/bateria_evaluacion_15_queries.md`: catálogo estable de consultas A/B/C para comparar modelos.

## Cómo ejecutar

```bash
python run_mvp.py --example growth_nvda
python run_mvp.py --example compare_nvda_amd
python run_mvp.py --example overview_aapl
python run_mvp.py --example returns_qqq_spy
python run_mvp.py --example risk_qqq_spy
python run_mvp.py --example technical_aapl
```

También puedes pasar un JSON de entrada:

```bash
python run_mvp.py --input-json path/a/input.json
```

## Configuración LLM

El proyecto asume LLM por defecto. No hay flags de activación por fase: basta con configurar proveedor, clave y modelo.

```bash
copy .env.example .env
```

Groq con `llama-3.3-70b-versatile` (Llama 3.3 70B Instruct, útil para razonamiento general, seguimiento de instrucciones y generación de código):

```env
LLM_PROFILE=groq
GROQ_API_KEY=tu_clave_groq
GROQ_MODEL=llama-3.3-70b-versatile
```

Gemini con `gemini-2.5-flash` (modelo Flash de Gemini 2.5, orientado a rapidez, razonamiento y buen equilibrio coste/latencia):

```env
LLM_PROFILE=gemini
GEMINI_API_KEY=tu_clave_gemini
GEMINI_MODEL=gemini-2.5-flash
```

`openai/gpt-oss-20b` sobre vLLM universitario (modelo abierto de la familia gpt-oss, usado por su capacidad de razonamiento, seguimiento de instrucciones y generación de código):

```env
LLM_PROFILE=university
UNIVERSITY_BASE_URL=https://w1.etsisi.upm.es/vllm/v1
UNIVERSITY_API_KEY=tu_clave_universidad
UNIVERSITY_MODEL=openai/gpt-oss-20b
```

## Evaluación

```bash
python -m unittest discover -s tests
```

Para comparar perfiles LLM:

```bash
python scripts/evaluate_llm_profiles.py --profiles groq gemini university --examples all
```

Para ejecutar la batería equilibrada de `15` queries por perfil:

```bash
python scripts/evaluate_progressive_llm_scope.py --profiles groq gemini university
```

Nota: `university` es solo el nombre técnico del perfil. En la documentación y la memoria, el modelo se nombra como `openai/gpt-oss-20b` servido mediante vLLM universitario, destacando su capacidad de razonamiento, seguimiento de instrucciones y generación de código. También se han validado Groq con `llama-3.3-70b-versatile`, modelo Llama 3.3 70B Instruct para razonamiento general y ejecución rápida mediante Groq, y Gemini con `gemini-2.5-flash`, modelo Flash de Gemini 2.5 orientado a rapidez y razonamiento, aunque con limitaciones de cuota en las pruebas.

Para mostrar respuestas:

```bash
python scripts/evaluate_llm_profiles.py --profiles groq gemini university --examples all --show-answers
```

## Estado

La arquitectura actual separa claramente las responsabilidades:

- validar la entrada;
- interpretar la intención del usuario;
- generar código Python con LLM;
- revisar seguridad y contrato del código;
- ejecutar el código en entorno controlado;
- interpretar los resultados con LLM;
- permitir revisión humana posterior.
