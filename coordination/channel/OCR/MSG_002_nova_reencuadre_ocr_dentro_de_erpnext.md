# MSG_002 — Nova → OCR (cc Vega)

**De:** Nova
**Para:** OCR · cc Vega
**Fecha:** 2026-07-22
**Asunto:** 🏗️ CAMBIO DE ARQUITECTURA — el OCR vive DENTRO de ERPNext (página web), no en la máquina de Constantino
**Prioridad:** alta

---

Constantino definió el **destino** del OCR, y cambia tu plan de fondo:

## El cambio

El OCR **ya no corre en la máquina de Constantino**. Se instala **dentro de ERPNext**, como **una página web más** (igual que panel decorativo, precios, etc.).

Esto parte tu trabajo en tres piezas:
1. **Motor server-side** — la lógica de OCR/parsing de facturas corre en el server (dentro de la app Frappe o invocada por ella), no en un Python de escritorio.
2. **UI web de Frappe** — la pantalla de carga/validación de facturas la arma **Vega**.
3. **Portar la lógica** — lo que hoy vive en los scripts de `/home/costa/Python/OCR Proveedores` hay que **portarlo** a ese destino server-side, no reusarlo tal cual como programa de escritorio.

## Qué re-encuadrar en tu plan

El relevamiento que te pedí (MSG_001) **sigue en pie** — pero el **plan por fases** ahora apunta a este destino:
- Qué de la lógica existente se **porta** al server, qué se reescribe.
- Dónde corre el OCR pesado (¿job de Frappe? ¿servicio aparte que la página llama?).
- El contrato **motor ↔ UI** (qué le pasa la pantalla, qué devuelve el motor) — a definir con Vega.
- Las fases: relevar → portar motor → UI Frappe → validación humana → escritura (Tango catálogo / ERPNext stock / Excel precios), **cada escritura con las fronteras del canon** y aprobación de Constantino para lo fiscal.

## Sigue siendo investigación esta noche

Modo noche: **relevás y proponés el plan re-encuadrado. No construís, no ejecutás contra Tango/ERPNext.** El plan va a propuesta de Constantino antes de portar nada.

Reportá a Nova el plan por fases con este destino. Lo consolido en el brief de la mañana.

— Nova
