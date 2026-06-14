# Ejecucion Completa de la Fase de Datos

## Objetivo

Este documento no resume la fase de datos de forma abstracta.
La idea aqui es ver una ejecucion completa y comentada de esa parte del flujo para entender:

- que entra realmente
- que funciones se usan
- que valida cada una
- que objetos se van generando
- que artefactos se escriben en disco
- que queda listo justo antes del Agente 2

## Caso trazado

Consulta usada:

```text
Dame una vision general de AAPL en 3 meses
```

La traza se ha ejecutado de forma controlada para poder inspeccionarla bien:

- el Agente 1 se simulo con un `FinancialDataRequest` correcto
- la descarga se simulo reutilizando un CSV historico del proyecto
- los nodos, validaciones, normalizacion y persistencia si se ejecutaron de verdad

Esto permite ver la logica real de la fase de datos sin depender del LLM ni de red.

## Flujo exacto que se ejecuta

Hasta antes del Agente 2, el recorrido es este:

1. `WorkflowState.from_input(...)`
2. `ingest_node(...)`
3. `data_request_planning_node(...)`
4. `data_request_structural_validation_node(...)`
5. `data_download_node(...)`

Dentro de esos nodos, las funciones relevantes que participan son:

1. `FinancialQueryInput.from_dict(...)`
2. `validate_query_input(...)`
3. `build_llm_data_request(...)`
4. `_apply_data_request_to_state(...)`
5. `validate_financial_data_request_structure(...)`
6. `download_market_data(...)`
7. `normalize_downloaded_data(...)`
8. `validate_operational_download(...)`
9. `persist_download_artifacts(...)`

## Entrada real

Ahora mismo `FinancialQueryInput` ya solo contiene la consulta original del usuario:

```python
FinancialQueryInput(query="Dame una vision general de AAPL en 3 meses")
```

Eso significa que al empezar no existen todavia:

- tickers resueltos
- fechas finales
- intervalo final
- csvs generados
- artefactos de descarga

## Paso 0. Creacion del estado inicial

Funcion usada:

```python
state = WorkflowState.from_input(query_input)
```

Que mete dentro:

```json
{
  "user_query": "Dame una vision general de AAPL en 3 meses",
  "normalized_query": {
    "query": "Dame una vision general de AAPL en 3 meses"
  },
  "csv_paths": [],
  "warnings": [],
  "status": "created"
}
```

Interpretacion:

- `user_query` conserva el texto original
- `normalized_query` arranca minimo, solo con `query`
- todavia no se ha enriquecido nada

Nota importante:

Aunque aqui lo vemos serializado como JSON, internamente `normalized_query`
ya no se trata como un diccionario generico. El workflow lo mantiene como un
contexto resuelto tipado que se va enriqueciendo paso a paso.

## Paso 1. `ingest_node`

Codigo implicado:

1. `state.normalized_query.to_query_input()`
2. `validate_input(query_input)`
3. `validate_query_input(query_input)`

Que valida aqui:

- solo que la query no venga vacia

Salida real:

```json
{
  "step": "ingest_node",
  "status": "ingested",
  "error_message": null,
  "normalized_query": {
    "query": "Dame una vision general de AAPL en 3 meses"
  }
}
```

Que significa:

- la entrada es valida como consulta minima
- el flujo puede pasar al Agente 1
- todavia seguimos sin tickers, rango ni csvs

## Paso 2. `data_request_planning_node`

Codigo implicado:

1. `state.normalized_query.to_query_input()`
2. `build_llm_data_request(query_input)`
3. `_build_data_request_from_payload(...)`
4. `_apply_data_request_to_state(state, request)`

En esta traza, el Agente 1 devolvio este `FinancialDataRequest`:

```json
{
  "user_query": "Dame una vision general de AAPL en 3 meses",
  "provider": "yfinance",
  "instruments": [
    {
      "ticker": "AAPL"
    }
  ],
  "interval": "1d",
  "start": null,
  "end": null,
  "period": "3mo",
  "required_fields": [
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume"
  ],
  "needs_clarification": false,
  "clarification_reason": null
}
```

Salida del nodo:

```json
{
  "step": "data_request_planning_node",
  "status": "data_request_planned",
  "financial_data_request": {
    "user_query": "Dame una vision general de AAPL en 3 meses",
    "provider": "yfinance",
    "instruments": [
      {
        "ticker": "AAPL"
      }
    ],
    "interval": "1d",
    "start": null,
    "end": null,
    "period": "3mo",
    "required_fields": [
      "Open",
      "High",
      "Low",
      "Close",
      "Adj Close",
      "Volume"
    ],
    "needs_clarification": false,
    "clarification_reason": null
  },
  "normalized_query": {
    "query": "Dame una vision general de AAPL en 3 meses",
    "tickers": [
      "AAPL"
    ],
    "start": null,
    "end": null,
    "period": "3mo",
    "interval": "1d",
    "needs_clarification": false,
    "warnings": []
  }
}
```

Que ha pasado realmente aqui:

1. La query libre se ha convertido en un contrato tecnico de descarga.
2. El ticker ya esta resuelto a `AAPL`.
3. El rango ya esta resuelto a `period="3mo"`.
4. El intervalo ya esta resuelto a `1d`.
5. `normalized_query` deja de ser minimo y empieza a contener contexto util.

Esto es importante:

- `FinancialQueryInput` sigue siendo solo la entrada original
- el enriquecimiento ocurre en `WorkflowState` dentro de un contexto resuelto tipado

## Paso 3. `data_request_structural_validation_node`

Codigo implicado:

1. `FinancialDataRequest.from_dict(state.financial_data_request)`
2. `validate_financial_data_request_structure(request)`

Que valida aqui:

- que exista `user_query`
- que exista `provider`
- que sea `yfinance`
- que haya al menos un instrumento
- que el ticker no este vacio
- que exista `interval`
- que el intervalo este permitido
- que no se mezcle `period` con `start/end`
- que exista `period` o `start`
- que las fechas tengan formato correcto
- que `needs_clarification` no bloquee el caso

Salida del nodo:

```json
{
  "step": "data_request_structural_validation_node",
  "status": "data_request_validated",
  "structural_repair_attempts": 0,
  "financial_data_request": {
    "user_query": "Dame una vision general de AAPL en 3 meses",
    "provider": "yfinance",
    "instruments": [
      {
        "ticker": "AAPL"
      }
    ],
    "interval": "1d",
    "start": null,
    "end": null,
    "period": "3mo",
    "required_fields": [
      "Open",
      "High",
      "Low",
      "Close",
      "Adj Close",
      "Volume"
    ],
    "needs_clarification": false,
    "clarification_reason": null
  }
}
```

Que significa:

- la estructura es correcta
- no entra Subagente 1
- el request ya merece probarse contra yfinance

## Paso 4. `data_download_node`

Este es el paso mas importante porque aqui la fase de datos deja de ser teorica y se vuelve operativa.

Codigo implicado:

1. `download_market_data(request)`
2. `normalize_downloaded_data(downloaded, request.tickers)`
3. `validate_operational_download(request, normalized)`
4. `persist_download_artifacts(request, downloaded, normalized)`

### 4.1 Descarga bruta

La descarga bruta reutilizada en esta traza tiene esta forma:

```csv
Ticker,AAPL,AAPL,AAPL,AAPL,AAPL,AAPL
Price,Open,High,Low,Close,Adj Close,Volume
Date,,,,,,
2025-12-17,275.010009765625,276.1600036621094,271.6400146484375,271.8399963378906,271.5858764648437,50138700
2025-12-18,273.6099853515625,273.6300048828125,266.95001220703125,272.19000244140625,271.935546875,51630700
2025-12-19,272.1499938964844,274.6000061035156,269.8999938964844,273.6700134277344,273.4141845703125,144632000
```

Esto refleja bastante bien la salida tipica de yfinance:

- columnas jerarquicas
- formato ancho
- no es el formato ideal para el resto del pipeline

### 4.2 Normalizacion

`normalize_downloaded_data(...)` transforma eso a formato canonico largo:

```csv
Date,Ticker,Open,High,Low,Close,Adj Close,Volume
2025-12-17,AAPL,275.010009765625,276.1600036621094,271.6400146484375,271.8399963378906,271.5858764648437,50138700
2025-12-18,AAPL,273.6099853515625,273.6300048828125,266.95001220703125,272.19000244140625,271.935546875,51630700
2025-12-19,AAPL,272.1499938964844,274.6000061035156,269.8999938964844,273.6700134277344,273.4141845703125,144632000
2025-12-22,AAPL,272.8599853515625,273.8800048828125,270.510009765625,270.9700012207031,270.7166748046875,36571800
2025-12-23,AAPL,270.8399963378906,272.5,269.5599975585937,272.3599853515625,272.1053771972656,29642000
2025-12-24,AAPL,272.3399963378906,275.42999267578125,272.20001220703125,273.8099975585937,273.55401611328125,17910600
2025-12-26,AAPL,274.1600036621094,275.3699951171875,272.8599853515625,273.3999938964844,273.1444091796875,21521800
```

Este ya es el formato que interesa al resto del sistema porque:

- tiene `Date` explicita
- tiene `Ticker` explicito
- deja columnas numericas limpias
- sirve tanto para un ticker como para varios

### 4.3 Validacion operativa

`validate_operational_download(...)` comprueba sobre ese dataframe normalizado:

- que no este vacio
- que existan `Date`, `Ticker`, `Close`
- que aparezca `AAPL`
- que `Close` tenga valores validos

En este ejemplo:

- no entra Subagente 2
- `operational_repair_attempts = 0`

### 4.4 Persistencia de artefactos

`persist_download_artifacts(...)` escribe cuatro cosas reales en disco:

1. request usado
2. csv bruto
3. csv normalizado
4. metadata de apoyo

Estado de salida del nodo:

```json
{
  "step": "data_download_node",
  "status": "data_downloaded",
  "operational_repair_attempts": 0,
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_115136_570323.csv"
  ],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": [
      "AAPL"
    ],
    "tickers_found": [
      "AAPL"
    ],
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
  },
  "download_artifacts": {
    "request_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_requests\\request_20260613_115136_570323.json",
    "raw_data_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_raw\\raw_20260613_115136_570323.csv",
    "normalized_data_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_115136_570323.csv",
    "metadata_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_raw\\raw_20260613_115136_570323.metadata.json"
  },
  "normalized_query": {
    "query": "Dame una vision general de AAPL en 3 meses",
    "tickers": [
      "AAPL"
    ],
    "start": null,
    "end": null,
    "period": "3mo",
    "interval": "1d",
    "needs_clarification": false,
    "warnings": [],
    "csv_paths": [
      "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_115136_570323.csv"
    ]
  }
}
```

## Artefactos reales generados

### Request persistido

Fichero:

`results/data_requests/request_20260613_115136_570323.json`

Contenido real:

```json
{
  "user_query": "Dame una vision general de AAPL en 3 meses",
  "provider": "yfinance",
  "instruments": [
    {
      "ticker": "AAPL"
    }
  ],
  "interval": "1d",
  "start": null,
  "end": null,
  "period": "3mo",
  "required_fields": [
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume"
  ],
  "needs_clarification": false,
  "clarification_reason": null
}
```

### Metadata persistida

Fichero:

`results/data_raw/raw_20260613_115136_570323.metadata.json`

Contenido real:

```json
{
  "provider": "yfinance",
  "tickers_requested": [
    "AAPL"
  ],
  "tickers_found": [
    "AAPL"
  ],
  "interval": "1d",
  "period": "3mo",
  "start": null,
  "end": null,
  "download_timestamp": "2026-06-13T11:51:36",
  "raw_data_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_raw\\raw_20260613_115136_570323.csv",
  "normalized_data_path": "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_115136_570323.csv"
}
```

### CSV final que se entrega al resto del flujo

Fichero:

`results/data_normalized/normalized_20260613_115136_570323.csv`

Cabecera y primeras filas:

```csv
Date,Ticker,Open,High,Low,Close,Adj Close,Volume
2025-12-17,AAPL,275.010009765625,276.1600036621094,271.6400146484375,271.8399963378906,271.5858764648437,50138700
2025-12-18,AAPL,273.6099853515625,273.6300048828125,266.95001220703125,272.19000244140625,271.935546875,51630700
2025-12-19,AAPL,272.1499938964844,274.6000061035156,269.8999938964844,273.6700134277344,273.4141845703125,144632000
2025-12-22,AAPL,272.8599853515625,273.8800048828125,270.510009765625,270.9700012207031,270.7166748046875,36571800
2025-12-23,AAPL,270.8399963378906,272.5,269.5599975585937,272.3599853515625,272.1053771972656,29642000
```

## Que queda justo antes del Agente 2

Cuando termina bien la fase de datos, `WorkflowState` ya contiene lo importante:

### 1. `financial_data_request`

El contrato tecnico definitivo de descarga.

### 2. `normalized_query`

La query ya enriquecida con:

- tickers
- rango
- intervalo
- flags de aclaracion
- warnings
- `csv_paths`

### 3. `csv_paths`

La ruta del CSV normalizado real que alimentara el resto del pipeline.

### 4. `download_summary`

Resumen ligero de lo descargado:

- provider
- tickers pedidos
- tickers encontrados
- periodo
- filas
- columnas

### 5. `download_artifacts`

Rutas completas a:

- request JSON
- CSV bruto
- CSV normalizado
- metadata

## Traduccion practica de lo que ha pasado

Si lo bajamos a lenguaje muy directo, esta ejecucion hace esto:

1. El usuario solo escribe una consulta libre.
2. El sistema valida que haya consulta.
3. El Agente 1 transforma esa consulta en una peticion tecnica descargable.
4. El validador estructural comprueba que la peticion tenga sentido formal.
5. Se intenta la descarga real.
6. La salida de yfinance se normaliza.
7. El validador operativo comprueba que los datos realmente sirvan.
8. Se persisten los artefactos.
9. El sistema queda listo para pasar al Agente 2.

## Que usa exactamente el Agente 2 al entrar

Aunque `FinancialQueryInput` ya solo tiene `query`, el Agente 2 no entra “ciego”.

En la implementacion actual, el nodo que llama al Agente 2 hace esto conceptualmente:

```python
query_input = state.normalized_query.to_query_input()
phase2_input_payload = _build_phase2_input_payload(state)
plan, warnings = build_llm_analysis(
    query_input,
    input_payload=phase2_input_payload.to_dict(),
)
```

Por tanto, hay que distinguir dos cosas:

### 1. Lo que existe en `WorkflowState` al terminar la fase de datos

Existe todo esto:

- la query original
- los tickers ya resueltos
- el rango ya resuelto
- el intervalo ya resuelto
- el CSV normalizado generado
- el resumen de descarga
- las rutas a artefactos

### 2. Lo que se le pasa realmente al Agente 2 hoy

Lo que le entra directamente al Agente 2 en la implementacion actual es:

#### `query_input`

```json
{
  "query": "Dame una vision general de AAPL en 3 meses"
}
```

#### `input_payload=phase2_input_payload.to_dict()`

```json
{
  "query": "Dame una vision general de AAPL en 3 meses",
  "tickers": [
    "AAPL"
  ],
  "temporal_context": {
    "start": null,
    "end": null,
    "period": "3mo",
    "interval": "1d"
  },
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_20260613_115136_570323.csv"
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
    "tickers_requested": [
      "AAPL"
    ],
    "tickers_found": [
      "AAPL"
    ]
  }
}
```

Puede ser confuso ver dos veces la query pero estas dos entradas tienen roles diferentes, una es la consulta original 
como base segura, y lo demas es el contexto que tendra el agente 2.

Esto significa que, realmente, el Agente 2 ve:

- la consulta original;
- los tickers ya resueltos;
- el rango temporal ya resuelto;
- el intervalo ya resuelto;
- la ruta al CSV normalizado que se ha generado;
- y el resumen minimo real de los datos disponibles.

### Lo que no se le pasa directamente hoy

Aunque ya existen en `WorkflowState`, en la implementacion actual no se le pasan de forma directa al prompt del Agente 2:

- `financial_data_request`
- `download_artifacts`

Es decir:

- si hablamos de estado global del workflow, esas piezas ya existen;
- si hablamos estrictamente de entrada real al Agente 2, hoy entra `query_input` y un payload compacto de fase 2.

### Respuesta corta y defendible

Si en la defensa te preguntan “¿que le entra realmente al Agente 2?”, la forma mas precisa de responder seria:

- le entra la consulta original del usuario;
- le entra una version enriquecida de esa consulta con tickers, rango, intervalo, ruta al CSV normalizado y resumen minimo de los datos disponibles;
- y no decide ya que descargar, porque la fase de datos le entrega ese contexto resuelto.

Eso es precisamente lo bueno de la separacion actual:

- la entrada inicial es limpia
- el contexto tecnico aparece donde debe aparecer
- y el Agente 2 ya no decide que descargar, solo que analizar

## Conclusión

La fase de datos no solo “planea” una descarga.
En una ejecucion completa hace cuatro cosas distintas:

1. interpreta la consulta
2. construye un request tecnico
3. demuestra que ese request es formalmente correcto
4. demuestra que operativamente produce datos utiles

Solo despues de esas cuatro comprobaciones el sistema pasa al Agente 2.
