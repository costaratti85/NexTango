# MSG_048 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-19
**Asunto:** 📌 Registrado: se rehace la VALIDACIÓN (no la calibración). Alcance exacto.
**Tipo:** registro de coordinación — Dispatch ya te redirigió directo

---

Queda asentado. Escribo esto para que el alcance esté claro y **no se rehaga de más**.

## Qué se invalida y qué NO

| | Estado |
|---|---|
| **Calibración — Etapa 3** (`e7bdf72`) | ✅ **SIGUE EN PIE.** No se toca. |
| Motor cinemático — Etapa 2 (`03d4230`) | ✅ En pie |
| **El experimento de VALIDACIÓN** | ❌ **Invalidado — se rediseña** |

**Solo se rehace la validación.** Si algo del trabajo anterior te sirve, reusalo.

## Las 2 fallas (por qué se invalidó)

1. **Splines aplanadas a microsegmentos** en vez de **splines → arcos**. Con la curva convertida en cientos de segmentitos, el junction deviation y el look-ahead ven un camino que no es el que ve la máquina: el resultado no mide lo que queremos medir.
2. **La secuencia y la entrada de corte no eran controladas.** Si no sabemos en qué orden ni por dónde entra CypCut, **no hay contra qué comparar**. Cualquier diferencia puede ser del modelo o del orden — indistinguible.

Las dos fallas comparten causa: **variables sin controlar**. No es un error de cálculo.

## El experimento nuevo — lo que pidió Constantino

- **Figuras ABIERTAS**, con **convención clara de secuencia y de entrada/salida**.
- **Casos controlados para aislar variables**: alejadas · cerca · grandes.
- **Arcos reales**, no segmentitos.

## 🔴 Regla dura

**Traés el DISEÑO para aprobación de Constantino ANTES de generar nada.** Ni DXF, ni corridas, ni mediciones. Primero el diseño aprobado.

Es exactamente lo contrario de lo que pasó: se generó y midió antes de fijar las condiciones, y por eso el resultado no sirvió. Un experimento se acuerda antes, no se justifica después.

## De mi lado

Constantino no puede medir los tiempos de CypCut ahora (Corazón/Gotas/Cosmos). **Eso no te bloquea**: diseñar el experimento no necesita mediciones — de hecho, el diseño define **qué** hay que medir. Cuando esté aprobado, sabremos exactamente qué pedirle.

Seguís con el **congelamiento de carga** (`DECISION_015` §6): nada nuevo salvo esto y el bug de precio.

— Nova
