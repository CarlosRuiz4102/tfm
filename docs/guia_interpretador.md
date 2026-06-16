# Guia del interpretador

## Objetivo de esta parte

Esta guia cubre el tramo final del flujo, desde que ya existe una salida de
ejecucion valida hasta que el sistema produce una respuesta final legible para
el usuario.

Su objetivo no es:

- decidir que datos descargar;
- planificar el analisis;
- generar o validar codigo;
- recalcular metricas;
- inventar cifras, causas o contexto externo;
- reutilizar pistas internas sobre el nivel de analisis esperado.

Su objetivo si es:

1. recibir la consulta original y los resultados ya obtenidos por el flujo;
2. interpretar esos resultados de forma fiel, clara y prudente;
3. inferir por si mismo el grado de elaboracion de la respuesta;
4. adaptar la forma de salida a la consulta y a la riqueza real de los resultados;
5. producir una respuesta final comprensible sin exponer artefactos tecnicos internos.

## Alcance de esta parte

Esta parte empieza justo despues de una ejecucion valida y termina en la
respuesta final que vera el usuario.

Recorrido completo:

```text
Consulta original del usuario
-> Fase de datos completada
-> Analisis y generacion de codigo completados
-> Ejecucion valida
-> Agente 5: Interpretador
-> Respuesta final
```

## Idea central de esta parte

El interpretador debe actuar como un agente que observa:

1. **la intencion del usuario**
   La consulta original orienta el tipo de respuesta que debe redactarse.

2. **los hechos ya obtenidos**
   La salida de ejecucion contiene las metricas, tablas, series y limitaciones
   que el sistema realmente ha conseguido producir.

3. **el contexto minimo ya resuelto**
   Tickers, rango temporal y avisos relevantes ayudan a redactar mejor, pero no
   deben convertirse en una pista oculta sobre el formato final esperado.

La decision sobre si la respuesta debe ser breve, comparativa, mas desarrollada
o mas explicativa debe surgir de la combinacion entre la `query` y lo que
realmente exista en la salida de ejecucion.

## Principios de diseno

- El interpretador trabaja sobre hechos ya ejecutados, no sobre intenciones intermedias del sistema.
- La fuente principal de verdad es `execution_output`.
- La `query` original debe seguir presente porque orienta el tipo de respuesta esperada.
- El interpretador no debe recibir `analysis_plan` ni pistas equivalentes.
- La profundidad de la respuesta debe inferirse, no venir impuesta por una etiqueta previa.
- La respuesta final debe adaptarse a la riqueza real de los resultados: no debe sonar mas completa de lo que permiten los datos.
- Los avisos y limitaciones relevantes deben reflejarse cuando condicionen la lectura de los resultados.
- La salida final debe ser legible para un humano y limpia de detalles internos del workflow.

## Principio de aislamiento frente a pistas internas

Esta parte del diseno exige una regla fuerte: el Agente 5 no debe conocer de
forma directa ni indirecta el plan analitico con el que se trabajo antes.

### Campos que no deben llegar al interpretador

No pasan a esta fase campos como:

- `analysis_plan`
- `analysis_type`
- `presentation_preferences`
- `output_requirements`
- etiquetas de nivel como `A`, `B` o `C`
- instrucciones internas sobre como debe sonar la respuesta
- codigo generado
- rutas internas de artefactos
- logs tecnicos largos
- errores de parsing o mensajes de infraestructura que no aporten valor al usuario

### Por que esta restriccion es importante

Si el interpretador recibe esas pistas, ya no estara deduciendo por si mismo el
grado de elaboracion necesario. En la practica estaria siguiendo una guia
interna del sistema, y eso contaminaria la evaluacion real de su capacidad de
interpretar la consulta y los resultados.

## Estado compartido minimo

En esta parte, la implementacion mantiene al menos esta informacion:

```json
{
  "user_query": "Compara Nvidia y AMD en 2 anos",
  "status": "executed",
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
    "metrics": {},
    "summary": "texto breve generado por el script",
    "limitations": []
  },
  "warnings": [],
  "final_answer": ""
}
```

Estados reales de esta parte en la implementacion:

- `executed`
- `interpretation_preparing`
- `interpreting`
- `interpreted`
- `completed`
- `completed_with_error`

## Bloque 1: que entra realmente al interpretador

## Que le entra

La implementacion construye un `interpretation_payload` limpio de
interpretacion. No coincide con todo `WorkflowState`.

Entran estos bloques:

- `user_query`
- `resolved_context`
- `execution_output`
- `warnings` relevantes

Payload real:

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

## Que no le entra

No forman parte del payload:

- `analysis_plan`
- `analysis_type`
- `level`
- `presentation_preferences`
- `generated_code`
- `execution_stdout` completo
- `execution_stderr` completo
- `payload_path`, `script_path`, `stdout_path`, `stderr_path`

## Distincion importante entre estado y payload del Agente 5

El workflow puede seguir conservando internamente informacion tecnica por
trazabilidad, pero el interpretador no la ve completa.

Hay que distinguir dos niveles:

### 1. Lo que existe en el estado interno

Puede existir:

- `execution_artifacts`
- `execution_stdout`
- `execution_stderr`
- `analysis_plan`
- `generated_code`
- contadores de reintentos

### 2. Lo que entra al prompt del Agente 5

Entra solo un paquete depurado, orientado a interpretar para un
usuario humano, no para depurar internamente el workflow.

## Bloque 2: funcion del Agente 5

## Funcion del agente

El Agente 5 transforma resultados estructurados ya ejecutados en una respuesta
final en espanol.

Su trabajo es:

- leer la consulta original del usuario;
- observar que resultados existen realmente;
- decidir cuanta elaboracion necesita la respuesta;
- separar hechos observados de lectura interpretativa;
- incorporar limitaciones cuando condicionen la lectura;
- producir una respuesta final comprensible.

Su trabajo no es:

- rehacer el analisis previo;
- deducir metricas no presentes;
- completar resultados ausentes;
- recomendar compra o venta;
- predecir comportamiento futuro;
- exponer el funcionamiento interno del sistema.

## Que tiene que sacar

La salida principal del interpretador debe ser texto final para el usuario.

Conceptualmente:

```json
{
  "final_answer": "Respuesta final redactada en espanol para el usuario."
}
```

Internamente se puede conservar mas traza, pero el producto principal de esta
fase es `final_answer`.

## Que ocurre dentro del Agente 5

En la implementacion actual, esta parte sigue esta secuencia:

1. preparar un payload limpio de interpretacion;
2. compactar listas o bloques demasiado grandes para no saturar el prompt;
3. llamar al LLM en modo texto natural;
4. comprobar que la respuesta no venga en JSON puro ni vacia;
5. guardar la respuesta final;
6. dejar avisos si hubo que regenerar la salida.

La logica importante aqui no es recalcular, sino transformar una salida
estructurada en una respuesta humana util.

### Nota de implementacion actual

En la version actual del proyecto, esta parte conserva ademas el
`interpretation_payload` dentro de `WorkflowState`. Eso permite inspeccionar
despues:

- que vio exactamente el Agente 5;
- con que contexto interpreto;
- y como se conectaron realmente la parte 4 y la parte 5.

Tambien hay que recordar que esta fase no introduce una validacion semantica
intermedia de la respuesta del Agente 5. Los controles que hoy se mantienen son
minimos:

- que la ejecucion previa haya terminado bien;
- que la respuesta no venga vacia;
- que la salida final no sea JSON puro cuando esperamos texto natural.

## Bloque 3: como infiere el tipo de respuesta

## La forma de salida no viene predefinida por una etiqueta

El Agente 5 no recibe una instruccion del tipo:

- "esto es nivel A"
- "esto es una consulta compleja"
- "responde en formato informe"

Esa decision debe tomarla leyendo:

- la `query` original;
- el numero y tipo de metricas disponibles;
- si existen tablas, series o comparaciones;
- si existen limitaciones relevantes;
- si la consulta pide explicitamente una tabla, comparacion o desglose.

## Regla de adaptacion

La respuesta debe adaptarse a dos ejes a la vez:

1. **intencion expresada en la consulta**
2. **densidad real de resultados en `execution_output`**

Si la consulta es simple y los resultados tambien lo son, la respuesta debe ser
simple.

Si la consulta pide comparacion, explicacion o desglose y la salida ejecutada
lo soporta, la respuesta puede ser mas desarrollada.

Si la consulta es compleja pero la salida es limitada, la respuesta debe
decirlo con honestidad en vez de sonar artificialmente completa.

## Ejemplos de adaptacion

### Consulta simple

Ejemplo:

```text
Cuanto ha subido Nvidia en 5 anos
```

Respuesta esperable:

- breve;
- centrada en la cifra principal;
- con una lectura corta;
- con limitaciones solo si son relevantes.

### Consulta comparativa

Ejemplo:

```text
Compara Nvidia y AMD en 2 anos y dime cual rindio mejor
```

Respuesta esperable:

- comparacion clara entre activos;
- una o dos metricas principales;
- conclusion comparativa breve;
- limitaciones al final si aplican.

### Consulta rica o estructurada

Ejemplo:

```text
Resume los resultados por trimestres, separa hechos, interpretacion y limitaciones
```

Respuesta esperable:

- mas desarrollada;
- con bloques visibles o estructura clara;
- usando tablas o resumenes si existen en `execution_output`;
- sin inventar apartados que no se puedan sostener con los resultados.

## Bloque 4: diseno del payload de interpretacion

## El payload debe ser rico pero limpio

No interesa pasarle al Agente 5 el estado entero. Interesa pasarle un
`interpretation_payload` construido expresamente para esta fase.

Contrato del `interpretation_payload`:

```json
{
  "user_query": "str",
  "resolved_context": {
    "tickers": ["str"],
    "temporal_context": {
      "start": "str o null",
      "end": "str o null",
      "period": "str o null",
      "interval": "str o null"
    }
  },
  "execution_output": {
    "metrics": {},
    "summary": "str",
    "limitations": [],
    "tables": [],
    "series": [],
    "diagnostics": {}
  },
  "warnings": ["str"]
}
```

## Que papel tiene cada bloque

- `user_query`
  marca la intencion del usuario y el tono de profundidad esperada.

- `resolved_context`
  permite hablar con precision de tickers, fechas o intervalos sin tener que
  exponer contratos internos previos.

- `execution_output`
  es la fuente factual principal.

- `warnings`
  ayuda a no ocultar irregularidades que convenga trasladar al usuario.

## Compactacion de la implementacion

Si `tables`, `series` o `diagnostics` son grandes, la implementacion los compacta antes
de construir el prompt:

- truncar listas largas;
- limitar cadenas enormes;
- conservar cabecera y muestra representativa;
- mantener siempre `metrics`, `summary` y `limitations`.

La compactacion no debe cambiar los hechos, solo reducir ruido.

## Bloque 5: prompt del interpretador

## Objetivo del prompt

El prompt debe dejar claras tres ideas:

1. el Agente 5 trabaja solo con la consulta y los resultados ejecutados;
2. debe inferir por si mismo el nivel de elaboracion de la respuesta;
3. no debe recibir ni usar pistas internas del plan analitico.

## Prompt base

```text
Eres el Agente 5 del flujo de analisis financiero historico.
Tu tarea es redactar la respuesta final para el usuario usando solo:
- la consulta original;
- el contexto resuelto minimo;
- los resultados realmente obtenidos en execution_output;
- los warnings y limitaciones relevantes.

Debes:
- interpretar los resultados sin recalcular metricas;
- adaptar la profundidad y la estructura de la respuesta a la consulta del usuario;
- separar hechos observados de interpretacion cuando tenga sentido;
- mencionar limitaciones relevantes si condicionan la lectura;
- escribir en espanol claro y natural.

No debes:
- usar analysis_plan ni pistas equivalentes;
- inventar cifras, eventos, noticias o causas externas;
- hacer predicciones;
- recomendar compra o venta;
- sonar mas concluyente de lo que permiten los resultados;
- devolver JSON ni markdown tecnico interno.
```

## Consideraciones finas del prompt

El prompt refuerza tambien estas reglas:

- si la consulta es simple, responde de forma simple;
- si la consulta pide comparacion o desglose, estructura la respuesta en consecuencia;
- si faltan datos para responder del todo, dilo claramente;
- si la salida ejecutada ya incluye limitaciones, no las ocultes;
- no menciones nombres internos del workflow.

## Bloque 6: salida final y control de calidad

## Que se considera una buena salida

Una buena respuesta final cumple estas propiedades:

- responde a la consulta original;
- usa solo resultados realmente presentes;
- no cambia cifras;
- adapta bien el nivel de detalle;
- reconoce limitaciones cuando corresponde;
- evita recomendaciones o predicciones;
- no filtra detalles tecnicos irrelevantes.

## Fallos que vigilar

- responder con JSON puro en vez de texto natural;
- repetir mecanicamente `summary` sin adaptarlo a la consulta;
- sonar como un informe complejo para una consulta simple;
- sonar demasiado breve para una consulta que pide desglose;
- meter informacion externa que no aparece en el flujo;
- ignorar limitaciones importantes;
- mencionar `analysis_plan`, niveles A/B/C o terminos internos.

## Regla de regeneracion minima

Si el modelo devuelve:

- respuesta vacia;
- JSON puro;
- o una salida tecnicamente inutilizable;

la implementacion pide una reformulacion textual, manteniendo el mismo principio:
interpretar solo desde la consulta y los resultados.

## Bloque 7: trazabilidad de esta parte

## Que conserva esta parte

Aunque el usuario solo vea `final_answer`, esta parte deja cierta
traza interna.

La implementacion conserva:

- payload de interpretacion usado;
- respuesta final generada;
- warnings si hubo reintento o reformulacion;
- estado final de la fase.

## Implementacion actual de la traza

Ahora mismo la parte 5 ya queda trazada dentro de la carpeta global del
workflow:

- `results/traces/<run_id>/manifest.json`
- `results/traces/<run_id>/events.jsonl`
- `results/traces/<run_id>/snapshots/09_interpretation_node.json`

En ese snapshot final puede inspeccionarse:

- `interpretation_payload`
- `final_answer`
- `warnings`
- `status`

La ventaja de este enfoque es que no se pierde la conexion con la parte 4:
en la misma carpeta quedan tanto la salida validada del ejecutor como la
interpretacion final generada a partir de ella.

## Artefactos adicionales posibles

Si en una iteracion futura hiciera falta una inspeccion aun mas granular,
podrian persistirse tambien:

- `results/logs/interpretation_payload_<run_id>.json`
- `results/logs/final_answer_<run_id>.txt`

Pero eso seria un refuerzo adicional, no una condicion para que esta parte
quede bien trazada.

## Bloque 8: casos limite

## Cuando la ejecucion no fue valida

Si la ejecucion no termino correctamente, esta parte no intenta producir una
interpretacion normal. En esos casos devuelve una salida controlada de
error o bloqueo.

## Cuando la salida es valida pero pobre

Si `execution_output` es formalmente valido pero muy escaso, el interpretador
debe responder con prudencia:

- aprovechar lo que exista;
- no rellenar huecos;
- explicar que el alcance de la lectura queda limitado.

## Cuando existen tablas o series

Si la consulta sugiere comparacion o desglose y la salida trae tablas o series,
el Agente 5 puede apoyarse en ellas para enriquecer la respuesta.

Eso si:

- solo si existen realmente;
- sin fingir analisis adicionales;
- sin prometer visualizaciones que no se hayan generado.

## Salida final deseada de esta parte

La salida final deseada de esta parte es una respuesta en espanol que:

- interprete fielmente lo que el sistema ha obtenido;
- se adapte a la consulta original;
- no dependa de pistas internas del `analysis_plan`;
- conserve prudencia y claridad;
- cierre el flujo con una comunicacion util para el usuario;
- pueda auditarse despues desde `results/traces/<run_id>/`.

## Resumen operativo final

La parte del interpretador debe quedar pensada como una subarquitectura con
seis responsabilidades:

1. recibir un payload limpio de interpretacion;
2. excluir pistas internas sobre el plan o el nivel esperado;
3. inferir desde la `query` y los resultados el tipo de respuesta adecuado;
4. redactar una respuesta fiel, clara y prudente;
5. regenerar la salida si el modelo devuelve un formato inutilizable;
6. dejar trazabilidad suficiente de esta ultima fase.

Si esta parte queda bien implementada, el sistema gana en:

- mejor separacion entre calculo e interpretacion;
- respuesta final mas honesta respecto a lo realmente ejecutado;
- menor contaminacion por pistas internas del workflow;
- mejor capacidad para observar que tal interpreta el Agente 5 por si mismo;
- una salida final mas alineada con la consulta real del usuario.
