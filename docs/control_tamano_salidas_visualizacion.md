# Control de tamaño de salidas para interpretación LLM

## Motivo

Las consultas de Nivel B y C pueden producir series temporales extensas para tablas o visualizaciones. Una serie completa resulta útil como artefacto auditable, pero no siempre debe enviarse íntegramente al agente 2: cientos o miles de puntos consumen contexto y pueden superar el límite de tokens del proveedor sin mejorar la explicación final.

El agente 2 necesita:

- métricas principales;
- limitaciones;
- rango temporal;
- tipo de visualización;
- una muestra representativa de la serie;
- referencia al artefacto completo.

No necesita recibir cada observación histórica para redactar una interpretación prudente.

## Aplicación en el flujo implementado

En la arquitectura experimental con codegen se aplican dos medidas:

- `src/llm/prompts.py` pide limitar `chart_data` o `visualization_data` a un máximo de 120 puntos muestreados por serie.
- `src/graph/nodes.py -> _compact_for_interpretation` resume listas y textos extensos antes de llamar al agente 2.

La salida completa permanece registrada en `results/logs/stdout_*.json`.

## Aplicación en la arquitectura objetivo

El criterio continúa siendo necesario cuando el codegen deje de ser el camino principal. En el nuevo flujo:

```text
Agente 1
-> receta JSON
-> motor analítico Python
-> constructor de AnalysisResult
-> agente 2
```

el constructor de `AnalysisResult` deberá:

1. conservar las métricas completas;
2. limitar los puntos incluidos en `visualizations`;
3. registrar el número original de observaciones;
4. conservar la serie completa como artefacto local cuando sea necesario;
5. enviar al agente 2 únicamente la versión compactada.

## Justificación metodológica

Esta decisión mejora:

- eficiencia de contexto;
- estabilidad frente a límites de tokens;
- trazabilidad;
- claridad de la interfaz entre fases;
- comparabilidad entre proveedores LLM.

La compactación no elimina información: separa el artefacto completo utilizado para auditoría de la representación resumida adecuada para interpretación lingüística.
