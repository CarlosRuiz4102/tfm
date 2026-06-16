# Guia de trazabilidad del workflow completo

## Objetivo

Esta guia define como trazar una ejecucion completa del proyecto de inicio a
fin sin depender solo del resultado final ni de logs dispersos.

La idea es que, cuando ejecutemos ejemplos sueltos o una bateria mas grande,
podamos responder rapido a preguntas como:

- donde fallo exactamente el flujo;
- que salio de cada nodo;
- que artefactos reales se generaron;
- que se entrego a la parte siguiente;
- y si el problema esta en datos, analisis, codigo, ejecucion o interpretacion.

## Principio general

Cada ejecucion del workflow crea un identificador unico `run_id` y una carpeta
propia de traza:

```text
results/traces/<run_id>/
```

Esa carpeta se crea al principio del workflow y acompana toda la ejecucion
hasta el final.

## Estructura actual de la traza

Minimo que queda guardado:

- `manifest.json`
- `events.jsonl`
- `snapshots/00_initial_state.json`
- `snapshots/01_ingest_node.json`
- `snapshots/02_data_request_planning_node.json`
- `snapshots/...`
- `snapshots/09_interpretation_node.json`

Si el flujo termina antes por invalidez, bloqueo o error, tambien queda el
snapshot del nodo terminal correspondiente.

## Que contiene cada artefacto

### `manifest.json`

Resume la ejecucion:

- `run_id`
- consulta original
- estado actual o final
- rutas de la propia traza
- orden de nodos
- resumen de artefactos importantes

Sirve para orientarse rapido sin abrir todos los snapshots.

### `events.jsonl`

Guarda eventos de seguimiento en formato JSON Lines.

Ahora mismo incluye, como minimo:

- inicio del workflow
- inicio de cada nodo
- fin de cada nodo
- escritura de snapshots
- fin del workflow

En los eventos de fin de nodo tambien quedan:

- `status_before`
- `status_after`
- `duration_ms`
- resumen ligero del estado
- resumen ligero de artefactos

La idea es poder localizar rapido donde se degrado una ejecucion sin cargar
todo el estado completo.

### `snapshots/*.json`

Cada snapshot guarda `WorkflowState.to_dict()` en un punto concreto del flujo.

Esto permite reconstruir despues:

- que request de datos se habia resuelto;
- que salida produjo el analista;
- que codigo quedo finalmente generado;
- que devolvio la ejecucion;
- que payload limpio recibio el interpretador;
- que respuesta final se entrego.

## Como se conecta con cada parte

### Parte 1 y fase de datos

La traza permite ver:

- consulta original;
- request de datos generado;
- correcciones estructurales u operativas;
- artefactos descargados y CSVs resultantes.

### Parte 2

La traza permite ver:

- el contrato analitico realmente construido;
- que metricas y columnas se pidieron;
- si hubo warnings relevantes en la planificacion.

### Parte 3

La traza permite ver:

- el codigo generado;
- el resultado de la validacion de codigo;
- si hubo reparaciones previas a la ejecucion.

### Parte 4

La traza permite ver:

- el `execution_output` validado;
- los intentos de ejecucion;
- stderr, stdout y artefactos tecnicos asociados;
- si hubo reparacion por fallo de runtime.

### Parte 5

La traza permite ver:

- el `interpretation_payload` limpio;
- la respuesta final;
- los warnings heredados;
- el estado final de la interpretacion.

Importante: el interpretador decide el nivel de elaboracion desde la consulta y
los resultados reales, no desde pistas de `analysis_plan` en su payload.

## Como usar esta traza al depurar ejemplos

Orden de uso:

1. abrir `manifest.json` para identificar `status` final y artefactos clave;
2. revisar `events.jsonl` para localizar el nodo donde cambio el estado;
3. abrir el snapshot inmediatamente anterior y posterior a ese nodo;
4. decidir si el problema viene de datos, analisis, codigo, ejecucion o interpretacion;
5. solo despues tocar prompts o logica del agente afectado.

Este orden evita corregir a ciegas.

## Que problema resuelve esta trazabilidad

Sin una traza estructurada, al ejecutar una bateria de ejemplos es facil ver
solo que "el resultado final sale mal", pero no por que.

Con esta carpeta por ejecucion ganamos:

- depuracion mas rapida;
- comparacion mas fiable entre ejemplos;
- menos errores de interpretacion humana;
- base mejor para futuras evaluaciones;
- mas robustez antes de entrar en metricas formales.

## Limitaciones actuales

La traza actual esta pensada para depuracion operativa y funcional.

Todavia puede reforzarse mas con:

- un resumen agregado por bateria de ejecuciones;
- clasificacion automatica de errores por fase;
- persistencia separada de prompts y respuestas LLM;
- utilidades para comparar dos `run_id` entre si.

## Siguiente iteracion

Antes de montar metricas de rendimiento, la siguiente mejora util es apoyar esta traza con una
herramienta de lectura o resumen automatico por `run_id`.

Eso permitiria procesar lotes de ejemplos sin depender de abrir manualmente cada
JSON.
