# Configuración de APIs LLM

El proyecto se centra en el modo con API LLM: usa un proveedor compatible con OpenAI para planificar, generar código e interpretar el resultado del workflow. Si el LLM no está configurado, la ejecución informa un error explícito.

## Modelos Utilizados

| Perfil técnico | Proveedor / infraestructura | Modelo que debe citarse | Capacidad relevante para el TFM |
|---|---|---|---|
| `university` | Servidor vLLM universitario compatible con OpenAI | `openai/gpt-oss-20b` | Modelo abierto de la familia gpt-oss, usado por su capacidad de razonamiento, seguimiento de instrucciones y generación de código Python. |
| `groq` | Groq, API compatible con OpenAI | `llama-3.3-70b-versatile` | Modelo Llama 3.3 70B Instruct, útil para razonamiento general, cumplimiento de instrucciones y respuestas rápidas mediante la infraestructura de Groq. |
| `gemini` | Gemini API | `gemini-2.5-flash` | Modelo Flash de Gemini 2.5, orientado a rapidez, razonamiento y buen equilibrio entre latencia y calidad. |

En la memoria y la documentación se debe mencionar siempre el modelo, no solo el perfil técnico. Por ejemplo, se escribirá `openai/gpt-oss-20b` sobre vLLM universitario, Groq con `llama-3.3-70b-versatile` y Gemini con `gemini-2.5-flash`.

## Modo con Groq y llama-3.3-70b-versatile

Groq se utiliza con `llama-3.3-70b-versatile`, un modelo Llama 3.3 70B Instruct adecuado para razonamiento general, seguimiento de instrucciones y generación de código con baja latencia en la infraestructura de Groq.

```env
LLM_PROFILE=groq
```

El proyecto lee:

```env
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
```

## Modo con Gemini y gemini-2.5-flash

Gemini se utiliza con `gemini-2.5-flash`, un modelo Flash de Gemini 2.5 orientado a rapidez, razonamiento y equilibrio entre coste, latencia y calidad de respuesta.

```env
LLM_PROFILE=gemini
```

El proyecto lee:

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

## Modo con openai/gpt-oss-20b sobre vLLM universitario

El modelo `openai/gpt-oss-20b` se sirve desde el entorno universitario mediante un servidor vLLM compatible con OpenAI. En el código, este modelo se activa con el perfil técnico `university`. Es el modelo principal usado en la depuración del flujo por su capacidad de razonamiento, seguimiento de instrucciones y generación de código Python.

```env
LLM_PROFILE=university
UNIVERSITY_BASE_URL=https://w1.etsisi.upm.es/vllm/v1
UNIVERSITY_API_KEY=...
UNIVERSITY_MODEL=openai/gpt-oss-20b
```

## Evaluación automatizada

El script `scripts/evaluate_llm_profiles.py` permite ejecutar una misma batería de ejemplos contra varios perfiles y guardar un JSON por ejecución en `results/evaluations/`.

Ejemplo:

```bash
python scripts/evaluate_llm_profiles.py --profiles groq gemini --examples all
```

Ese comando evalúa Groq con `llama-3.3-70b-versatile` y Gemini con `gemini-2.5-flash`.

Para incluir `openai/gpt-oss-20b` sobre vLLM universitario junto con Groq con `llama-3.3-70b-versatile` y Gemini con `gemini-2.5-flash`:

```bash
python scripts/evaluate_llm_profiles.py --profiles groq gemini university --examples all
```

En la validación inicial de `openai/gpt-oss-20b` se recomienda ejecutar primero solo dos casos para confirmar conectividad, latencia y formato de respuesta:

```bash
python scripts/evaluate_llm_profiles.py --profiles university --examples growth_nvda technical_aapl
```
