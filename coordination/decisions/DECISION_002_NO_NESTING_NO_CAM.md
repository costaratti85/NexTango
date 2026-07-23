# Decision 002 - La app no implementa nesting ni CAM

> **Enmendada 2026-07-19 por Nova** (autoridad delegada por Constantino). Motivo: la redacción original decía
> *"SistemaIndustrial no implementa nesting, G-code ni CAM"*, lo que se podía leer como *"el G-code no es asunto nuestro"*.
> Eso es **falso**: el postprocesador propio existe. Ver §2. Alineada con Brújula reglas 5 y 6.

## 1. La app Frappe no reimplementa

**La app Frappe `SistemaIndustrial` NO implementa nesting, toolpaths ni generación de G-code.**

El output de la app son **archivos DXF** con las piezas a cortar y/o plegar, compilados por material/espesor.

- **CypCut hace el nesting** — no se reimplementa (Brújula, regla 5).
- La secuencia de corte y la ejecución en máquina son de herramientas externas.

**Ningún agente debe implementar ni mantener lógica de nesting o toolpaths dentro de la app.**

## 2. El postprocesador propio SÍ existe y es válido

Brújula, regla 6: *"El postprocesador propio hace G-code — no reimplementar."*

El proyecto **sí tiene** un postprocesador propio (**CostADCAM**, en `Programas_hechos/`, código standalone según `DECISION_004`). Es una herramienta **nuestra**, legítima y en uso.

**El límite es de ubicación y de duplicación, no de dominio:**
- ✅ El postprocesador propio genera G-code — es válido y se mantiene.
- ❌ La **app Frappe** no lo reimplementa ni duplica esa lógica.
- ❌ Nadie escribe un segundo generador de G-code (Brújula regla 10: no duplicar lógica entre módulos).

## 3. Frontera resumida

| Etapa | Dueño |
|---|---|
| Geometría / DXF de pieza y de lote | **App SistemaIndustrial** |
| Nesting | **CypCut** (externo) |
| G-code / postproceso | **CostADCAM** (propio, standalone — no en la app) |
| Ejecución en máquina | Máquina / operario |

Relacionado: `DECISION_004` (standalone en git) · Brújula reglas 5, 6 y 10.
