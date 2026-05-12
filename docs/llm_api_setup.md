# Configuracion de APIs LLM

El proyecto puede funcionar en dos modos:

- Sin API externa: usa las plantillas deterministas del MVP.
- Con API LLM: usa un proveedor compatible con OpenAI para fases concretas del workflow.

## Modo sin API

Es el modo estable para desarrollo, tests y ejecuciones reproducibles.

```env
LLM_ENABLED=false
```

Con esta configuracion, las claves pueden estar guardadas en `.env`, pero no se llama a ningun proveedor externo.

## Modo con Groq

Groq queda recomendado como primera prueba porque encaja directamente con el cliente OpenAI-compatible del proyecto.

```env
LLM_ENABLED=true
LLM_PROFILE=groq
LLM_USE_FOR_PLANNING=false
LLM_USE_FOR_CODEGEN=false
LLM_USE_FOR_INTERPRETATION=true
```

El proyecto lee:

```env
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
```

## Modo con Gemini

Gemini queda preparado como segunda API para comparar calidad de respuesta.

```env
LLM_ENABLED=true
LLM_PROFILE=gemini
LLM_USE_FOR_PLANNING=false
LLM_USE_FOR_CODEGEN=false
LLM_USE_FOR_INTERPRETATION=true
```

El proyecto lee:

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

## Modo con API de la universidad

El perfil `university` queda preparado para un proveedor compatible con OpenAI.
Cuando se reciba la clave, solo hay que rellenar:

```env
LLM_ENABLED=true
LLM_PROFILE=university
UNIVERSITY_BASE_URL=https://endpoint_del_modelo/openai/v1
UNIVERSITY_API_KEY=...
UNIVERSITY_MODEL=...
```

## Activacion por fases

La integracion esta pensada para ser gradual:

- `LLM_USE_FOR_INTERPRETATION=true`: el LLM solo redacta la respuesta final usando los resultados ya calculados.
- `LLM_USE_FOR_PLANNING=true`: el LLM puede ajustar el plan analitico, pero no puede cambiar la intent.
- `LLM_USE_FOR_CODEGEN=true`: el LLM puede generar codigo Python. Conviene dejarlo para el final porque es la fase con mas riesgo.

Recomendacion actual del TFM: empezar solo por interpretacion.

## Evaluacion automatizada

El script `scripts/evaluate_llm_profiles.py` permite ejecutar una misma bateria
de ejemplos contra varios perfiles y guardar un JSON por ejecucion en
`results/evaluations/`.

Ejemplo:

```bash
python scripts/evaluate_llm_profiles.py --profiles deterministic groq gemini --examples all
```

Para incluir el modelo universitario cuando este disponible:

```bash
python scripts/evaluate_llm_profiles.py --profiles deterministic groq gemini university --examples all
```
