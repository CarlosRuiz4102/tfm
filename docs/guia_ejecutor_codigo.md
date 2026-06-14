# Guia del ejecutor de codigo

## Objetivo de esta parte

Esta parte cubre el recorrido que empieza cuando ya existe un script Python aceptado por la parte 3 y termina cuando el sistema decide si la ejecucion fue valida, si necesita reparacion o si debe bloquearse.

Su objetivo no es:

- rehacer el analisis anterior;
- reinterpretar la consulta del usuario desde cero;
- volver a pasar por la validacion estatica de codigo;
- redactar la respuesta final para el usuario.

Su objetivo si es:

1. recibir un script ya aceptado por la parte 3;
2. construir el payload operativo con el que debe ejecutarse;
3. lanzar la ejecucion real y registrar sus artefactos;
4. decidir si la ejecucion fue `valid`, `repairable` o `blocked`;
5. activar un subagente de reparacion cuando el fallo sea recuperable;
6. entregar a la siguiente fase solo una salida de ejecucion util y trazable.

## Alcance de esta parte

Esta parte empieza justo despues del Agente 4 y termina justo antes de la siguiente fase del flujo.

Recorrido completo:

```text
Codigo validado por la parte 3
-> Ejecutor de codigo
-> Validacion del resultado de ejecucion
-> Subagente 4 si hay fallo reparable
-> Nueva ejecucion si procede
-> Salida valida para la siguiente fase
```

## Idea central de esta parte

Esta parte no decide que hay que calcular.
Eso ya se resolvio antes.

Aqui solo existen tres preguntas:

1. **Que script vamos a ejecutar**
   El codigo ya viene aceptado desde la parte 3.

2. **Con que contexto operativo se va a ejecutar**
   El sistema debe preparar un payload estable, trazable y coherente con los CSV ya disponibles.

3. **Que hacemos si falla**
   Si la ejecucion falla, el sistema debe decidir si el caso es recuperable o si ya no merece la pena seguir corrigiendo.

La idea importante es esta:

- el ejecutor no "opina" sobre el codigo;
- el ejecutor lo lanza y recoge evidencia;
- la validez de la parte 4 se decide por el resultado observable de la ejecucion;
- el Subagente 4 no demuestra por si solo que el codigo ya esta bien;
- la unica validacion real de su reparacion es volver a ejecutar el script.

## Principios de diseno

- El ejecutor trabaja sobre codigo ya aceptado por la parte 3.
- El resultado de ejecucion debe medirse con evidencia observable: `returncode`, `stdout`, `stderr` y artefactos persistidos.
- Un `returncode = 0` no basta por si solo: tambien hace falta una salida estructurada util.
- Los fallos reparables de ejecucion deben tratarse con un subagente propio, distinto del Subagente 3.
- La reparacion del Subagente 4 solo se considera valida si el nuevo script vuelve a ejecutarse correctamente.
- Debe existir un maximo de intentos totales para evitar bucles opacos.
- La semantica de estados debe mantenerse igual que en el resto del sistema: `valid`, `repairable`, `blocked`.

## Estado compartido minimo

Durante esta parte conviene mantener al menos esta informacion:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "status": "code_validated",
  "generated_code": "script Python completo",
  "csv_paths": [
    "C:\\Users\\usuario\\Desktop\\tfm\\results\\data_normalized\\normalized_id.csv"
  ],
  "execution_stdout": "",
  "execution_stderr": "",
  "execution_returncode": null,
  "execution_output": null,
  "execution_artifacts": null,
  "execution_validation_decision": null,
  "warnings": [],
  "error_message": null,
  "execution_attempts": 0,
  "execution_repair_attempts": 0
}
```

Estados recomendados:

- `code_validated`
- `executing`
- `execution_validating`
- `execution_repairing`
- `execution_valid`
- `execution_blocked`
- `ready_for_next_phase`
- `failed_execution_phase`

## Bloque 1: que entra realmente en la parte 4

### Que entra

La parte 4 recibe como minimo:

- `generated_code`
- `user_query`
- `tickers`
- `temporal_context`
- `csv_paths`
- `data_context`
- `warnings`
- `download_summary`

Entrada conceptual:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "generated_code": "script Python completo ya aceptado por la parte 3",
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
    "available_columns": ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
  },
  "warnings": [],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["NVDA", "AMD"],
    "tickers_found": ["NVDA", "AMD"]
  }
}
```

### Que se hace aqui internamente

- comprobar que existe un script a ejecutar;
- construir el payload operativo;
- preparar rutas de artefactos;
- pasar al ejecutor.

### Que sale

Un intento real de ejecucion con evidencia completa para decidir el siguiente paso del flujo.

## Bloque 2: ejecutor de codigo

## Funcion del ejecutor

El ejecutor de codigo lanza el script Python y recoge evidencia tecnica.

Su trabajo es:

- persistir el script que se va a lanzar;
- persistir el payload efectivo de entrada;
- ejecutar el script en un proceso aislado del workflow principal;
- recoger `stdout`, `stderr` y `returncode`;
- persistir los artefactos de ese intento;
- devolver un resultado bruto para la validacion de ejecucion.

Su trabajo no es:

- decidir si el script implementa bien el problema original;
- reinterpretar la consulta del usuario;
- corregir el codigo;
- inventar una salida si la ejecucion falla.

## Que le entra

Le entra:

- el `generated_code` actual;
- el payload operativo ya construido;
- la configuracion de tiempo maximo y ejecutable Python.

### Payload de ejecucion recomendado

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
    "available_columns": ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
  },
  "warnings": [],
  "download_summary": {
    "provider": "yfinance",
    "tickers_requested": ["NVDA", "AMD"],
    "tickers_found": ["NVDA", "AMD"]
  }
}
```

### Regla importante sobre el payload

El payload debe contener solo contexto operativo necesario para ejecutar el script.

No debe arrastrar contratos viejos que no pertenecen a esta parte.

## Como se ejecuta

Secuencia conceptual:

1. guardar el script en `results/code/generated_<run_id>.py`;
2. guardar el payload en `results/logs/payload_<run_id>.json`;
3. lanzar el proceso Python con `script_path` y `payload_path`;
4. capturar `stdout` y `stderr`;
5. guardar `stdout` y `stderr` en artefactos persistidos;
6. intentar parsear `stdout` como JSON.

### Pseudocodigo orientativo

```python
script_path.write_text(code, encoding="utf-8")
payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

completed = subprocess.run(
    [python_executable, str(script_path), str(payload_path)],
    capture_output=True,
    text=True,
    timeout=timeout_seconds,
    check=False,
)

stdout = completed.stdout
stderr = completed.stderr
returncode = completed.returncode
```

## Artefactos recomendados

- `results/code/generated_<run_id>.py`
- `results/logs/payload_<run_id>.json`
- `results/logs/stdout_<run_id>.json`
- `results/logs/stderr_<run_id>.log`

## Bloque 3: validacion del resultado de ejecucion

## Funcion de esta validacion

La validacion de ejecucion decide si el intento recien lanzado deja una salida util para continuar o si hace falta reparacion.

Pregunta que responde esta validacion:

- "La ejecucion ha producido una salida suficientemente buena para pasar a la siguiente fase?"

Es importante insistir en esto:

- ejecutar no equivale automaticamente a validar;
- un script puede correr y aun asi devolver una salida inutil;
- la parte 4 debe medir la ejecucion, no solo lanzarla.

## Idea central de esta validacion

La validacion de ejecucion debe responder a dos preguntas principales:

1. El script se ha ejecutado correctamente como proceso?
2. La salida generada esta en una forma correcta para que la parte 5 pueda trabajar bien con ella?

Esta forma de plantearlo es importante porque evita convertir la parte 4 en una lista de checks aislados sin criterio funcional.

La parte 4 existe para garantizar dos cosas:

- que el script realmente ha sido ejecutable dentro del workflow;
- que lo que deja como salida sirve como artefacto estructurado para la siguiente fase.

## Que le entra

Le entra el resultado bruto del ejecutor:

```json
{
  "returncode": 1,
  "stdout": "",
  "stderr": "KeyError: 'Close'",
  "parsed_output": null,
  "artifacts": {
    "script_path": "results/code/generated_20260614_120000_000001.py",
    "payload_path": "results/logs/payload_20260614_120000_000001.json",
    "stdout_path": "results/logs/stdout_20260614_120000_000001.json",
    "stderr_path": "results/logs/stderr_20260614_120000_000001.log"
  }
}
```

## Que se valida

A partir de esas dos preguntas principales, la validacion revisa dos bloques tecnicos y, despues, toma una decision de flujo.

### 1. Validacion de ejecucion del proceso

- el proceso termina dentro del tiempo maximo;
- no hay excepcion de infraestructura al lanzar;
- `returncode` permite distinguir exito de fallo.

Pregunta que responde:

- "El script llego a ejecutarse como proceso util?"

### 2. Validacion de la salida para la parte 5

- `stdout` existe;
- `stdout` es JSON parseable;
- el JSON contiene como minimo:
  - `metrics`
  - `summary`
  - `limitations`

Pregunta que responde:

- "Aunque el proceso haya corrido, la salida sirve realmente para el resto del workflow?"

### 3. Calidad minima del artefacto de salida

- `summary` no viene vacio;
- `limitations` existe aunque sea una lista vacia;
- `metrics` no esta ausente;
- la salida no es texto libre ni logs mezclados con JSON.

Pregunta que responde:

- "La salida es utilizable como artefacto estructurado?"

## Decision posterior del flujo

Despues de validar ejecucion y salida, el workflow ya puede clasificar el resultado del intento.

Esta clasificacion no es una validacion adicional distinta de las anteriores, sino la consecuencia de lo observado.

Si algo falla, conviene clasificar si el caso parece:

- recuperable con un nuevo intento de codigo;
- o no recuperable en esta ejecucion.

Ejemplos tipicos de fallo recuperable:

- `KeyError`
- `NameError`
- `TypeError`
- `JSONDecodeError` en la salida
- `stdout` vacio
- claves obligatorias ausentes
- timeout puntual

Ejemplos tipicos de bloqueo:

- se agotaron los intentos maximos;
- el script sigue rompiendo el contrato tras varios intentos;
- la salida sigue siendo inutil de forma persistente.

## Que es una ejecucion correcta

Una ejecucion correcta no significa solo "el script no ha explotado".

Conviene considerar correcta una ejecucion cuando:

- el proceso termina sin error;
- `returncode == 0`;
- `stdout` es JSON valido;
- la salida contiene `metrics`, `summary` y `limitations`;
- el resultado queda persistido en artefactos trazables.

## Que es una ejecucion no correcta

Una ejecucion no correcta es cualquier intento donde el flujo no puede confiar todavia en la salida.

Casos tipicos:

- el script lanza una excepcion;
- el proceso termina con `returncode != 0`;
- `stdout` viene vacio;
- `stdout` no es JSON valido;
- el JSON no tiene las claves requeridas;
- el proceso excede el timeout;
- la salida esta mezclada con prints o logs no esperados.

## Salidas posibles de esta validacion

1. `valid`
2. `repairable`
3. `blocked`

Semantica recomendada:

- `valid`
  significa: la salida puede pasar a la siguiente fase.
- `repairable`
  significa: el error observado parece corregible con un nuevo script.
- `blocked`
  significa: ya no vamos a seguir corrigiendo en esta ejecucion.

### Caso `valid`

La salida se guarda como `execution_output` y el flujo puede continuar.

### Caso `repairable`

Se activa el Subagente 4.

### Caso `blocked`

La ejecucion termina con error controlado y el flujo deja de reintentar.

## Subagente 4: reparador de errores de ejecucion

## Funcion y alcance

El Subagente 4 corrige el script cuando la ejecucion real ha fallado de forma reparable.

Su funcion es:

- recibir el script que fallo;
- leer el error observable del intento real;
- devolver un nuevo script completo corregido;
- dejarlo listo para un nuevo intento de ejecucion.

Su funcion no es:

- rehacer el razonamiento anterior del flujo;
- usar `analysis_plan`;
- probar por si mismo que el codigo ya es correcto;
- saltarse el contrato de entrada y salida del workflow.

## Que le entra

Entrada conceptual:

```json
{
  "original_user_message": "Compara Nvidia y AMD en 2 anos",
  "execution_input": {
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
      "available_columns": ["Date", "Ticker", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    },
    "warnings": []
  },
  "previous_code": "script Python completo que fallo",
  "execution_error": {
    "returncode": 1,
    "stdout": "",
    "stderr": "KeyError: 'Close'",
    "error_summary": "El script fallo al acceder a una clave o columna ausente."
  },
  "attempt_number": 2,
  "execution_output_contract": {
    "stdout": "un unico JSON valido",
    "required_top_level_keys": ["metrics", "summary", "limitations"],
    "optional_top_level_keys": ["analysis_type", "tables", "series", "diagnostics"]
  }
}
```

## Que devuelve

Debe devolver exclusivamente un JSON con un unico campo `code`.

Contrato:

```json
{
  "code": "script Python completo corregido"
}
```

## Como funciona internamente

El Subagente 4 no "sabe" con certeza que su reparacion ya es correcta.

Su funcionamiento real es este:

1. observa el error de ejecucion;
2. infiere una correccion razonable;
3. reescribe el script completo;
4. devuelve ese script al workflow;
5. el workflow vuelve a lanzarlo en el ejecutor.

La idea clave es esta:

- el Subagente 4 propone;
- el ejecutor confirma o desmiente.

## Como determina si cree que el codigo ya esta bien

La respuesta correcta aqui debe ser prudente:

- no lo determina de forma definitiva;
- solo puede producir una version que, segun el error observado, parece mejor alineada con el contrato del workflow;
- la unica validacion real de esa hipotesis es volver a ejecutar el script.

Por tanto, no conviene introducir una validacion local adicional que finja certeza.

La regla operativa deberia ser:

- si el Subagente 4 devuelve un nuevo script, ese script no se considera bueno por el mero hecho de existir;
- solo se considera aceptable si el nuevo intento de ejecucion resulta `valid`.

## Prompt base recomendado para Subagente 4

```text
Eres el Subagente 4 del flujo de ejecucion de codigo.
Tu tarea es corregir un script Python que ya fue aceptado por la validacion estatica,
pero que fallo durante la ejecucion real.

Devuelve exclusivamente JSON valido con un unico campo code.
El valor code debe ser un script Python completo, corregido y ejecutable.
No incluyas markdown ni texto adicional.

Debes:
- leer la consulta original del usuario;
- leer el contexto operativo de ejecucion;
- leer el codigo anterior;
- leer el error observado durante la ejecucion;
- corregir el script para que pueda ejecutarse dentro del workflow;
- mantener el mismo contrato de entrada y salida del sistema.

No debes:
- usar analysis_plan;
- reinterpretar la consulta desde cero;
- cambiar libremente tickers, fechas, intervalo o csv_paths;
- devolver un parche parcial;
- producir texto adicional fuera del JSON.

Reglas obligatorias:
- el script debe leer el payload desde argv[1];
- debe imprimir un unico JSON valido por stdout;
- debe mantener las claves requeridas por el workflow;
- si faltan datos, debe reflejarlo en limitations en vez de inventar resultados;
- debe corregir el error observado sin introducir dependencias externas ni rutas ocultas.
```

## Reejecucion y bucle de reparacion

La ruta general en esta parte deberia entenderse asi:

```text
Codigo validado por la parte 3
-> Ejecutor de codigo
-> Validacion de ejecucion
-> si valid, continua
-> si repairable, corrige Subagente 4
-> nueva ejecucion
-> nueva validacion
-> si no converge, blocked
```

## Regla importante sobre intentos

Conviene fijar un maximo total de ejecuciones.

Recomendacion:

- `MAX_EXECUTION_ATTEMPTS = 3`

Interpretacion recomendada:

- 1 ejecucion inicial;
- hasta 2 reintentos tras reparacion.

Regla general:

- si la ejecucion es correcta -> `valid`
- si falla y aun parece corregible -> `repairable`
- si ya no existe una correccion razonable -> `blocked`
- si se han agotado los intentos maximos -> `blocked`

## Que deberia recibir la siguiente fase

Minimo recomendable:

- `execution_output`
- `execution_artifacts`
- `execution_stdout`
- `execution_stderr`
- `execution_returncode`
- avisos relevantes acumulados

La siguiente fase no deberia recibir una salida dudosa ni un intento fallido como si fuera resultado bueno.

## Condiciones para considerar esta parte completada

- existe un script ejecutado con artefactos persistidos;
- la salida estructurada es valida para el workflow;
- no quedan dudas sobre si el intento que se entrega fue realmente el ultimo valido;
- si hubo reparaciones, estas quedaron trazadas mediante artefactos y contadores de intentos.

## Resumen operativo final

La parte del ejecutor de codigo debe quedar pensada como una subarquitectura con seis responsabilidades:

1. recibir un script ya aceptado por la parte 3;
2. construir y persistir el payload operativo;
3. ejecutar el script y recoger evidencia tecnica;
4. validar si el resultado de ejecucion es `valid`, `repairable` o `blocked`;
5. corregir mediante el Subagente 4 cuando el fallo sea recuperable;
6. entregar a la siguiente fase solo una salida de ejecucion ya confirmada por el propio ejecutor.

Si esta parte queda bien implementada, el sistema gana en:

- trazabilidad de runtime;
- separacion clara entre validacion estatica y validacion de ejecucion;
- control de reintentos;
- facilidad de depuracion;
- coherencia con el flujo multiagente completo.
