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

## Bateria propuesta por niveles

### Nivel A: seis queries simples

| ID | Consulta | Datos esperados | Primer agente debe generar | Segundo agente debe explicar | Fallo que detecta |
|---|---|---|---|---|---|
| `level_a_nvda_growth` | Cuanto ha crecido Nvidia en los ultimos 5 anos | NVDA, periodo 5y | Precio inicial/final, crecimiento absoluto y porcentual | Lectura breve del crecimiento historico | Responder sin periodo, sin porcentaje o con recomendacion |
| `level_a_nvda_amd_compare` | Compara Nvidia y AMD en 2 anos | NVDA/AMD, periodo 2y | Rentabilidad total por activo y ranking simple | Cual subio mas y con que cautela | Comparar precios absolutos en vez de rentabilidad |
| `level_a_aapl_overview` | Dame una vision general de AAPL en 3 meses | AAPL, periodo 3mo | Precio inicial/final, maximo, minimo y volumen si existe | Tendencia general sin tecnicismos | Omitir rango o inventar noticias |
| `level_a_qqq_spy_returns` | Analiza los retornos de QQQ y SPY en 2024 | QQQ/SPY, 2024 | Retorno total y retorno medio diario | Diferencia de rendimiento historico | No comparar ambos activos |
| `level_a_qqq_spy_risk` | Analiza el riesgo historico de QQQ y SPY en 2024 | QQQ/SPY, 2024 | Volatilidad y peor/mejor dia | Que activo fue mas variable | Confundir riesgo con rentabilidad |
| `level_a_aapl_technical` | Haz un analisis tecnico basico de AAPL en 3 meses | AAPL, periodo 3mo | Media movil 20/50 si hay datos suficientes y ultimo cierre | Posicion del cierre frente a medias | Convertirlo en recomendacion de trading |

### Nivel B: tres queries mejoradas

| ID | Consulta | Datos esperados | Primer agente debe generar | Segundo agente debe explicar | Fallo que detecta |
|---|---|---|---|---|---|
| `level_b_nvda_complete` | Hazme un analisis mas completo de Nvidia en los ultimos 5 anos con tabla y una grafica de evolucion | NVDA, periodo 5y | Tabla de rentabilidad, extremos, volatilidad y datos para grafica de cierre | Crecimiento, variabilidad y limites | No incluir estructura para grafica |
| `level_b_qqq_spy_clear_compare` | Comparame QQQ y SPY en 2024 de forma clara, con tabla y grafica normalizada | QQQ/SPY, 2024 | Tabla comparativa y serie normalizada a 100 | Rentabilidad relativa y riesgo asumido | Usar precios absolutos no comparables |
| `level_b_aapl_risk_return` | Quiero entender retorno y riesgo de AAPL en 3 meses con una explicacion sencilla | AAPL, periodo 3mo | Retorno, volatilidad, drawdown y precio final | Explicacion sencilla de retorno frente a riesgo | Dar una explicacion demasiado tecnica o incompleta |

### Nivel C: tres queries profesionales

| ID | Consulta | Datos esperados | Primer agente debe generar | Segundo agente debe explicar | Fallo que detecta |
|---|---|---|---|---|---|
| `level_c_qqq_spy_professional` | Haz un analisis profesional de QQQ y SPY en 2024 con tabla, grafica normalizada, drawdown y conclusion para usuario no tecnico | QQQ/SPY, 2024 | Tabla, serie normalizada, drawdown, volatilidad y correlacion | Comparacion completa con lenguaje accesible | Ignorar una grafica o no explicar correlacion |
| `level_c_nvda_amd_multicriteria` | Compara NVDA y AMD en 2 anos con ranking por rentabilidad, riesgo y drawdown, y separa metricas, visualizaciones y limitaciones | NVDA/AMD, periodo 2y | Ranking multicriterio, tabla, datos de evolucion y drawdown | Por que un activo domina o no domina segun criterio | Reducir todo a rentabilidad |
| `level_c_sp500_report` | Prepara un informe detallado del S&P 500 desde 2020 con crecimiento, volatilidad, maximo drawdown, mejores y peores periodos, y resumen ejecutivo | ^GSPC, desde 2020 | Tabla de metricas, drawdown, extremos, retornos por periodo si procede | Resumen ejecutivo, lectura historica y limitaciones | Presentar el informe como prediccion |

## Registro de diferencias entre modelos

Para cada modelo se recomienda registrar:

- Si completo el flujo.
- Si el codigo fue valido a la primera o necesito reparacion.
- Si produjo las metricas esperadas para el nivel A/B/C.
- Si respeto tablas, graficas o salidas solicitadas.
- Si la interpretacion fue clara y prudente.
- Si aparecieron recomendaciones de inversion, predicciones o datos no observados.

La comparacion final debe formularse como evidencia observada, no como una clasificacion absoluta.

