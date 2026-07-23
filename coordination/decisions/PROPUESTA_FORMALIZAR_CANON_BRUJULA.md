# PROPUESTA — Formalizar el canon de Brújula como DECISIONs

**Estado:** 🟡 PROPUESTA — **NO ejecutada**. Requiere revisión y aprobación de Constantino.
**Autor:** Nova · **Fecha:** 2026-07-19
**Fuente:** `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` + `coordination/research/RELEVAMIENTO_REPOS_HISTORICOS.md` (Orbit)

---

## A. Ya cubierto por DECISIONs vigentes (no hace falta formalizar)

| Regla de Brújula | Ya es |
|---|---|
| 1. ERPNext columna operativa, app Frappe encima | `DECISION_001` |
| 5. CypCut hace nesting — no reimplementar | `DECISION_002` |
| 3. Excel se respeta como pricing humano | `DECISION_003` |
| 2/4. Tango dueño fiscal + maestro de precios | `DECISION_001` + `DECISION_003` (parcial — ver C.4) |

## B. Candidatas a formalizar (reglas concretas de taller, hoy sin DECISION)

| # | Regla | Cita de Brújula | A quién afecta |
|---|---|---|---|
| **007** | **65% de barra → cobrar entera** | "si última barra supera ~65% del largo estándar, sugerir cobrar barra entera" | Gemu (corte lineal) |
| **008** | **Espaciados de lote DXF** | "300mm entre piezas, 500mm entre filas de espesor, etiquetas con espesor y cantidad" | Nido (compilador DXF batch) |
| **009** | **Matriz de decisión de proceso** | "rectángulo sin perforaciones → guillotina; espesor alto → oxicorte; general → láser/plasma" | Punto / Atlas |
| **010** | **14 estados por pieza + Pedido ≠ Lote** | "pedida→cotizada→aprobada→en lote→cortada parcial/completa→pendiente plegado→plegada parcial/completa→observada→lista→entregada parcial→entregada" · "el pedido pertenece al cliente, el lote a producción y mezcla piezas de varios pedidos" | Lechu (MES), Atlas |
| **011** | **Tolerancias CAD + orientación de contornos** | (del repo ORIGINAL, no de Brújula) snap 0.01 / min_seg 0.05 / max_gap 0.10 / epsilon 0.001 mm · outer CCW, holes CW | Punto |

*Nota:* 007–010 son **de Brújula** (canon fundacional, alta confianza). **011 es del repo viejo** — hay que confirmar vigencia contra el motor actual antes de fijarla.

## C. Tensiones detectadas por Nova (requieren decisión de Constantino)

### C.1 ⚠️ "Recurso industrial como unidad económica" vs `DECISION_006`
- **Brújula:** "el sistema **vende** chapa, corte, plegado, metro lineal, tiempo de máquina" (recursos como unidades económicas).
- **DECISION_006:** todo se factura como **UN** artículo "chapa procesada"; hierro cortado/plegado **nunca** se facturan.
- **Lectura propuesta (no contradicción real):** Brújula describe el modelo de **cálculo/costeo**; DECISION_006 describe el modelo de **facturación**. Se desglosa por recurso para *calcular*, se emite un renglón para *cobrar*.
- **Gana:** `DECISION_006` (más reciente y explícita). **Propongo dejar el matiz escrito** en DECISION_006 para que ningún agente lea Brújula y arme renglones por recurso.

### C.2 ⚠️ Regla 6 — "el postprocesador propio hace G-code" vs `DECISION_002`
- **Brújula regla 6:** "El **postprocesador propio** hace G-code — no reimplementar."
- **DECISION_002:** "no implementa nesting, **G-code** ni CAM".
- **Matiz:** el postprocesador propio **existe** (CostADCAM, en `Programas_hechos/`). Brújula no dice "no hay G-code": dice que **ya lo resuelve una herramienta nuestra, fuera de la app**. `DECISION_002` es correcta *para la app Frappe*, pero su redacción puede leerse como "el G-code no es asunto nuestro", y eso es falso.
- **Propongo:** aclarar la redacción de `DECISION_002` — el límite es *la app no reimplementa*, no *el proyecto no tiene*.

### C.3 Regla 4 — "Tango es maestro de precios finales, ERPNext sincroniza copia"
- **Impacto hoy:** Vega está construyendo la página de precios en ERPNext. Si Tango es el maestro, esa página es **copia/consulta**, no origen de verdad.
- **A confirmar con Constantino:** ¿la página de precios **escribe** precios o solo los muestra? Definirlo antes de que Vega cierre.

### C.4 `ezdxf` tras adapter (repo viejo) vs uso directo actual
- Contradicho de hecho. Buena práctica, no urgente. **Gana el actual.**

## D. Source of Truth Matrix (aporte de Nova en el repo ORIGINAL)

**Propuesta: SÍ rescatarla** como doc de referencia en `NexTango`, con dos condiciones:
1. **Quitar** las filas `Nesting plan → SistemaIndustrial Nesting` y `CAM output/GCode → SistemaIndustrial CAM` (contradichas por `DECISION_002` + Brújula 5/6).
2. Conservar lo valioso: frontera explícita ERPNext (cliente operativo, cotización, pedido, item master, stock operativo) vs **Tango** (factura oficial, asiento contable, comportamiento fiscal — *requiere aprobación de Constantino*), y la **regla de conflicto**: si un documento contradice la matriz, el agente **para y produce un decision pack** en vez de improvisar.

Esa regla de conflicto es, en mi opinión, lo más valioso de todo el relevamiento para la operación del equipo.

---

## E. Lo que NO se rescata

- Nesting / CAM / G-code propios dentro de la app → contradicho (`DECISION_002`, Brújula 5/6).
- ERP desde cero → contradicho (`DECISION_001`, Brújula 1).
- **Fórmulas de precio o de plegado**: no existen en los repos viejos. El modelo de precio **no se resuelve** con estos históricos — sigue por el simulador de Punto.
