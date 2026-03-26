# TFM Financial Multiagent MVP

Este repositorio contiene el MVP del sistema multiagente analista del TFM y una segunda iteracion que amplia su cobertura analitica.

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

La generacion de plan, codigo y respuesta final sigue hecha con plantillas programaticas. Esto permite ejecutar y depurar el pipeline sin depender todavia de un LLM real, GPU o `vllm`.

## Estructura

- `data/raw/`: CSV y metadata ya generados
- `data/catalog/`: catalogo de casos y utilidades
- `docs/`: notas y material auxiliar
- `src/`: codigo del MVP
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

## Que hace cada modulo

- `src/schemas.py`: modelos de entrada, salida y estado
- `src/io/csv_loader.py`: lectura de CSV de yfinance y normalizacion a formato tabular
- `src/graph/nodes.py`: nodos del workflow
- `src/graph/routing.py`: validaciones y reglas de enrutado
- `src/graph/build_graph.py`: construccion del workflow y fallback secuencial
- `src/graph/prompts.py`: plantillas de plan y de codigo para cada intencion
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

## Siguiente paso tecnico recomendado

Cuando esta iteracion este estable, lo siguiente es:

1. separar mejor la logica por agentes o familias analiticas
2. separar mejor la logica por agentes o familias analiticas
3. incorporar nodos LLM reales para planificacion, codegen e interpretacion
4. evaluar tasa de exito, utilidad de respuesta y distribucion de errores
