# Demo ejecutada de salidas cliente A/B/C

Generado: 2026-05-27T17:12:54

Este documento muestra una ejecución local reproducible sobre los CSV reales del proyecto.
Se usa para visualizar como quedarian las salidas que recibira el cliente en los niveles A, B y C.

> Nota: la ejecucion LLM real con el endpoint universitario se intento, pero no completo dentro del tiempo disponible. Por eso este documento no compara modelos; muestra la salida calculada desde datos reales y redactada con una plantilla local para validar la presentacion.

## Resumen de casos

| ID | Nivel | Salida esperada |
|---|---:|---|
| `level_a_nvda_growth` | A | Texto breve + metricas basicas. |
| `level_a_nvda_amd_compare` | A | Comparacion simple con rentabilidad y ranking basico. |
| `level_a_aapl_overview` | A | Vision general breve con metricas basicas. |
| `level_a_qqq_spy_returns` | A | Retornos historicos resumidos. |
| `level_a_qqq_spy_risk` | A | Riesgo historico basico con volatilidad y extremos. |
| `level_a_aapl_technical` | A | Analisis tecnico basico sin recomendacion de trading. |
| `level_b_nvda_complete` | B | Texto + tabla de metricas + datos para grafica de evolucion. |
| `level_b_qqq_spy_clear_compare` | B | Comparativa clara con tabla y grafica normalizada. |
| `level_b_aapl_risk_return` | B | Explicacion sencilla de retorno y riesgo. |
| `level_c_qqq_spy_professional` | C | Informe profesional con tabla, normalizacion, drawdown y conclusion. |
| `level_c_nvda_amd_multicriteria` | C | Ranking multicriterio por rentabilidad, riesgo y drawdown. |
| `level_c_sp500_report` | C | Informe detallado de indice con resumen ejecutivo. |
| `stress_visual_qqq_spy_monthly` | C | Query exigente con formato impuesto: tabla resumen, ranking mensual, grafica normalizada y grafica de drawdown. |

## level_a_nvda_growth - Nivel A

**Consulta:** Cuanto ha crecido Nvidia en los ultimos 5 anos

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 13.34 | 183.22 | 1273.33% | 51.73% | -66.36% | 207.04 | 11.23 |

Para NVDA, entre 2021-03-17 y 2026-03-16, el precio paso de 13.34 a 183.22, con una rentabilidad total de 1273.33%. El maximo drawdown fue -66.36% y la volatilidad anualizada aproximada fue 51.73%. Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "price_growth",
  "level": "A",
  "metrics": {
    "NVDA": {
      "precio_inicial": 13.3412504196167,
      "precio_final": 183.22000122070312,
      "rentabilidad_total": 12.733345485465156,
      "maximo": 207.0399932861328,
      "minimo": 11.22700023651123,
      "volatilidad_anualizada": 0.5172666383751224,
      "max_drawdown": -0.6636205530533923,
      "mejor_periodo": 0.24369635894280006,
      "peor_periodo": -0.16968165598629847,
      "fecha_inicio": "2021-03-17",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {}
}
```

## level_a_nvda_amd_compare - Nivel A

**Consulta:** Compara Nvidia y AMD en 2 anos

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 88.46 | 183.22 | 107.13% | 49.34% | -36.89% | 207.04 | 76.20 |
| AMD | 190.65 | 196.58 | 3.11% | 55.67% | -58.98% | 264.33 | 78.21 |

La comparativa ordena mejor a NVDA por rentabilidad historica en el periodo. NVDA: rentabilidad 107.13%, volatilidad 49.34%, drawdown -36.89% | AMD: rentabilidad 3.11%, volatilidad 55.67%, drawdown -58.98%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "compare_assets",
  "level": "A",
  "metrics": {
    "NVDA": {
      "precio_inicial": 88.45500183105469,
      "precio_final": 183.22000122070312,
      "rentabilidad_total": 1.0713356783446297,
      "maximo": 207.0399932861328,
      "minimo": 76.19999694824219,
      "volatilidad_anualizada": 0.49344815296435085,
      "max_drawdown": -0.36886835186281197,
      "mejor_periodo": 0.18722739572091607,
      "peor_periodo": -0.16968165598629847,
      "fecha_inicio": "2024-03-18",
      "fecha_fin": "2026-03-16"
    },
    "AMD": {
      "precio_inicial": 190.6499938964844,
      "precio_final": 196.5800018310547,
      "rentabilidad_total": 0.03110416010708117,
      "maximo": 264.3299865722656,
      "minimo": 78.20999908447266,
      "volatilidad_anualizada": 0.5567482542547432,
      "max_drawdown": -0.5897718248711947,
      "mejor_periodo": 0.23820480081192907,
      "peor_periodo": -0.1731444304789821,
      "fecha_inicio": "2024-03-18",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {},
  "correlation": {
    "NVDA": {
      "NVDA": 1.0,
      "AMD": 0.5508
    },
    "AMD": {
      "NVDA": 0.5508,
      "AMD": 1.0
    }
  }
}
```

## level_a_aapl_overview - Nivel A

**Consulta:** Dame una vision general de AAPL en 3 meses

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| AAPL | 271.84 | 252.82 | -7.00% | 24.07% | -10.07% | 278.12 | 246.70 |

Para AAPL, entre 2025-12-17 y 2026-03-16, el precio paso de 271.84 a 252.82, con una rentabilidad total de -7.00%. El maximo drawdown fue -10.07% y la volatilidad anualizada aproximada fue 24.07%. Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "asset_overview",
  "level": "A",
  "metrics": {
    "AAPL": {
      "precio_inicial": 271.8399963378906,
      "precio_final": 252.82000732421875,
      "rentabilidad_total": -0.06996758854436746,
      "maximo": 278.1199951171875,
      "minimo": 246.6999969482422,
      "volatilidad_anualizada": 0.24070645799526247,
      "max_drawdown": -0.10067596897591646,
      "mejor_periodo": 0.04058115590203082,
      "peor_periodo": -0.049981811301894274,
      "fecha_inicio": "2025-12-17",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {}
}
```

## level_a_qqq_spy_returns - Nivel A

**Consulta:** Analiza los retornos de QQQ y SPY en 2024

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 402.59 | 515.61 | 28.07% | 17.96% | -13.56% | 538.17 | 396.28 |
| SPY | 472.65 | 588.22 | 24.45% | 12.61% | -8.41% | 607.81 | 467.28 |

La comparativa ordena mejor a QQQ por rentabilidad historica en el periodo. QQQ: rentabilidad 28.07%, volatilidad 17.96%, drawdown -13.56% | SPY: rentabilidad 24.45%, volatilidad 12.61%, drawdown -8.41%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "return_analysis",
  "level": "A",
  "metrics": {
    "QQQ": {
      "precio_inicial": 402.5899963378906,
      "precio_final": 515.6099853515625,
      "rentabilidad_total": 0.28073223388992274,
      "maximo": 538.1699829101562,
      "minimo": 396.2799987792969,
      "volatilidad_anualizada": 0.17961377348921978,
      "max_drawdown": -0.1355773890565939,
      "mejor_periodo": 0.03059093002421731,
      "peor_periodo": -0.036076927081440724,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    },
    "SPY": {
      "precio_inicial": 472.6499938964844,
      "precio_final": 588.219970703125,
      "rentabilidad_total": 0.24451492287959642,
      "maximo": 607.8099975585938,
      "minimo": 467.2799987792969,
      "volatilidad_anualizada": 0.12611587893527634,
      "max_drawdown": -0.08405619392423236,
      "mejor_periodo": 0.024865554910313614,
      "peor_periodo": -0.029803487374158943,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    }
  },
  "chart_data": {},
  "correlation": {
    "QQQ": {
      "QQQ": 1.0,
      "SPY": 0.945
    },
    "SPY": {
      "QQQ": 0.945,
      "SPY": 1.0
    }
  }
}
```

## level_a_qqq_spy_risk - Nivel A

**Consulta:** Analiza el riesgo historico de QQQ y SPY en 2024

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 402.59 | 515.61 | 28.07% | 17.96% | -13.56% | 538.17 | 396.28 |
| SPY | 472.65 | 588.22 | 24.45% | 12.61% | -8.41% | 607.81 | 467.28 |

La comparativa ordena mejor a QQQ por rentabilidad historica en el periodo. QQQ: rentabilidad 28.07%, volatilidad 17.96%, drawdown -13.56% | SPY: rentabilidad 24.45%, volatilidad 12.61%, drawdown -8.41%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "historical_risk_analysis",
  "level": "A",
  "metrics": {
    "QQQ": {
      "precio_inicial": 402.5899963378906,
      "precio_final": 515.6099853515625,
      "rentabilidad_total": 0.28073223388992274,
      "maximo": 538.1699829101562,
      "minimo": 396.2799987792969,
      "volatilidad_anualizada": 0.17961377348921978,
      "max_drawdown": -0.1355773890565939,
      "mejor_periodo": 0.03059093002421731,
      "peor_periodo": -0.036076927081440724,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    },
    "SPY": {
      "precio_inicial": 472.6499938964844,
      "precio_final": 588.219970703125,
      "rentabilidad_total": 0.24451492287959642,
      "maximo": 607.8099975585938,
      "minimo": 467.2799987792969,
      "volatilidad_anualizada": 0.12611587893527634,
      "max_drawdown": -0.08405619392423236,
      "mejor_periodo": 0.024865554910313614,
      "peor_periodo": -0.029803487374158943,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    }
  },
  "chart_data": {
    "drawdown": {
      "QQQ": [
        {
          "date": "2024-01-02",
          "value": 0.0
        },
        {
          "date": "2024-02-05",
          "value": -0.0013
        },
        {
          "date": "2024-03-07",
          "value": -0.0004
        },
        {
          "date": "2024-04-10",
          "value": -0.0179
        },
        {
          "date": "2024-05-13",
          "value": -0.0074
        },
        {
          "date": "2024-06-14",
          "value": 0.0
        },
        {
          "date": "2024-07-18",
          "value": -0.0467
        },
        {
          "date": "2024-08-20",
          "value": -0.0451
        },
        {
          "date": "2024-09-23",
          "value": -0.0396
        },
        {
          "date": "2024-10-24",
          "value": -0.0212
        },
        {
          "date": "2024-11-25",
          "value": -0.0147
        },
        {
          "date": "2024-12-30",
          "value": -0.0419
        }
      ],
      "SPY": [
        {
          "date": "2024-01-02",
          "value": 0.0
        },
        {
          "date": "2024-02-05",
          "value": -0.0036
        },
        {
          "date": "2024-03-07",
          "value": 0.0
        },
        {
          "date": "2024-04-10",
          "value": -0.0173
        },
        {
          "date": "2024-05-13",
          "value": -0.0043
        },
        {
          "date": "2024-06-14",
          "value": 0.0
        },
        {
          "date": "2024-07-18",
          "value": -0.0216
        },
        {
          "date": "2024-08-20",
          "value": -0.0109
        },
        {
          "date": "2024-09-23",
          "value": -0.0023
        },
        {
          "date": "2024-10-24",
          "value": -0.0092
        },
        {
          "date": "2024-11-25",
          "value": -0.0021
        },
        {
          "date": "2024-12-30",
          "value": -0.0322
        }
      ]
    }
  },
  "correlation": {
    "QQQ": {
      "QQQ": 1.0,
      "SPY": 0.945
    },
    "SPY": {
      "QQQ": 0.945,
      "SPY": 1.0
    }
  }
}
```

## level_a_aapl_technical - Nivel A

**Consulta:** Haz un analisis tecnico basico de AAPL en 3 meses

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| AAPL | 271.84 | 252.82 | -7.00% | 24.07% | -10.07% | 278.12 | 246.70 |

Para AAPL, entre 2025-12-17 y 2026-03-16, el precio paso de 271.84 a 252.82, con una rentabilidad total de -7.00%. El maximo drawdown fue -10.07% y la volatilidad anualizada aproximada fue 24.07%. El ultimo cierre fue 252.82, frente a una SMA20 de 262.60 y una SMA50 de 262.33. Lectura: es una salida breve porque la consulta no exige visualizaciones ni formato avanzado. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "technical_analysis",
  "level": "A",
  "metrics": {
    "AAPL": {
      "precio_inicial": 271.8399963378906,
      "precio_final": 252.82000732421875,
      "rentabilidad_total": -0.06996758854436746,
      "maximo": 278.1199951171875,
      "minimo": 246.6999969482422,
      "volatilidad_anualizada": 0.24070645799526247,
      "max_drawdown": -0.10067596897591646,
      "mejor_periodo": 0.04058115590203082,
      "peor_periodo": -0.049981811301894274,
      "fecha_inicio": "2025-12-17",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {},
  "technical": {
    "sma_20": 262.6014991760254,
    "sma_50": 262.3267990112305,
    "ultimo_cierre": 252.82000732421875
  }
}
```

## level_b_nvda_complete - Nivel B

**Consulta:** Hazme un analisis mas completo de Nvidia en los ultimos 5 anos con tabla y una grafica de evolucion

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 13.34 | 183.22 | 1273.33% | 51.73% | -66.36% | 207.04 | 11.23 |

Para NVDA, entre 2021-03-17 y 2026-03-16, el precio paso de 13.34 a 183.22, con una rentabilidad total de 1273.33%. El maximo drawdown fue -66.36% y la volatilidad anualizada aproximada fue 51.73%. Lectura: se acompana de datos para una grafica principal porque el usuario pide un analisis mas completo. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "improved_growth_analysis",
  "level": "B",
  "metrics": {
    "NVDA": {
      "precio_inicial": 13.3412504196167,
      "precio_final": 183.22000122070312,
      "rentabilidad_total": 12.733345485465156,
      "maximo": 207.0399932861328,
      "minimo": 11.22700023651123,
      "volatilidad_anualizada": 0.5172666383751224,
      "max_drawdown": -0.6636205530533923,
      "mejor_periodo": 0.24369635894280006,
      "peor_periodo": -0.16968165598629847,
      "fecha_inicio": "2021-03-17",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {
    "close_price": {
      "NVDA": [
        {
          "date": "2021-03-17",
          "value": 13.3413
        },
        {
          "date": "2021-08-27",
          "value": 22.636
        },
        {
          "date": "2022-02-09",
          "value": 26.705
        },
        {
          "date": "2022-07-26",
          "value": 16.533
        },
        {
          "date": "2023-01-06",
          "value": 14.859
        },
        {
          "date": "2023-06-22",
          "value": 43.025
        },
        {
          "date": "2023-12-04",
          "value": 45.51
        },
        {
          "date": "2024-05-17",
          "value": 92.479
        },
        {
          "date": "2024-10-30",
          "value": 139.34
        },
        {
          "date": "2025-04-16",
          "value": 104.49
        },
        {
          "date": "2025-09-30",
          "value": 186.58
        },
        {
          "date": "2026-03-16",
          "value": 183.22
        }
      ]
    }
  }
}
```

## level_b_qqq_spy_clear_compare - Nivel B

**Consulta:** Comparame QQQ y SPY en 2024 de forma clara, con tabla y grafica normalizada

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 402.59 | 515.61 | 28.07% | 17.96% | -13.56% | 538.17 | 396.28 |
| SPY | 472.65 | 588.22 | 24.45% | 12.61% | -8.41% | 607.81 | 467.28 |

La comparativa ordena mejor a QQQ por rentabilidad historica en el periodo. QQQ: rentabilidad 28.07%, volatilidad 17.96%, drawdown -13.56% | SPY: rentabilidad 24.45%, volatilidad 12.61%, drawdown -8.41%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: se acompana de datos para una grafica principal porque el usuario pide un analisis mas completo. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "improved_asset_comparison",
  "level": "B",
  "metrics": {
    "QQQ": {
      "precio_inicial": 402.5899963378906,
      "precio_final": 515.6099853515625,
      "rentabilidad_total": 0.28073223388992274,
      "maximo": 538.1699829101562,
      "minimo": 396.2799987792969,
      "volatilidad_anualizada": 0.17961377348921978,
      "max_drawdown": -0.1355773890565939,
      "mejor_periodo": 0.03059093002421731,
      "peor_periodo": -0.036076927081440724,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    },
    "SPY": {
      "precio_inicial": 472.6499938964844,
      "precio_final": 588.219970703125,
      "rentabilidad_total": 0.24451492287959642,
      "maximo": 607.8099975585938,
      "minimo": 467.2799987792969,
      "volatilidad_anualizada": 0.12611587893527634,
      "max_drawdown": -0.08405619392423236,
      "mejor_periodo": 0.024865554910313614,
      "peor_periodo": -0.029803487374158943,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    }
  },
  "chart_data": {
    "normalized_to_100": {
      "QQQ": [
        {
          "date": "2024-01-02",
          "value": 100.0
        },
        {
          "date": "2024-02-05",
          "value": 106.4234
        },
        {
          "date": "2024-03-07",
          "value": 110.6461
        },
        {
          "date": "2024-04-10",
          "value": 108.8875
        },
        {
          "date": "2024-05-13",
          "value": 110.0574
        },
        {
          "date": "2024-06-14",
          "value": 119.0268
        },
        {
          "date": "2024-07-18",
          "value": 119.1013
        },
        {
          "date": "2024-08-20",
          "value": 119.2926
        },
        {
          "date": "2024-09-23",
          "value": 119.9831
        },
        {
          "date": "2024-10-24",
          "value": 122.2882
        },
        {
          "date": "2024-11-25",
          "value": 125.8327
        },
        {
          "date": "2024-12-30",
          "value": 128.0732
        }
      ],
      "SPY": [
        {
          "date": "2024-01-02",
          "value": 100.0
        },
        {
          "date": "2024-02-05",
          "value": 104.2103
        },
        {
          "date": "2024-03-07",
          "value": 108.9199
        },
        {
          "date": "2024-04-10",
          "value": 108.7739
        },
        {
          "date": "2024-05-13",
          "value": 110.2105
        },
        {
          "date": "2024-06-14",
          "value": 114.8376
        },
        {
          "date": "2024-07-18",
          "value": 116.928
        },
        {
          "date": "2024-08-20",
          "value": 118.2059
        },
        {
          "date": "2024-09-23",
          "value": 120.5268
        },
        {
          "date": "2024-10-24",
          "value": 122.5516
        },
        {
          "date": "2024-11-25",
          "value": 126.4212
        },
        {
          "date": "2024-12-30",
          "value": 124.4515
        }
      ]
    }
  },
  "correlation": {
    "QQQ": {
      "QQQ": 1.0,
      "SPY": 0.945
    },
    "SPY": {
      "QQQ": 0.945,
      "SPY": 1.0
    }
  }
}
```

## level_b_aapl_risk_return - Nivel B

**Consulta:** Quiero entender retorno y riesgo de AAPL en 3 meses con una explicacion sencilla

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| AAPL | 271.84 | 252.82 | -7.00% | 24.07% | -10.07% | 278.12 | 246.70 |

Para AAPL, entre 2025-12-17 y 2026-03-16, el precio paso de 271.84 a 252.82, con una rentabilidad total de -7.00%. El maximo drawdown fue -10.07% y la volatilidad anualizada aproximada fue 24.07%. Lectura: se acompana de datos para una grafica principal porque el usuario pide un analisis mas completo. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "improved_risk_return_analysis",
  "level": "B",
  "metrics": {
    "AAPL": {
      "precio_inicial": 271.8399963378906,
      "precio_final": 252.82000732421875,
      "rentabilidad_total": -0.06996758854436746,
      "maximo": 278.1199951171875,
      "minimo": 246.6999969482422,
      "volatilidad_anualizada": 0.24070645799526247,
      "max_drawdown": -0.10067596897591646,
      "mejor_periodo": 0.04058115590203082,
      "peor_periodo": -0.049981811301894274,
      "fecha_inicio": "2025-12-17",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {
    "close_price": {
      "AAPL": [
        {
          "date": "2025-12-17",
          "value": 271.84
        },
        {
          "date": "2025-12-24",
          "value": 273.81
        },
        {
          "date": "2026-01-05",
          "value": 267.26
        },
        {
          "date": "2026-01-12",
          "value": 260.25
        },
        {
          "date": "2026-01-20",
          "value": 246.7
        },
        {
          "date": "2026-01-28",
          "value": 256.44
        },
        {
          "date": "2026-02-04",
          "value": 276.49
        },
        {
          "date": "2026-02-12",
          "value": 261.73
        },
        {
          "date": "2026-02-20",
          "value": 264.58
        },
        {
          "date": "2026-02-27",
          "value": 264.18
        },
        {
          "date": "2026-03-09",
          "value": 259.88
        },
        {
          "date": "2026-03-16",
          "value": 252.82
        }
      ]
    },
    "drawdown": {
      "AAPL": [
        {
          "date": "2025-12-17",
          "value": 0.0
        },
        {
          "date": "2025-12-24",
          "value": 0.0
        },
        {
          "date": "2026-01-05",
          "value": -0.0239
        },
        {
          "date": "2026-01-12",
          "value": -0.0495
        },
        {
          "date": "2026-01-20",
          "value": -0.099
        },
        {
          "date": "2026-01-28",
          "value": -0.0634
        },
        {
          "date": "2026-02-04",
          "value": 0.0
        },
        {
          "date": "2026-02-12",
          "value": -0.0589
        },
        {
          "date": "2026-02-20",
          "value": -0.0487
        },
        {
          "date": "2026-02-27",
          "value": -0.0501
        },
        {
          "date": "2026-03-09",
          "value": -0.0656
        },
        {
          "date": "2026-03-16",
          "value": -0.091
        }
      ]
    }
  }
}
```

## level_c_qqq_spy_professional - Nivel C

**Consulta:** Haz un analisis profesional de QQQ y SPY en 2024 con tabla, grafica normalizada, drawdown y conclusion para usuario no tecnico

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 402.59 | 515.61 | 28.07% | 17.96% | -13.56% | 538.17 | 396.28 |
| SPY | 472.65 | 588.22 | 24.45% | 12.61% | -8.41% | 607.81 | 467.28 |

La comparativa ordena mejor a QQQ por rentabilidad historica en el periodo. QQQ: rentabilidad 28.07%, volatilidad 17.96%, drawdown -13.56% | SPY: rentabilidad 24.45%, volatilidad 12.61%, drawdown -8.41%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: se incluyen metricas y datos visuales adicionales porque el usuario pide un analisis profesional o multicriterio. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "professional_asset_comparison",
  "level": "C",
  "metrics": {
    "QQQ": {
      "precio_inicial": 402.5899963378906,
      "precio_final": 515.6099853515625,
      "rentabilidad_total": 0.28073223388992274,
      "maximo": 538.1699829101562,
      "minimo": 396.2799987792969,
      "volatilidad_anualizada": 0.17961377348921978,
      "max_drawdown": -0.1355773890565939,
      "mejor_periodo": 0.03059093002421731,
      "peor_periodo": -0.036076927081440724,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    },
    "SPY": {
      "precio_inicial": 472.6499938964844,
      "precio_final": 588.219970703125,
      "rentabilidad_total": 0.24451492287959642,
      "maximo": 607.8099975585938,
      "minimo": 467.2799987792969,
      "volatilidad_anualizada": 0.12611587893527634,
      "max_drawdown": -0.08405619392423236,
      "mejor_periodo": 0.024865554910313614,
      "peor_periodo": -0.029803487374158943,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    }
  },
  "chart_data": {
    "normalized_to_100": {
      "QQQ": [
        {
          "date": "2024-01-02",
          "value": 100.0
        },
        {
          "date": "2024-02-05",
          "value": 106.4234
        },
        {
          "date": "2024-03-07",
          "value": 110.6461
        },
        {
          "date": "2024-04-10",
          "value": 108.8875
        },
        {
          "date": "2024-05-13",
          "value": 110.0574
        },
        {
          "date": "2024-06-14",
          "value": 119.0268
        },
        {
          "date": "2024-07-18",
          "value": 119.1013
        },
        {
          "date": "2024-08-20",
          "value": 119.2926
        },
        {
          "date": "2024-09-23",
          "value": 119.9831
        },
        {
          "date": "2024-10-24",
          "value": 122.2882
        },
        {
          "date": "2024-11-25",
          "value": 125.8327
        },
        {
          "date": "2024-12-30",
          "value": 128.0732
        }
      ],
      "SPY": [
        {
          "date": "2024-01-02",
          "value": 100.0
        },
        {
          "date": "2024-02-05",
          "value": 104.2103
        },
        {
          "date": "2024-03-07",
          "value": 108.9199
        },
        {
          "date": "2024-04-10",
          "value": 108.7739
        },
        {
          "date": "2024-05-13",
          "value": 110.2105
        },
        {
          "date": "2024-06-14",
          "value": 114.8376
        },
        {
          "date": "2024-07-18",
          "value": 116.928
        },
        {
          "date": "2024-08-20",
          "value": 118.2059
        },
        {
          "date": "2024-09-23",
          "value": 120.5268
        },
        {
          "date": "2024-10-24",
          "value": 122.5516
        },
        {
          "date": "2024-11-25",
          "value": 126.4212
        },
        {
          "date": "2024-12-30",
          "value": 124.4515
        }
      ]
    },
    "drawdown": {
      "QQQ": [
        {
          "date": "2024-01-02",
          "value": 0.0
        },
        {
          "date": "2024-02-05",
          "value": -0.0013
        },
        {
          "date": "2024-03-07",
          "value": -0.0004
        },
        {
          "date": "2024-04-10",
          "value": -0.0179
        },
        {
          "date": "2024-05-13",
          "value": -0.0074
        },
        {
          "date": "2024-06-14",
          "value": 0.0
        },
        {
          "date": "2024-07-18",
          "value": -0.0467
        },
        {
          "date": "2024-08-20",
          "value": -0.0451
        },
        {
          "date": "2024-09-23",
          "value": -0.0396
        },
        {
          "date": "2024-10-24",
          "value": -0.0212
        },
        {
          "date": "2024-11-25",
          "value": -0.0147
        },
        {
          "date": "2024-12-30",
          "value": -0.0419
        }
      ],
      "SPY": [
        {
          "date": "2024-01-02",
          "value": 0.0
        },
        {
          "date": "2024-02-05",
          "value": -0.0036
        },
        {
          "date": "2024-03-07",
          "value": 0.0
        },
        {
          "date": "2024-04-10",
          "value": -0.0173
        },
        {
          "date": "2024-05-13",
          "value": -0.0043
        },
        {
          "dat
... [salida truncada en el informe]
```

## level_c_nvda_amd_multicriteria - Nivel C

**Consulta:** Compara NVDA y AMD en 2 anos con ranking por rentabilidad, riesgo y drawdown, y separa metricas, visualizaciones y limitaciones

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| NVDA | 88.46 | 183.22 | 107.13% | 49.34% | -36.89% | 207.04 | 76.20 |
| AMD | 190.65 | 196.58 | 3.11% | 55.67% | -58.98% | 264.33 | 78.21 |

La comparativa ordena mejor a NVDA por rentabilidad historica en el periodo. NVDA: rentabilidad 107.13%, volatilidad 49.34%, drawdown -36.89% | AMD: rentabilidad 3.11%, volatilidad 55.67%, drawdown -58.98%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: se incluyen metricas y datos visuales adicionales porque el usuario pide un analisis profesional o multicriterio. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "professional_multicriteria_comparison",
  "level": "C",
  "metrics": {
    "NVDA": {
      "precio_inicial": 88.45500183105469,
      "precio_final": 183.22000122070312,
      "rentabilidad_total": 1.0713356783446297,
      "maximo": 207.0399932861328,
      "minimo": 76.19999694824219,
      "volatilidad_anualizada": 0.49344815296435085,
      "max_drawdown": -0.36886835186281197,
      "mejor_periodo": 0.18722739572091607,
      "peor_periodo": -0.16968165598629847,
      "fecha_inicio": "2024-03-18",
      "fecha_fin": "2026-03-16"
    },
    "AMD": {
      "precio_inicial": 190.6499938964844,
      "precio_final": 196.5800018310547,
      "rentabilidad_total": 0.03110416010708117,
      "maximo": 264.3299865722656,
      "minimo": 78.20999908447266,
      "volatilidad_anualizada": 0.5567482542547432,
      "max_drawdown": -0.5897718248711947,
      "mejor_periodo": 0.23820480081192907,
      "peor_periodo": -0.1731444304789821,
      "fecha_inicio": "2024-03-18",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {
    "normalized_to_100": {
      "NVDA": [
        {
          "date": "2024-03-18",
          "value": 100.0
        },
        {
          "date": "2024-05-21",
          "value": 107.8356
        },
        {
          "date": "2024-07-29",
          "value": 126.1545
        },
        {
          "date": "2024-10-01",
          "value": 132.2706
        },
        {
          "date": "2024-12-04",
          "value": 164.0834
        },
        {
          "date": "2025-02-12",
          "value": 148.2562
        },
        {
          "date": "2025-04-17",
          "value": 114.7363
        },
        {
          "date": "2025-06-25",
          "value": 174.4503
        },
        {
          "date": "2025-08-28",
          "value": 203.6855
        },
        {
          "date": "2025-10-31",
          "value": 228.9187
        },
        {
          "date": "2026-01-08",
          "value": 209.1911
        },
        {
          "date": "2026-03-16",
          "value": 207.1336
        }
      ],
      "AMD": [
        {
          "date": "2024-03-18",
          "value": 100.0
        },
        {
          "date": "2024-05-21",
          "value": 86.3677
        },
        {
          "date": "2024-07-29",
          "value": 73.3019
        },
        {
          "date": "2024-10-01",
          "value": 83.7923
        },
        {
          "date": "2024-12-04",
          "value": 75.5258
        },
        {
          "date": "2025-02-12",
          "value": 58.5995
        },
        {
          "date": "2025-04-17",
          "value": 45.8956
        },
        {
          "date": "2025-06-25",
          "value": 75.2164
        },
        {
          "date": "2025-08-28",
          "value": 88.4238
        },
        {
          "date": "2025-10-31",
          "value": 134.3404
        },
        {
          "date": "2026-01-08",
          "value": 107.359
        },
        {
          "date": "2026-03-16",
          "value": 103.1104
        }
      ]
    },
    "drawdown": {
      "NVDA": [
        {
          "date": "2024-03-18",
          "value": 0.0
        },
        {
          "date": "2024-05-21",
          "value": 0.0
        },
        {
          "date": "2024-07-29",
          "value": -0.1769
        },
        {
          "date": "2024-10-01",
          "value": -0.137
        },
        {
          "date": "2024-12-04",
          "value": -0.0251
        },
        {
          "date": "2025-02-12",
          "value": -0.1224
        },
        {
          "date": "2025-04-17",
          "value": -0.3208
        },
        {
          "date": "2025-06-25",
          "value": 0.0
        },
        {
          "date": "2025-08-28",
          "value": -0.0163
        },
        {
          "date": "2025-10-31",
          "value": -0.022
        },
        {
          "date": "2026-01-08",
          "value": -0.1063
        },
        {
          "date": "2026-03-16",
          "value": -0.1151
        }
      ],
      "AMD": [
        {
          "date": "2024-03-18",
          "value": 0.0
        },
        {
          "date": "2024-05-21",
          "value": -0.1363
        },
        {
          "date": "2024-07-29",
          "value": -0.267
        },
        {
          "date": "2024-10-01",
          "value": -0.1621
        },
        {
          "date": "2024-12-04",
          "value": -0.2447
        },
        {
          "date": 
... [salida truncada en el informe]
```

## level_c_sp500_report - Nivel C

**Consulta:** Prepara un informe detallado del S&P 500 desde 2020 con crecimiento, volatilidad, maximo drawdown, mejores y peores periodos, y resumen ejecutivo

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| ^GSPC | 3257.85 | 6699.38 | 105.64% | 20.71% | -33.92% | 6978.60 | 2237.40 |

Para ^GSPC, entre 2020-01-02 y 2026-03-16, el precio paso de 3257.85 a 6699.38, con una rentabilidad total de 105.64%. El maximo drawdown fue -33.92% y la volatilidad anualizada aproximada fue 20.71%. Lectura: se incluyen metricas y datos visuales adicionales porque el usuario pide un analisis profesional o multicriterio. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "professional_index_report",
  "level": "C",
  "metrics": {
    "^GSPC": {
      "precio_inicial": 3257.85009765625,
      "precio_final": 6699.3798828125,
      "rentabilidad_total": 1.056380644288128,
      "maximo": 6978.60009765625,
      "minimo": 2237.39990234375,
      "volatilidad_anualizada": 0.20705080195169834,
      "max_drawdown": -0.3392496000265327,
      "mejor_periodo": 0.09515387644904849,
      "peor_periodo": -0.11984055240393443,
      "fecha_inicio": "2020-01-02",
      "fecha_fin": "2026-03-16"
    }
  },
  "chart_data": {
    "close_price": {
      "^GSPC": [
        {
          "date": "2020-01-02",
          "value": 3257.8501
        },
        {
          "date": "2020-07-27",
          "value": 3239.4099
        },
        {
          "date": "2021-02-17",
          "value": 3931.3301
        },
        {
          "date": "2021-09-09",
          "value": 4493.2798
        },
        {
          "date": "2022-03-31",
          "value": 4530.4102
        },
        {
          "date": "2022-10-24",
          "value": 3797.3401
        },
        {
          "date": "2023-05-17",
          "value": 4158.77
        },
        {
          "date": "2023-12-08",
          "value": 4604.3701
        },
        {
          "date": "2024-07-03",
          "value": 5537.02
        },
        {
          "date": "2025-01-28",
          "value": 6067.7002
        },
        {
          "date": "2025-08-20",
          "value": 6395.7798
        },
        {
          "date": "2026-03-16",
          "value": 6699.3799
        }
      ]
    },
    "drawdown": {
      "^GSPC": [
        {
          "date": "2020-01-02",
          "value": 0.0
        },
        {
          "date": "2020-07-27",
          "value": -0.0433
        },
        {
          "date": "2021-02-17",
          "value": -0.0009
        },
        {
          "date": "2021-09-09",
          "value": -0.0096
        },
        {
          "date": "2022-03-31",
          "value": -0.0555
        },
        {
          "date": "2022-10-24",
          "value": -0.2083
        },
        {
          "date": "2023-05-17",
          "value": -0.133
        },
        {
          "date": "2023-12-08",
          "value": -0.0401
        },
        {
          "date": "2024-07-03",
          "value": 0.0
        },
        {
          "date": "2025-01-28",
          "value": -0.0083
        },
        {
          "date": "2025-08-20",
          "value": -0.0112
        },
        {
          "date": "2026-03-16",
          "value": -0.04
        }
      ]
    }
  },
  "volume": {
    "^GSPC": 4538428670.731708
  }
}
```

## stress_visual_qqq_spy_monthly - Nivel C

**Consulta:** Compara QQQ y SPY durante 2024 como si fuera un informe para un cliente no tecnico. Quiero que me muestres los datos exactamente en cuatro bloques: 1) una tabla resumen con rentabilidad total, volatilidad anualizada, maximo drawdown, mejor mes y peor mes; 2) una tabla ranking mensual indicando que activo gano cada mes; 3) datos para una grafica normalizada base 100 de ambos activos; 4) datos para una grafica de drawdown. Cierra con una conclusion clara, sin recomendar comprar ni vender.

### Lo que mostrariamos al cliente

| Activo | Inicio | Fin | Rentabilidad | Volatilidad | Max drawdown | Maximo | Minimo |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 402.59 | 515.61 | 28.07% | 17.96% | -13.56% | 538.17 | 396.28 |
| SPY | 472.65 | 588.22 | 24.45% | 12.61% | -8.41% | 607.81 | 467.28 |

La comparativa ordena mejor a QQQ por rentabilidad historica en el periodo. QQQ: rentabilidad 28.07%, volatilidad 17.96%, drawdown -13.56% | SPY: rentabilidad 24.45%, volatilidad 12.61%, drawdown -8.41%. La correlacion se incluye como contexto para entender si ambos activos se movieron de forma parecida. Lectura: se incluyen metricas y datos visuales adicionales porque el usuario pide un analisis profesional o multicriterio. El analisis es historico y descriptivo; no constituye recomendacion de inversion.

### Datos para visualizacion o trazabilidad

```json
{
  "analysis_type": "stress_visual_client_report",
  "level": "C",
  "metrics": {
    "QQQ": {
      "precio_inicial": 402.5899963378906,
      "precio_final": 515.6099853515625,
      "rentabilidad_total": 0.28073223388992274,
      "maximo": 538.1699829101562,
      "minimo": 396.2799987792969,
      "volatilidad_anualizada": 0.17961377348921978,
      "max_drawdown": -0.1355773890565939,
      "mejor_periodo": 0.03059093002421731,
      "peor_periodo": -0.036076927081440724,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    },
    "SPY": {
      "precio_inicial": 472.6499938964844,
      "precio_final": 588.219970703125,
      "rentabilidad_total": 0.24451492287959642,
      "maximo": 607.8099975585938,
      "minimo": 467.2799987792969,
      "volatilidad_anualizada": 0.12611587893527634,
      "max_drawdown": -0.08405619392423236,
      "mejor_periodo": 0.024865554910313614,
      "peor_periodo": -0.029803487374158943,
      "fecha_inicio": "2024-01-02",
      "fecha_fin": "2024-12-30"
    }
  },
  "chart_data": {
    "normalized_to_100": {
      "QQQ": [
        {
          "date": "2024-01-02",
          "value": 100.0
        },
        {
          "date": "2024-02-05",
          "value": 106.4234
        },
        {
          "date": "2024-03-07",
          "value": 110.6461
        },
        {
          "date": "2024-04-10",
          "value": 108.8875
        },
        {
          "date": "2024-05-13",
          "value": 110.0574
        },
        {
          "date": "2024-06-14",
          "value": 119.0268
        },
        {
          "date": "2024-07-18",
          "value": 119.1013
        },
        {
          "date": "2024-08-20",
          "value": 119.2926
        },
        {
          "date": "2024-09-23",
          "value": 119.9831
        },
        {
          "date": "2024-10-24",
          "value": 122.2882
        },
        {
          "date": "2024-11-25",
          "value": 125.8327
        },
        {
          "date": "2024-12-30",
          "value": 128.0732
        }
      ],
      "SPY": [
        {
          "date": "2024-01-02",
          "value": 100.0
        },
        {
          "date": "2024-02-05",
          "value": 104.2103
        },
        {
          "date": "2024-03-07",
          "value": 108.9199
        },
        {
          "date": "2024-04-10",
          "value": 108.7739
        },
        {
          "date": "2024-05-13",
          "value": 110.2105
        },
        {
          "date": "2024-06-14",
          "value": 114.8376
        },
        {
          "date": "2024-07-18",
          "value": 116.928
        },
        {
          "date": "2024-08-20",
          "value": 118.2059
        },
        {
          "date": "2024-09-23",
          "value": 120.5268
        },
        {
          "date": "2024-10-24",
          "value": 122.5516
        },
        {
          "date": "2024-11-25",
          "value": 126.4212
        },
        {
          "date": "2024-12-30",
          "value": 124.4515
        }
      ]
    },
    "drawdown": {
      "QQQ": [
        {
          "date": "2024-01-02",
          "value": 0.0
        },
        {
          "date": "2024-02-05",
          "value": -0.0013
        },
        {
          "date": "2024-03-07",
          "value": -0.0004
        },
        {
          "date": "2024-04-10",
          "value": -0.0179
        },
        {
          "date": "2024-05-13",
          "value": -0.0074
        },
        {
          "date": "2024-06-14",
          "value": 0.0
        },
        {
          "date": "2024-07-18",
          "value": -0.0467
        },
        {
          "date": "2024-08-20",
          "value": -0.0451
        },
        {
          "date": "2024-09-23",
          "value": -0.0396
        },
        {
          "date": "2024-10-24",
          "value": -0.0212
        },
        {
          "date": "2024-11-25",
          "value": -0.0147
        },
        {
          "date": "2024-12-30",
          "value": -0.0419
        }
      ],
      "SPY": [
        {
          "date": "2024-01-02",
          "value": 0.0
        },
        {
          "date": "2024-02-05",
          "value": -0.0036
        },
        {
          "date": "2024-03-07",
          "value": 0.0
        },
        {
          "date": "2024-04-10",
          "value": -0.0173
        },
        {
          "date": "2024-05-13",
          "value": -0.0043
        },
        {
          "date"
... [salida truncada en el informe]
```
