# Guia del validador de codigo

## Objetivo de esta parte

Esta guia cubre el recorrido que empieza cuando ya existen un
`AnalysisPlan` y un script Python generado, y termina cuando el sistema decide
si ese script puede pasar a ejecucion, si debe corregirse o si debe bloquearse.

Su objetivo no es:

- rehacer el `AnalysisPlan`;
- volver a interpretar la consulta del usuario;
- ejecutar el codigo para ver si funciona;
- redactar la respuesta final para el usuario.

Su objetivo si es:

1. recibir el contexto analitico y el script generado en la parte anterior;
2. decidir si el codigo es `valid`, `repairable` o `blocked`;
3. explicar por que toma esa decision;
4. activar un subagente de correccion cuando el fallo sea reparable;
5. entregar al ejecutor solo codigo ya aceptado por esta fase.

## Alcance de esta parte

Esta parte empieza justo despues del Agente 3 y termina justo antes del
ejecutor de codigo.

Recorrido completo:

```text
Fase de datos completada
-> Agente 2: Analista
-> AnalysisPlan JSON
-> Agente 3: Generador de codigo
-> Script Python
-> Agente 4: Validador de codigo
-> Subagente 3 si hay fallo reparable
-> Codigo validado
-> Ejecutor de codigo
```

## Idea central de esta parte

Aqui hay tres responsabilidades separadas:

1. **Agente 2**
   Decide que hay que calcular.

2. **Agente 3**
   Genera un script que implementa ese plan.

3. **Agente 4**
   Decide si ese script puede aceptarse dentro del flujo.

La diferencia importa mucho.
Que el Agente 3 haya producido un script no significa todavia que ese script
deba ejecutarse.
Hace falta una etapa propia que valore si el codigo respeta el plan, si encaja
con el contrato del sistema y si merece pasar a la siguiente fase.

## Principios de diseno

- El Agente 4 se plantea como un agente LLM del workflow, no como una compuerta local escondida.
- El Agente 4 no genera codigo nuevo: valida y decide.
- El Subagente 3 solo se activa cuando el caso es `repairable`.
- La salida del Agente 4 debe ser estructurada y auditable.
- La parte 3 debe mantener separadas validacion, correccion y ejecucion.
- La arquitectura debe seguir siendo fiel a la figura del flujo general.

## Estado compartido minimo

En esta parte, la implementacion mantiene al menos esta informacion:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "status": "code_generated",
  "analysis_plan": {
    "analytical_goal": "Comparar el rendimiento historico de Nvidia y AMD",
    "analysis_type": "comparative_return_analysis",
    "metrics": ["retorno_total", "volatilidad"],
    "required_columns": ["Date", "Ticker", "Close"],
    "data_requirements": ["CSV historico normalizado"],
    "output_requirements": ["JSON con metricas, resumen y limitations"],
    "presentation_preferences": ["respuesta breve y clara"],
    "reasoning": "La consulta exige comparacion entre dos activos."
  },
  "generated_code": "script Python completo",
  "warnings": [],
  "error_message": null
}
```

Estados reales de esta parte en la implementacion:

- `code_generated`
- `code_validating`
- `code_repairing`
- `code_validated`
- `code_rejected`
- `error`

## Bloque 1: que entra a la parte 3

### Que entra realmente

Cuando termina la parte anterior, la parte 3 recibe como base:

- `state.analysis_plan`
- `state.generated_code`

Y cuando se prepara la ejecucion, ese contexto se completa con:

- `query`
- `tickers`
- `temporal_context`
- `csv_paths`
- `data_context`
- `warnings`
- `download_summary`

La idea importante aqui es esta:
la validacion no arranca desde una consulta ambigua, sino desde un plan ya
fijado y desde un script que se supone que implementa ese plan.

### Estructura compacta que ya llega resuelta

El contexto heredado de la parte anterior puede representarse asi:

```json
{
  "query": "Compara Nvidia y AMD en 2 anos",
  "tickers": ["NVDA", "AMD"],
  "temporal_context": {
    "start": null,
    "end": null,
    "period": "2y",
    "interval": "1d"
  },
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_id.csv"
  ],
  "data_context": {
    "row_count": 503,
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
  "warnings": []
}
```

## Bloque 2: Agente 4, validador de codigo

## Funcion del agente

El Agente 4 decide si el codigo generado por el Agente 3:

- puede aceptarse tal como esta;
- necesita una correccion;
- o debe bloquearse.

Su trabajo es:

- leer el contexto analitico y el script generado;
- revisar si el codigo implementa de forma coherente el plan recibido;
- revisar si respeta el contrato operativo del sistema;
- emitir una decision estructurada;
- dejar motivos observables para esa decision.

Su trabajo no es:

- rehacer el plan analitico;
- generar directamente otro script;
- ejecutar el codigo;
- producir la respuesta final del usuario.

En la implementacion actual, esta fase se articula principalmente en:

- `code_validation_node(...)` en `src/graph/nodes.py`
- `build_llm_code_validation(...)` en `src/llm/pipeline.py`
- `build_code_validation_messages(...)` en `src/llm/prompts.py`

### Que le entra

Le entra un bloque como este:

```json
{
  "original_user_message": "Compara Nvidia y AMD en 2 anos",
  "input": {
    "query": "Compara Nvidia y AMD en 2 anos",
    "tickers": ["NVDA", "AMD"],
    "temporal_context": {
      "start": null,
      "end": null,
      "period": "2y",
      "interval": "1d"
    },
    "csv_paths": [
      "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_id.csv"
    ],
    "data_context": {
      "row_count": 503,
      "available_columns": ["Date", "Ticker", "Close", "Volume"]
    },
    "warnings": []
  },
  "analysis_plan": {
    "analytical_goal": "Comparar Nvidia y AMD en 2 anos",
    "analysis_type": "comparative_return_analysis",
    "metrics": ["retorno_total", "volatilidad"],
    "required_columns": ["Date", "Ticker", "Close"],
    "data_requirements": ["CSV historico normalizado"],
    "output_requirements": ["JSON con metricas, summary y limitations"],
    "presentation_preferences": ["respuesta breve"],
    "reasoning": "Comparacion historica entre activos."
  },
  "generated_code": "script Python completo"
}
```

### Que tiene que sacar

Debe devolver exclusivamente un JSON estructurado con una decision clara.

Contrato de salida:

```json
{
  "decision": "valid | repairable | blocked",
  "errors": ["str"],
  "warnings": ["str"],
  "required_fixes": ["str"],
  "reasoning": "str"
}
```

### Comentarios importantes sobre esta salida

- `decision` fija el estado de trabajo de esta fase.
- `errors` recoge fallos concretos detectados por el Agente 4.
- `warnings` conserva observaciones no bloqueantes.
- `required_fixes` acota que debe corregir el subagente.
- `reasoning` deja una justificacion breve y revisable de la decision.

### Nota de robustez importante

En la implementacion actual, el workflow sigue exigiendo que exista un
`reasoning` util en la decision del Agente 4. Sin embargo, se ha anadido una
normalizacion local para tolerar un fallo frecuente del LLM: que devuelva una
decision valida y errores claros, pero omita ese campo.

La regla actual es esta:

- si el LLM ya devuelve `reasoning`, se usa tal cual;
- si no lo devuelve, el pipeline construye un razonamiento minimo a partir de
  `errors`, `required_fixes` o, en ultimo termino, de la propia `decision`.

Esto no cambia el contrato de la parte 3, pero evita que toda la
ejecucion se rompa por una omision menor de formato en una respuesta que por lo
demas ya resultaba util.

## Que cosas nos interesa validar aqui

Esta parte es importante porque el Agente 4 debe revisar propiedades distintas
del script, no solo una impresion general.

### 1. Coherencia con el `AnalysisPlan`

El Agente 4 debe comprobar que el codigo:

- responde al objetivo analitico pedido;
- calcula metricas alineadas con `metrics`;
- usa las columnas coherentes con `required_columns`;
- no cambia el problema original por otro distinto.

### 2. Coherencia con el contexto de datos

El Agente 4 debe comprobar que el script:

- use el payload que recibe;
- trabaje sobre los CSV ya resueltos;
- no suponga columnas o datos ajenos al contexto recibido;
- no altere tickers, rango o intervalo sin base.

### 3. Contrato de entrada

El Agente 4 debe vigilar que el codigo este pensado para integrarse en el
workflow.

Eso incluye revisar si:

- espera el payload correcto;
- carga el contexto del modo pactado;
- no introduce dependencias ocultas;
- no rompe la arquitectura compartida por el sistema.

### 4. Contrato de salida

La salida del script debe seguir siendo estructurada.
No interesa aceptar un codigo que responda con texto libre o con un formato que
el resto del flujo no pueda interpretar.

Como minimo, el Agente 4 debe comprobar si la salida esperada mantiene:

- `metrics`
- `summary`
- `limitations`

### 5. Riesgo de implementacion

Tambien debe revisar si el codigo introduce decisiones poco controladas, por
ejemplo:

- cambios no justificados respecto al plan;
- pasos que mezclan calculo con interpretacion narrativa;
- dependencia de supuestos no presentes en la entrada;
- soluciones que no resultan estables dentro del workflow.

## Como trabaja el Agente 4

La secuencia real de esta fase es:

1. leer el script y el contexto heredado;
2. emitir una decision `valid`, `repairable` o `blocked`;
3. si es `valid`, dejar pasar al ejecutor;
4. si es `repairable`, activar el Subagente 3;
5. si es `blocked`, detener la fase en esta ejecucion.

Recorrido del nodo:

```text
script generado
-> Agente 4 revisa
-> decision structured JSON
-> si valid, continua
-> si repairable, corrige Subagente 3
-> si blocked, termina la fase
```

En el workflow actual, la decision del Agente 4 se conserva ademas en:

- `state.code_validation_decision`

Y el numero de correcciones intentadas se registra en:

- `state.code_repair_attempts`

## Prompt base del Agente 4

```text
Eres el Agente 4 del flujo de analisis financiero.
Tu tarea es validar el script Python generado a partir de un AnalysisPlan.

Debes:
- leer la consulta original;
- leer el contexto de entrada ya resuelto;
- leer el AnalysisPlan;
- leer el codigo generado;
- decidir si el caso es valid, repairable o blocked;
- devolver exclusivamente JSON valido con los campos decision, errors, warnings, required_fixes y reasoning.

No debes:
- ejecutar el codigo;
- reescribir directamente el script;
- rehacer el AnalysisPlan;
- producir una respuesta final al usuario.

Considera al menos:
- si el codigo implementa el plan recibido;
- si respeta el contrato de entrada y salida;
- si mantiene una salida estructurada;
- si el fallo debe pasar a `repairable` o a `blocked`.
```

## Salidas posibles de esta validacion

### Caso `valid`

El codigo puede pasar a ejecucion.

Esto significa:

- el script encaja con el plan;
- el contrato es suficiente para la siguiente fase;
- no hace falta correccion previa.

### Caso `repairable`

El codigo no pasa todavia a ejecucion, pero el fallo entra en `repairable`.

Errores que suelen caer en `repairable`:

- la salida no esta bien alineada con el formato esperado;
- el script interpreta mal una parte concreta del plan;
- usa una estructura mejorable, pero no rompe por completo el flujo;
- hay desajustes concretos que pueden describirse como correcciones.

### Caso `blocked`

El flujo deja de corregir en esta ejecucion.

Esto puede ocurrir cuando:

- el codigo se aleja demasiado del plan;
- la salida no resulta recuperable con una correccion razonable;
- el Agente 4 considera que seguir corrigiendo no merece la pena;
- se han agotado los intentos de reparacion.

## Subagente 3: correccion de codigo

## Funcion y alcance

El Subagente 3 corrige el script cuando el Agente 4 decide `repairable`.

Su funcion es:

- recibir el script previo;
- leer la decision del Agente 4;
- leer los errores y correcciones pedidas;
- devolver un script completo corregido;
- dejarlo listo para nueva validacion.

Su funcion no es:

- reinterpretar libremente la consulta;
- inventar un plan nuevo;
- saltarse la decision del Agente 4;
- ejecutar el codigo.

### Que le entra

En la implementacion, el subagente recibe:

```json
{
  "original_user_message": "Compara Nvidia y AMD en 2 anos",
  "input": {
    "query": "Compara Nvidia y AMD en 2 anos",
    "tickers": ["NVDA", "AMD"],
    "csv_paths": [
      "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_id.csv"
    ]
  },
  "analysis_plan": {
    "analytical_goal": "Comparar Nvidia y AMD en 2 anos",
    "analysis_type": "comparative_return_analysis"
  },
  "previous_code": "script completo rechazado",
  "validator_decision": {
    "decision": "repairable",
    "errors": [
      "La salida no refleja bien las metricas pedidas en el plan."
    ],
    "required_fixes": [
      "Alinear la salida con metrics, summary y limitations."
    ],
    "reasoning": "El script es corregible, pero la implementacion actual no sigue bien el contrato."
  }
}
```

### Que devuelve

Debe devolver exclusivamente un JSON con un unico campo `code` cuyo valor sea
el script Python completo corregido.

## Prompt base del Subagente 3

```text
Eres el Subagente 3 del flujo de analisis financiero.
Tu tarea es corregir un script Python que el Agente 4 ha marcado como repairable.

Debes:
- leer la consulta original;
- leer el contexto de entrada;
- leer el AnalysisPlan;
- leer el codigo anterior;
- leer la decision del Agente 4;
- devolver exclusivamente JSON valido con un unico campo code;
- devolver un script completo y corregido, no un parche parcial.

No debes:
- reinterpretar la consulta desde cero;
- inventar metricas nuevas;
- cambiar libremente tickers, fechas o intervalo;
- devolver texto adicional fuera del JSON.
```

## Revalidacion y bucle de correccion

La ruta general en esta parte es esta:

```text
Codigo generado
-> Agente 4 valida
-> si valid, continua
-> si repairable, corrige Subagente 3
-> nueva validacion por Agente 4
-> si no converge, blocked
```

Regla general:

- si no hay problemas relevantes -> `valid`
- si hay problemas corregibles -> `repairable`
- si no existe una correccion razonable -> `blocked`
- si se agotan los intentos de reparacion -> `blocked`

En la implementacion actual se usa:

- `MAX_CODE_REPAIR_ATTEMPTS = 2`

## Salida final de esta parte

La salida final deseada de esta parte es un script que:

- ha sido evaluado por el Agente 4;
- ha pasado, si hacia falta, por el Subagente 3;
- queda aceptado para la fase de ejecucion.

### Que recibe el ejecutor

El ejecutor recibe:

- `state.generated_code`, ya aceptado por el Agente 4;
- el payload de ejecucion construido por `_build_phase2_input_payload(state)`;
- los `warnings` acumulados en el estado.

## Resumen operativo final

La parte del validador de codigo debe quedar pensada como una subarquitectura
con cinco responsabilidades:

1. recibir el `AnalysisPlan` y el script generado;
2. decidir si el codigo es `valid`, `repairable` o `blocked`;
3. explicar de forma estructurada esa decision;
4. corregir mediante subagente cuando el caso sea reparable;
5. entregar al ejecutor solo codigo previamente aceptado.
