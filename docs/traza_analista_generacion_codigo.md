# Trazabilidad de la parte de analista y generacion de codigo

## Como se conecta esta parte con la fase de datos

Este documento no repite toda la fase de datos. Parte de una ejecucion en la que esa fase ya ha terminado bien y deja preparado el contexto para el Agente 2.

La conexion entre ambas partes se hace ahora de forma explicita mediante un payload comun construido en `src/graph/nodes.py` con `_build_phase2_input_payload(...)`.

Eso significa que la parte 2 ya no recibe solo:

- la `query`;
- los `tickers`;
- la ruta al CSV.

Ahora recibe ademas:

- el contexto temporal ya fijado;
- la ruta al CSV normalizado;
- el numero de filas disponibles;
- la lista real de columnas que existen en la descarga;
- y, solo si hace falta, `warnings` acumulados.

Esto es importante porque mejora la conexion entre ambas fases en tres sentidos:

1. evita que el Agente 2 vuelva a razonar como si no supiera que datos se han validado;
2. permite que el Agente 3 implemente el plan sobre el mismo contexto que vio el Agente 2;
3. deja una transicion visible y auditable entre la salida de la fase 1 y la entrada de la fase 2.

En otras palabras: la conexion entre ambas partes se hace bien cuando el analista y el generador no trabajan sobre una interpretacion vaga de la consulta, sino sobre el resultado real de la fase de datos.

## Objetivo de esta traza

La idea aqui es ver de forma concreta:

- que entra exactamente al Agente 2;
- que plan analitico sale;
- que entra exactamente al Agente 3;
- que script se genera;
- que queda listo para entregar al Agente 4.

## Caso trazado

Consulta usada:

```text
Dame una vision general de AAPL en 3 meses
```

Tipo de traza:

- la fase de datos se ejecuto de forma controlada reutilizando un CSV congelado del proyecto;
- el Agente 2 se simulo con un `AnalysisPlan` valido;
- el Agente 3 se simulo con un script Python valido y sencillo;
- se dejo continuar la ejecucion completa para poder inspeccionar el payload persistido, aunque el foco del documento termina en el script generado.

## Punto de partida: salida ya valida de la fase de datos

Antes de entrar al Agente 2, el estado ya contenia:

```json
{
  "status": "data_downloaded",
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_125633_603987.csv"
  ],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["AAPL"],
    "tickers_found": ["AAPL"],
    "interval": "1d",
    "period": "3mo",
    "start": null,
    "end": null,
    "row_count": 60,
    "columns": [
      "Date",
      "Ticker",
      "Open",
      "High",
      "Low",
      "Close",
      "Adj Close",
      "Volume"
    ]
  }
}
```

Interpretacion:

- la fase 1 ya ha resuelto instrumento, rango e intervalo;
- ya existe un CSV normalizado real;
- ya sabemos cuantas filas hay y que columnas reales puede usar la parte 2;
- el Agente 2 no entra a ciegas.

## Paso 1. Construccion del handoff explicito

Funcion usada:

```python
_build_phase2_input_payload(state)
```

Su funcion es construir el contexto comun que comparten Agente 2 y Agente 3.
Ese contexto ya no intenta arrastrar toda la trazabilidad de la fase 1 hacia el prompt. Solo pasa lo necesario para planificar e implementar.

Salida real observada en esta traza:

```json
{
  "query": "Dame una vision general de AAPL en 3 meses",
  "tickers": ["AAPL"],
  "temporal_context": {
    "start": null,
    "end": null,
    "period": "3mo",
    "interval": "1d"
  },
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_125633_603987.csv"
  ],
  "data_context": {
    "row_count": 60,
    "available_columns": [
      "Date",
      "Ticker",
      "Open",
      "High",
      "Low",
      "Close",
      "Adj Close",
      "Volume"
    ]
  },
  "warnings": [],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["AAPL"],
    "tickers_found": ["AAPL"]
  }
}
```

Que significa:

- el handoff ya no es implicito;
- el analista y el generador reciben el mismo contexto base;
- la parte 2 queda conectada con el resultado operativo de la fase 1 sin arrastrar redundancias innecesarias al prompt.

## Paso 2. `llm_analysis_node`

Funcion del nodo:

```python
llm_analysis_node(state)
```

Que hace internamente:

1. reconstruye `FinancialQueryInput` desde el contexto resuelto;
2. construye `phase2_input_payload`;
3. llama a `build_llm_analysis(...)`;
4. guarda el resultado en `state.analysis_plan`.

## Plan analitico observado

Salida real del Agente 2 en esta traza controlada:

```json
{
  "analytical_goal": "Describir el comportamiento historico reciente de AAPL y resumir sus metricas basicas.",
  "analysis_type": "historical_overview",
  "metrics": [
    "ultimo_cierre",
    "variacion_total"
  ],
  "required_columns": [
    "Date",
    "Close"
  ],
  "data_requirements": [
    "Usar el CSV normalizado descargado para AAPL."
  ],
  "output_requirements": [
    "JSON con metrics, summary y limitations."
  ],
  "presentation_preferences": [
    "Resumen breve y prudente."
  ],
  "reasoning": "La consulta pide una vision general breve de un solo activo sobre los datos ya descargados."
}
```

## Estado al salir del Agente 2

```json
{
  "status": "planned",
  "analysis_plan": {
    "analytical_goal": "Describir el comportamiento historico reciente de AAPL y resumir sus metricas basicas.",
    "analysis_type": "historical_overview",
    "metrics": ["ultimo_cierre", "variacion_total"],
    "required_columns": ["Date", "Close"],
    "data_requirements": ["Usar el CSV normalizado descargado para AAPL."],
    "output_requirements": ["JSON con metrics, summary y limitations."],
    "presentation_preferences": ["Resumen breve y prudente."],
    "reasoning": "La consulta pide una vision general breve de un solo activo sobre los datos ya descargados."
  }
}
```

## Paso 3. `code_generation_node`

Funcion del nodo:

```python
code_generation_node(state)
```

Que hace internamente:

1. toma `state.analysis_plan`;
2. reconstruye `FinancialQueryInput`;
3. vuelve a construir `phase2_input_payload`;
4. llama a `build_llm_code(...)` con el plan ya generado por el Agente 2;
5. guarda el script completo en `state.generated_code`.

## Entrada conceptual al Agente 3

El Agente 3 recibe:

- la consulta original;
- el `phase2_input_payload` completo;
- el `AnalysisPlan` ya validado.

Eso significa que el generador de codigo no necesita volver a deducir:

- que ticker se usa;
- que periodo se usa;
- que CSV debe leer;
- que columnas existen;
- que calculos debe intentar.

Todo eso le llega ya fijado por la fase 1 y por el Agente 2.

## Script generado observado

Cabecera real del script generado en esta traza:

```python
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    output = {
        'analysis_type': 'historical_overview',
        'metrics': {
            'tickers': payload['tickers'],
            'row_count': payload['data_context']['row_count'],
            'csv_count': len(payload['csv_paths']),
        },
        'summary': 'Analisis completado para AAPL.',
        'limitations': [],
```

## Que significa esta salida

Aunque el script de esta traza es intencionadamente simple, permite ver bien el contrato:

- lee el payload desde `argv[1]`;
- usa el `analysis_plan` ya calculado;
- usa el contexto que viene de la fase de datos;
- construye un unico JSON de salida;
- deja el script listo para pasar a la validacion de la parte 3.

## Estado al salir del Agente 3

Conceptualmente, el estado queda asi:

```json
{
  "status": "code_generated",
  "analysis_plan": {
    "analysis_type": "historical_overview",
    "metrics": ["ultimo_cierre", "variacion_total"]
  },
  "generated_code": "script Python completo"
}
```

Interpretacion:

- `analysis_plan` es el contrato analitico que sale del Agente 2;
- `generated_code` es el script que sale del Agente 3;
- estas son las dos piezas principales que la parte 2 entrega a la parte 3.

## Que recibe exactamente la parte 3

Cuando termina la parte 2, la parte 3 recibe como base:

- `state.analysis_plan`
- `state.generated_code`

Y cuando se prepara la ejecucion, el payload incorpora ademas:

- `query`
- `tickers`
- `temporal_context`
- `csv_paths`
- `data_context`
- `warnings`
- `download_summary`

Por eso la parte 3 no empieza desde cero: arranca con el contrato analitico, el
script generado y el contexto operativo que viene arrastrado desde la fase de datos.

## Artefactos observables asociados

Como la traza se dejo correr hasta ejecucion para poder inspeccionar el payload persistido, quedaron estas rutas:

```json
{
  "script_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\code\\generated_20260613_125633_637156.py",
  "payload_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\payload_20260613_125633_637156.json",
  "stdout_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stdout_20260613_125633_637156.json",
  "stderr_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\logs\\stderr_20260613_125633_637156.log"
}
```

Esto ayuda a revisar despues:

- que contexto recibio exactamente el script;
- que codigo se genero;
- que salida estructurada produjo;
- que diferencia hubo entre el plan, el payload y el resultado.

## Resumen interpretativo de la conexion entre ambas partes

La conexion fase 1 -> fase 2 se puede defender bien asi:

1. la fase de datos no entrega solo un CSV, sino un contexto resuelto y validado;
2. ese contexto se empaqueta en un handoff explicito con `_build_phase2_input_payload(...)`;
3. el Agente 2 planifica sobre ese contexto y no sobre una consulta ambigua;
4. el Agente 3 implementa ese plan sobre el mismo contexto compartido.

Por eso esta conexion puede considerarse buena desde el punto de vista del TFM:

- mejora la trazabilidad;
- reduce la ambiguedad entre fases;
- alinea el plan con los datos reales;
- facilita explicar que el codegen no trabaja sobre supuestos opacos.
