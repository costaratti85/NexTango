# DECISION_009 — Matriz de decisión de proceso (guillotina / oxicorte / láser-plasma)

**Fecha:** 2026-07-19 · **Autora:** Nova (autoridad delegada por Constantino)
**Origen:** canon fundacional — `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`, §4 y §3 flujo de guillotina
**Estado:** Vigente · **Afecta a:** Punto (geometría), Atlas (backend), Lechu (MES)

## La regla

> "rectángulo sin perforaciones → **guillotina**; espesor alto → **oxicorte**; general → **láser/plasma**."

Y el flujo de guillotina:
> "Sistema detecta pieza rectangular sin perforaciones → sugiere guillotina → genera tarea → **fuera del lote láser** salvo override humano."

## Cómo aplica

| Condición | Proceso sugerido |
|---|---|
| Rectángulo **sin perforaciones** | **Guillotina** — y **sale del lote láser** |
| Espesor **≥ 19 mm** (3/4") | **Oxicorte** |
| Resto | **Láser / plasma** |

Consecuencia operativa fuerte: una pieza derivada a guillotina **no se compila en el DXF de lote láser** (ver `DECISION_008`), salvo override.

## Es sugerencia, no imposición

Brújula regla 8: **el sistema sugiere, el humano decide, el sistema audita.** El override humano es explícito en el canon para el caso de la guillotina. Todo override queda trazado (regla 9: quién, cuándo, qué, desde qué rol).

## Umbral de oxicorte: **19 mm (3/4")** ✅ DEFINIDO

**Fuente:** definición de **Constantino** (2026-07-19), criterio de taller. **No** proviene de Brújula — Brújula decía solo "espesor alto", sin número. Este es el número.

- **Espesor ≥ 19 mm (3/4") → oxicorte.**
- Por debajo de 19 mm → láser/plasma (según el resto de los criterios).
- El valor **19 mm es parametrizable**, no hardcodeado, y la sugerencia es **overrideable** como todo el resto del canon.

Con esto la matriz de proceso queda **completa**: ya no hay ramas inactivas ni pendientes de definición. Queda levantada la instrucción anterior de "no implementar la rama de oxicorte" — ahora sí se implementa, con este valor.

## Historial

- **2026-07-19** — creada por Nova a partir del canon de Brújula, con el umbral de oxicorte **pendiente** (Brújula no lo especificaba).
- **2026-07-19** — Constantino define **19 mm (3/4")**. Matriz completa.
