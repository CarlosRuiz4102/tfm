# Control de tamano de salidas para interpretacion LLM

Durante la ejecucion de la muestra A/B/C con Groq se observo una limitacion practica: algunos scripts generados devolvian series completas dentro de `chart_data`. Aunque la ejecucion del codigo terminaba correctamente, la salida enviada al segundo agente era demasiado grande y podia superar el limite de tokens del proveedor.

## Problema observado

En queries de Nivel B y C, el primer agente puede generar datos de visualizacion con cientos o miles de puntos. Esto es util como artefacto de ejecucion, pero no siempre es necesario para que el segundo agente redacte el analisis final. El interpretador necesita entender la forma general de la serie, sus metricas principales y algunos puntos representativos, no recibir todos los valores historicos.

## Ajuste realizado

Se han aplicado dos medidas:

- En `src/llm/prompts.py` se indica al agente de codigo que, si genera `chart_data` o `visualization_data`, limite cada serie larga a un maximo de 120 puntos muestreados.
- En `src/graph/nodes.py` se compacta la salida antes de enviarla al segundo agente. La salida completa sigue guardada en los artefactos de ejecucion, pero la interpretacion recibe una version resumida de listas y textos largos.

## Criterio metodologico

Este ajuste mantiene la trazabilidad sin penalizar la interpretacion:

- El usuario o revisor puede consultar la salida completa en los logs.
- El segundo agente recibe suficiente informacion para redactar una explicacion clara.
- Se reduce el riesgo de errores por limites de tokens.
- El Nivel B y C siguen pudiendo pedir graficas, pero la comunicacion entre agentes usa datos visuales compactos.

Este punto tambien refuerza la separacion entre primer agente y segundo agente: el primero calcula y estructura; el segundo interpreta una version adecuada para lenguaje natural.

