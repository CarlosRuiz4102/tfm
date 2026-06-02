# Evaluacion cualitativa de analisis LLM

Este documento define la metodologia cualitativa propuesta para evaluar el MVP de analisis financiero historico con LLM, generacion de codigo y ejecucion controlada. Complementa las metricas tecnicas ya registradas por el sistema, como estado final, errores, tiempo de ejecucion, salida JSON y respuesta final.

## Motivacion

La comparacion entre modelos LLM no puede reducirse solo a una metrica numerica. En este TFM el objetivo no es predecir mercados, sino comprobar si un modelo interpreta una consulta financiera, genera codigo suficiente para calcular datos historicos relevantes y redacta una explicacion util para el usuario.

Dos respuestas pueden completar el workflow y, aun asi, tener calidad distinta. Por ejemplo, una puede devolver solo una rentabilidad acumulada, mientras otra puede explicar tambien volatilidad, drawdown, rango de precios y limitaciones. Por este motivo se propone una revision humana basada en criterios cualitativos definidos antes de revisar las respuestas.

La evaluacion no pretende afirmar que un modelo sea objetivamente superior en sentido estadistico. Se plantea como una comparacion exploratoria, trazable y revisable, apoyada en evidencias observadas durante las ejecuciones.

## Apoyo metodologico

Los criterios se apoyan en fuentes de educacion financiera y visualizacion:

- SEC / Investor.gov advierte que la informacion de rendimiento puede presentarse de distintas formas, que debe entenderse como se calcula y presenta, y que el rendimiento pasado no predice necesariamente resultados futuros.
- Investor.gov define el riesgo como incertidumbre o posible perdida, relacionando riesgo y retorno esperado.
- CFA Institute incluye retorno, varianza, volatilidad, covarianza y correlacion como elementos basicos para interpretar carteras y activos a partir de datos historicos.
- CFA Institute describe el drawdown como una metrica intuitiva de riesgo historico, facil de interpretar y basada en datos observados, sin exigir supuestos de distribucion.
- Las guias de visualizacion recomiendan graficos de linea para series temporales, limitar el numero de series, evitar ejes dobles potencialmente engañosos y elegir intervalos adecuados. En comparaciones de activos con escalas distintas, una evolucion normalizada facilita la lectura.

## Que se entiende por buen analisis

Un buen analisis debe cumplir los siguientes principios:

- Responder exactamente a la consulta del usuario.
- Calcular o mostrar los datos esenciales para esa consulta.
- Respetar tablas, graficas o formatos solicitados por el usuario.
- Seleccionar metricas razonables cuando la consulta sea general: rentabilidad, volatilidad, drawdown, maximos/minimos, correlacion, medias moviles o volumen, segun corresponda.
- Diferenciar dato historico observado, interpretacion y limitacion.
- No inventar informacion externa, noticias, predicciones ni recomendaciones de inversion.
- Mantener trazabilidad entre consulta, plan, codigo generado, salida estructurada e interpretacion final.

## Dos agentes, dos responsabilidades

La calidad se revisa separando dos componentes:

1. Primer agente: interpretacion y generacion de codigo.
   Debe producir el material necesario para que el analisis sea verificable: metricas, tablas, series temporales, datos para graficas o resumen estructurado. No debe limitarse a generar un numero aislado si la consulta pide una comparacion, un analisis de riesgo o una salida visual.

2. Segundo agente: interpretacion final.
   Debe explicar las metricas calculadas con lenguaje claro, sin anadir datos externos. Su valor esta en convertir los resultados estructurados en una respuesta comprensible, prudente y util.

## Niveles de profundidad

La profundidad del analisis se adapta a la consulta del usuario.

### Nivel A: analisis simple por defecto

Se usa cuando la query es simple y el usuario no pide formato especial. La salida debe ser breve y trazable.

Salida esperada:

- Texto corto.
- Tabla o bloque estructurado de metricas basicas.
- Sin obligacion de generar graficas.

Ejemplos:

- "Cuanto ha crecido Nvidia en 5 anos".
- "Dame una vision general de AAPL en 3 meses".
- "Analiza los retornos de QQQ y SPY en 2024".

### Nivel B: analisis mejorado

Se usa cuando el usuario pide un analisis mas completo, una comparativa clara o una explicacion con mas detalle.

Salida esperada:

- Texto explicativo.
- Tabla de metricas.
- Una grafica principal o datos estructurados para representarla.

Criterio de grafica principal:

- Un solo activo: evolucion de cierre/precio.
- Dos o mas activos comparables: evolucion normalizada a 100.
- Consulta de riesgo: drawdown.
- Consulta tecnica: medias moviles.

### Nivel C: analisis profesional o enriquecido

Se usa cuando el usuario pide expresamente un analisis profesional, avanzado, detallado, con varias graficas o con formato concreto.

Salida esperada:

- Texto interpretativo.
- Una o varias tablas.
- Varias visualizaciones o datos estructurados para generarlas.
- Desglose por metricas, conclusion y limitaciones.

Puede incluir evolucion normalizada, drawdown, retornos diarios o mensuales, volatilidad, correlacion, volumen, medias moviles, ranking comparativo o desglose por periodos.

## Regla de adaptacion

- Si el usuario no especifica nivel ni formato, se usa Nivel A.
- Si el usuario pide "analisis completo", "mejor analisis", "comparativa clara" o similar, se usa Nivel B.
- Si pide "profesional", "detallado", "avanzado", varias graficas o formato concreto, se usa Nivel C.
- Si el usuario pide explicitamente que quiere ver algo, eso tiene prioridad sobre la plantilla por defecto. Por ejemplo, una query simple que pida grafica de drawdown debe producir esa salida.

## Rubrica cualitativa

| Criterio | Excelente | Correcto | Parcial | Deficiente |
|---|---|---|---|---|
| Comprension de la consulta | Responde exactamente a la intencion y restricciones | Responde a la idea principal | Responde solo a parte de la consulta | Interpreta mal la solicitud |
| Seleccion de metricas | Elige metricas suficientes y pertinentes | Elige metricas basicas adecuadas | Omite metricas importantes | Usa metricas irrelevantes o insuficientes |
| Primer agente: codigo/datos | Genera salida estructurada completa y trazable | Genera datos suficientes | Genera datos incompletos | No permite analizar bien la consulta |
| Tablas/graficas solicitadas | Respeta lo pedido y lo estructura con claridad | Respeta lo esencial | Solo cumple parte del formato | Ignora la peticion visual o tabular |
| Exactitud historica | Interpreta solo datos ejecutados | No inventa datos, con algun detalle menor | Hay ambiguedades | Mezcla datos externos o no trazables |
| Segundo agente: claridad | Explica datos, lectura y limites con lenguaje claro | Explica correctamente lo principal | Explicacion superficial | Texto confuso o no util |
| Utilidad para el usuario | Ayuda a entender comportamiento y riesgo | Aporta una lectura razonable | Aporta poco valor | No ayuda a tomar contexto |
| Limitaciones | Distingue historico, interpretacion y no prediccion | Incluye cautela basica | Cautela insuficiente | Presenta conclusiones como certezas |
| Seguridad financiera | Evita recomendaciones y predicciones | No recomienda invertir | Usa lenguaje ambiguo | Recomienda comprar/vender o predice |
| Trazabilidad | Se conectan consulta, plan, codigo, metricas y respuesta | Trazabilidad suficiente | Trazabilidad parcial | No se puede auditar la respuesta |

## Plantilla de revision manual

| Campo | Valor |
|---|---|
| ID de query |  |
| Modelo / perfil |  |
| Nivel esperado | A / B / C |
| Estado tecnico | completed / completed_with_error / error |
| Primer agente: metricas generadas |  |
| Primer agente: tablas/graficas/datos visuales |  |
| Segundo agente: interpretacion final |  |
| Criterio global | Excelente / Correcto / Parcial / Deficiente |
| Fallos observados |  |
| Comentario humano |  |

## Bateria definitiva por niveles

La bateria ejecutable esta cerrada y equilibrada:

- 5 queries de Nivel A.
- 5 queries de Nivel B.
- 5 queries de Nivel C.

El catalogo completo, con texto de cada consulta, datos locales y objetivo, se mantiene en `docs/bateria_evaluacion_15_queries.md`. La definicion que consume el programa vive en `scripts/generate_qualitative_demo_report.py`, dentro de `DEMO_CASES`.

Ademas de acciones e indices diarios, la bateria incluye Bitcoin, EUR/USD horario y oro horario. Esto permite observar si el flujo mantiene su comportamiento con distintas clases de activo e intervalos temporales.

## Registro de diferencias entre modelos

Para cada modelo se recomienda registrar:

- Si completo el flujo.
- Si el codigo fue valido a la primera o necesito reparacion.
- Si produjo las metricas esperadas para el nivel A/B/C.
- Si respeto tablas, graficas o salidas solicitadas.
- Si la interpretacion fue clara y prudente.
- Si aparecieron recomendaciones de inversion, predicciones o datos no observados.

La comparacion final debe formularse como evidencia observada, no como una clasificacion absoluta.
