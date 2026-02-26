# Diseño e implementación de un agente conversacional para análisis financiero automatizado mediante NL→SQL, detección de patrones y generación de insights

## Descripción general

Objetivo TFM: diseñar e implementar un **agente conversacional inteligente** que permita a analista financiero interactuar con base de datos mediante lenguaje natural. Este será capaz no solo de traducir preguntas a SQL, sino también de interpretar resultados, detectar patrones y generar insights explicativos.

El usuario podrá realizar preguntas como:

> "¿Cómo evolucionaron las ventas este trimestre respecto al anterior?"

y el sistema será capaz de:

- traducir la consulta a SQL
- ejecutar la consulta en la base de datos
- analizar los resultados
- generar visualizaciones automáticas
- explicar los hallazgos en lenguaje natural


## Objetivos específicos

✅ Traducción robusta NL → SQL  
✅ Razonamiento sobre datos estructurados  
✅ Generación automática de insights financieros  
✅ Explicabilidad de respuestas  
✅ Arquitectura basada en agentes  
✅ Generación automática de visualizaciones  
✅ Evaluación de calidad de respuestas  


## Arquitectura 

&nbsp;    Usuario

&nbsp;       ↓

&nbsp;  Interfaz conversacional

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


## Componentes del sistema

### Módulo NL → SQL

Responsabilidades:

- traducir lenguaje natural a consultas SQL
- validar consultas
- evitar errores sintácticos
- manejar ambigüedad semántica

Posibles tecnologías:
- OpenAI/open-source
- LlamaIndex

### Ejecución de Base de Datos

- SQLite / PostgreSQL
- datasets financieros reales o sintéticos
- conexión segura desde el agente
- Kaggle (ventas, mercados, facturación)


##  Roadmap inicial de desarrollo

### Fase 1 — Base
- [ ] Dataset financiero
- [ ] Base de datos SQL
- [ ] Pipeline NL → SQL básico

### Fase 2 — Agente
- [ ] Orquestador
- [ ] Tools (query, analysis, plot)

### Fase 3 — Inteligencia analítica
- [ ] Detección de patrones
- [ ] Generador de insights

### Fase 4 — Visualización
- [ ] Generación automática de gráficos

### Fase 5 — Evaluación
- [ ] Métricas
- [ ] Experimentos


## Duda conceptual clave

### ¿Chatbot o modelo generativo específico?

El sistema será un chatbot ya que si no tardariamos mucho en entrenarlo. Vamos a realizar una busqueda de que LLMs podemos utilizar de hugging face que sean en un ambito de financias.



consensus buscar papers
poetry lo intentamos meter