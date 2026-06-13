# Tarea para Vega — Diseño UX: módulo Paneles Decorativos V1

**De:** Nova  
**Fecha:** 2026-06-12  
**Prioridad:** Alta — define el flujo que Punto va a implementar  
**Entrega esperada:** Wireframes o mockup HTML del flujo completo

---

## Contexto

El módulo de Paneles Decorativos está siendo rediseñado desde cero. La arquitectura fue definida por Constantino el 2026-06-12. Lo que existe hoy (`panel_sales_local_app.py`) es un prototipo funcional que va a ser reemplazado por este diseño.

**Usuarios V1:** vendedores internos, desktop, sin portal cliente.

---

## Flujo definitivo — tres pasos

### Paso 1 — Galería de patrones

El vendedor elige el patrón perforado visualmente, con los ojos.

- Grilla de tarjetas, una por patrón
- Cada tarjeta muestra: imagen/preview del patrón + nombre
- Al hacer clic en una tarjeta, queda seleccionada y se avanza al paso 2
- El Tresbolillo es una tarjeta más en la galería. Su imagen es un thumbnail pre-generado mostrando el patrón hexagonal a modo de ejemplo. Al seleccionarlo, en el paso 3 aparecen los campos de diámetro y distancia entre centros (únicos parámetros que lo definen). Los patrones DXF no tienen esos campos.
- Si la librería tiene un solo patrón (caso del primer uso), la galería muestra una sola tarjeta. El diseño debe verse bien con 1 tarjeta y también con 20.
- **No hay toggle "¿Perforar Sí/No"** — entrar a este módulo implica que se quiere perforar.

### Paso 2 — Contorno exterior

El vendedor elige la forma de la pieza.

- V1 muestra una sola opción activa: **"Rectángulo simple"** (chapa plana)
- Las opciones de presets plegados (bandeja, U, C, omega) se ven en la grilla pero en estado *deshabilitado* o *"próximamente"* — para que el vendedor entienda que ese módulo existe pero aún no está activo
- Si el vendedor elige "Rectángulo simple", pasa al paso 3 inmediatamente

### Paso 3 — Parámetros

Formulario con los datos concretos de la pieza.

Campos siempre presentes:
- Ancho mm / Alto mm
- Cantidad
- Margen mm (borde sin perforar)
- Material
- Espesor mm

Campos condicionales — solo si el patrón elegido es Tresbolillo:
- Diámetro agujero mm
- Distancia entre centros mm

Campos condicionales — solo si el patrón elegido es DXF:
- Offset X mm / Offset Y mm (cargados automáticamente al elegir el patrón, editables)

Modo de distribución (siempre presente):
- "Figuras completas centradas" vs "Cortar en borde" (dos opciones, una activa)

Al final: botón **AGREGAR A LA LISTA** — acumula esta configuración en una tabla de lotes pendientes.

### Lista de lotes + GENERAR DXF

Abajo del formulario (o en panel lateral):
- Tabla de lotes acumulados: patrón | contorno | dimensiones | cantidad
- Opción de eliminar un lote
- Botón **GENERAR DXF** — ejecuta el motor para todos los lotes, descarga el archivo

---

## Qué necesita Vega entregar

Un mockup HTML estático o wireframe con:
1. Vista de la galería (paso 1) con al menos 4 tarjetas de ejemplo
2. Vista del selector de contorno (paso 2) con Rectángulo activo y 2-3 presets deshabilitados
3. Vista del formulario de parámetros (paso 3) en los dos casos: Tresbolillo y DXF
4. Vista de la tabla de lotes con el botón GENERAR DXF

No hace falta que el HTML sea funcional — es para que Constantino lo valide visualmente antes de que Punto lo implemente.

---

## Lo que no necesita diseñar Vega todavía

- El módulo de Presets de Plegados (separado, futuro)
- El portal de clientes
- La integración con piezas plegadas como contorno (conexión entre módulos, futuro)
- Gestión de la librería de patrones (agregar/borrar patrones) — eso vive en un panel de administración separado, no en el flujo de venta

---

## Reportar en

`coordination/reports/VEGA_PANEL_GALLERY_UX_REPORT.md`

Incluir: mockup o ruta al HTML, y las decisiones de diseño que tomaste que merezcan validación de Constantino.
