# Resumen ejecutivo de evaluacion de amplitud del TFM

Este documento resume la ejecucion progresiva realizada con queries de Nivel A, B, C y una query de estres visual. El informe detallado esta en [evaluacion_amplitud_tfm_llms.md](C:/Users/usuario/Desktop/tfm/docs/evaluacion_amplitud_tfm_llms.md).

## Resultado global

- Completados: `14/15`.
- La evaluacion usa tres perfiles ejecutados de nuevo el 2026-05-28 con cuota disponible: Groq, Gemini y universidad/vLLM.
- Se guardan salidas, planes LLM, ejecuciones, errores y respuestas finales en JSON y Markdown.

## Matriz compacta

| Perfil | A simple | A retornos | B visual | C profesional | C estres visual | Lectura |
|---|---|---|---|---|---|---|
| gemini | OK | OK | OK | OK | Parcial codegen | Muy buen salto frente a la pasada anterior; solo falla la query de estres visual. |
| groq | OK | OK | OK | OK | OK | Repetido con cuota disponible: completa los cinco casos progresivos. |
| university | OK | OK | OK | OK | OK | Cobertura completa, aunque con mayor latencia en algunos casos. |

## Archivos visuales generados

- [Informe completo](C:/Users/usuario/Desktop/tfm/docs/evaluacion_amplitud_tfm_llms.md)
- [JSON completo](C:/Users/usuario/Desktop/tfm/results/evaluations/progressive_llm_scope_20260528_180822.json)
- [Salidas Groq 2026-05-28](C:/Users/usuario/Desktop/tfm/docs/salidas_ejecucion_groq_20260528.md)
- [Grafica normalizada QQQ/SPY](C:/Users/usuario/Desktop/tfm/docs/figures/evaluacion_amplitud_llm/qqq_spy_normalizada_2024.png)
- [Grafica drawdown QQQ/SPY](C:/Users/usuario/Desktop/tfm/docs/figures/evaluacion_amplitud_llm/qqq_spy_drawdown_2024.png)
- [Completitud por modelo y nivel](C:/Users/usuario/Desktop/tfm/docs/figures/evaluacion_amplitud_llm/completitud_por_modelo_nivel.png)

## Que demuestra para la memoria

- La amplitud del TFM esta bien enfocada: el sistema no solo responde queries simples, tambien fuerza tablas, graficas y salidas estructuradas.
- El pipeline completo funciona de extremo a extremo cuando el proveedor responde y el contexto cabe en el modelo.
- Los fallos observados son defendibles metodologicamente: cuota, contexto, JSON de codegen e interpretacion con salidas largas.
- La compactacion de salidas visuales es una mejora necesaria y queda documentada.
- La evaluacion debe presentarse como exploratoria/cualitativa, no como ranking estadistico absoluto.

## Lectura de competencia de resultados

Los resultados actualizados son muy competentes: Groq y el perfil universitario completan 5 de 5 casos, incluyendo los niveles C y la query de estres visual. Gemini completa 4 de 5 y solo falla en la query visual mas exigente por generacion de codigo. La comparacion sigue siendo exploratoria y depende de disponibilidad, contexto, latencia y coste de cada proveedor.
