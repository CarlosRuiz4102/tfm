# Ejecucion Completa de la Parte 5

## Objetivo

Este documento no resume la parte 5 de forma abstracta.
La idea aqui es ver con claridad como se conectan la parte 4 y la parte 5 para
entender:

- que sale realmente de la ejecucion valida;
- que le llega exactamente al interpretador;
- que informacion se limpia antes de construir la respuesta final;
- que funciones participan;
- que controles minimos siguen existiendo;
- y que queda guardado al terminar la interpretacion.

## Como se conectan la parte 4 y la parte 5

La conexion entre ambas partes se apoya en una regla sencilla:

- la parte 4 entrega una `execution_output` ya confirmada como valida para el workflow;
- la parte 5 no vuelve a validar semanticamente esos resultados;
- la parte 5 construye un `interpretation_payload` limpio y llama al Agente 5;
- la respuesta del agente se guarda como `final_answer`.

Esto significa que la relacion entre ambas partes no es:

```text
Parte 4
-> plan analitico
-> interpretador
```

Sino esta otra:

```text
Parte 4
-> execution_output ya validada
-> limpieza de pistas internas
-> interpretation_payload
-> Agente 5
-> final_answer
```

La idea importante es que el interpretador no debe recibir una guia oculta
sobre como responder. Debe trabajar con:

- la `query` original;
- el contexto resuelto minimo;
- la salida real de ejecucion;
- los `warnings` relevantes.

## Caso trazado

Consulta usada:

```text
Compara Nvidia y AMD en 2 anos y dime cual rindio mejor
```

La traza se plantea de forma controlada para poder inspeccionarla bien:

- la parte 4 se considera ya completada con una `execution_output` valida;
- la construccion del payload de interpretacion si se hace de verdad;
- el Agente 5 puede simularse para inspeccionar con claridad que ve;
- la logica real de limpieza, compactacion y conexion entre nodos si se ejecuta.

Esto permite estudiar la parte 5 sin depender del LLM real.

## Flujo exacto que se ejecuta

Desde que la parte 4 termina bien hasta la respuesta final, el recorrido actual
es este:

1. `code_execution_node(...)`
2. `validate_execution_result(...)`
3. `interpretation_node(...)`
4. `_build_interpretation_payload(...)`
5. `_strip_interpretation_hints(...)`
6. `_compact_for_interpretation(...)`
7. `build_llm_interpretation(...)`
8. `build_interpretation_messages(...)`

## Que deja la parte 4 justo antes de la parte 5

La parte 5 no empieza desde cero. Empieza con un estado ya enriquecido por la
ejecucion.

Estado conceptual minimo al salir de la parte 4:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos y dime cual rindio mejor",
  "normalized_query": {
    "query": "Compara Nvidia y AMD en 2 anos y dime cual rindio mejor",
    "tickers": ["NVDA", "AMD"],
    "period": "2y",
    "interval": "1d"
  },
  "execution_returncode": 0,
  "execution_output": {
    "analysis_type": "comparative_return_analysis",
    "analysis_level": "C",
    "metrics": {
      "retorno_total": {
        "NVDA": 135.4,
        "AMD": 62.8
      }
    },
    "summary": "NVDA obtuvo mejor retorno total que AMD en el periodo analizado.",
    "limitations": [
      "El analisis se limita a precios historicos ajustados disponibles en el CSV."
    ],
    "tables": [
      {
        "name": "comparativa_principal",
        "rows": [
          {"ticker": "NVDA", "retorno_total": 135.4},
          {"ticker": "AMD", "retorno_total": 62.8}
        ]
      }
    ]
  },
  "warnings": []
}
```

Interpretacion:

- la parte 4 ya ha comprobado que `returncode == 0`;
- la parte 4 ya ha comprobado que `execution_output` es JSON utilizable;
- la parte 5 no necesita volver a decidir si el output era valido para el workflow;
- la parte 5 necesita transformar ese output en lenguaje natural.

## Paso 1. Entrada real a `interpretation_node`

La entrada al nodo de interpretacion es `WorkflowState`.

Pero el Agente 5 no recibe todo `WorkflowState`.

Lo primero que hace el nodo es comprobar si la ejecucion termino bien:

```python
if state.execution_returncode != 0:
    return execution_error_node(state)
```

Interpretacion:

- si la parte 4 no ha terminado bien, no se intenta una interpretacion narrativa normal;
- la parte 5 solo trabaja sobre ejecuciones correctas.

## Paso 2. Construccion del `interpretation_payload`

Funcion usada:

```python
interpretation_payload = _build_interpretation_payload(state)
```

Esta funcion hace tres cosas importantes:

1. construir `resolved_context`;
2. limpiar pistas internas desde `execution_output`;
3. compactar la salida para no saturar el prompt.

### 2.1 `resolved_context`

Bloque construido:

```json
{
  "tickers": ["NVDA", "AMD"],
  "temporal_context": {
    "start": null,
    "end": null,
    "period": "2y",
    "interval": "1d"
  }
}
```

Que significa:

- el interpretador si ve los tickers resueltos;
- si ve el rango o periodo resuelto;
- si ve el intervalo final;
- pero no necesita conocer contratos internos del analisis previo.

### 2.2 Limpieza de pistas internas

Funcion usada:

```python
execution_output = _strip_interpretation_hints(state.execution_output or {})
```

Esta limpieza elimina claves como:

- `analysis_plan`
- `analysis_type`
- `analysis_level`
- `level`
- `presentation_preferences`
- `output_requirements`

Si partimos del ejemplo anterior, la salida limpia pasa de:

```json
{
  "analysis_type": "comparative_return_analysis",
  "analysis_level": "C",
  "metrics": {
    "retorno_total": {
      "NVDA": 135.4,
      "AMD": 62.8
    }
  },
  "summary": "NVDA obtuvo mejor retorno total que AMD en el periodo analizado.",
  "limitations": [
    "El analisis se limita a precios historicos ajustados disponibles en el CSV."
  ]
}
```

A esto:

```json
{
  "metrics": {
    "retorno_total": {
      "NVDA": 135.4,
      "AMD": 62.8
    }
  },
  "summary": "NVDA obtuvo mejor retorno total que AMD en el periodo analizado.",
  "limitations": [
    "El analisis se limita a precios historicos ajustados disponibles en el CSV."
  ]
}
```

Interpretacion:

- la parte 5 sigue viendo los hechos;
- deja de ver la etiqueta del tipo de analisis;
- deja de ver la etiqueta del nivel;
- deja de tener una pista oculta sobre el formato esperado.

### 2.3 Compactacion

Funcion usada:

```python
_compact_for_interpretation(...)
```

Esta funcion no valida ni reinterpreta resultados.
Solo reduce ruido cuando hay:

- listas demasiado largas;
- tablas muy grandes;
- cadenas enormes.

La idea es que el Agente 5 vea una carga util, no una masa de datos cruda
dificil de leer.

## Paso 3. Payload final que recibe el Agente 5

Tras la limpieza y compactacion, el payload conceptual queda asi:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos y dime cual rindio mejor",
  "resolved_context": {
    "tickers": ["NVDA", "AMD"],
    "temporal_context": {
      "start": null,
      "end": null,
      "period": "2y",
      "interval": "1d"
    }
  },
  "execution_output": {
    "metrics": {
      "retorno_total": {
        "NVDA": 135.4,
        "AMD": 62.8
      }
    },
    "summary": "NVDA obtuvo mejor retorno total que AMD en el periodo analizado.",
    "limitations": [
      "El analisis se limita a precios historicos ajustados disponibles en el CSV."
    ],
    "tables": [
      {
        "name": "comparativa_principal",
        "rows": [
          {"ticker": "NVDA", "retorno_total": 135.4},
          {"ticker": "AMD", "retorno_total": 62.8}
        ]
      }
    ]
  },
  "warnings": []
}
```

Esto es precisamente lo importante de la conexion entre la parte 4 y la parte
5:

- lo que llega es suficiente para interpretar;
- no llega la logica del plan;
- no llegan rutas ni logs tecnicos largos;
- llegan hechos, contexto minimo y avisos.

## Paso 4. Que hace `build_llm_interpretation(...)`

Funcion usada:

```python
final_answer, warnings = build_llm_interpretation(interpretation_payload)
```

Esta funcion:

1. construye los mensajes del prompt;
2. llama al LLM con `complete_text(...)`;
3. comprueba que la respuesta no venga vacia;
4. comprueba que la respuesta no sea JSON puro;
5. si vino JSON puro, pide una reformulacion textual;
6. devuelve la respuesta final.

## Importante: que no valida esta parte

La parte 5 no valida semanticamente que la interpretacion sea "correcta" antes
de guardarla.

No existe aqui una etapa del tipo:

- "comparar respuesta con rubrica";
- "confirmar que el razonamiento era bueno";
- "volver a revisar si la lectura financiera convence".

Los controles que si existen son minimos y de formato:

- que no venga vacia;
- que no venga como JSON puro;
- que la ejecucion previa fuera correcta.

Interpretacion:

- la parte 4 valida que el resultado sea util para el workflow;
- la parte 5 interpreta en bruto ese resultado;
- la unica disciplina extra es que la salida final sea texto utilizable.

## Paso 5. Prompt real del Agente 5

Funcion usada:

```python
messages = build_interpretation_messages(interpretation_payload)
```

Idea central del prompt actual:

- usar solo la consulta original;
- usar solo el contexto resuelto minimo;
- usar solo `execution_output` y `warnings`;
- inferir por si mismo cuanta elaboracion necesita la respuesta;
- no recalcular ni inventar datos externos.

Punto importante:

En esta parte ya no se menciona `analysis_plan`.

Tampoco se le pasan:

- `analysis_type`
- `analysis_level`
- `presentation_preferences`
- `output_requirements`

## Paso 6. Que se guarda al terminar

Si todo va bien, `interpretation_node(...)` deja:

```json
{
  "interpretation_payload": {
    "user_query": "Compara Nvidia y AMD en 2 anos y dime cual rindio mejor",
    "resolved_context": {
      "tickers": ["NVDA", "AMD"],
      "temporal_context": {
        "start": null,
        "end": null,
        "period": "2y",
        "interval": "1d"
      }
    },
    "execution_output": {
      "metrics": {
        "retorno_total": {
          "NVDA": 135.4,
          "AMD": 62.8
        }
      },
      "summary": "NVDA obtuvo mejor retorno total que AMD en el periodo analizado.",
      "limitations": [
        "El analisis se limita a precios historicos ajustados disponibles en el CSV."
      ]
    },
    "warnings": []
  },
  "final_answer": "Respuesta final redactada por el Agente 5",
  "status": "completed"
}
```

Interpretacion:

- queda trazado que vio exactamente el Agente 5;
- queda trazado lo que devolvio;
- ya no dependemos del plan analitico para reconstruir esta fase.

## Traduccion practica de lo que ha pasado

Si lo bajamos a lenguaje muy directo, esta ejecucion hace esto:

1. la parte 4 deja una salida valida de ejecucion;
2. la parte 5 recoge esa salida y el contexto minimo resuelto;
3. elimina pistas internas sobre el analisis previo;
4. compacta la carga para que el prompt sea legible;
5. llama al Agente 5;
6. acepta su interpretacion textual como respuesta final;
7. guarda tanto el payload usado como la respuesta final.

## Respuesta corta y defendible

Si en la defensa te preguntan "que le llega realmente al interpretador", la
respuesta mas precisa seria:

- le llega la consulta original del usuario;
- le llega el contexto resuelto minimo, como tickers, periodo e intervalo;
- le llega la `execution_output` ya validada por la parte 4;
- le llegan los `warnings` relevantes;
- y no le llega ni el `analysis_plan` ni etiquetas internas sobre el nivel esperado.

## ConclusiÃ³n

La parte 5 no es un lector del plan analitico.
Es un bloque de interpretacion final apoyado en resultados ejecutados.

La conexion correcta entre ambas partes queda asi:

1. la parte 4 garantiza que la salida exista y sea util para el workflow;
2. la parte 5 transforma esa salida en lenguaje natural;
3. antes de llamar al Agente 5 se eliminan las pistas que podrian condicionar su respuesta;
4. el sistema conserva ademas la carga exacta usada para poder trazar despues la interpretacion final.
