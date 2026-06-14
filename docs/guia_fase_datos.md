# Guia de la fase de datos

## Objetivo de esta fase

Esta fase cubre el recorrido completo desde que el usuario escribe una consulta en lenguaje natural hasta que el sistema deja preparada una descarga fiable de datos, lista para entregarse al Agente 2.

Su objetivo no es:

- resolver el analisis financiero final;
- calcular metricas definitivas;
- generar codigo Python;
- redactar la respuesta final.

Su objetivo si es:

1. traducir la consulta del usuario a una peticion estructurada de datos;
2. comprobar que esa peticion esta bien construida;
3. comprobar que esa peticion descarga de verdad lo que buscamos en `yfinance`;
4. corregir de forma controlada los fallos reparables;
5. entregar al Agente 2 datos ya descargados desde una peticion validada.

## Alcance de la fase

La fase termina justo antes del Agente 2.

Recorrido completo:

```text
Consulta del usuario
-> Agente 1: Planificador de Datos
-> FinancialDataRequest JSON
-> Validacion estructural de datos
-> Subagente 1 si hay fallo estructural
-> Validacion operativa de descarga
-> Subagente 2 si hay fallo operativo
-> Descarga valida de yfinance
-> Agente 2
```

## Idea central de la fase

La fase de datos se apoya en dos validaciones distintas dentro del mismo bloque:

1. **Validacion estructural**
   Comprueba que lo que devuelve el Agente 1 tiene el formato, la coherencia y los campos esperados.

2. **Validacion operativa de descarga**
   Comprueba que esa peticion no solo es correcta en teoria, sino que ademas descarga bien en `yfinance` y devuelve datos utiles.

El significado de "valido" en esta fase debe ser fuerte:

- el `FinancialDataRequest` esta bien construido;
- la descarga real funciona;
- los datos resultantes sirven para pasar al Agente 2.

## Principios de diseno

- La consulta del usuario es texto libre, pero el resto del flujo trabaja con contratos estructurados.
- El Agente 1 decide que datos hacen falta, no como se realiza el analisis financiero final.
- El sistema no debe llamar a `yfinance` con una peticion no validada.
- Una peticion bien formada no basta: tambien debe demostrarse que descarga correctamente.
- Los fallos estructurales y los fallos operativos no son lo mismo y deben corregirse de forma distinta.
- Los datos descargados deben quedar persistidos como artefactos trazables.
- El Agente 2 solo debe recibir datos descargados desde una peticion previamente validada.

## Estado compartido minimo

Durante esta fase conviene mantener un estado comun. Conceptualmente deberia existir al menos esta informacion:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "status": "query_received",
  "financial_data_request": null,
  "download_artifacts": null,
  "download_summary": null,
  "warnings": [],
  "errors": [],
  "structural_repair_attempts": 0,
  "operational_repair_attempts": 0
}
```

Estados recomendados:

- `query_received`
- `data_request_planned`
- `data_request_structurally_validating`
- `data_request_structurally_repairing`
- `data_request_operationally_validating`
- `data_request_operationally_repairing`
- `data_downloaded`
- `ready_for_agent_2`
- `blocked_for_clarification`
- `failed_data_phase`

## Bloque 1: entrada del usuario

### Que entra

La consulta original del usuario.

Ejemplo:

```json
{
  "user_query": "Quiero comparar Nvidia y AMD en 2 anos con datos diarios"
}
```

### Que se hace aqui internamente

- guardar la consulta original sin modificar;
- inicializar el estado;
- preparar el contexto para el Agente 1.

### Que sale

Un estado base listo para pasar al Agente 1.

## Bloque 2: Agente 1, Planificador de Datos

## Funcion del agente

El Agente 1 transforma una consulta libre en un `FinancialDataRequest JSON`.

Su trabajo es:

- identificar instrumentos o tickers;
- inferir rango temporal;
- inferir granularidad o intervalo;
- decidir si usar `period` o `start/end`;
- indicar si falta informacion critica;
- dejar la peticion en un formato que el sistema pueda usar para descargar datos.

Su trabajo no es:

- decidir metricas financieras finales;
- planificar tablas o apartados para el usuario;
- redactar conclusiones;
- generar codigo Python.

### Que le entra

Le entra la consulta del usuario y, si se quiere, un contexto de configuracion con restricciones conocidas.

Entrada conceptual:

```json
{
  "user_query": "Quiero el oro en 1 semana a 1h",
  "allowed_provider": "yfinance",
  "allowed_intervals": ["1h", "1d", "1wk", "1mo"],
  "notes": [
    "Debes producir solo un FinancialDataRequest JSON",
    "No debes hacer analisis financiero final"
  ]
}
```

### Que tiene que sacar

Debe devolver exclusivamente un `FinancialDataRequest JSON`.

Esquema propuesto:

```json
{
  "user_query": "Quiero el oro en 1 semana a 1h",
  "provider": "yfinance",
  "instruments": [
    {
      "ticker": "GC=F"
    }
  ],
  "interval": "1h",
  "start": null,
  "end": null,
  "period": "1wk",
  "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
  "needs_clarification": false,
  "clarification_reason": null
}
```

### Comentarios importantes sobre este JSON

- `user_query` conserva la peticion original.
- `provider` deja claro que la descarga se hara en `yfinance`.
- `instruments` evita depender de una lista suelta de tickers.
- `interval` fija la granularidad.
- `period` y `start/end` no deberian competir entre si.
- `required_fields` deja explicito que columnas esperamos.
- `needs_clarification` permite frenar el flujo si la consulta es demasiado ambigua.

## `needs_clarification` y `clarification_reason`

Estos dos campos existen para evitar que el Agente 1 invente silenciosamente una peticion de datos cuando la consulta no da informacion suficiente.

Regla conceptual:

- `needs_clarification = false`
  significa: "con la informacion disponible se puede construir una peticion de datos razonable y ejecutable".
- `needs_clarification = true`
  significa: "la consulta no permite construir una peticion fiable sin asumir demasiado".

Regla recomendada:

- si `needs_clarification = false`, entonces `clarification_reason = null`
- si `needs_clarification = true`, entonces `clarification_reason` debe contener un motivo breve y concreto

Ejemplos correctos:

```json
{
  "needs_clarification": false,
  "clarification_reason": null
}
```

```json
{
  "needs_clarification": true,
  "clarification_reason": "La consulta no fija claramente instrumento ni rango temporal."
}
```

### Cuando deberia activarse

Cuando falta informacion critica para descargar datos de forma fiable. Por ejemplo:

- no queda claro el instrumento;
- no queda claro el periodo o rango temporal;
- no queda clara la granularidad;
- la consulta puede referirse a varios activos distintos y no hay una resolucion segura;
- cualquier correccion automatica obligaria a inventar demasiado.

### Como se usa en el flujo

1. El Agente 1 evalua si puede resolver instrumentos, rango e intervalo.
2. Si puede hacerlo, devuelve `needs_clarification=false` y `clarification_reason=null`.
3. Si no puede hacerlo sin asumir demasiado, devuelve `needs_clarification=true` y un motivo.
4. La validacion estructural revisa que ambos campos sean coherentes.
5. Si `needs_clarification=true`, el flujo no debe pasar a descarga normal; debe bloquearse o pedir aclaracion.

### Prompt base recomendado para Agente 1

```text
Eres el Agente 1 del flujo de analisis financiero.
Tu unica tarea es convertir la consulta del usuario en un FinancialDataRequest JSON valido.

No debes:
- hacer analisis financiero;
- calcular metricas;
- proponer respuesta final;
- generar codigo Python.

Debes:
- identificar el o los instrumentos;
- inferir ticker si es razonable y evidente;
- inferir rango temporal e intervalo;
- usar period o start/end segun corresponda;
- marcar needs_clarification=true si la consulta no permite una descarga fiable;
- devolver exclusivamente JSON valido, sin markdown y sin texto adicional.

Contrato de salida:
{
  "user_query": "str",
  "provider": "yfinance",
  "instruments": [{"ticker": "str"}],
  "interval": "str",
  "start": "YYYY-MM-DD o null",
  "end": "YYYY-MM-DD o null",
  "period": "str o null",
  "required_fields": ["str"],
  "needs_clarification": "bool",
  "clarification_reason": "str o null"
}

Si falta informacion critica, no inventes una solucion opaca:
marca needs_clarification=true y explica brevemente el motivo en clarification_reason.
```

## Bloque 3: validacion estructural de datos

## Funcion de esta validacion

Comprobar que el `FinancialDataRequest JSON` generado por el Agente 1 esta bien construido antes de llamar a `yfinance`.

Pregunta que responde esta validacion:

- "¿La peticion tiene forma tecnica correcta para merecer un intento real de descarga?"

Es importante insistir en esto: aqui todavia no se comprueba si `yfinance` devuelve datos.
Solo se comprueba si el request esta formalmente bien planteado.

### Que le entra

Le entra el `FinancialDataRequest JSON` producido por el Agente 1.

En implementacion real, esto se traduce en:

1. parsear el JSON a un `FinancialDataRequest`;
2. revisar sus campos obligatorios;
3. revisar reglas de coherencia internas;
4. decidir si el caso es `valid`, `repairable` o `blocked`.

### Que se valida

La validacion estructural se compone de cuatro capas.
La idea es no responder solo "esta mal", sino detectar exactamente en que tipo de error estamos.

### 1. Validacion estructural

- el JSON existe y es parseable;
- los campos obligatorios existen;
- los tipos son correctos;
- `instruments` es una lista;
- `interval` es texto;
- `needs_clarification` es booleano.

Esto responde a una pregunta muy basica:

- "¿El Agente 1 ha devuelto realmente un objeto con la forma esperada?"

Si esto falla, el problema suele ser de formato o de serializacion.

### 2. Validacion de contrato

- existe al menos un instrumento si `needs_clarification=false`;
- existe `period` o `start`;
- si existe `end`, debe tener sentido con `start`;
- no deberia usarse simultaneamente `period` y `start/end` sin una regla explicita;
- el proveedor debe ser uno permitido.

Esto ya no revisa formato puro, sino reglas del contrato de datos.

Pregunta que responde:

- "¿Aunque el JSON exista, representa una peticion tecnica coherente?"

### 3. Validacion temporal y de granularidad

- fechas con formato ISO si aparecen;
- `end >= start`;
- el intervalo pertenece a una lista permitida;
- la combinacion rango-intervalo es razonable para `yfinance`.

Aqui se protege una de las zonas que mas errores generan en este tipo de sistemas:

- fechas mal formadas;
- rangos invertidos;
- intervalos que el proveedor no soporta;
- combinaciones poco realistas.

Pregunta que responde:

- "¿La parte temporal del request esta planteada de forma utilizable?"

### 4. Validacion de negocio

- los tickers no estan vacios;
- existe coherencia minima entre consulta e instrumentos detectados;
- si la consulta es ambigua, `needs_clarification` lo refleja.

Esta capa es importante para defender la arquitectura.
No basta con tener un JSON valido y con fechas correctas.
Tambien hace falta que el request respete la intencion de la consulta.

Pregunta que responde:

- "¿El request parece realmente la traduccion razonable de lo que pidio el usuario?"

### Como se valida realmente

En terminos practicos, la validacion estructural revisa reglas como estas:

- `provider` debe ser `yfinance`;
- debe existir al menos un instrumento;
- todos los instrumentos deben tener ticker;
- `interval` debe pertenecer a una lista permitida;
- no deben coexistir `period` y `start/end`;
- debe existir `period` o `start`;
- `start` y `end` deben tener formato ISO si aparecen;
- si existen ambas fechas, `end >= start`;
- si `needs_clarification=true`, el flujo no intenta seguir descargando.

### Como defender esta parte en una exposicion

Una forma clara de explicarlo seria:

- primero comprobamos que el Agente 1 haya devuelto un request con forma correcta;
- despues comprobamos que ese request cumpla el contrato tecnico que espera nuestro sistema;
- por ultimo comprobamos que la intencion del usuario no se haya perdido ni forzado.

Lo importante es dejar claro que esta validacion no comprueba todavia si la descarga funciona.
Solo decide si tiene sentido intentarla.

### Posibles errores tipicos

- el agente devuelve texto adicional fuera del JSON;
- usa `daily` en vez de `1d`;
- usa `start` y `period` a la vez sin criterio;
- devuelve lista de instrumentos vacia sin marcar aclaracion;
- las fechas no son validas.

### Salidas posibles

1. `valid`
2. `repairable`
3. `blocked`

Estas tres salidas deben entenderse como la regla general para medir el estado del flujo dentro de las validaciones y de los subagentes.

Semantica recomendada:

- `valid`
  significa: no hay errores y el flujo puede continuar.
- `repairable`
  significa: hay errores, pero todavia merece la pena intentar corregirlos.
- `blocked`
  significa: en esta ejecucion ya no vamos a seguir corrigiendo y el flujo debe detenerse.

Esta semantica nos interesa especialmente porque sera la medida base para decidir el estado de trabajo de los subagentes.

#### Caso `valid`

El request puede pasar a la validacion operativa de descarga.

#### Caso `repairable`

El request tiene errores corregibles y se activa el Subagente 1.

Este caso se usa cuando todavia tiene sentido intentar una correccion automatica.
Ejemplos tipicos:

- ticker vacio;
- intervalo no permitido;
- mezcla de `period` con `start/end`;
- fechas mal formadas;
- falta algun campo esperado.

#### Caso `blocked`

La ejecucion se detiene. Esto puede ocurrir por dos motivos:

1. el caso no era corregible con fiabilidad desde el principio;
2. ya se ha superado el numero maximo de intentos de reparacion.

En otras palabras, `blocked` no significa simplemente "hay error", sino "ya no seguimos corrigiendo en esta ejecucion".

## Subagente 1: correccion estructural

## Funcion y alcance

El Subagente 1 corrige fallos estructurales del `FinancialDataRequest`.

Su funcion es:

- recibir el request fallido;
- leer los errores de validacion estructural;
- producir una version corregida;
- devolverla para nueva validacion estructural.

Su funcion no es:

- hacer el analisis financiero;
- forzar el paso si el request sigue mal;
- modificar la logica del validador;
- corregir problemas reales de descarga en `yfinance`.

### Que le entra

```json
{
  "user_query": "Quiero comparar Nvidia y AMD en 2 anos",
  "previous_financial_data_request": {
    "provider": "yfinance",
    "instruments": [],
    "interval": "daily",
    "start": null,
    "end": null,
    "period": "2 years",
    "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
    "needs_clarification": false,
    "clarification_reason": null
  },
  "validator_errors": [
    "No existe ningun instrumento valido.",
    "El intervalo daily no pertenece a la lista permitida.",
    "El periodo 2 years no sigue el formato esperado."
  ]
}
```

### Que devuelve

Una version corregida del `FinancialDataRequest`.

### Prompt base recomendado para Subagente 1

```text
Eres el Subagente 1 del flujo de datos.
Tu tarea es corregir un FinancialDataRequest que no ha superado la validacion estructural.

Debes:
- leer la consulta original;
- leer el request fallido;
- leer los errores del validador;
- devolver solo un FinancialDataRequest corregido en JSON valido.

No debes:
- generar texto adicional;
- hacer analisis financiero;
- ignorar los errores del validador;
- pasar el problema a la siguiente etapa sin corregirlo.

Si no puedes corregir el problema de forma fiable, marca:
- needs_clarification=true
- clarification_reason con una explicacion breve
```

## Bloque 4: validacion operativa de descarga

## Funcion de esta validacion

Comprobar que un `FinancialDataRequest` estructuralmente valido descarga bien en `yfinance` y devuelve datos utiles.

Esta validacion incluye la descarga real. No es solo una comprobacion teorica.

Pregunta que responde esta validacion:

- "Aunque el request este bien construido, ¿la descarga real produce datos utiles para continuar?"

Aqui esta la diferencia clave con la validacion estructural:

- la estructural valida la forma del request;
- la operativa valida el resultado real de ejecutarlo.

### Que le entra

Le entra el `FinancialDataRequest` ya validado estructuralmente.

Y durante la ejecucion se construyen dos objetos intermedios:

1. la descarga bruta de `yfinance`;
2. una version normalizada del dataset, con columnas canonicas.

### Que hace internamente

1. Extraer tickers e informacion temporal.
2. Ejecutar la descarga real en `yfinance`.
3. Comprobar que la respuesta no viene vacia.
4. Comprobar que aparecen los tickers esperados.
5. Comprobar que la estructura devuelta permite generar un dataframe normalizado util.
6. Persistir la descarga si todo sale bien.

### Pseudocodigo orientativo

```python
tickers = [item["ticker"] for item in financial_data_request["instruments"]]

data = yf.download(
    tickers=tickers,
    start=financial_data_request["start"],
    end=financial_data_request["end"],
    period=financial_data_request["period"],
    interval=financial_data_request["interval"],
    auto_adjust=False,
    group_by="ticker",
    progress=False,
    threads=False,
)
```

### Que se considera valido operativamente

- `yfinance` devuelve datos;
- no viene un dataset vacio;
- aparecen los tickers solicitados o, si falta alguno, el caso se detecta claramente;
- la estructura resultante se puede normalizar a columnas utiles como `Date`, `Ticker` y `Close`;
- se puede generar el artefacto final esperado de esta fase.

### Como se valida realmente

En terminos practicos, la validacion operativa comprueba cosas como estas:

- el dataframe normalizado no esta vacio;
- existen columnas minimas obligatorias, al menos `Date`, `Ticker` y `Close`;
- aparecen los tickers pedidos en el request;
- la columna `Close` tiene valores utilizables;
- si todo eso se cumple, la descarga se persiste como artefacto.

Es decir, la pregunta ya no es "¿el request tiene buena pinta?",
sino "¿lo que ha devuelto el proveedor sirve de verdad para el sistema?".

### Como defender esta parte en una exposicion

Una forma clara de explicarlo seria:

- primero resolvemos la peticion tecnica;
- luego demostramos que esa peticion funciona en la fuente real;
- y solo si los datos descargados son utilizables se permite avanzar al Agente 2.

Esto es importante porque evita un error muy comun en arquitecturas con LLM:
dar por buena una peticion solo porque el modelo la redacto bien.

### Que puede salir mal aqui

- `yfinance` devuelve vacio;
- falta uno de los tickers;
- la API responde con estructura incompleta;
- el rango pedido no devuelve suficientes observaciones;
- el intervalo no produce datos utiles en la practica;
- la respuesta no sirve para generar el CSV o parquet esperado.

Todos esos casos significan que el request era descargable "en teoria", pero no util "en la practica".
Por eso pertenecen al Subagente 2 y no al Subagente 1.

### Artefactos recomendados

- `results/data_requests/request_<id>.json`
- `results/data_raw/raw_<id>.parquet`
- `results/data_raw/raw_<id>.metadata.json`

Contenido util del metadata:

```json
{
  "provider": "yfinance",
  "tickers_requested": ["NVDA", "AMD"],
  "interval": "1d",
  "period": "2y",
  "start": null,
  "end": null,
  "download_timestamp": "2026-06-12T19:00:00Z"
}
```

## Subagente 2: correccion operativa de descarga

## Funcion y alcance

El Subagente 2 corrige fallos operativos detectados al intentar descargar en `yfinance`.

Su funcion es:

- recibir un request estructuralmente valido que no ha descargado bien;
- leer el resultado operativo del intento;
- proponer una correccion que permita descargar de forma util;
- devolver un request ajustado para nueva validacion operativa.

Su funcion no es:

- corregir JSON mal formado;
- hacer analisis financiero;
- inventar datos cuando `yfinance` no los devuelve;
- cambiar libremente la intencion del usuario.

### Que le entra

```json
{
  "user_query": "Quiero el oro en 1 semana a 1h",
  "financial_data_request": {
    "provider": "yfinance",
    "instruments": [
      {"ticker": "GC=F"}
    ],
    "interval": "1h",
    "start": null,
    "end": null,
    "period": "2y",
    "required_fields": ["Open", "High", "Low", "Close", "Adj Close", "Volume"],
    "needs_clarification": false,
    "clarification_reason": null
  },
  "download_errors": [
    "La descarga no devolvio datos utiles para la combinacion interval=1h y period=2y."
  ],
  "download_result_summary": {
    "is_empty": true,
    "tickers_found": [],
    "provider": "yfinance"
  }
}
```

### Que devuelve

Devuelve un `FinancialDataRequest` ajustado o, si no existe una correccion fiable, un bloqueo con aclaracion.

La idea de fondo es esta:

- el Subagente 1 corrige forma;
- el Subagente 2 corrige viabilidad real de descarga.

### Prompt base recomendado para Subagente 2

```text
Eres el Subagente 2 del flujo de datos.
Tu tarea es corregir un FinancialDataRequest que ha superado la validacion estructural,
pero no ha descargado bien en yfinance.

Debes:
- leer la consulta original;
- leer el request actual;
- leer los errores operativos de descarga;
- devolver solo un FinancialDataRequest ajustado en JSON valido.

No debes:
- generar texto adicional;
- hacer analisis financiero;
- ignorar los errores de descarga;
- inventar una solucion que cambie la intencion del usuario sin base suficiente.

Si no puedes corregir el problema de forma fiable, marca:
- needs_clarification=true
- clarification_reason con una explicacion breve
```

## Revalidacion y bucles de correccion

Hay dos rutas de correccion distintas:

### Ruta 1: correccion estructural

```text
FinancialDataRequest invalido
-> Subagente 1 corrige
-> nueva validacion estructural
-> si es valido, pasa a validacion operativa
```

### Ruta 2: correccion operativa

```text
FinancialDataRequest estructuralmente valido
-> intento real de descarga
-> fallo operativo
-> Subagente 2 corrige
-> nueva validacion operativa
-> si descarga bien, continua
```

### Regla importante

Conviene fijar maximos de reintentos. Recomendacion:

- `max_structural_repair_attempts = 2`
- `max_operational_repair_attempts = 2`

Regla general de transicion de estado:

- si no hay errores -> `valid`
- si hay errores y todavia existe una correccion razonable -> `repairable`
- si no existe una correccion fiable -> `blocked`
- si se han agotado los intentos maximos de reparacion -> `blocked`

Esto debe tenerse en cuenta porque es la forma de medir el estado de trabajo de los subagentes:

- el Subagente 1 actua mientras el caso siga en `repairable` dentro de la validacion estructural;
- el Subagente 2 actua mientras el caso siga en `repairable` dentro de la validacion operativa;
- cuando cualquiera de los dos alcanza `blocked`, la fase deja de avanzar en esa ejecucion.

Si tras esos ciclos no se consigue una peticion descargable y util, el flujo deberia pasar a un estado terminal de bloqueo, por ejemplo:

- `blocked_for_clarification`
- o `failed_data_phase`

## Salida final de la fase de datos

La salida final deseada de esta fase es una descarga realizada correctamente en `yfinance`, respaldada por un `FinancialDataRequest` ya validado, y lista para entregarse al Agente 2.

### Que deberia recibir el Agente 2

Minimo recomendable:

- consulta original;
- request resuelto y validado;
- ruta a los artefactos descargados;
- metadatos de descarga;
- resumen basico de lo descargado.

Ejemplo conceptual:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "resolved_request": {
    "provider": "yfinance",
    "instruments": [
      {"ticker": "NVDA"},
      {"ticker": "AMD"}
    ],
    "interval": "1d",
    "period": "2y",
    "start": null,
    "end": null
  },
  "artifacts": {
    "raw_data_path": "results/data_raw/raw_id-unico.parquet",
    "metadata_path": "results/data_raw/raw_id-unico.metadata.json"
  },
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["NVDA", "AMD"],
    "interval": "1d",
    "period": "2y"
  }
}
```

### Conexion con la traza global del workflow

Ademas de entregar estos datos al Agente 2, la implementacion actual deja una
traza transversal desde el inicio del workflow en:

- `results/traces/<run_id>/manifest.json`
- `results/traces/<run_id>/events.jsonl`
- `results/traces/<run_id>/snapshots/`

Eso permite revisar despues, para cada ejemplo ejecutado:

- que `FinancialDataRequest` se genero realmente;
- si hubo correccion estructural u operativa;
- que CSVs y artefactos quedaron persistidos;
- con que estado exacto se entro en la parte analitica.

Para depurar el proyecto completo, esta carpeta de traza deberia ser el punto
de partida antes de revisar artefactos aislados.

### Condiciones para considerar la fase completada

- existe un `FinancialDataRequest` estructuralmente valido;
- la descarga real en `yfinance` se ha ejecutado correctamente;
- existen artefactos persistidos;
- el Agente 2 puede trabajar sobre datos descargados desde una peticion ya comprobada.

## Resumen operativo final

La fase de datos debe quedar pensada como una subarquitectura con seis responsabilidades:

1. traducir consulta libre a `FinancialDataRequest`;
2. validar estructuralmente ese request;
3. corregir fallos estructurales si aparecen;
4. validar operativamente la descarga real en `yfinance`;
5. corregir fallos operativos de descarga si aparecen;
6. entregar al Agente 2 datos descargados desde una peticion previamente validada.

Si esta fase queda bien implementada, el resto del flujo gana en:

- trazabilidad;
- robustez;
- separacion de responsabilidades;
- facilidad de depuracion;
- calidad de la descarga que recibe el analista.
