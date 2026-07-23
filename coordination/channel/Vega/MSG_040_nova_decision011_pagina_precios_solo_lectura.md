# MSG_040 — Nova → Vega

**De:** Nova
**Para:** Vega
**Fecha:** 2026-07-19
**Asunto:** 🔴 DECISIÓN — la página de precios **MUESTRA, no escribe**. Aplicar YA (antes de cerrar)
**Prioridad:** urgente — estás construyéndola ahora

---

Decisión tomada: **`DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`**. Te llega ahora justamente para que no la descubras después de cerrar.

## Qué cambia

**Brújula regla 4 (canon fundacional): "Tango es maestro de precios finales — ERPNext sincroniza copia."**

La cadena de verdad es: **Excel (pricing humano) → Tango (maestro) → ERPNext (copia)**.

Entonces la página:
- ❌ **NO edita precios de venta** de artículos.
- ❌ **NO escribe hacia Tango**, por ningún camino.
- ✅ **Muestra** los precios sincronizados, **por familia** (como definió Constantino), en **solo lectura**.
- ✅ **Muestra la fecha de la última sincronización.** Esto no es opcional: un precio en pantalla sin fecha de sync engaña al que lo lee.

## La distinción que sí o sí tenés que respetar

Hay **dos cosas** que se llaman "precio" y **no son lo mismo**:

| | Dueño | ¿Editable? |
|---|---|---|
| **Precio de venta de artículo** | **Tango** | ❌ solo lectura |
| **Parámetros de costeo** (precio por segundo de láser, coeficientes, factores) | **nuestros** — no existen en Tango | ✅ sí, en su DocType |

Que la página sea de solo lectura **no bloquea** editar los parámetros de costeo — esos van en su propio lugar, no acá.

## Por qué lo decido así

Constantino pidió recuperar "la página donde anotábamos los precios" de la versión vieja. Pero **la arquitectura cambió**: en aquel entonces no había maestro; hoy el maestro es Tango. Una página que escriba precios crea una **segunda fuente de verdad** y desincroniza el sistema de la facturación real — en silencio, y se descubre tarde.

Si hace falta corregir un precio, el camino es **Excel → Tango → sync**.

## Si no cierra

Si al implementarlo ves que Constantino **necesita** editar precios desde ahí para que la página le sirva, **NO lo implementes igual**: eso es cambio de criterio de negocio y no lo decido yo. **Pará y escribime** — lo escalo a Constantino con el costo puesto sobre la mesa.

Aplica también la nueva **`coordination/reference/SOURCE_OF_TRUTH_MATRIX.md`** (lectura obligatoria, abajo).

— Nova
