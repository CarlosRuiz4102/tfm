# Rúbrica de evaluación de respuestas finales

## Finalidad

Esta rúbrica sirve para evaluar la calidad de la respuesta final que recibe el
usuario cuando un caso completa el flujo de extremo a extremo.

No pretende medir la calidad interna de artefactos intermedios del sistema ni
actuar como una auditoría experta del contenido financiero. Su objetivo es
valorar si la salida final resulta adecuada para la consulta planteada, si es
comprensible para un lector no especializado y si mantiene un tratamiento
prudente de lo que puede inferirse a partir de datos históricos.

## Estructura general de la evaluación

La evaluación se divide en dos partes:

1. Casos no completados.
2. Casos completados.

### 1. Casos no completados

Los casos que no llegan a producir una respuesta final utilizable no se puntúan
con esta rúbrica. Se analizan por separado según el tipo de fallo observado.

Como clasificación general de partida, los fallos pueden agruparse en:

- fallo en resolución o descarga de datos;
- fallo en generación o validación del análisis;
- fallo de ejecución;
- fallo en la obtención de una salida final utilizable.

Esta clasificación puede refinarse después al revisar los resultados reales de
la batería, pero ofrece una base suficiente para ordenar los casos no
completados sin forzar una taxonomía artificial desde el principio.

### 2. Casos completados

Solo los casos que llegan a una respuesta final se evalúan con la rúbrica.

El hecho de completar el flujo no basta por sí solo para considerar que el
resultado es exitoso. Para que un caso se considere satisfactorio dentro del
trabajo, la respuesta final debe alcanzar una calidad mínima en esta evaluación
manual.

## Escala de puntuación

Cada criterio se valora con una escala discreta de `0`, `1` o `2`.

- `0`: incumplimiento claro del criterio.
- `1`: cumplimiento parcial o insuficiente.
- `2`: cumplimiento adecuado del criterio.

Se utiliza esta escala por tres motivos:

- facilita una aplicación consistente de la evaluación;
- reduce la ambigüedad entre respuestas claramente malas, intermedias y
  adecuadas;
- evita una falsa precisión que no estaría justificada en una revisión humana
  de este tipo.

Los cinco criterios pesan lo mismo. La puntuación máxima total es de `10`
puntos.

## Criterios de evaluación

## 1. Adecuación a la consulta

Evalúa si la respuesta final responde realmente a lo que pidió el usuario.

Aquí se valora:

- si responde al objetivo principal de la consulta;
- si se ajusta a los activos, periodo o comparación solicitados;
- si respeta restricciones explícitas de formato, tono o estructura cuando las
  haya;
- si no se desvía hacia cuestiones que el usuario no pidió.

Puntuación:

```text
0 = la respuesta no responde a la consulta o falla en elementos esenciales.
1 = responde de forma parcial, pero omite, altera o no respeta alguna parte importante de lo pedido.
2 = responde de forma adecuada a la consulta y respeta sus elementos principales y, cuando procede, el formato solicitado.
```

## 2. Cobertura analítica

Evalúa si la respuesta incluye los elementos analíticos que la consulta exigía.

No se trata de premiar que la respuesta diga muchas cosas, sino de comprobar si
cubre lo necesario para contestar bien al usuario.

Aquí se valora:

- si aparecen las métricas o comparaciones que la consulta requería;
- si están presentes los bloques o componentes esenciales del análisis;
- si no faltan partes importantes para sostener la respuesta.

Puntuación:

```text
0 = faltan elementos analíticos esenciales y la respuesta queda incompleta.
1 = cubre una parte relevante de la consulta, pero omite algún elemento importante.
2 = cubre de forma suficiente los elementos principales que pedía la consulta.
```

## 3. Coherencia y solidez aparente

Evalúa si la respuesta mantiene coherencia interna y si el resultado parece
estar bien construido desde el punto de vista del lector.

Esta métrica no exige una auditoría financiera experta completa. Lo que se
valora es si la respuesta presenta cifras, relaciones y conclusiones de forma
consistente y sin contradicciones visibles.

Aquí se valora:

- si las cifras y porcentajes están bien integrados en el texto;
- si no hay contradicciones entre distintas partes de la respuesta;
- si las conclusiones parecen acordes con los datos presentados;
- si no hay afirmaciones que resulten arbitrarias o internamente incoherentes.

Puntuación:

```text
0 = la respuesta presenta contradicciones, cifras mal integradas o conclusiones claramente incoherentes.
1 = la respuesta es en general coherente, pero contiene alguna imprecisión, debilidad o enlace poco sólido entre datos y conclusión.
2 = la respuesta es coherente, consistente y presenta un resultado aparentemente sólido.
```

## 4. Claridad y utilidad comunicativa

Evalúa si la respuesta puede entenderse con facilidad y si resulta útil para un
lector amplio, no necesariamente especializado.

Aquí se valora:

- si la redacción es clara;
- si la respuesta está bien organizada;
- si transmite una idea útil al usuario;
- si evita una formulación excesivamente críptica, desordenada o poco legible.

Puntuación:

```text
0 = la respuesta es confusa, poco clara o difícilmente útil para el lector.
1 = la respuesta se entiende, pero presenta carencias de orden, claridad o utilidad práctica.
2 = la respuesta es clara, comprensible y útil para un lector no especializado.
```

## 5. Prudencia y tratamiento de limitaciones

Evalúa si la respuesta mantiene un tono prudente y si trata correctamente los
límites del análisis histórico.

Aquí se valora:

- si evita predicciones no justificadas;
- si evita recomendaciones de compra o venta;
- si no presenta el resultado como asesoramiento financiero;
- si reconoce limitaciones cuando la consulta o el contenido lo requieren.

Puntuación:

```text
0 = la respuesta incurre en recomendaciones, predicciones o afirmaciones impropias del alcance del sistema.
1 = la respuesta mantiene cierta prudencia, pero trata las limitaciones de forma insuficiente o poco clara.
2 = la respuesta mantiene prudencia, respeta el alcance histórico del análisis y trata adecuadamente sus limitaciones.
```

## Interpretación de la puntuación total

La puntuación total se interpreta del siguiente modo:

- `8 a 10 puntos`: resultado satisfactorio. La respuesta final alcanza una
  calidad suficientemente alta como para considerarla un resultado exitoso
  dentro del trabajo.
- `6 a 7 puntos`: caso completado con calidad insuficiente. La respuesta puede
  ser útil, pero todavía requiere mejoras para alcanzar un nivel suficientemente
  sólido o profesional.
- `0 a 5 puntos`: caso completado con calidad baja. La respuesta no ofrece un
  nivel adecuado para considerarse satisfactoria.

Por tanto, un caso exitoso en sentido metodológico no es solo aquel que
consigue producir una respuesta final, sino aquel que además alcanza al menos
`8/10` en esta rúbrica.

## Plantilla de evaluación manual

```text
Caso:
Consulta:
Estado final:

1. ¿El caso completó el flujo?
- Sí / No

2. Si no completó:
- Familia de fallo:
- Comentario breve:

3. Si completó, aplicar la rúbrica:
- Adecuación a la consulta: 0 / 1 / 2
- Cobertura analítica: 0 / 1 / 2
- Coherencia y solidez aparente: 0 / 1 / 2
- Claridad y utilidad comunicativa: 0 / 1 / 2
- Prudencia y tratamiento de limitaciones: 0 / 1 / 2

Puntuación total: __ / 10

Clasificación final:
- Satisfactorio (8-10)
- Completado con calidad insuficiente (6-7)
- Completado con calidad baja (0-5)

Comentario humano:
```
