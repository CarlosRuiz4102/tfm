# Guion de Presentación del TFM (15 minutos)

## Diapositiva 1. Presentación

- Buenos días. Soy Carlos Ruiz Oyarzun y voy a presentar mi Trabajo Fin de Máster, titulado "Sistema LLM para análisis financiero histórico mediante generación automática de código".

## Diapositiva 2. Idea y motivación

- La idea del trabajo surge de una pregunta sencilla:
- Si un LLM ya puede interpretar consultas y generar código, ¿hasta qué punto puede ayudar a una persona a interpretar mejor datos históricos de bolsa?
- Esa fue la idea principal con la que construí el trabajo.
- Desde el principio quise evitar un enfoque de caja negra.
- La motivación no era pedirle una respuesta al modelo y aceptarla tal cual.
- Lo que quería era construir un flujo que ayudara a explicar mejor el resultado.
- Ese flujo debía dejar artefactos intermedios y hacer visible:
- qué datos usa,
- qué cálculos ejecuta,
- y dónde falla si algo sale mal.
- Por eso, el objetivo no ha sido construir un asesor financiero ni un sistema de predicción.
- El objetivo ha sido construir una herramienta de apoyo para interpretar datos históricos de la forma más explicativa, trazable y controlada posible.

## Diapositiva 3. Pequeña revisión del estado del arte

- En el estado del arte hay tres ideas clave para este trabajo.
- Primero, que el ámbito financiero tiene particularidades propias, como muestran modelos especializados como FinBERT o BloombergGPT.
- Segundo, que las arquitecturas con agentes permiten separar tareas y combinar el modelo con herramientas externas.
- Tercero, que la generación de código permite apoyar la respuesta en cálculos observables, y no solo en texto plausible.
- Mi propuesta se sitúa precisamente ahí:
- usar un modelo generalista dentro de un flujo fijo,
- con validaciones,
- ejecución controlada,
- y trazabilidad.

## Diapositiva 4. Visión general del sistema

- En esta diapositiva quiero mostrar el pipeline general del sistema.
- Es decir, el recorrido que sigue una consulta desde que entra en lenguaje natural hasta que se convierte en una respuesta final legible para el usuario.
- A muy alto nivel, ese recorrido puede resumirse así:
- consulta,
- validación,
- resolución de datos,
- planificación analítica,
- generación de código,
- ejecución,
- e interpretación final.
- En la siguiente diapositiva entraré con más detalle en lo que ocurre dentro de cada fase.

## Diapositiva 5. Flujo de ejecución por fases

- La parte central del trabajo es este flujo multiagente.
- La primera fase resuelve el problema de datos.
- A partir de la consulta, el sistema construye un `FinancialDataRequest`, valida su coherencia y descarga datos históricos reales.
- Esto permite que el resto del flujo trabaje sobre una base efectiva y no sobre una suposición.
- La segunda fase corresponde a la planificación analítica.
- Aquí el sistema decide qué quiere calcular, con qué columnas y con qué formato de salida.
- Es decir, todavía no calcula cifras, sino que fija el plan del análisis.
- La tercera fase genera código.
- Ese plan se traduce a un script Python ejecutable que implementa las métricas y estructuras necesarias.
- La cuarta fase introduce control.
- Antes de ejecutar, el código se valida.
- Después se ejecuta de verdad y se comprueba no solo que termine, sino que deje una salida estructurada útil para la fase final.
- Por último, la quinta fase corresponde a la interpretación.
- El sistema redacta la respuesta final a partir de resultados ya obtenidos, no rehaciendo el análisis desde cero.
- Un punto importante es que el sistema no solo contempla la ruta ideal.
- Si falla la estructura del request, la descarga, el código o la ejecución, hay rutas de reparación específicas.
- Además, esas reparaciones están acotadas, de modo que el flujo puede bloquearse de forma controlada en lugar de entrar en bucles indefinidos.
- En resumen, la aportación fuerte del trabajo es que la respuesta final queda respaldada por contratos intermedios, validaciones explícitas y evidencia persistida.

## Diapositiva 6. Introducción al ejemplo completo

- Una vez vista la arquitectura, voy a aterrizarla rápidamente con un ejemplo completo de ejecución.
- La consulta elegida es:
- "Analiza AAPL en 3 meses y explica qué se puede concluir solo con estos datos históricos".
- No voy a recorrer todas las trazas, pero sí voy a mostrar tres artefactos que he considerado especialmente interesantes:
- lo que genera el Agente 1 en la fase de datos,
- lo que genera el Agente 3 en la fase de código,
- y lo que finalmente produce el Agente 5 como respuesta para el usuario.

## Diapositiva 7. Ejemplo completo: Agente 1

- Lo primero que quiero enseñar es la salida del Agente 1.
- A partir de la consulta original, el sistema construye un `FinancialDataRequest` estructurado.
- En este caso, identifica el ticker `AAPL`, fija el proveedor `yfinance`, usa intervalo diario, periodo de `3 meses` y explicita los campos requeridos.
- Lo importante aquí no es solo que aparezca el ticker correcto.
- Lo importante es que la petición deja de ser una frase ambigua y pasa a convertirse en un artefacto validable.
- Solo cuando ese request es coherente, el sistema pasa a la descarga y normalización de los datos.

## Diapositiva 8. Ejemplo completo: Agente 3

- Después de la fase de planificación, el Agente 3 genera el script Python.
- Aquí se ve un fragmento representativo.
- El código lee el payload desde disco, carga los datos normalizados, calcula métricas como el retorno, la volatilidad o el drawdown y devuelve una salida estructurada con `metrics`, `summary` y `limitations`.
- Este punto es importante porque aquí ya no se está describiendo el análisis en abstracto, sino materializándolo en código que luego puede validarse y ejecutarse dentro del flujo.

## Diapositiva 9. Ejemplo completo: Agente 5

- Por último, esta es la respuesta generada por el Agente 5.
- Aquí ya aparece una salida legible para el usuario, con las métricas principales, una interpretación del comportamiento de AAPL en esos tres meses y las limitaciones del análisis.
- Lo importante es que esta respuesta no aparece directamente tras la consulta inicial.
- Aparece al final de un proceso en el que antes se han resuelto los datos, se ha planificado el análisis, se ha generado código y se ha validado la ejecución.
- Eso es precisamente lo que hace que el sistema pueda ayudar a interpretar mejor los datos de una manera más trazable y más defendible.

## Diapositiva 10. Manera en que se evalúa el proyecto

- Para evaluar el sistema se diseñó una batería de 50 consultas financieras organizada en tres niveles de complejidad: A, B y C.
- La idea era observar no solo si el sistema respondía, sino cómo se comportaba cuando aumentaban las exigencias analíticas, de formato o de prudencia.
- La unidad de análisis es la consulta completa de extremo a extremo.
- Es decir, un caso solo se considera completado si el flujo llega a producir una respuesta final utilizable.
- Además, los casos completados no se daban por buenos automáticamente.
- Los revisábamos con una rúbrica de cinco criterios, puntuando cada uno de 0 a 2:
- 0 significaba que no cumplía,
- 1 que cumplía de forma parcial,
- y 2 que cumplía de forma satisfactoria.
- La adecuación a la consulta medía si la respuesta realmente contestaba a lo que se había pedido.
- La cobertura analítica valoraba si incluía las métricas, comparaciones o elementos relevantes para ese caso.
- La coherencia medía si la respuesta estaba bien hilada y no contenía contradicciones entre resultados e interpretación.
- La claridad evaluaba si la explicación era comprensible y estaba bien expresada para el usuario.
- Y la prudencia valoraba si el sistema evitaba afirmaciones excesivas o conclusiones no justificadas por los datos.

## Diapositiva 11. Resultados

- En total, 27 de las 50 consultas produjeron una respuesta final utilizable, lo que supone una tasa global de completitud del 54 %.
- Si se desglosa por niveles, el comportamiento fue del 80 % en el nivel A, del 60 % en el nivel B y del 35 % en el nivel C.
- La tendencia principal es clara:
- cuando aumenta la complejidad de la consulta, cae la capacidad del sistema para cerrar correctamente todo el flujo.
- Ahora bien, hay un matiz importante.
- Cuando el sistema consigue completar una consulta, la calidad final suele ser buena.
- Por tanto, el problema principal no está tanto en la redacción final como en la robustez de las fases previas.

## Diapositiva 12. Limitaciones

- Antes de comentar las conclusiones, me gustaría señalar varias limitaciones.
- La evaluación se ha realizado con una única configuración del sistema y un único modelo.
- Además, depende de un proveedor de datos históricos y la revisión cualitativa de los casos completados ha sido realizada por el autor.
- También es importante recordar que el alcance del trabajo se limita al análisis histórico.
- No se evalúan la predicción de mercado, el asesoramiento financiero ni la incorporación de factores externos como noticias o macroeconomía.

## Diapositiva 13. Conclusiones

- Como conclusión, diría que la principal aportación del trabajo no es demostrar que un LLM pueda resolver cualquier consulta financiera.
- La principal aportación es mostrar que puede integrarse en un flujo mucho más inspeccionable para ayudar a una persona a interpretar mejor datos históricos de bolsa.
- La evaluación muestra además que, cuando el sistema consigue cerrar bien una consulta, la respuesta final suele mantener el foco, cubrir las métricas principales y conservar un tono prudente.
- Por tanto, el valor del sistema no está solo en responder, sino en ayudar a explicar mejor lo que muestran los datos de una forma más controlada, trazable y metodológicamente defendible.
