# TFM Financial Multiagent MVP

Este repositorio contiene un primer MVP pequeño del sistema multiagente analista del TFM.

El MVP no rehace el parser de lenguaje natural. Parte de una entrada ya estructurada con:

- `query`
- `intent`
- `tickers`
- `start` / `end` o `period`
- `interval`
- `csv_paths`

## Que hace este MVP

Implementa un flujo completo y pequeño:

1. `ingest`
2. `router`
3. `specialist_analysis`
4. `code_generation`
5. `code_execution`
6. `interpretation`

Soporta dos intenciones:

- `price_growth`
- `compare_assets`

La generacion de plan, codigo y respuesta final esta hecha con plantillas programaticas para que el pipeline sea ejecutable ya mismo, incluso si `langgraph` o `vllm` aun no estan instalados.

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
```

Tambien puedes pasar un JSON de entrada:

```bash
python run_mvp.py --input-json path/a/input.json
```

## Que hace cada modulo

- `src/schemas.py`: modelos de entrada, salida y estado
- `src/io/csv_loader.py`: lectura de CSV de yfinance y normalizacion a formato tabular
- `src/graph/nodes.py`: nodos del workflow
- `src/graph/routing.py`: validaciones y reglas de enrutado
- `src/graph/build_graph.py`: construccion del workflow y fallback secuencial
- `src/execution/code_runner.py`: persistencia y ejecucion segura del script generado
- `src/prompts.py`: plantillas de plan y de codigo

## Siguiente paso tecnico recomendado

Cuando este MVP este estable, lo siguiente es sustituir las plantillas programaticas por nodos LLM reales:

1. plan analitico estructurado
2. generacion de codigo controlada
3. interpretacion final con LLM

Y solo despues integrar `vLLM` como backend del modelo.
