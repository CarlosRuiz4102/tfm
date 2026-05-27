# Resumen ejecutivo de evaluacion de amplitud del TFM

Este documento resume la ejecucion progresiva realizada con queries de Nivel A, B, C y una query de estres visual. El informe detallado esta en [evaluacion_amplitud_tfm_llms.md](C:/Users/usuario/Desktop/tfm/docs/evaluacion_amplitud_tfm_llms.md).

## Resultado global

- Completados: `6/15`.
- La evaluacion usa tres perfiles: Groq, Gemini y universidad/vLLM.
- Se guardan salidas, planes LLM, ejecuciones, errores y respuestas finales en JSON y Markdown.

## Matriz compacta

| Perfil | A simple | A retornos | B visual | C profesional | C estres visual | Lectura |
|---|---|---|---|---|---|---|
| gemini | Parcial plan | OK | OK | Parcial plan | Falla/cuota | Competente en A/B, pero limitado por formato/cuota en C. |
| groq | Falla/cuota | Falla/cuota | Falla/cuota | Falla/cuota | Falla/cuota | No medible en esta pasada por cuota diaria; hay muestras previas A/B/C en docs. |
| university | OK | OK | Parcial ejec. | OK | OK | Mejor cobertura: completa A, C y estres; falla B por contexto en interpretacion. |

## Archivos visuales generados

- [Informe completo](C:/Users/usuario/Desktop/tfm/docs/evaluacion_amplitud_tfm_llms.md)
- [JSON completo](C:/Users/usuario/Desktop/tfm/results/evaluations/progressive_llm_scope_20260527_173646.json)
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

Los resultados son competentes especialmente con el perfil universitario, que completa 4 de 5 casos incluyendo una query C profesional y la query de estres visual. Gemini demuestra buen rendimiento en A/B, pero tiene limitaciones en C por cuota/formato. Groq habia mostrado buenos resultados en ejecuciones previas, pero en esta pasada la cuota diaria impidio medirlo de forma justa.
