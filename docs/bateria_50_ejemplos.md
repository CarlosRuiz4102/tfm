# Bateria de 50 ejemplos para evaluacion del MVP

Este documento resume la bateria definida en `data/catalog/bateria_50_ejemplos.json`.

- Total de casos: 50
- Nivel A: 15 consultas directas
- Nivel B: 20 consultas intermedias
- Nivel C: 15 consultas profesionales o de estres
- Datos usados: CSV locales congelados en `data/raw/`

La bateria esta pensada para revisar primero las consultas y despues ejecutarlas con el workflow LLM + codegen + validacion + ejecucion + interpretacion.

## Nivel A

| ID | Dataset | Consulta |
|---|---|---|
| A01_nvda_crecimiento_5y | cunto_ha_crecido_nvidia_en_5_aos.csv | Cuanto ha crecido Nvidia en los ultimos 5 anos |
| A02_nvda_maximo_minimo_5y | cunto_ha_crecido_nvidia_en_5_aos.csv | Dime el maximo, minimo y ultimo cierre de Nvidia en los ultimos 5 anos |
| A03_nvda_volatilidad_basica_5y | cunto_ha_crecido_nvidia_en_5_aos.csv | Resume la volatilidad historica de Nvidia en 5 anos con el peor dia observado |
| A04_nvda_amd_comparacion_simple | compara_nvidia_y_amd_en_2_aos.csv | Compara Nvidia y AMD en 2 anos y dime cual crecio mas |
| A05_nvda_amd_precio_inicial_final | compara_nvidia_y_amd_en_2_aos.csv | Para NVDA y AMD en 2 anos, dame precio inicial, precio final y rentabilidad de cada uno |
| A06_aapl_vision_general_3mo | aapl_en_3_meses.csv | Dame una vision general de AAPL en 3 meses |
| A07_aapl_cierre_y_volumen | aapl_en_3_meses.csv | Resume AAPL en 3 meses con ultimo cierre, volumen medio y dia de mayor volumen |
| A08_aapl_media_movil_simple | aapl_en_3_meses.csv | Calcula una media movil simple de 20 sesiones para AAPL en 3 meses y compara el ultimo cierre con esa media |
| A09_qqq_spy_retornos_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Analiza los retornos de QQQ y SPY en 2024 |
| A10_qqq_spy_riesgo_basico_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Analiza el riesgo historico de QQQ y SPY en 2024 |
| A11_sp500_crecimiento_desde_2020 | descrgame_el_histrico_del_sp_500_desde_2020.csv | Resume cuanto ha crecido el S&P 500 desde 2020 |
| A12_btc_crecimiento_2024 | datos_de_bitcoin_desde_20240101_hasta_20241231.csv | Cuanto crecio Bitcoin durante 2024 |
| A13_eurusd_cambio_10d_1h | eurusd_en_10_das_a_1h.csv | Cuanto cambio EUR/USD en los ultimos 10 dias con datos horarios |
| A14_oro_rango_1wk_1h | quiero_el_oro_en_1_semana_a_1h.csv | Dime el rango maximo y minimo del oro en la ultima semana con datos horarios |
| A15_qqq_spy_mejor_activo_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Entre QQQ y SPY, cual tuvo mejor comportamiento historico en 2024 |

## Nivel B

| ID | Dataset | Consulta |
|---|---|---|
| B01_nvda_tabla_evolucion_5y | cunto_ha_crecido_nvidia_en_5_aos.csv | Hazme un analisis mas completo de Nvidia en los ultimos 5 anos con tabla y una serie de evolucion |
| B02_nvda_metricas_riesgo_5y | cunto_ha_crecido_nvidia_en_5_aos.csv | Analiza Nvidia en 5 anos con retorno anualizado, volatilidad anualizada, maximo drawdown, mejor dia y peor dia |
| B03_nvda_resumen_mensual_5y | cunto_ha_crecido_nvidia_en_5_aos.csv | Agrupa Nvidia por meses en los ultimos 5 anos y muestra mejor mes, peor mes y una tabla resumen mensual |
| B04_nvda_amd_tabla_comparativa | compara_nvidia_y_amd_en_2_aos.csv | Compara NVDA y AMD en 2 anos con una tabla de rentabilidad, volatilidad y maximo drawdown |
| B05_nvda_amd_serie_normalizada | compara_nvidia_y_amd_en_2_aos.csv | Compara NVDA y AMD en 2 anos con una serie normalizada base 100 y una tabla resumen |
| B06_nvda_amd_correlacion | compara_nvidia_y_amd_en_2_aos.csv | Calcula la correlacion de retornos diarios entre NVDA y AMD en 2 anos y compara su volatilidad |
| B07_aapl_retorno_riesgo_3mo | aapl_en_3_meses.csv | Quiero entender retorno y riesgo de AAPL en 3 meses con una explicacion sencilla |
| B08_aapl_tecnico_sma_20_50 | aapl_en_3_meses.csv | Haz un analisis tecnico de AAPL en 3 meses con medias moviles de 20 y 50 sesiones y lectura prudente |
| B09_aapl_volumen_y_precio | aapl_en_3_meses.csv | Analiza AAPL en 3 meses relacionando dias de mayor volumen con variacion del precio y dame una tabla |
| B10_qqq_spy_tabla_serie_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Comparame QQQ y SPY en 2024 de forma clara, con tabla y serie normalizada |
| B11_qqq_spy_retorno_riesgo_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Compara QQQ y SPY en 2024 por retorno, volatilidad y relacion retorno volatilidad |
| B12_qqq_spy_drawdown_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Analiza el drawdown de QQQ y SPY en 2024 e incluye datos para una serie de drawdown |
| B13_qqq_spy_meses_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Para QQQ y SPY en 2024, calcula retornos mensuales y dime que activo gano cada mes |
| B14_btc_2024_perfil_volatil | datos_de_bitcoin_desde_20240101_hasta_20241231.csv | Analiza Bitcoin durante 2024 con rentabilidad, volatilidad, maximo drawdown y datos para una serie de evolucion |
| B15_btc_2024_mejores_peores_dias | datos_de_bitcoin_desde_20240101_hasta_20241231.csv | Identifica los 5 mejores y 5 peores dias de Bitcoin en 2024 y resume el riesgo observado |
| B16_sp500_desde_2020_riesgo | descrgame_el_histrico_del_sp_500_desde_2020.csv | Resume el S&P 500 desde 2020 con crecimiento total, volatilidad, maximo drawdown y mejores y peores periodos |
| B17_sp500_serie_base_100 | descrgame_el_histrico_del_sp_500_desde_2020.csv | Prepara una serie normalizada base 100 del S&P 500 desde 2020 y una tabla de rentabilidad anual |
| B18_eurusd_intradia_10d | eurusd_en_10_das_a_1h.csv | Resume el comportamiento intradia de EUR/USD durante los ultimos 10 dias con tabla de variacion, rango medio, volatilidad horaria y serie de evolucion |
| B19_oro_intradia_1wk | quiero_el_oro_en_1_semana_a_1h.csv | Analiza el oro durante la ultima semana con datos horarios, incluyendo cambio total, rango, volatilidad horaria y tabla de mejores y peores horas |
| B20_btc_sp500_lectura_contextual | datos_de_bitcoin_desde_20240101_hasta_20241231.csv | Analiza Bitcoin en 2024 y explica su perfil de riesgo sin compararlo con datos externos no incluidos |

## Nivel C

| ID | Dataset | Consulta |
|---|---|---|
| C01_qqq_spy_informe_profesional_2024 | qqq_y_spy_desde_20240101_hasta_20241231.csv | Haz un analisis profesional de QQQ y SPY en 2024 con tabla, serie normalizada, drawdown y conclusion para usuario no tecnico |
| C02_qqq_spy_formato_cuatro_bloques | qqq_y_spy_desde_20240101_hasta_20241231.csv | Compara QQQ y SPY durante 2024 como informe para un cliente no tecnico. Muestra exactamente cuatro bloques: tabla resumen, ranking mensual, serie normalizada y serie de drawdown |
| C03_qqq_spy_retorno_riesgo_meses | qqq_y_spy_desde_20240101_hasta_20241231.csv | Prepara un informe comparativo de QQQ y SPY en 2024 con retorno anual, volatilidad, drawdown, ranking mensual y limitaciones |
| C04_nvda_amd_ranking_multicriterio | compara_nvidia_y_amd_en_2_aos.csv | Compara NVDA y AMD en 2 anos con ranking por rentabilidad, riesgo y drawdown, y separa metricas, datos estructurados y limitaciones |
| C05_nvda_amd_informe_cliente | compara_nvidia_y_amd_en_2_aos.csv | Redacta un informe para cliente no tecnico comparando NVDA y AMD en 2 anos con resumen ejecutivo, tabla de metricas, riesgos historicos y cierre prudente |
| C06_nvda_5y_informe_completo | cunto_ha_crecido_nvidia_en_5_aos.csv | Prepara un informe completo de Nvidia en 5 anos con resumen ejecutivo, tabla de metricas, serie base 100, drawdown y limitaciones |
| C07_nvda_estres_salida_json | cunto_ha_crecido_nvidia_en_5_aos.csv | Analiza Nvidia en 5 anos y devuelve datos estructurados en cuatro secciones: metrics, table_data, chart_data y limitations |
| C08_sp500_informe_desde_2020 | descrgame_el_histrico_del_sp_500_desde_2020.csv | Prepara un informe detallado del S&P 500 desde 2020 con crecimiento, volatilidad, maximo drawdown, mejores y peores periodos, y resumen ejecutivo |
| C09_sp500_crisis_y_recuperacion | descrgame_el_histrico_del_sp_500_desde_2020.csv | Analiza el S&P 500 desde 2020 separando comportamiento por anos, caidas relevantes, recuperaciones y limitaciones de usar solo precios historicos |
| C10_btc_2024_informe_riesgo | datos_de_bitcoin_desde_20240101_hasta_20241231.csv | Prepara un informe de riesgo de Bitcoin en 2024 con tabla resumen, mejores y peores dias, drawdown, serie normalizada y conclusion prudente |
| C11_btc_2024_meses_y_drawdown | datos_de_bitcoin_desde_20240101_hasta_20241231.csv | Analiza Bitcoin en 2024 por meses, identifica mejor y peor mes, calcula maximo drawdown y explica limitaciones |
| C12_aapl_informe_tecnico_3mo | aapl_en_3_meses.csv | Haz un informe tecnico de AAPL en 3 meses con medias moviles de 20 y 50 sesiones, volatilidad, volumen, tabla de metricas y conclusion prudente |
| C13_eurusd_informe_intradia | eurusd_en_10_das_a_1h.csv | Prepara un informe intradia de EUR/USD durante 10 dias con tabla diaria, rango horario, volatilidad horaria, serie de evolucion y limitaciones |
| C14_oro_informe_intradia | quiero_el_oro_en_1_semana_a_1h.csv | Prepara un informe detallado del oro durante la ultima semana con datos horarios, metricas, extremos, serie, volatilidad, rango y limitaciones |
| C15_caso_control_limitaciones | aapl_en_3_meses.csv | Analiza AAPL en 3 meses y explica que se puede concluir solo con estos datos historicos. No uses noticias, no predigas el futuro y no recomiendes comprar ni vender |
