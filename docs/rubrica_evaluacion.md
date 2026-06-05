# Rúbrica de evaluación subjetiva del sistema

## Métrica 1: comprensión de la consulta

Evalúa si el sistema entiende correctamente la intención del usuario. Debe revisar si el plan analítico identifica de forma adecuada:

- activos o tickers solicitados;
- periodo, fechas o intervalo temporal;
- tipo de análisis requerido;
- nivel A/B/C;
- restricciones explícitas;
- formato solicitado por el usuario.

Esta métrica se observa principalmente en `analysis_plan`, aunque también puede contrastarse con el código generado y la respuesta final.

Puntuación:

```text
0 = no entiende la consulta o interpreta mal elementos esenciales.
1 = entiende la idea general, pero omite o distorsiona algún elemento importante.
2 = entiende correctamente la consulta, sus activos, periodo, nivel y restricciones.
```

Ejemplo:

Si el usuario pide comparar QQQ y SPY en 2024 y el sistema analiza solo QQQ, la puntuación sería 0.

Si analiza QQQ y SPY, pero no respeta que el periodo sea 2024, la puntuación podría ser 1.

Si identifica ambos activos, el periodo correcto y el tipo de comparación, la puntuación sería 2.

## Métrica 2: pertinencia de métricas

Evalúa si las métricas seleccionadas son adecuadas para responder a la consulta. No todas las consultas requieren las mismas métricas. La selección debe depender del objetivo:

- crecimiento: retorno total, precio inicial/final, CAGR;
- riesgo: volatilidad, drawdown, peor día, desviación estándar;
- comparación: rentabilidad por activo, volatilidad relativa, correlación;
- análisis técnico: medias móviles, tendencia, cruces, soporte contextual;
- evolución visual: serie normalizada, datos de gráfica, tabla temporal;
- ranking: mejor/peor activo, mejor/peor mes, ordenación por métricas.

Puntuación:

```text
0 = las métricas no responden a la consulta o son claramente incorrectas.
1 = incluye algunas métricas útiles, pero faltan métricas importantes o hay métricas innecesarias.
2 = selecciona métricas coherentes, suficientes y proporcionadas al nivel A/B/C.
```

Ejemplo:

Para una consulta de crecimiento simple de Nvidia, `retorno_total` y `cagr` son métricas pertinentes.

Para una consulta de riesgo, solo calcular precio final sería insuficiente.

## Métrica 3: calidad de ejecución analítica

Evalúa si el código generado ejecuta correctamente el análisis propuesto. Esta métrica no se centra en si el código es bonito, sino en si calcula bien y produce una salida útil.

Debe revisar:

- si usa los CSV correctos;
- si carga correctamente los datos;
- si usa columnas adecuadas, como `Close`, `High`, `Low` o `Volume`;
- si calcula las métricas necesarias;
- si evita errores evidentes de fechas, NaN o división por cero;
- si genera JSON estructurado;
- si incluye tablas o series visuales cuando proceden;
- si las limitaciones quedan reflejadas.

Se observa principalmente en:

```text
generated_code
execution_output
stdout_path
stderr_path
execution_returncode
```

Puntuación:

```text
0 = el código falla, usa datos incorrectos o produce resultados no válidos.
1 = el código ejecuta, pero la salida es incompleta, frágil o contiene problemas relevantes.
2 = el código ejecuta correctamente, calcula lo pedido y produce una salida estructurada y trazable.
```

Ejemplo:

Si el script calcula el retorno usando la columna `Close` correcta y devuelve un JSON con métricas y limitaciones, la puntuación puede ser 2.

Si ejecuta pero omite una métrica pedida, puede ser 1.

Si falla por error de ejecución, puede ser 0.

## Métrica 4: fidelidad de la interpretación

Evalúa si la respuesta final interpreta fielmente los resultados ejecutados.

El Agente 3 debe explicar los resultados, no inventarlos.

Debe comprobarse si:

- usa solo `execution_output` y `analysis_plan`;
- no modifica cifras;
- no introduce datos externos;
- no inventa precios, noticias o causas;
- no recalcula métricas de forma contradictoria;
- no oculta limitaciones;
- mantiene coherencia con el plan analítico.

Puntuación:

```text
0 = la interpretación inventa datos, cambia cifras o contradice la ejecución.
1 = interpreta en general bien, pero introduce alguna imprecisión o explicación no suficientemente apoyada.
2 = interpreta fielmente los resultados ejecutados y respeta las cifras y limitaciones.
```

Ejemplo:

Si `execution_output` dice que el retorno total es 12.7333 y la respuesta final dice 12.7333 o 1273.33%, es fiel.

Si la respuesta dice 900% sin que aparezca en la ejecución, no es fiel.

## Métrica 5: claridad, utilidad y prudencia

Evalúa si la respuesta final es comprensible y útil para el usuario, manteniendo prudencia financiera.

Esta métrica combina calidad comunicativa y restricciones éticas del MVP.

Debe revisar:

- si la respuesta está ordenada;
- si usa lenguaje comprensible;
- si explica qué significan las métricas;
- si separa resultados históricos de interpretación;
- si reconoce limitaciones;
- si evita predicciones;
- si evita recomendaciones de compra o venta;
- si evita lenguaje persuasivo o de asesoramiento.

Puntuación:

```text
0 = la respuesta es confusa, poco útil o contiene recomendaciones/predicciones financieras.
1 = la respuesta es comprensible, pero poco explicativa, desordenada o con prudencia insuficiente.
2 = la respuesta es clara, útil, prudente y adecuada para interpretar resultados históricos.
```

Ejemplo:

Una respuesta que dice "compra Nvidia porque subirá" debe recibir 0.

Una respuesta que solo repite dos números sin explicar nada podría recibir 1.

Una respuesta breve que explica retorno, CAGR y limitaciones sin recomendar inversión podría recibir 2.

## Plantilla de evaluación manual

La siguiente tabla puede usarse para corregir manualmente cada caso:

```text
Caso:
Consulta:
Nivel esperado:
Status final:

Completitud del flujo:
- status = completed: sí/no
- analysis_plan existe: sí/no
- generated_code existe: sí/no
- execution_output existe: sí/no
- final_answer existe: sí/no

Métricas subjetivas:
1. Comprensión de la consulta: 0 / 1 / 2
2. Pertinencia de métricas: 0 / 1 / 2
3. Calidad de ejecución analítica: 0 / 1 / 2
4. Fidelidad de la interpretación: 0 / 1 / 2
5. Claridad, utilidad y prudencia: 0 / 1 / 2

Puntuación total subjetiva: __ / 10

Comentario humano:
```