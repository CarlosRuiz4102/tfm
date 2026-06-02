# Bateria definitiva de 15 queries A/B/C

Este documento define las consultas que se utilizan en la evaluacion multi-modelo del MVP. La bateria esta equilibrada: cinco queries de Nivel A, cinco de Nivel B y cinco de Nivel C.

La definicion ejecutable vive en `scripts/generate_qualitative_demo_report.py`, dentro de la constante `DEMO_CASES`. El script `scripts/evaluate_progressive_llm_scope.py` recorre esas consultas para cada perfil LLM.

## Criterio de niveles

- Nivel A: consulta habitual, respuesta breve y metricas basicas.
- Nivel B: analisis mejorado con tabla y una visualizacion principal o sus datos.
- Nivel C: informe profesional o detallado con varias metricas, tablas, visualizaciones o restricciones explicitas.

## Nivel A

| ID | Consulta | Datos locales | Objetivo |
|---|---|---|---|
| `level_a_nvda_growth` | Cuanto ha crecido Nvidia en los ultimos 5 anos | NVDA, diario, 5 anos | Crecimiento historico basico |
| `level_a_nvda_amd_compare` | Compara Nvidia y AMD en 2 anos | NVDA y AMD, diario, 2 anos | Comparacion simple por rentabilidad |
| `level_a_aapl_overview` | Dame una vision general de AAPL en 3 meses | AAPL, diario, 3 meses | Resumen descriptivo |
| `level_a_qqq_spy_returns` | Analiza los retornos de QQQ y SPY en 2024 | QQQ y SPY, diario, 2024 | Retornos historicos resumidos |
| `level_a_qqq_spy_risk` | Analiza el riesgo historico de QQQ y SPY en 2024 | QQQ y SPY, diario, 2024 | Riesgo, volatilidad y extremos |

## Nivel B

| ID | Consulta | Datos locales | Objetivo |
|---|---|---|---|
| `level_b_nvda_complete` | Hazme un analisis mas completo de Nvidia en los ultimos 5 anos con tabla y una grafica de evolucion | NVDA, diario, 5 anos | Tabla y serie de precio |
| `level_b_qqq_spy_clear_compare` | Comparame QQQ y SPY en 2024 de forma clara, con tabla y grafica normalizada | QQQ y SPY, diario, 2024 | Comparacion relativa base 100 |
| `level_b_aapl_risk_return` | Quiero entender retorno y riesgo de AAPL en 3 meses con una explicacion sencilla | AAPL, diario, 3 meses | Relacion retorno-riesgo |
| `level_b_btc_2024_profile` | Analiza Bitcoin durante 2024 con una tabla de rentabilidad, volatilidad, maximo drawdown, maximo y minimo, y datos para una grafica de evolucion | BTC-USD, diario, 2024 | Cobertura de criptoactivo |
| `level_b_eurusd_intraday` | Resume el comportamiento intradia de EUR/USD durante los ultimos 10 dias con datos horarios. Incluye tabla de variacion, rango medio, volatilidad horaria y datos para una grafica de evolucion | EURUSD=X, horario, 10 dias | Cobertura intradia de divisa |

## Nivel C

| ID | Consulta | Datos locales | Objetivo |
|---|---|---|---|
| `level_c_qqq_spy_professional` | Haz un analisis profesional de QQQ y SPY en 2024 con tabla, grafica normalizada, drawdown y conclusion para usuario no tecnico | QQQ y SPY, diario, 2024 | Informe profesional comparativo |
| `level_c_nvda_amd_multicriteria` | Compara NVDA y AMD en 2 anos con ranking por rentabilidad, riesgo y drawdown, y separa metricas, visualizaciones y limitaciones | NVDA y AMD, diario, 2 anos | Ranking multicriterio |
| `level_c_sp500_report` | Prepara un informe detallado del S&P 500 desde 2020 con crecimiento, volatilidad, maximo drawdown, mejores y peores periodos, y resumen ejecutivo | ^GSPC, diario, desde 2020 | Serie larga de indice amplio |
| `level_c_gold_intraday_report` | Prepara un informe detallado del oro durante la ultima semana con datos horarios. Separa metricas, tabla de mejores y peores intervalos, datos para una grafica de evolucion, volatilidad horaria, rango maximo-minimo y limitaciones del analisis | GC=F, horario, 1 semana | Materia prima e intervalo horario |
| `stress_visual_qqq_spy_monthly` | Compara QQQ y SPY durante 2024 como si fuera un informe para un cliente no tecnico. Exige tabla resumen, ranking mensual, grafica normalizada base 100, grafica de drawdown y conclusion sin recomendar comprar ni vender | QQQ y SPY, diario, 2024 | Estres de formato visual |

## CSV utilizados

Los datos ya existen en `data/raw/`:

- `cunto_ha_crecido_nvidia_en_5_aos.csv`
- `compara_nvidia_y_amd_en_2_aos.csv`
- `aapl_en_3_meses.csv`
- `qqq_y_spy_desde_20240101_hasta_20241231.csv`
- `datos_de_bitcoin_desde_20240101_hasta_20241231.csv`
- `eurusd_en_10_das_a_1h.csv`
- `descrgame_el_histrico_del_sp_500_desde_2020.csv`
- `quiero_el_oro_en_1_semana_a_1h.csv`

## Ejecucion

La matriz completa se ejecuta con:

```powershell
python scripts\evaluate_progressive_llm_scope.py --profiles groq gemini university
```

El informe Markdown se genera en:

```text
results/reports/evaluacion_15_queries_llms.md
```

El JSON completo y auditable se genera con timestamp en:

```text
results/evaluations/progressive_llm_scope_YYYYMMDD_HHMMSS.json
```
