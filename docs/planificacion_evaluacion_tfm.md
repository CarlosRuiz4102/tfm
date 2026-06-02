# Planificacion de la evaluacion del TFM

Este documento reune el material de trabajo que sigue siendo util para preparar la evaluacion definitiva del MVP. Separa el protocolo reproducible, los aprendizajes tecnicos y las lineas futuras de los informes generados por ejecuciones concretas.

Los resultados de cada nueva pasada deben tratarse como artefactos temporales: se generan, se revisan y solo se incorporan a la memoria cuando se haya decidido que forman parte de la evaluacion final.

## Objetivo

La evaluacion debe comprobar si el flujo LLM + codegen controlado puede:

- interpretar consultas financieras historicas con distinta dificultad;
- generar codigo Python suficiente para calcular las metricas solicitadas;
- leer correctamente los CSV locales sin descargar datos nuevos;
- superar la validacion de seguridad;
- ejecutar el script en un entorno controlado;
- devolver datos estructurados para tablas o graficas cuando se soliciten;
- redactar una explicacion clara, prudente y trazable;
- evitar predicciones y recomendaciones de inversion.

La evaluacion tecnica debe complementarse con la rubrica cualitativa definida en `docs/evaluacion_cualitativa_llm.md`.

La bateria definitiva se documenta en `docs/bateria_evaluacion_15_queries.md`.

## Alcance de la bateria

La bateria cualitativa principal se organiza en los niveles A, B y C descritos en `docs/evaluacion_cualitativa_llm.md`:

- Nivel A: consultas simples con metricas basicas y respuesta breve.
- Nivel B: analisis mejorados con tabla y una visualizacion principal o sus datos.
- Nivel C: analisis profesionales o enriquecidos con varias salidas concretas.

Ademas, conviene conservar una bateria tecnica complementaria para cubrir familias de datos y calculos diferentes:

| Familia | Datos sugeridos | Que permite comprobar |
|---|---|---|
| Crecimiento individual | NVDA, 5 anos | Rentabilidad, maximos, minimos y volatilidad |
| Ranking de activos | NVDA y AMD, 2 anos | Comparacion, ranking, riesgo y drawdown |
| Vision descriptiva | AAPL, 3 meses | Tendencia, rango de precios y volumen |
| Contexto tecnico | AAPL, 3 meses | Medias moviles y posicion del ultimo cierre |
| Riesgo-retorno | QQQ y SPY, 2024 | Rentabilidad, volatilidad y correlacion |
| Drawdown comparado | QQQ y SPY, 2024 | Caidas historicas y riesgo relativo |
| Criptoactivo | BTC-USD, 2024 | Volatilidad y extremos en otro tipo de activo |
| Indice amplio | S&P 500, desde 2020 | Series largas, crecimiento y drawdown |
| Divisa intradia | EUR/USD, datos horarios | Intervalos horarios y rangos intradia |
| Materia prima intradia | Oro, datos horarios | Intervalos horarios, volumen y volatilidad |

Estas familias no sustituyen a la bateria A/B/C. Sirven para ampliar cobertura cuando se prepare la evaluacion final.

## Query de estres visual

Conviene mantener una consulta que obligue al sistema a respetar un formato de salida preciso:

> Compara QQQ y SPY durante 2024 como si fuera un informe para un cliente no tecnico. Quiero que me muestres los datos exactamente en cuatro bloques: 1) una tabla resumen con rentabilidad total, volatilidad anualizada, maximo drawdown, mejor mes y peor mes; 2) una tabla ranking mensual indicando que activo gano cada mes; 3) datos para una grafica normalizada base 100 de ambos activos; 4) datos para una grafica de drawdown. Cierra con una conclusion clara, sin recomendar comprar ni vender.

Esta query comprueba simultaneamente comprension, seleccion de metricas, generacion de codigo, formato, visualizacion e interpretacion final.

## Aprendizajes tecnicos reutilizables

Durante el desarrollo aparecieron varios problemas que justifican decisiones actuales del sistema:

### Contrato de lectura del payload

El script generado debe leer el payload con una forma permitida por la capa de seguridad:

```python
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
```

Esto evita depender de `open()`, bloqueado por la validacion de seguridad.

### Normalizacion de CSV

Los CSV historicos pueden tener cabeceras multinivel o formatos diferentes segun el activo y el intervalo. El modulo `src/execution/market_data.py` centraliza la lectura y normalizacion:

- `load_market_data`
- `load_close_prices`
- `ticker_summary`
- `make_json_safe`

El codigo generado debe reutilizar estos helpers en lugar de adivinar el formato de cada fichero.

### Serializacion de pandas y numpy

El codigo generado puede producir `Timestamp`, `Series`, arrays, valores `NaN` o tipos `numpy` no serializables. Antes de imprimir el JSON debe transformar la salida con `make_json_safe`.

### Reparacion y reintentos

Las respuestas LLM pueden llegar fuera de formato, contener codigo invalido o fallar de forma transitoria. El flujo incorpora reintentos y reparacion controlada del codigo para mejorar robustez sin saltarse la validacion AST.

### Compactacion para interpretacion

Las series extensas son utiles como artefacto, pero no siempre deben enviarse completas al segundo agente. La compactacion documentada en `docs/control_tamano_salidas_visualizacion.md` reduce el riesgo de superar limites de contexto manteniendo la salida completa en logs.

## Protocolo para la evaluacion definitiva

1. Fijar la bateria exacta de queries y los CSV locales usados.
2. Ejecutar la misma bateria con cada perfil LLM seleccionado.
3. Guardar para cada caso el plan, el codigo, la salida estructurada, los avisos, el estado y el tiempo.
4. Revisar cada respuesta con la plantilla manual de `docs/evaluacion_cualitativa_llm.md`.
5. Separar fallos del proveedor, fallos de codegen, rechazos de seguridad, fallos de ejecucion y defectos de interpretacion.
6. Comparar modelos como evidencia observada bajo condiciones concretas, no como ranking estadistico absoluto.
7. Incorporar a la memoria solo la pasada final seleccionada y sus artefactos reproducibles.

## Lineas de trabajo futuro

- Incorporar revision de analistas o docentes con conocimiento financiero para contrastar la rubrica.
- Realizar una ablacion de prompts: comparar resultados con instrucciones minimas y con prompts reforzados.
- Estudiar si las capacidades multimodales de algunos modelos aportan valor al interpretar graficas, sin mezclar esa extension con el MVP actual.
- Respetar siempre los formatos solicitados por el usuario y anadir solo informacion complementaria relevante.
- Clasificar errores por causa y calcular porcentajes por categoria cuando exista una muestra suficientemente amplia.
- Valorar coste, cuota, latencia y disponibilidad de APIs como limitaciones practicas.
- Revisar las conclusiones de la memoria una vez cerrada la evaluacion final.

## Gestion de artefactos

Los informes Markdown y JSON generados por scripts de evaluacion no deben mantenerse como documentacion estable mientras sean pasadas provisionales. Los scripts pueden regenerarlos cuando se ejecute la bateria definitiva.

La documentacion estable del proyecto queda centrada en:

- `docs/arquitectura_llm_codegen.md`
- `docs/evolucion_mvp_tfm.md`
- `docs/evaluacion_cualitativa_llm.md`
- `docs/control_tamano_salidas_visualizacion.md`
- `docs/llm_api_setup.md`
- `docs/planificacion_evaluacion_tfm.md`
- `docs/bateria_evaluacion_15_queries.md`
- `docs/detalle_iteracion_workflow.md`
