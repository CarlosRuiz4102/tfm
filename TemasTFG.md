***Diseño e implementación de un agente conversacional para análisis financiero automatizado mediante NL→SQL, detección de patrones y generación de insight***



Construir un agente conversacional que permita a un analista financiero interactuar con una base de datos usando lenguaje natural. El agente no solo traduce preguntas a SQL, sino que también:



* interpreta resultados
* detecta patrones en los datos
* genera insights explicativos
* crea visualizaciones
* responde con lenguaje natural



Es básicamente un copiloto de análisis financiero.





*El tfm intentará tratar de:*

✅ NL → SQL robusto

✅ Razonamiento sobre datos

✅ Generación automática de insights

✅ Explicabilidad

✅ Arquitectura de agentes

✅ Evaluación de calidad de respuestas

✅ Integración con visual analytics





El LLM es el “cerebro”, pero el análisis real lo hacen herramientas externas:



Usuario → Interfaz conversacional

&nbsp;       ↓

&nbsp;  Agente LLM orquestador

&nbsp;       ↓

&nbsp;┌─────────────────────────┐

&nbsp;│ 1. NL → SQL             │

&nbsp;│ 2. Ejecución BD         │

&nbsp;│ 3. Análisis estadístico │

&nbsp;│ 4. Generación insights  │

&nbsp;│ 5. Visualización        │

&nbsp;└─────────────────────────┘

&nbsp;       ↓

&nbsp;Respuesta explicada al usuario



Posibles datasets:

·Kaggle (ventas, mercados, facturación)



LLM:

·OpenAI/open-source

·LlamaIndex



