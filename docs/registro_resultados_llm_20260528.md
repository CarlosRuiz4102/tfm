# Registro de resultados LLM - 2026-05-28

Este registro deja trazada la actualizacion realizada tras liberar la cuota diaria de Groq.

## Ejecuciones realizadas

1. Se lanzo una pasada completa con `groq gemini university`. La llamada de herramienta agoto el tiempo de espera, pero el proceso continuo hasta generar el JSON final.
2. Tambien se ejecuto una repeticion acotada solo para `groq`, archivada como evidencia auxiliar.
3. La fuente principal para la memoria pasa a ser la pasada completa del 2026-05-28.

## Resultado actualizado

| Perfil | Resultado | Lectura |
|---|---:|---|
| Groq / `llama-3.3-70b-versatile` | `5/5` | Completa todos los casos tras repetir con cuota disponible. |
| Gemini / `gemini-2.5-flash` | `4/5` | Completa A, B y un C; falla la query de estres visual por codegen. |
| `openai/gpt-oss-20b` / vLLM universitario | `5/5` | Completa todos los casos, incluido estres visual. |

Total: `14/15` casos completos.

## Artefactos

- Informe principal: `docs/evaluacion_amplitud_tfm_llms.md`.
- Resumen ejecutivo: `docs/resumen_evaluacion_amplitud_tfm.md`.
- Salida Groq-only: `docs/salidas_ejecucion_groq_20260528.md`.
- JSON completo actualizado: `results/evaluations/progressive_llm_scope_20260528_180822.json`.
- JSON Groq-only: `results/evaluations/progressive_llm_scope_20260528_180641.json`.
- JSON previo de referencia: `results/evaluations/progressive_llm_scope_20260527_173646.json`.

## Artefactos no usados como fuente principal

- `results/evaluations/progressive_llm_scope_20260528_174639.json`: salida de diagnostico con `Connection error` en todos los perfiles; no representa rendimiento de los modelos.
- `results/evaluations/progressive_llm_scope_consolidated_20260528_180641.json`: consolidado intermedio creado antes de que terminase la pasada completa; queda superado por `progressive_llm_scope_20260528_180822.json`.

## Lectura para la memoria

La conclusion anterior de que Groq no era medible por cuota queda sustituida por una lectura mas justa: con cuota disponible, Groq completa la bateria. La comparacion sigue siendo exploratoria porque los resultados dependen de red, cuota, latencia, contexto y formato de salida, pero ahora hay evidencias guardadas en Markdown y JSON para defender la actualizacion.
