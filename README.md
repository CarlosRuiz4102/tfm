# TFM Financial LLM Codegen MVP

Este repositorio contiene el MVP del TFM para analisis financiero historico con LLMs. La arquitectura actual se centra en interpretar la consulta con un LLM, generar codigo Python, validar ese codigo, ejecutarlo de forma controlada e interpretar los resultados.

La entrada parte de datos estructurados:

- `query`
- `tickers`
- `start` / `end` o `period`
- `interval`
- `csv_paths`
- `intent` opcional, solo como pista inicial si existe

## Flujo Actual

1. `ingest`: validacion minima de formato, fechas y CSV.
2. `llm_analysis`: interpreta la intencionalidad de la consulta y disena el analisis.
3. `code_generation`: genera codigo Python a partir del plan y del mensaje original.
4. `code_security`: valida contrato del script, imports permitidos y salida JSON.
5. `code_execution`: ejecuta el script en un proceso controlado.
6. `interpretation`: usa el LLM para explicar las metricas y redactar la respuesta final.

Si falta configuracion LLM, el proveedor falla, el codigo no cumple el contrato o la ejecucion devuelve error, el workflow informa el problema de forma explicita.

## Estructura

- `data/raw/`: CSV y metadata ya generados.
- `data/catalog/`: catalogo de casos y utilidades.
- `docs/`: notas y memoria del TFM.
- `src/`: codigo del MVP.
- `src/llm/`: prompts, cliente compatible con OpenAI y pipeline LLM.
- `src/graph/`: nodos del workflow y validacion de entrada.
- `src/execution/`: validacion de seguridad, persistencia y ejecucion controlada del script.
- `results/code/`: scripts generados.
- `results/logs/`: payloads y salidas de ejecucion.
- `tests/`: pruebas basicas.

## Como Ejecutar

```bash
python run_mvp.py --example growth_nvda
python run_mvp.py --example compare_nvda_amd
python run_mvp.py --example overview_aapl
python run_mvp.py --example returns_qqq_spy
python run_mvp.py --example risk_qqq_spy
python run_mvp.py --example technical_aapl
```

Tambien puedes pasar un JSON de entrada:

```bash
python run_mvp.py --input-json path/a/input.json
```

## Configuracion LLM

El proyecto asume LLM por defecto. No hay flags de activacion por fase: basta con configurar proveedor, clave y modelo.

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

## Evaluacion

```bash
python -m unittest discover -s tests
```

Para comparar perfiles LLM:

```bash
python scripts/evaluate_llm_profiles.py --profiles groq gemini university --examples all
```

Nota: `university` es solo el nombre técnico del perfil. En la documentación y la memoria, el modelo se nombra como `openai/gpt-oss-20b` servido mediante vLLM universitario, destacando su capacidad de razonamiento, seguimiento de instrucciones y generación de código. También se han validado Groq con `llama-3.3-70b-versatile`, modelo Llama 3.3 70B Instruct para razonamiento general y ejecución rápida mediante Groq, y Gemini con `gemini-2.5-flash`, modelo Flash de Gemini 2.5 orientado a rapidez y razonamiento, aunque con limitaciones de cuota en las pruebas.

Para mostrar respuestas:

```bash
python scripts/evaluate_llm_profiles.py --profiles groq gemini university --examples all --show-answers
```

## Estado

La arquitectura actual separa claramente las responsabilidades:

- validar la entrada;
- interpretar la intencion del usuario;
- generar codigo Python con LLM;
- revisar seguridad y contrato del codigo;
- ejecutar el codigo en entorno controlado;
- interpretar los resultados con LLM;
- permitir revision humana posterior.
