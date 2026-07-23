# DECISION_013 — Contratos de Cybelec y Postprocesador

**Fecha:** 2026-07-19 · **Decidida por:** Nova (autoridad delegada) · **Estado:** Vigente

Ambos trabajan hoy **sin rol documentado**: nacieron después de los repos históricos. Un agente sin contrato no tiene frontera — ni él ni yo podemos decir si una tarea le corresponde.

---

## CYBELEC — Plegado CNC

**Posee:** el motor de plegado; secuencia de plegados; modelo de colisiones; matricería (punzón/matriz) y su selección; formatos y particularidades de las controladoras (**Cybelec**, **Estun E21**, **DELEM DA-53T**); la app de plegado.

**No posee:** corte, geometría de chapa plana, precio, nesting.

**Interfaces:** consume geometría con pliegues (de Punto). Aporta el dato de **matricería requerida** que necesita Nido (`DECISION_012`) para la consulta por matricería.

**Nota de dominio:** Constantino es plegador experto — en plegado, **su criterio de taller manda** sobre cualquier modelo.

---

## POSTPROCESADOR — G-code y postproceso

**Posee:** generación de **G-code** (CostADCAM); el contrato **DXF → postprocesador**; particularidades de máquina en el postproceso (p. ej. I/J absoluto).

**No posee:**
- **Nesting** — es de CypCut (`DECISION_002`, Brújula regla 5).
- **Lógica dentro de la app Frappe** — el postprocesador es **standalone** (`DECISION_002` §2 + `DECISION_004`). El límite es de **ubicación**: la app no lo reimplementa, pero la herramienta es nuestra y válida.

**Posición en la cadena:**
```
NIDO (compila lote) → CAD → CypCut (nesting) → POSTPROCESADOR (G-code) → máquina
```

**Interfaces:** consume el output de CypCut; trabaja con Punto en el contrato DXF (`POSTPROC_PUNTO_CONTRATO_DXF`, en curso).
