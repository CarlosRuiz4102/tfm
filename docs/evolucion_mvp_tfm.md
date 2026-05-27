# Evolución Incremental del MVP

Este documento resume cómo ha evolucionado el MVP del TFM desde las primeras pruebas hasta el estado actual. La idea es dejar constancia del proceso real de desarrollo: primero se buscó que el flujo funcionara, después se amplió su cobertura funcional y finalmente se empezó a evaluar portabilidad entre modelos y consultas más complejas.

## Punto De Partida

El primer objetivo no era construir desde el inicio un sistema amplio, sino validar que el flujo completo podía funcionar de extremo a extremo:

```text
consulta -> interpretación LLM -> generación de código -> ejecución -> respuesta
```

En esta fase inicial se trabajó con un LLM de OpenAI o compatible con OpenAI para reducir incertidumbre y centrarse en el diseño del flujo. El objetivo era comprobar que el modelo podía interpretar una consulta financiera sencilla, producir una salida útil y permitir una primera automatización trazable.

## MVP 1: Dos Intencionalidades

El primer MVP se centró en dos intencionalidades básicas:

- `growth`: analizar cuánto había crecido un activo.
- `compare`: comparar el comportamiento histórico de dos activos.

Estas dos intenciones fueron elegidas porque cubrían dos formas muy habituales de consulta financiera:

- una pregunta individual sobre un activo;
- una comparación relativa entre activos.

Con este MVP inicial se validaron las piezas mínimas:

- entrada estructurada con query, ticker, fechas o periodo y CSV;
- llamada al LLM;
- interpretación de la intención;
- cálculo de métricas históricas;
- respuesta final comprensible;
- revisión manual de que los resultados tenían sentido.

La importancia de esta fase fue comprobar que el proyecto tenía una base funcional. No se buscaba todavía cubrir muchos casos, sino demostrar que el flujo podía completarse.

## MVP 2: Seis Intencionalidades

Una vez comprobado que el primer flujo funcionaba, el segundo MVP amplió la cobertura desde dos a seis intencionalidades analíticas:

- crecimiento de precio;
- comparación de activos;
- visión descriptiva de un activo;
- análisis de retornos;
- análisis de riesgo histórico;
- análisis técnico básico.

Esta ampliación permitió comprobar si el sistema podía manejar consultas con necesidades distintas:

- cálculos simples de crecimiento;
- comparaciones entre varios tickers;
- métricas descriptivas;
- retornos y volatilidad;
- riesgo y drawdown;
- indicadores técnicos básicos.

El segundo MVP sirvió para consolidar la estructura general del proyecto y para detectar que el sistema necesitaba contratos más claros entre fases: qué recibe el LLM, qué debe devolver, qué código se puede ejecutar y cómo se valida la salida.

## Cambio Arquitectónico Posterior

Tras las primeras iteraciones, se decidió simplificar la arquitectura y centrar el TFM en un flujo LLM + generación de código controlada.

El enfoque actual ya no se basa en separar familias de agentes, sino en una secuencia más clara:

```text
entrada estructurada
-> validación mínima
-> análisis con LLM
-> generación de código con LLM
-> control de seguridad
-> ejecución controlada
-> interpretación final con LLM
```

Este cambio hizo más fácil explicar el sistema, depurarlo y justificarlo académicamente. También permitió separar mejor las responsabilidades:

- el LLM interpreta;
- el LLM genera código;
- el sistema valida;
- el sistema ejecuta;
- el LLM explica resultados ya calculados.

## MVP Actual: Flujo LLM Con Codegen Controlado

El MVP actual incorpora:

- validación mínima de entradas;
- prompts diferenciados para análisis, generación de código, reparación e interpretación;
- validación de seguridad mediante AST;
- ejecución del script en proceso controlado;
- guardado de artefactos en `results/code` y `results/logs`;
- reintentos ante respuestas LLM no parseables;
- reparación del código generado si falla seguridad o ejecución;
- helpers de carga de datos para CSV de yfinance;
- evaluación con varios perfiles LLM.

Esta versión ya no pretende ser solo una prueba de concepto pequeña, sino una base experimental para comparar modelos y estudiar la robustez del flujo.

## Ampliación A Más LLMs

Después de validar el flujo con el modelo inicial, se preparó el sistema para trabajar con más proveedores compatibles con OpenAI.

Los perfiles actuales son:

| Perfil técnico | Modelo / proveedor | Estado |
|---|---|---|
| `university` | `openai/gpt-oss-20b` servido mediante vLLM universitario | Modelo abierto de la familia gpt-oss, usado en la depuración principal por su capacidad de razonamiento, seguimiento de instrucciones y generación de código Python. |
| `groq` | `llama-3.3-70b-versatile` en Groq | Modelo Llama 3.3 70B Instruct, validado con la batería compleja por su razonamiento general y baja latencia. |
| `gemini` | `gemini-2.5-flash` en Gemini | Modelo Flash de Gemini 2.5, validado en pruebas puntuales por su rapidez y razonamiento; limitado por cuota. |

Esta ampliación es importante porque el TFM no depende conceptualmente de un único proveedor. El mismo flujo puede ejecutarse con distintos modelos, manteniendo la misma entrada, los mismos contratos y la misma capa de ejecución.

## Fase Actual: Queries Más Complejas

La fase actual consiste en aumentar la dificultad de las consultas sin descargar datos nuevos.

La idea no es ampliar el dataset, sino hacer que los mensajes enviados al LLM sean más exigentes:

- pedir varias métricas en una misma consulta;
- combinar rentabilidad, volatilidad, drawdown y rankings;
- exigir respuestas estructuradas;
- trabajar con datos diarios e intradiarios;
- comprobar si el modelo mantiene el formato JSON;
- observar si el código generado sigue siendo ejecutable.

Esta fase debe tratarse como periodo de pruebas y resultados. Todavía requiere refinamiento, repetición de experimentos y una presentación más sistemática en la memoria.

## Lectura Para La Memoria

Una posible redacción breve para la memoria sería:

> El desarrollo del MVP siguió una estrategia incremental. En primer lugar se implementó un flujo mínimo con un LLM de OpenAI o compatible con OpenAI y dos intencionalidades básicas: crecimiento de un activo y comparación entre activos. Esta fase permitió validar que la cadena completa de consulta, interpretación, cálculo y respuesta podía funcionar. Posteriormente, el MVP se amplió a seis intencionalidades analíticas, incorporando visión descriptiva, retornos, riesgo histórico y análisis técnico básico. Una vez consolidada esta versión, el trabajo evolucionó hacia una arquitectura centrada en LLM y generación de código controlada, con validación de seguridad, ejecución aislada y trazabilidad de artefactos. Finalmente, se preparó la evaluación con varios modelos y se inició una fase de consultas más complejas sobre los mismos datos históricos.

## Resumen

La evolución del MVP puede entenderse así:

```text
MVP 1
2 intenciones: growth + compare
flujo mínimo funcionando

MVP 2
6 intenciones analíticas
mayor cobertura funcional

MVP actual
LLM + codegen controlado
seguridad, ejecución, trazabilidad y reparación

Fase experimental
varios LLMs + queries más complejas
periodo de pruebas para resultados
```
