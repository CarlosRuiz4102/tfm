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

En esta fase, la implementacion mantiene un estado compartido con al menos esta
informacion:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "normalized_query": {
    "query": "Compara Nvidia y AMD en 2 anos"
  },
  "csv_paths": [],
  "status": "created",
  "financial_data_request": null,
  "download_artifacts": null,
  "download_summary": null,
  "warnings": [],
  "error_message": null,
  "structural_repair_attempts": 0,
  "operational_repair_attempts": 0
}
```

Estados reales de esta fase en la implementacion:

- `created`
- `ingested`
- `data_request_planned`
- `data_request_validated`
- `data_downloaded`
- `blocked`
- `error`

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

Le entra la consulta del usuario. En la implementacion actual,
`build_llm_data_request(...)` recibe un `FinancialQueryInput` con la query
original. Las restricciones del sistema forman parte del contrato del prompt,
no de un segundo payload variable.

Ejemplo de entrada:

```json
{
  "user_query": "Quiero el oro en 1 semana a 1h"
}
```

### Que tiene que sacar

Debe devolver exclusivamente un `FinancialDataRequest JSON`.

Contrato de salida:

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
- `period` y `start/end` son mutuamente excluyentes dentro del request.
- `required_fields` deja explicito que columnas esperamos.
- `needs_clarification` permite frenar el flujo si la consulta es demasiado ambigua.

## `needs_clarification` y `clarification_reason`

Estos dos campos existen para evitar que el Agente 1 invente silenciosamente una peticion de datos cuando la consulta no da informacion suficiente.

Reglas del contrato:

- `needs_clarification = false`
  significa: "la fase de datos puede continuar sin aclaracion adicional".
- `needs_clarification = true`
  significa: "la consulta no permite construir una peticion fiable sin asumir demasiado".

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

### Cuando se activa

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
5. Si `needs_clarification=true`, la validacion estructural devuelve
   `blocked` y la fase de datos no pasa a descarga.

### Prompt base del Agente 1

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
- inferir ticker solo si la resolucion es directa y univoca;
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

- "Â¿La peticion tiene forma tecnica correcta para merecer un intento real de descarga?"

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

En esta version, la validacion estructural no aplica capas semanticas
adicionales fuera del propio contrato del `FinancialDataRequest`. Las
comprobaciones exactas son estas:

1. Si `needs_clarification = true`, la validacion devuelve directamente
   `blocked` y usa `clarification_reason` como motivo principal del bloqueo.
2. `user_query` debe existir y no puede estar vacia.
3. `provider` debe existir y debe ser exactamente `yfinance`.
4. Debe existir al menos un instrumento.
5. Todos los instrumentos deben incluir un `ticker` no vacio.
6. `interval` debe existir y pertenecer a la lista permitida por la
   implementacion.
7. No pueden coexistir `period` y `start/end` en el mismo request.
8. Debe existir `period` o `start`.
9. `start` y `end`, si aparecen, deben tener formato ISO `YYYY-MM-DD`.
10. Si existen `start` y `end`, entonces `end >= start`.

La validacion estructural de esta implementacion no comprueba todavia si la
descarga funciona contra el proveedor ni si la combinacion rango-intervalo
produce datos utiles en la practica. Todo eso pertenece a la validacion
operativa.

### Como se valida realmente

En la implementacion actual, el recorrido exacto es este:

1. Se parsea la salida del Agente 1 a un `FinancialDataRequest`.
2. Se evalua si `needs_clarification` obliga a bloquear el caso.
3. Se revisan los campos obligatorios del contrato.
4. Se revisan las restricciones temporales y de granularidad.
5. Se devuelve una `ValidationDecision` con uno de estos tres estados:
   `valid`, `repairable` o `blocked`.

### Como defender esta parte en una exposicion

Una forma clara de explicarlo seria:

- primero comprobamos que el Agente 1 haya devuelto un request con forma correcta;
- despues comprobamos que ese request cumpla el contrato tecnico que espera nuestro sistema;
- por ultimo comprobamos que la intencion del usuario no se haya perdido ni forzado.

Lo importante es dejar claro que esta validacion no comprueba todavia si la descarga funciona.
Solo decide si tiene sentido intentarla.

### Errores que detecta esta validacion

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

Semantica de la implementacion:

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
Errores que caen en `repairable` dentro de esta validacion:

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

### Prompt base del Subagente 1

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

- "Aunque el request este bien construido, Â¿la descarga real produce datos utiles para continuar?"

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
3. Normalizar la respuesta bruta a un formato canonico del sistema.
4. Comprobar que la respuesta no viene vacia.
5. Comprobar que aparecen los tickers esperados.
6. Comprobar que la estructura devuelta permite generar un dataframe normalizado util.
7. Persistir la descarga si todo sale bien.

### Llamada real de descarga

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

## Por que la normalizacion va antes de validar

Entre la descarga bruta y la validacion operativa existe un paso intermedio de
normalizacion. Esto no es una validacion en si misma, sino un preprocesado
estructural de los datos descargados.

La razon de incluirlo aqui es que `yfinance` no siempre devuelve la informacion
con la misma forma. En consultas con un solo ticker puede devolver columnas
simples, mientras que en consultas con varios tickers puede devolver un
`MultiIndex`. Si la validacion operativa trabajara directamente sobre esa salida
bruta, tendria que conocer demasiadas variantes del proveedor y mezclar dos
responsabilidades distintas:

- interpretar la estructura variable de `yfinance`;
- decidir si los datos sirven realmente para continuar.

La normalizacion separa ambos problemas. Primero transforma la salida del
proveedor a un formato tabular canonico comun del sistema. Despues, la
validacion operativa comprueba si esa representacion normalizada es
suficientemente consistente y utilizable.

En otras palabras:

- la descarga responde a la pregunta "que ha devuelto el proveedor";
- la normalizacion responde a la pregunta "como convertimos eso al contrato interno del sistema";
- la validacion operativa responde a la pregunta "ese contrato interno ya sirve para continuar".

## Que hace exactamente la normalizacion

La normalizacion convierte la salida bruta de `yfinance` en un dataframe comun
con columnas explicitas como `Date`, `Ticker`, `Open`, `High`, `Low`, `Close`,
`Adj Close` y `Volume`.

En la implementacion actual, este tratamiento previo realiza exactamente estas
operaciones:

- si la descarga viene vacia, devuelve un dataframe vacio pero ya con las
  columnas esperadas por el sistema;
- si `yfinance` devuelve un `MultiIndex`, corrige el orden de niveles si hace
  falta para poder localizar correctamente los tickers;
- separa los datos por ticker cuando la descarga contiene varios activos;
- hace explicita la columna `Date` si la fecha venia como indice;
- inserta explicitamente la columna `Ticker` para que cada fila quede asociada
  a un instrumento concreto;
- convierte `Open`, `High`, `Low`, `Close`, `Adj Close` y `Volume` a valores
  numericos cuando es posible;
- convierte `Date` a tipo temporal;
- elimina filas invalidas en campos minimos como fecha o ticker;
- ordena el resultado por `Ticker` y `Date`.

Este paso es importante porque el resto del flujo no consume la salida bruta
del proveedor, sino esta representacion canonica. Por eso tambien tiene sentido
que la validacion operativa se apoye sobre el dataset ya normalizado: lo que se
valida no es solo que `yfinance` haya respondido, sino que la respuesta ya haya
quedado transformada a un formato util para el Agente 2 y para los scripts
posteriores.

### Que se considera valido operativamente

- el `FinancialDataRequest` ha podido ejecutarse contra `yfinance` sin quedar bloqueado por un fallo terminal;
- la salida bruta se ha podido transformar a un dataframe normalizado del sistema;
- el dataframe normalizado no esta vacio;
- el dataframe normalizado contiene las columnas minimas obligatorias `Date`, `Ticker` y `Close`;
- aparecen todos los tickers solicitados en el request;
- la columna `Close` contiene al menos algun valor no nulo utilizable.

### Como se valida realmente

En la implementacion actual, la validacion operativa aplica exactamente estas
comprobaciones sobre la descarga ya normalizada:

1. Comprobacion de vacio.
Si el dataframe normalizado esta vacio, la validacion devuelve `repairable`
con el error `La descarga no devolvio filas utilizables.`.

2. Comprobacion de columnas minimas obligatorias.
Se exige la presencia de `Date`, `Ticker` y `Close`.
Si falta alguna, la validacion devuelve `repairable` indicando exactamente que
columnas faltan.

3. Comprobacion de tickers encontrados.
Se extraen los tickers presentes en la columna `Ticker` del dataframe
normalizado y se comparan con los tickers pedidos en el request.
Si falta al menos uno de los tickers solicitados, la validacion devuelve
`repairable` indicando cuales no aparecieron.

4. Comprobacion de valores utiles en `Close`.
Si la columna `Close` existe pero todos sus valores son nulos o no
utilizables, la validacion devuelve `repairable` con el error
`La descarga no contiene valores validos en Close.`.

5. Decision final de la validacion.
Si falla cualquiera de las comprobaciones anteriores, la descarga no se
considera valida operativamente.
Si no falla ninguna, la validacion devuelve `valid`.

Conviene distinguir una cosa importante:

- persistir artefactos no forma parte de la validacion en si misma;
- la persistencia ocurre despues, y solo despues, de que la validacion haya
  devuelto `valid`.

Por tanto, la pregunta precisa de esta fase ya no es si el request parecia
formalmente correcto, sino si la descarga ya normalizada cumple exactamente
las condiciones minimas para que el resto del sistema pueda trabajar con ella.


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

### Artefactos persistidos en esta implementacion

- `results/data_requests/request_<id>.json`
- `results/data_raw/raw_<id>.csv`
- `results/data_normalized/normalized_<id>.csv`
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

### Prompt base del Subagente 2

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

### Limites de reintento en la implementacion

La implementacion fija estos maximos de reintento:

- `max_structural_repair_attempts = 2`
- `max_operational_repair_attempts = 2`

Regla general de transicion de estado:

- si no hay errores -> `valid`
- si hay errores y la ruta de correccion automatica de esa validacion sigue abierta -> `repairable`
- si no existe una correccion fiable -> `blocked`
- si se han agotado los intentos maximos de reparacion -> `blocked`

Esto debe tenerse en cuenta porque es la forma de medir el estado de trabajo de los subagentes:

- el Subagente 1 actua mientras el caso siga en `repairable` dentro de la validacion estructural;
- el Subagente 2 actua mientras el caso siga en `repairable` dentro de la validacion operativa;
- cuando cualquiera de los dos alcanza `blocked`, la fase deja de avanzar en esa ejecucion.

Si tras esos ciclos no se consigue una peticion descargable y util, el estado
de la fase de datos queda en `blocked`.

## Salida final de la fase de datos

La salida final deseada de esta fase es una descarga realizada correctamente en `yfinance`, respaldada por un `FinancialDataRequest` ya validado, y lista para entregarse al Agente 2.

### Que recibe el Agente 2 en esta implementacion

El Agente 2 no recibe directamente todo `WorkflowState`.
Recibe dos entradas:

- `query_input`, que conserva la consulta original;
- `input_payload`, construido por `_build_phase2_input_payload(state)`.

Ese `input_payload` contiene:

- `query`;
- `tickers`;
- `temporal_context`;
- `csv_paths`;
- `data_context` con `row_count` y `available_columns`;
- `warnings`;
- `download_summary`.

Ejemplo de payload:

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
    "results/data_normalized/normalized_id-unico.csv"
  ],
  "data_context": {
    "row_count": 503,
    "available_columns": ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
  },
  "warnings": [],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["NVDA", "AMD"],
    "tickers_found": ["NVDA", "AMD"],
    "interval": "1d",
    "period": "2y",
    "start": null,
    "end": null
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

Para depurar el proyecto completo, esta carpeta de traza es el punto de
partida mas util antes de revisar artefactos aislados.

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
