# TFM Financial Multiagent MVP

Este repositorio contiene el MVP del sistema multiagente analista del TFM. La version actual consolida la tercera iteracion: amplia la cobertura analitica, incorpora analisis tecnico, refuerza los escenarios de error y deja la logica organizada por familias de agentes antes de integrar nodos LLM reales.

El proyecto no rehace el parser de lenguaje natural. Parte de una entrada ya estructurada con:

- `query`
- `intent`
- `tickers`
- `start` / `end` o `period`
- `interval`
- `csv_paths`

## Que hace el sistema ahora

Implementa un flujo completo y pequeno:

1. `ingest`
2. `router`
3. `specialist_analysis`
4. `code_generation`
5. `code_execution`
6. `interpretation`

Actualmente soporta seis intenciones:

- `price_growth`
- `compare_assets`
- `asset_overview`
- `return_analysis`
- `historical_risk_analysis`
- `technical_analysis`

La generacion de plan, codigo y respuesta final sigue hecha con plantillas programaticas. Esto permite ejecutar y depurar el pipeline sin depender todavia de un LLM real, GPU o `vllm`. La logica analitica esta modularizada en familias de agentes para facilitar la futura sustitucion de plantillas por nodos LLM.

## Estructura

- `data/raw/`: CSV y metadata ya generados
- `data/catalog/`: catalogo de casos y utilidades
- `docs/`: notas y material auxiliar
- `src/`: codigo del MVP
- `src/agents/`: familias analiticas del MVP y registro de agentes
- `results/code/`: scripts generados
- `results/logs/`: payloads y salidas de ejecucion
- `tests/`: pruebas basicas

## Como ejecutar

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

## Como probar

```bash
python -m unittest tests/test_mvp.py
```

Los tests validan las seis intenciones soportadas y varios escenarios de error.

## Preparacion para API LLM

El MVP puede funcionar sin API externa. La integracion LLM esta preparada mediante un cliente compatible con OpenAI en `src/llm/`, pero queda desactivada por defecto.

Para probar una API compatible con OpenAI:

```bash
copy .env.example .env
```

Configura en `.env` el perfil que quieras usar:

```bash
LLM_ENABLED=true
LLM_PROFILE=groq
GROQ_API_KEY=tu_clave_groq
GROQ_MODEL=llama-3.3-70b-versatile
```

Tambien se puede probar Gemini cambiando el perfil:

```bash
LLM_ENABLED=true
LLM_PROFILE=gemini
GEMINI_API_KEY=tu_clave_gemini
GEMINI_MODEL=gemini-2.5-flash
```

Cuando este disponible el modelo de la universidad, se puede configurar como tercer perfil:

```bash
LLM_ENABLED=true
LLM_PROFILE=university
UNIVERSITY_BASE_URL=https://endpoint_del_modelo/openai/v1
UNIVERSITY_API_KEY=tu_clave_universidad
UNIVERSITY_MODEL=nombre_del_modelo
```

La activacion es granular:

- `LLM_USE_FOR_PLANNING=true`: el LLM puede ajustar el plan analitico.
- `LLM_USE_FOR_CODEGEN=true`: el LLM puede generar codigo Python. Mantener desactivado hasta validar bien el proveedor.
- `LLM_USE_FOR_INTERPRETATION=true`: el LLM puede redactar la respuesta final.

Si la API falla, falta configuracion o la respuesta no cumple el contrato minimo, el sistema mantiene el fallback determinista actual.

Hay una guia corta en `docs/llm_api_setup.md` con la diferencia entre ejecutar el MVP con y sin APIs externas.

Para comparar varios perfiles y guardar evidencias de evaluacion:

```bash
python scripts/evaluate_llm_profiles.py --profiles deterministic groq gemini --examples all
```

## Que hace cada modulo

- `src/schemas.py`: modelos de entrada, salida y estado
- `src/agents/`: definicion modular de agentes por familia analitica
- `src/io/csv_loader.py`: lectura de CSV de yfinance y normalizacion a formato tabular
- `src/graph/nodes.py`: nodos del workflow
- `src/graph/routing.py`: validaciones y reglas de enrutado
- `src/graph/build_graph.py`: construccion del workflow y fallback secuencial
- `src/graph/prompts.py`: fachada de generacion de plan y codigo a partir del registro de agentes
- `src/execution/code_runner.py`: persistencia y ejecucion segura del script generado
- `src/examples/sample_inputs.py`: ejemplos listos para ejecutar

## En que mejora al primer MVP

- amplia la cobertura de 2 a 6 intenciones
- introduce un analisis descriptivo general con `asset_overview`
- introduce un analisis de rentabilidades con `return_analysis`
- introduce un analisis de riesgo con `historical_risk_analysis`
- introduce un analisis tecnico con `technical_analysis`
- mantiene el workflow estable y determinista
- aumenta la cobertura de pruebas con ejemplos reales y errores controlados
- modulariza la logica por familias de agentes antes de integrar LLM reales

## Estado de validacion

La bateria principal se ejecuta con:

```bash
python -m unittest tests/test_mvp.py
```

Estado actual: 9 pruebas superadas sobre 9. La cobertura incluye seis ejecuciones correctas, una por cada intencion soportada, y tres escenarios negativos: intent no soportada, CSV inexistente y cardinalidad incorrecta en `technical_analysis`.

## Siguiente paso tecnico recomendado

Con la tercera iteracion cerrada y la modularizacion por agentes realizada, lo siguiente es:

1. definir la interfaz de los nodos LLM para planificacion, codegen e interpretacion
2. incorporar una primera version LLM manteniendo fallback determinista
3. evaluar tasa de exito, utilidad de respuesta y distribucion de errores
