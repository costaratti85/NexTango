> 📗 **NOTA 2026-07-19 — este documento tenía razón.** El banner de corrección genérico que llevaba antes **sobrecorregía** y fue reemplazado por esta nota.
>
> El flujo de OCR descrito acá es **correcto** y coincide con el **modelo definitivo de fuentes de verdad** (Constantino, *"así va a ser"*): **catálogo/artículos → TANGO** · **stock → ERPNext** · **precios → EXCEL**.
>
> - *"si es nuevo: agregar a **Tango**"* → ✅ correcto: Tango es máster del **catálogo**.
> - *"stock a **ERPNext**"* → ✅ correcto.
> - *"precio a **Excel** → pricing en Excel"* → ✅ correcto: Excel es máster de **precios**.
> - *"→ precios a Tango"* → ✅ correcto **como destino** (`Excel → Tango`, para facturar desde ahí). Nunca al revés.
>
> De hecho **`docs/05_OCR_SUPPLIERS_FLOW.md` fue el documento donde el modelo correcto estaba bien especificado desde el principio** — y quedó sin leer. Ver `DECISION_011` §7.

---

# DECISION_016 — Rol de OCR de Proveedores (contrato fijado, activación diferida)

**Fecha:** 2026-07-19 · **Confirmado por:** Constantino — *"va a ser una parte CLAVE de nuestro programa"*
**Registrado por:** Nova · **Estado:** Vigente — rol con dueño, **activación diferida**

---

## 1. Deja de ser un hueco

El cotejo de roles marcaba el OCR de proveedores como **hueco sin dueño**, y yo había propuesto dejarlo así por no haber frente activo.

**Constantino lo corrigió:** es **parte clave** del programa. Entonces tiene rol y contrato, aunque se active más adelante.

## 2. El rol

**OCR = ingreso automático de facturas de proveedores al sistema.**

Flujo definido en Brújula (§3):

> "Factura → **OCR QR** → identifica proveedor → **recuerda posición de campos** → OCR de artículos → si es nuevo: agregar a **Tango** → si existe: **stock a ERPNext** + **precio a Excel** → pricing en Excel → precios a Tango."

Dos piezas que vale destacar del canon:
- **Identificación por QR** — el proveedor se reconoce por el QR fiscal, no por texto libre.
- **Memoria de layout por proveedor** — "recuerda la posición de los campos": cada proveedor tiene su formato y el sistema lo aprende una vez.

## 3. Base existente — NO se arranca de cero

Ya hay trabajo hecho, y es sustancial:

- **Código:** `Programas_hechos/OCR Proveedores/` — con varias iteraciones (`facturas_multiples_a_tango_v4/v6/v8`, `analizador_tablas_facturas.py`, `lector_espacial_facturas_tango.py`, `generar_articulos_tango.py`, `api.py`).
- **Sesión satélite "OCR Mercadolibre"** — contexto acumulado.

**Primera tarea cuando se active:** relevar y consolidar esa base **antes** de escribir nada nuevo. Hay múltiples versiones del mismo programa; hay que determinar cuál es la buena. Aplica `DECISION_004` (standalone en `Programas_hechos/`).

## 4. Fronteras — 🔴 zona sensible

El OCR **escribe en Tango** (artículos nuevos) y en **stock de ERPNext**. Toca la `SOURCE_OF_TRUTH_MATRIX` en su zona roja.

| Acción | Regla |
|---|---|
| Crear artículo en **Tango** | 🔴 requiere **aprobación de Constantino** — Tango es dueño fiscal |
| Stock a **ERPNext** | ✅ ERPNext es dueño del stock operativo |
| Precio a **Excel** | ✅ `DECISION_003` — Excel es el pricing humano |
| Escribir **precios de venta** directo | ❌ **NO** — Excel → Tango → ERPNext (`DECISION_011`) |

Y por Brújula regla 8: **el OCR sugiere, el humano confirma.** Ninguna factura entra al sistema sin validación humana — un error de lectura que se propaga solo a stock y a precios es de los que se descubren tarde y caros.

## 5. Dueño

**Agente satélite propio: `OCR`.** No se cuelga de Tango (que es CRM/integración fiscal) ni de Atlas (backend): tiene tecnología, base de código y ciclo de vida propios.

## 6. Estado: activación diferida

**No es el sprint actual.** El foco sigue siendo Panel Decorativo / precio.

Lo que queda fijado hoy: **el rol, el dueño, el flujo canónico, la base existente y las fronteras**. Cuando Constantino lo active, no se re-deriva nada.

---

> 📗 Ver la nota del encabezado: el flujo de OCR de este documento **es correcto** y coincide con el modelo definitivo de fuentes de verdad (catálogo → Tango · stock → ERPNext · precios → Excel).