# Prompt para Codex: evaluacion cualitativa de analisis LLM en el TFM

Copia y pega este prompt en una nueva conversacion con Codex dentro del repositorio del TFM.

```text
Estas trabajando en el repositorio de mi TFM sobre un MVP de analisis financiero historico con LLM + generacion de codigo Python + ejecucion controlada + interpretacion final.

Contexto del proyecto:
- El sistema recibe una consulta de usuario, tickers, fechas/periodo, intervalo y rutas CSV.
- El workflow actual separa responsabilidades en varios nodos: ingestion, llm_analysis, code_generation, code_security, code_execution e interpretation.
- El primer bloque LLM interpreta la consulta y genera codigo Python para calcular/mostrar los datos necesarios.
- El segundo bloque LLM interpreta los resultados producidos por el codigo y redacta una respuesta final para el usuario.
- Los datos son historicos y locales, principalmente CSV ya existentes en `data/raw`. No quiero descargar datos nuevos salvo que sea imprescindible y se justifique.
- Ya existen documentos relevantes en `docs/`, especialmente `docs/plan_pruebas_queries_llm.md`, y la memoria LaTeX en `docs/memoria_latex/chapters/`.

Objetivo de esta tarea:
Quiero reforzar la parte metodologica y de evaluacion del TFM. La comparacion puramente cuantitativa entre LLMs es limitada, porque no se trata solo de medir un numero, sino de analizar la calidad de los resultados que cada LLM genera. La evaluacion debe centrarse en si cada modelo produce analisis financieros mas completos, utiles y coherentes para el usuario.

Tienes que trabajar con esta idea principal:
1. La calidad de una respuesta se evaluara mediante revision manual humana.
2. La eleccion puede tener parte subjetiva, pero hay que definir antes que entendemos por "buen analisis".
3. Un buen analisis depende de dos componentes:
   - Lo que genera el primer agente: codigo, metricas, tablas, graficas o datos necesarios para responder a la consulta.
   - Lo que genera el segundo agente: interpretacion, explicacion, contexto, limitaciones y claridad para el usuario.
4. El objetivo no es recomendar comprar/vender ni predecir el mercado, sino analizar datos historicos y explicar resultados.

Define claramente que es un buen analisis:
- Debe responder exactamente a la consulta del usuario.
- Debe calcular o mostrar los datos esenciales para esa consulta.
- Si el usuario pide una grafica concreta, tabla concreta o comparacion especifica, el sistema debe intentar producirla o justificar por que no puede.
- Si la consulta es general, el primer agente debe seleccionar metricas razonables: rentabilidad, volatilidad, drawdown, maximos/minimos, correlacion, medias moviles, volumen, segun corresponda.
- El segundo agente debe interpretar esos datos con lenguaje claro, explicar que significan y evitar conclusiones no soportadas por los datos.
- Debe distinguir entre dato historico observado, interpretacion y limitacion.
- No debe inventar datos externos, noticias, recomendaciones de inversion ni predicciones.

Define tambien un estandar de profundidad del analisis por niveles. Este punto es muy importante para el TFM:

Nivel A: analisis simple por defecto.
- Se aplica cuando el usuario no pide nada especial y la query es simple.
- Debe priorizar claridad, brevedad y trazabilidad.
- Salida esperada: texto breve + tabla o bloque estructurado con metricas basicas.
- No es obligatorio generar graficas si el usuario no las pide y la consulta se puede responder bien con datos resumidos.
- Ejemplos: "analiza NVDA en 2024", "dime la rentabilidad de AAPL", "resumeme SPY".

Nivel B: analisis mejorado.
- Se aplica cuando el usuario pide un analisis mas completo, una comparacion algo mas rica o una explicacion con mas detalle.
- Salida esperada: texto + tabla de metricas + grafica principal.
- La grafica por defecto debe ser:
  - un grafico de precio/cierre si hay un solo activo;
  - una evolucion normalizada a 100 si hay dos o mas activos comparables;
  - una grafica de drawdown si la consulta se centra en riesgo;
  - medias moviles si la consulta se centra en tendencia tecnica.
- Ejemplos: "hazme un analisis completo de NVDA", "comparame QQQ y SPY de forma clara", "quiero entender retorno y riesgo".

Nivel C: analisis profesional o enriquecido.
- Se aplica cuando el usuario pide expresamente algo mas profesional, detallado, con varias graficas, con formato concreto o con analisis avanzado.
- Salida esperada: texto + tablas + varias visualizaciones o salidas especificas segun la consulta.
- Puede incluir, si procede: evolucion normalizada, drawdown, retornos diarios/mensuales, volatilidad, correlacion, volumen, medias moviles, ranking comparativo o desglose por periodos.
- El sistema debe respetar siempre lo que el usuario pida ver. Si el usuario solicita graficas o tablas concretas, eso tiene prioridad sobre la plantilla por defecto.
- Ejemplos: "dame un analisis profesional", "incluye grafica normalizada y drawdown", "comparame estos indices con tabla, graficas y conclusion".

Regla de adaptacion:
- Si el usuario no especifica nivel ni formato, usar Nivel A.
- Si el usuario pide "mejor analisis", "mas completo", "comparativa clara" o similar, usar Nivel B.
- Si el usuario pide "profesional", "detallado", "avanzado", varias graficas, formato concreto o varios criterios de analisis, usar Nivel C.
- Si el usuario pide explicitamente que quiere ver algo, por ejemplo una grafica de drawdown, una tabla comparativa o una grafica normalizada, el primer agente debe intentar generarlo aunque el nivel general de la consulta parezca simple.

Punto importante sobre el primer agente:
El agente de generacion de codigo no debe limitarse a sacar cualquier numero. Su funcion es producir el material minimo necesario para que:
- el segundo agente pueda hacer un analisis completo;
- el usuario pueda ver los datos relevantes directamente;
- la respuesta final tenga trazabilidad.

Ejemplos:
- Si la consulta es "comparame estos dos indices", lo normal es generar una comparativa con rentabilidad, volatilidad, drawdown, correlacion y, si procede, una serie temporal comparada.
- Si la consulta es "comparame estos dos indices dandome una grafica de evolucion normalizada y otra grafica de drawdown", entonces el sistema debe incluir esas graficas solicitadas dentro del analisis, ademas de las metricas que ayuden a interpretarlas.
- Si la consulta pide "cual ha sido mas estable", no basta con decir cual subio mas: hay que calcular volatilidad, drawdown o variabilidad.
- Si la consulta pide "resumen sencillo para un usuario no tecnico", el codigo debe seguir calculando bien, pero la interpretacion debe simplificar el lenguaje.

Lo que quiero que hagas:

1. Revisa el estado actual del repositorio.
   - Lee `README.md`.
   - Lee `docs/plan_pruebas_queries_llm.md`.
   - Lee los capitulos de memoria que afecten a metodologia y resultados:
     - `docs/memoria_latex/chapters/04_metodologia.tex`
     - `docs/memoria_latex/chapters/08_resultados_evaluacion.tex`
   - Si necesitas entender prompts o arquitectura, revisa:
     - `src/llm/prompts.py`
     - `src/graph/nodes.py`
     - `scripts/evaluate_llm_profiles.py`

2. Crea o actualiza documentacion Markdown.
   Crea un documento nuevo, por ejemplo:
   - `docs/evaluacion_cualitativa_llm.md`

   Ese documento debe explicar:
   - por que la evaluacion no puede ser solo numerica;
   - como se hara la revision manual;
   - que criterios definen una buena generacion de analisis;
   - por que se distinguen tres niveles de analisis: A simple, B mejorado y C profesional/enriquecido;
   - que debe mostrar cada nivel en texto, datos, tablas y graficas;
   - como se adapta el sistema cuando el usuario pide explicitamente que quiere ver;
   - como se separa la calidad del primer agente y la calidad del segundo agente;
   - como se compararan modelos sin afirmar una objetividad falsa;
   - como se registraran observaciones, fallos y diferencias entre modelos.

   Incluye una seccion de apoyo bibliografico o referencias. Usa fuentes fiables para justificar las decisiones:
   - SEC / Investor.gov sobre presentacion de rendimiento historico, metodologia clara, ausencia de garantias y no usar rendimiento pasado como prediccion.
   - Investor.gov sobre relacion riesgo-retorno.
   - CFA Institute sobre retorno, volatilidad, correlacion y metricas historicas de riesgo.
   - CFA Institute sobre drawdown como metrica historica intuitiva basada en datos observados.
   - Guias de visualizacion de datos para justificar graficos de linea, no abusar de demasiadas series, evitar ejes dobles y usar normalizacion cuando se comparan activos con escalas distintas.

3. Define una rubrica cualitativa defendible.
   No la plantees como una metrica matematica absoluta. Puede usar niveles como:
   - Excelente
   - Correcto
   - Parcial
   - Deficiente

   La rubrica debe cubrir, como minimo:
   - comprension de la consulta;
   - seleccion de metricas/datos por el primer agente;
   - adecuacion del codigo generado;
   - adecuacion de tablas/graficas si se piden;
   - exactitud respecto a los datos ejecutados;
   - claridad del analisis final;
   - utilidad para el usuario;
   - reconocimiento de limitaciones;
   - ausencia de recomendaciones de inversion;
   - trazabilidad entre consulta, codigo, resultados e interpretacion.

   Puedes incluir una plantilla de revision manual en tabla Markdown para que yo pueda rellenarla tras cada ejecucion.

4. Diseña baterias de queries que permitan evaluar dificultad y tambien nivel de analisis.

   Quiero que la bateria incluya explicitamente ejemplos de los tres niveles A/B/C:

   - 6 queries de Nivel A, similares a las primeras queries simples del MVP.
     - Deben cubrir casos normales de uso.
     - Sirven para comprobar si el flujo responde bien en peticiones habituales sin pedir formato especial.
     - Deben generar una salida simple: texto breve + metricas basicas, sin obligar a graficas.
     - Ejemplos de familias: crecimiento de un activo, comparacion simple, resumen de volumen, rentabilidad, volatilidad, tendencia basica.

   - 3 queries de Nivel B.
     - Deben pedir un analisis mas completo o una comparativa mas clara.
     - Deben exigir texto + tabla de metricas + una grafica principal.
     - Ejemplos: comparacion entre dos activos con evolucion normalizada, analisis de retorno/riesgo, resumen completo de un activo con grafica de precio.

   - 3 queries de Nivel C.
     - Deben pedir expresamente un analisis profesional, detallado, avanzado o con varias salidas concretas.
     - Deben exigir texto + tablas + varias visualizaciones o elementos especificos.
     - Pueden incluir peticiones con varias condiciones, graficas concretas, comparaciones entre activos, restricciones de formato, explicacion para usuario no tecnico, o peticiones donde haya que elegir metricas adecuadas.

   Ademas de esta bateria A/B/C, si consideras util mantener una bateria de estres mas amplia, puedes proponer queries adicionales mas exigentes para apretar a los LLMs. En cualquier caso:
   - deben seguir siendo razonables y evaluables con datos historicos disponibles;
   - tienen que poder mostrar debilidades si el modelo no comprende bien la consulta;
   - no deben depender de noticias externas ni datos no presentes en los CSV.

   Para cada query, indica:
   - ID sugerido;
   - texto de la consulta;
   - datos/tickers esperados;
   - nivel esperado: A, B o C;
   - que deberia generar el primer agente;
   - que deberia explicar el segundo agente;
   - que fallo esperas detectar si el LLM no trabaja bien.

5. Actualiza la memoria en LaTeX.
   Modifica, con cuidado y estilo academico, los capitulos:
   - `docs/memoria_latex/chapters/04_metodologia.tex`
   - `docs/memoria_latex/chapters/08_resultados_evaluacion.tex`

   Objetivo de la actualizacion:
   - dejar claro que la evaluacion incluye una revision cualitativa/manual;
   - explicar que la calidad se valora segun completitud del analisis, no solo exito tecnico;
   - definir que se entiende por buen analisis;
   - introducir los tres niveles de analisis:
     - Nivel A: simple por defecto para queries basicas sin requisitos concretos;
     - Nivel B: mejorado para analisis mas completos con tabla y grafica principal;
     - Nivel C: profesional/enriquecido para peticiones avanzadas o con visualizaciones concretas;
   - explicar la diferencia entre el primer agente generador de codigo/datos y el segundo agente interpretador;
   - justificar las queries faciles y las queries de estres;
   - reconocer la subjetividad controlada de la evaluacion.

   Ademas, incorpora citas donde corresponda para justificar por que se seleccionan estos analisis como base. No hace falta saturar el texto con citas, pero si deben aparecer donde se definan los criterios:
   - al hablar de rendimiento historico y no prediccion, citar SEC / Investor.gov;
   - al hablar de riesgo-retorno, citar Investor.gov o CFA Institute;
   - al hablar de volatilidad, correlacion y retorno como metricas basicas, citar CFA Institute;
   - al hablar de drawdown como metrica interpretable de caidas historicas, citar CFA Institute;
   - al hablar de graficos de linea, normalizacion, evitar exceso de series y evitar ejes dobles, citar una guia reconocida de visualizacion de datos.

   Si el fichero LaTeX de bibliografia existe, añade entradas BibTeX. Si no existe o no esta claro, deja las referencias en una seccion o comentario metodologico coherente con la estructura actual de la memoria, sin romper la compilacion.

   Importante:
   - No exageres resultados.
   - No afirmes que un modelo es objetivamente mejor solo por impresiones manuales.
   - Usa expresiones como "revision humana", "criterios cualitativos", "comparacion exploratoria", "evidencia observada" y "limitacion metodologica".
   - Mantén coherencia con lo que ya esta escrito en la memoria.

6. Si hace falta, ajusta los prompts del sistema.
   Revisa `src/llm/prompts.py`.
   Solo si ves que encaja con la arquitectura actual, refuerza los prompts para que:
   - el agente de codigo genere metricas suficientes para la consulta;
   - respete graficas/tablas solicitadas;
   - produzca salidas estructuradas que el segundo agente pueda interpretar;
   - el segundo agente distinga datos, interpretacion y limitaciones;
   - se eviten recomendaciones de inversion.

   No hagas refactors grandes ni cambies la arquitectura si no es necesario.

7. Verificacion.
   Ejecuta las pruebas disponibles si el entorno lo permite:
   - `python -m unittest discover -s tests`

   Si no puedes ejecutar algo por falta de claves LLM, cuota o entorno, dejalo explicado claramente.

Resultado esperado:
- Un nuevo documento Markdown con la metodologia de evaluacion cualitativa.
- La memoria LaTeX actualizada en metodologia y resultados.
- Si procede, prompts reforzados de forma minima.
- Una lista clara de queries faciles y queries de estres.
- Una plantilla para revision manual.
- Un resumen final de cambios y de cualquier prueba ejecutada.

Trabaja de forma conservadora:
- Respeta la estructura actual del proyecto.
- No borres resultados existentes.
- No descargues datos nuevos.
- No inventes resultados que no hayan sido ejecutados.
- Diferencia claramente entre resultados observados y criterios propuestos para futuras revisiones.
```
