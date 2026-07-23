# Rebanada 002 — Panel Decorativo · PROPUESTA (pendiente de aprobación de Constantino)

**De:** Nova
**Para:** Constantino
**Fecha:** 2026-07-10
**Estado:** ⏸️ PARQUEADA (2026-07-11) — NO es la rebanada activa.

> **Aclaración de Constantino (2026-07-11):** la rebanada activa de Panel Decorativo es el **cálculo de precio**, destrabado por la **fórmula de segundos de láser** (segundos = f(largo de corte, velocidad); velocidad = f(material, espesor)), que Punto ya retomó. Esta propuesta de "gestión comercial" queda para **después** de cerrar el cálculo de precio. No despachar.

---

## Dónde quedó la Rebanada 1 (completa)

El camino de **crear** un presupuesto de Panel Decorativo está punta a punta y desplegado:

catálogo de patrones (paramétrico Tresbolillo + vectorizados + DXF subidos) → galería visual con thumbnails → página `panel-decorativo` con factores en vivo → descarga del DXF → **persistencia de la Quotation en ERPNext**. Vectorizador v2 y thumbnails cerrados.

**Lo que HOY todavía es débil o no existe** (base de esta propuesta):
- Se puede *crear* una Quotation, pero **gestionar** las ya creadas (buscar, reabrir, editar, reenviar) es fino. Existen endpoints `list_presupuestos` / `get_presupuesto`, pero sin una pantalla de gestión arriba.
- No hay **salida para el cliente** (PDF/impresión del presupuesto con logo, patrón elegido y precio).
- No hay **estados** del presupuesto (borrador / enviado / aprobado) ni forma de marcar uno como aprobado.

## Recomendación: Rebanada 2 = "Gestión comercial del presupuesto"

Cierra el lado **comercial** del punta a punta (crear → gestionar → mandar al cliente → aprobar), 100% dentro de Punto + Vega, **sin tocar MES ni el compilador** (que están en espera por decisión tuya). Es el incremento de mayor valor que no depende de frentes frenados.

### Checklist propuesto

| # | Owner | Ítem | Nota |
|---|---|---|---|
| 1 | Punto | Endpoints `list_presupuestos` con filtros (cliente, fecha, estado) + `get`/`update` para reabrir y editar | reusa lo que ya existe, lo completa |
| 2 | Vega | Pantalla **"Mis presupuestos"**: tabla con búsqueda, abrir, duplicar, editar | entrada natural desde la home |
| 3 | Punto | Campo **estado** en el presupuesto (borrador/enviado/aprobado) + endpoint para cambiarlo | |
| 4 | Vega | Acciones de estado en la UI + badge visual | |
| 5 | Punto | Generar **PDF/print del presupuesto para el cliente** (patrón elegido, medidas, precio, datos de la empresa) | ⚠ ver decisión B |
| 6 | Vega | Botón "Descargar/Imprimir PDF" + "Enviar" desde la pantalla | |

## Decisiones tuyas antes de despachar

- **A. ¿Confirmás el alcance comercial** (gestión + PDF + estados), o preferís que la Rebanada 2 apunte a **producción** (del presupuesto aprobado → archivo de corte definitivo para CypCut + trazabilidad)? El camino de producción es válido pero **cruza MES (Lechu) y el compilador (Nido)**, ambos hoy en espera — habría que reactivar al menos uno.
- **B. PDF para el cliente:** ¿lo querés como print format de ERPNext (rápido, estándar Frappe) o un diseño propio de Panel Decorativo? ¿Qué datos van sí o sí (logo, condiciones, validez del presupuesto)?
- **C. Estados:** ¿alcanzan borrador/enviado/aprobado, o querés alguno más (ej. "en producción", "facturado")? Si sumás "en producción" ya empieza a tocar MES.
- **D. Precios:** los de corte/plegado seguían **sin validar contra la máquina real** (velocidades/tiempos sin fuente). No bloquea esta rebanada (es comercial), pero si vas a mandar PDFs a clientes conviene cerrar ese número antes. ¿Lo agendamos en paralelo?

## Si aprobás
Convierto este checklist en tareas concretas (`PUNTO_TASK_0XX` / `VEGA_TASK_0XX`) con briefs por canal y las despacho. **No toco nada hasta tu OK.**

— Nova
