# Guia del analista y del generador de codigo

## Objetivo de esta fase

Esta guia cubre el tramo del flujo que empieza cuando la fase de datos ya ha terminado bien y acaba cuando el sistema deja preparado un script Python listo para validacion estatica.

Su objetivo no es:

- decidir que datos descargar;
- llamar a `yfinance`;
- validar seguridad del codigo;
- ejecutar el script;
- redactar la respuesta final para el usuario.

Su objetivo si es:

1. transformar una consulta ya resuelta a datos en un plan analitico estructurado;
2. convertir ese plan analitico en un script Python ejecutable;
3. mantener separados el razonamiento analitico y la implementacion tecnica;
4. dejar contratos y artefactos que permitan revisar despues que se pidio y que se genero;
5. entregar al validador de codigo un script trazable y coherente con la consulta original.

## Alcance de la fase

La fase empieza justo despues de la descarga valida y termina justo antes del Agente 4.

Recorrido completo:

```text
Consulta del usuario
-> Fase de datos completada
-> Agente 2: Analista
-> AnalysisPlan JSON
-> Normalizacion tipada del plan
-> Agente 3: Generador de codigo
-> Script Python en JSON
-> Chequeo minimo de contrato
-> Agente 4
```

## Idea central de la fase

Esta parte del flujo separa dos problemas distintos:

1. **Problema analitico**
   Decidir que calculos, metricas, columnas y formato de salida hacen falta para responder a la consulta.

2. **Problema de implementacion**
   Traducir ese plan a codigo Python que pueda ejecutarse de forma controlada sobre los CSV ya preparados.

La separacion importa mucho porque evita pedirle al mismo bloque que piense la logica analitica y a la vez improvise la implementacion. En esta arquitectura, el Agente 2 decide el que y el Agente 3 materializa el como.

## Principios de diseno

- El Agente 2 trabaja sobre datos ya descargados; no decide nuevas descargas.
- El Agente 2 devuelve un contrato analitico, no una respuesta final.
- El Agente 3 no deberia reinterpretar la consulta desde cero; deberia implementar el plan recibido.
- El script generado debe depender del payload de entrada, no de estado global oculto.
- La salida del script debe ser JSON estructurado para poder validarse e interpretarse despues.
- El pipeline debe tolerar pequenos fallos de formato del LLM, pero sin perder el contrato interno.
- El plan y el codigo se guardan en el estado como artefactos intermedios revisables.

## Estado compartido minimo

Durante esta fase conviene mantener al menos esta informacion:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "normalized_query": {
    "query": "Compara Nvidia y AMD en 2 anos",
    "tickers": ["NVDA", "AMD"],
    "period": "2y",
    "interval": "1d",
    "csv_paths": [
      "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_id.csv"
    ]
  },
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["NVDA", "AMD"],
    "tickers_found": ["NVDA", "AMD"]
  },
  "analysis_plan": null,
  "generated_code": null,
  "warnings": [],
  "error_message": null,
  "status": "data_downloaded"
}
```

Nota:

Aunque aqui lo mostramos en JSON por claridad documental, internamente el
workflow ya mantiene varios de estos bloques como objetos tipados en vez de
diccionarios genericos.

Estados recomendados en este tramo:

- `data_downloaded`
- `analysis_planning`
- `planned`
- `code_generating`
- `code_generated`
- `code_rejected`
- `error`

## Bloque 1: entrada a la fase analitica

## Que entra realmente

Cuando termina bien la fase de datos, el sistema ya no trabaja con una consulta vacia o ambigua. En este punto existen:

- la consulta original del usuario;
- los tickers ya resueltos;
- el rango temporal ya resuelto;
- el intervalo ya resuelto;
- la ruta al CSV normalizado;
- los artefactos y el resumen de descarga.

Esto es importante porque el Agente 2 no deberia volver a decidir que descargar. Su trabajo empieza sobre una base ya comprobada.

### Nota de diseno importante

Una cosa es lo que el workflow conserva internamente para trazabilidad y otra
lo que conviene pasar al prompt del LLM.

En el estado interno seguimos guardando:

- `financial_data_request`
- `download_artifacts`
- `download_summary`

Pero el payload que entra al Agente 2 y al Agente 3 se ha compactado para no
arrastrar repeticiones innecesarias al prompt.

## Distincion importante entre estado y prompt

Conviene distinguir dos niveles:

### 1. Lo que existe en `WorkflowState`

Existe todo esto:

- `user_query`
- `normalized_query`
- `csv_paths`
- `financial_data_request`
- `download_artifacts`
- `download_summary`

### 2. Lo que entra hoy directamente al prompt del Agente 2

En la implementacion actual, el prompt del Agente 2 recibe:

```json
{
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
    }
  }
}
```

Eso significa que el Agente 2 ve la consulta original enriquecida con el contexto minimo necesario para planificar el analisis.

La trazabilidad completa de la fase de datos sigue existiendo en `WorkflowState`,
pero el prompt del LLM recibe una version compacta orientada a decidir e implementar.

## Bloque 2: Agente 2, Analista

## Funcion del agente

El Agente 2 transforma una consulta ya soportada por datos en un `AnalysisPlan JSON`.

Su trabajo es:

- decidir que tipo de analisis hace falta;
- decidir que metricas se deben calcular;
- indicar que columnas del dataset son necesarias;
- describir que requisitos de datos debe respetar el script;
- definir que formato de salida espera del codigo;
- dejar una razon minima de por que ese plan responde a la consulta.

Su trabajo no es:

- descargar datos;
- rehacer el `FinancialDataRequest`;
- calcular cifras finales;
- generar codigo Python;
- redactar la respuesta final para el usuario.

## Que le entra

Le entra la consulta original mas una version enriquecida de esa consulta, ya resuelta por la fase de datos.

Entrada conceptual:

```json
{
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
  },
  "quality_guidelines": {
    "simple_queries": "Consulta simple...",
    "structured_queries": "Consulta estructurada...",
    "advanced_queries": "Consulta avanzada..."
  }
}
```

## Que tiene que sacar

Debe devolver exclusivamente un `AnalysisPlan JSON`.

Esquema actual:

```json
{
  "analytical_goal": "str",
  "analysis_type": "str",
  "metrics": ["str"],
  "required_columns": ["str"],
  "data_requirements": ["str"],
  "output_requirements": ["str"],
  "presentation_preferences": ["str"],
  "reasoning": "str"
}
```

## Comentarios importantes sobre este JSON

- `analytical_goal` resume que problema analitico se quiere resolver.
- `analysis_type` ayuda a tipificar el tipo de calculo que vendra despues.
- `metrics` acota que se debe calcular, en vez de dejarlo a interpretacion libre del generador.
- `required_columns` fuerza a explicitar que columnas necesita el script.
- `data_requirements` recoge reglas practicas del plan sobre cobertura, comparaciones o estructura de datos.
- `output_requirements` describe que forma deberia tener la salida del script.
- `presentation_preferences` permite orientar el nivel de detalle de la salida estructurada.
- `reasoning` deja una justificacion breve y revisable del plan.

## Que ocurre dentro del Agente 2

En la implementacion real, este bloque hace cuatro cosas:

1. construir los mensajes del prompt con `build_analysis_messages(...)`;
2. llamar al LLM en modo JSON con `client.complete_json(...)`;
3. reintentar hasta `MAX_LLM_ATTEMPTS = 3` si el modelo rompe el formato;
4. convertir la respuesta a un `AnalysisPlan` tipado en `build_llm_analysis(...)`.

La idea clave es que el pipeline no deja pasar el JSON crudo del modelo al resto del sistema. Primero lo parsea, lo limpia y lo mete en una estructura de dominio estable.

## Prompt base usado por el Agente 2

Version conceptual basada en `src/llm/prompts.py`:

```text
Agente 2 - ANALISTA.
Devuelve exclusivamente un objeto JSON valido con el esquema indicado. No incluyas markdown.
Tu tarea es convertir la peticion del usuario y los datos ya descargados en un plan verificable para un script Python posterior.
No calcules cifras y no redactes la respuesta final.
```

Ademas del texto anterior, el prompt incluye:

- `input` con la consulta enriquecida;
- `quality_guidelines` para modular la profundidad esperada;
- `required_json_schema` con el contrato exacto de salida.

## Que se guarda al salir

Si todo va bien, la salida del Agente 2 se guarda en:

- `state.analysis_plan`
- `state.status = "planned"`

Todavia no se escribe nada en disco. En este tramo el artefacto principal sigue viviendo en memoria compartida.

## Como defender esta parte en una exposicion

Una forma clara de explicarlo seria:

- el Agente 2 ya no decide que datos pedir;
- trabaja sobre una consulta enriquecida por la fase anterior;
- devuelve un plan analitico estructurado;
- ese plan actua como contrato entre el razonamiento analitico y el generador de codigo.

## Errores tipicos del Agente 2

- devolver texto fuera del JSON;
- proponer metricas que no encajan con la consulta;
- pedir columnas que no existen en el dataset esperado;
- describir una salida demasiado ambigua para el script;
- mezclar recomendaciones finales con el plan analitico.

## Consideraciones recomendadas para el Agente 2

- conviene que el plan sea suficientemente especifico para implementar, pero no tan rigido que fuerce una sola solucion tecnica;
- conviene revisar que `required_columns` y `metrics` esten alineados;
- conviene que `output_requirements` describa una salida estructurada, no narrativa;
- conviene evitar planes que dependan de informacion que no esta en los CSV disponibles.

## Bloque 3: paso intermedio entre Agente 2 y Agente 3

## Funcion de esta transicion

Entre ambos agentes no deberia existir una reinterpretacion libre del problema. Lo que ocurre aqui es una normalizacion tecnica:

1. el JSON del Agente 2 se parsea;
2. se convierte a `AnalysisPlan`;
3. se guarda en el estado;
4. se usa como entrada formal para el Agente 3.

La pregunta que responde este paso es:

- "Tenemos ya un contrato analitico suficientemente claro para pedir implementacion?"

## Capa breve de validacion entre Agente 2 y Agente 3

Antes de pasar el plan al generador de codigo, existe una validacion local en
`src/analysis/validation.py`.

Esta capa es deliberadamente pequena, pero cumple una funcion importante:
asegurar que el `AnalysisPlan` no solo tiene forma de JSON correcta, sino que
ademas es utilizable sobre los datos reales que ha dejado la fase 1.

En concreto, esta validacion comprueba que:

- `analytical_goal` no este vacio;
- `analysis_type` pertenezca al catalogo permitido;
- `metrics` no venga vacio;
- `required_columns` no venga vacio;
- las columnas de `required_columns` existan de verdad en `data_context.available_columns`;
- `data_requirements` no venga vacio;
- `output_requirements` no venga vacio;
- `presentation_preferences` no venga vacio;
- `reasoning` no venga vacio.

Ademas, puede anadir avisos no bloqueantes. Por ejemplo, si `metrics` trae
duplicados o si `output_requirements` no menciona explicitamente que la salida
del script debe ser JSON.

Desde el punto de vista del diseno, esta pieza hace en la parte 2 algo muy
parecido a lo que la validacion estructural hace en la fase de datos: revisar
el contrato del LLM antes de dejar que el flujo siga avanzando.

## Que pasa si esta validacion falla

Si el plan no supera esta comprobacion:

- no se llama al Agente 3;
- el workflow no genera codigo sobre un contrato inestable;
- el estado se marca con error y se conserva el detalle del problema.

Esto evita un fallo muy importante: generar codigo sobre un plan que parece
razonable en texto, pero que no encaja realmente con el CSV descargado.

## Por que puede fallar esta validacion

Este fallo puede aparecer aunque la respuesta del Agente 2 parezca razonable a
simple vista.

Las causas mas tipicas son:

- el agente propone columnas que no existen realmente en el CSV normalizado;
- devuelve un `analysis_type` fuera del catalogo permitido;
- deja vacio alguno de los campos obligatorios del plan;
- formula un plan demasiado generico, sin requisitos de datos o sin salida bien definida.

En la practica, esta capa existe precisamente para detectar ese tipo de
desalineacion antes de pasar al codegen.

## Que implica este fallo dentro del flujo

Cuando ocurre, el sistema no intenta "arreglarlo por debajo" generando codigo
de todas formas.

Lo que hace es:

- detener la transicion entre Agente 2 y Agente 3;
- registrar el motivo concreto en `state.error_message`;
- dejar trazabilidad suficiente para revisar despues si el problema estaba en
  el plan, en las columnas disponibles o en el propio contrato pedido al LLM.

Dicho de forma simple: si esta comprobacion falla, la parte 2 no entrega un
script. Entrega un bloqueo controlado que evita propagar un error hacia la
parte 3.

## Bloque 4: Agente 3, Generador de codigo

## Funcion del agente

El Agente 3 transforma el `AnalysisPlan` en un script Python completo y ejecutable.

Su trabajo es:

- leer el payload de entrada;
- cargar los datos usando los helpers permitidos del proyecto;
- implementar los calculos descritos en el plan;
- devolver una salida JSON unica y parseable por `stdout`;
- mantener el script dentro de las restricciones tecnicas y de seguridad previstas.

Su trabajo no es:

- redefinir el plan analitico;
- descargar datos nuevos;
- usar red o rutas externas;
- redactar la respuesta final al usuario;
- saltarse el contrato de carga y salida del sistema.

## Que le entra

En la implementacion actual, el prompt del Agente 3 recibe tres piezas:

1. `original_user_message`
2. `input`
3. `analysis_plan`

Entrada conceptual:

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
  },
  "analysis_plan": {
    "analytical_goal": "Comparar rendimiento historico de NVDA y AMD",
    "analysis_type": "comparative_return_analysis",
    "metrics": ["retorno_total", "volatilidad"],
    "required_columns": ["Date", "Ticker", "Close"],
    "data_requirements": [
      "usar tickers NVDA y AMD",
      "usar datos diarios"
    ],
    "output_requirements": [
      "JSON con metricas por ticker"
    ],
    "presentation_preferences": [
      "resumen breve"
    ],
    "reasoning": "La consulta pide una comparacion directa entre dos activos."
  }
}
```

## Que tiene que sacar

No devuelve codigo crudo directamente. Debe devolver un JSON con un unico campo `code`.

Contrato actual:

```json
{
  "code": "script Python completo"
}
```

## Restricciones importantes del script

El script que devuelve debe respetar varias reglas tecnicas:

- debe ser completo y autocontenido;
- debe definir `main()`;
- debe cargar el payload con `Path(sys.argv[1]).read_text(...)`;
- no debe usar `open()`;
- no debe usar `pd.read_csv` directamente;
- debe usar `load_close_prices(...)` o `load_market_data(...)`;
- debe imprimir un unico JSON por `stdout`;
- debe pasar la salida por `make_json_safe(...)`;
- debe mantenerse dentro de los imports permitidos.

## Que ocurre dentro del Agente 3

En la implementacion real, este bloque hace estas cosas:

1. construir el prompt con `build_codegen_messages(...)`;
2. llamar al LLM en modo JSON con `client.complete_json(...)`;
3. intentar extraer el campo `code` con `_code_from_text(...)`;
4. tolerar, solo como compatibilidad, que el modelo haya devuelto el script sin wrapper JSON;
5. reintentar hasta `MAX_LLM_ATTEMPTS = 3` si el formato falla;
6. aplicar un chequeo minimo local antes de seguir.

Ese chequeo minimo exige al menos:

- `def main(`
- `json.dumps`

Este chequeo no reemplaza la validacion de seguridad posterior, pero evita continuar si el modelo ni siquiera ha generado un script con forma minima razonable.

## Prompt base usado por el Agente 3

Version conceptual basada en `src/llm/prompts.py`:

```text
Agente 3 - GENERADOR DE CODIGO.
Devuelve exclusivamente un objeto JSON valido con un unico campo code. No incluyas markdown.
El valor code debe ser un script Python completo, autocontenido y ejecutable.
```

Ademas, el prompt incluye:

- la consulta original;
- la consulta enriquecida;
- el `analysis_plan`;
- un `code_contract` explicito con reglas de carga, imports y salida.

## Contrato tecnico que hoy recibe el Agente 3

El `code_contract` actual especifica, entre otras cosas:

- `argv_1`: ruta a un JSON payload con query, tickers, csv_paths y analysis_plan;
- `stdout`: un unico JSON valido;
- `required_top_level_keys`: `metrics`, `summary`, `limitations`;
- `allowed_imports`: `json`, `sys`, `pathlib`, `math`, `statistics`, `pandas`, `numpy`, `src.execution.market_data`;
- `mandatory_data_loader`: obliga a usar `load_close_prices`, `load_market_data`, `ticker_summary` y `make_json_safe`;
- `payload_loading`: obliga a leer el payload con `Path(...).read_text(...)`.

## Que se guarda al salir

Si todo va bien, la salida del Agente 3 se guarda en:

- `state.generated_code`
- `state.status = "code_generated"`

Todavia no se ejecuta nada en esta etapa. Solo se produce el artefacto de codigo.

### Donde queda ese codigo

En este tramo el codigo vive primero en memoria compartida, dentro de:

- `WorkflowState.generated_code`

Mas adelante, cuando la parte 3 lo ejecuta, ese mismo contenido se persiste en:

- `results/code/generated_<run_id>.py`

Por tanto, en la parte 2 el artefacto principal de salida es el script en
memoria; en la parte 3 aparece ademas su version persistida en disco.

## Como defender esta parte en una exposicion

Una forma clara de explicarlo seria:

- el Agente 3 no inventa libremente una respuesta final;
- recibe un contrato analitico ya decidido;
- genera un script con restricciones de carga, imports y salida;
- ese script se somete despues a una validacion independiente antes de ejecutarse.

## Errores tipicos del Agente 3

- devolver texto fuera del JSON;
- devolver un script parcial en vez de completo;
- usar `open()` o `pd.read_csv` directamente;
- devolver varias impresiones por `stdout`;
- ignorar el `analysis_plan`;
- producir una salida JSON que no encaja con lo que espera el sistema.

## Consideraciones recomendadas para el Agente 3

- conviene que la salida del script sea estable y poco ambigua;
- conviene que el script lea del payload todo lo necesario, en vez de asumir rutas o valores ocultos;
- conviene que el codigo transforme los resultados a JSON seguro antes de imprimir;
- conviene que la logica analitica este alineada con `metrics`, `required_columns` y `output_requirements`;
- conviene recordar que la interpretacion narrativa pertenece al Agente 5, no al script.

## Bloque 5: relacion con la validacion posterior

Aunque esta guia se centra en Agente 2 y Agente 3, conviene dejar clara la frontera con el siguiente bloque.

La salida del Agente 3 no se considera automaticamente valida. Despues pasan al menos dos comprobaciones:

1. validacion estatica y de seguridad del codigo;
2. validacion de ejecucion cuando el script ya se lanza.

Eso es precisamente lo que permite defender que esta arquitectura no confia ciegamente en el LLM aunque el prompt este bien disenado.

## Salida final deseada de esta fase

La salida final deseada de este tramo no es aun una respuesta para el usuario. Es:

- un `AnalysisPlan` coherente con la consulta;
- un script Python coherente con ese plan;
- un estado compartido que deja trazabilidad suficiente para revisar que se decidio y que se genero.

## Que se le pasa a la parte 3

La parte 3 recibe principalmente dos salidas de este tramo:

- `state.analysis_plan`
- `state.generated_code`

Y, cuando prepara la ejecucion, el sistema les suma:

- `query`
- `tickers`
- `csv_paths`
- `temporal_context`
- `data_context`
- `download_artifacts`
- `download_summary`

Eso significa que la parte 3 no recibe solo un script aislado. Recibe un script
mas el contrato analitico y el contexto operativo necesario para validarlo y
luego ejecutarlo de forma controlada.

## Resumen operativo final

La fase del analista y del generador de codigo debe quedar pensada como una subarquitectura con cinco responsabilidades:

1. recibir la consulta ya resuelta por la fase de datos;
2. convertirla en un plan analitico estructurado;
3. normalizar ese plan a un contrato interno estable;
4. generar un script Python a partir de ese contrato;
5. entregar ese script al validador posterior sin mezclar analisis, implementacion e interpretacion final.

Si esta fase queda bien implementada, el sistema gana en:

- trazabilidad entre consulta, plan y codigo;
- separacion de responsabilidades;
- facilidad para depurar fallos;
- menor ambiguedad entre lo que se queria calcular y lo que se implemento;
- mejor capacidad para justificar la arquitectura del TFM.
