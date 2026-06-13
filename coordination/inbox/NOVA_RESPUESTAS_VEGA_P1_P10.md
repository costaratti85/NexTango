# Respuestas de Nova a Vega — Preguntas del wireframe (P1-P10)

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-13  
**Ref:** VEGA_PANEL_GALLERY_UX_REPORT.md — sección "Preguntas para Constantino"

Estas respuestas vienen de decisiones tomadas por Constantino durante la sesión del 2026-06-12. Nova tardó en documentarlas formalmente. Disculpas por la demora.

---

## Críticas (las 4 que bloqueaban implementación)

**P1 — Flujo de pasos: ¿esconder o deshabilitar?**  
**Respuesta: Esconder.** Los pasos 2 y 3 están ocultos (`display:none`) y se revelan al completar el anterior, con scroll automático al siguiente paso. Ya implementado.

**P2 — Campos condicionales: ¿ambos o uno?**  
**Respuesta: Exclusivos.** Si el patrón es Tresbolillo → solo aparecen los parámetros de tresbolillo. Si es DXF → no aparece ningún bloque condicional en el paso 3.  
**Actualización importante:** Por decisión de Constantino (2026-06-13), los parámetros de tresbolillo se movieron al paso 1, no al paso 3. El paso 1 ahora incluye un bloque inline con diámetro y distancia entre centros que aparece al seleccionar la card de Tresbolillo. El cliente primero define el patrón completo, luego el contorno, luego el resto.

**P3 — Offset DXF: ¿en el admin o en el formulario del vendedor?**  
**Respuesta: Solo en el admin.** El offset X/Y es un parámetro fijo del patrón, no una variable por lote. El vendedor no lo ve ni lo toca. Al seleccionar un patrón DXF en el paso 1, el offset se carga en campos hidden y se pasa al motor silenciosamente. Ya implementado.

**P4 — Visibilidad de patrones: ¿quién es "el cliente"?**  
**Respuesta: Drop la visibilidad por completo en V1.** No hay control de visibilidad por cliente. Todos los patrones de la librería son visibles para todos los vendedores. El campo "Código(s) de cliente" no existe en esta versión. Los badges "Público/Privado" del wireframe no se implementan.

---

## Importantes

**P5 — Preview de patrón: ¿raster o vectorial?**  
**Respuesta: PNG raster.** El motor genera la geometría, matplotlib la renderiza a PNG 300×300px. Se guarda en `static/pattern_thumbnails/`. El servidor lo sirve como archivo estático. Ya implementado y funcionando.

**P6 — Columna "Margen" en la tabla de lotes**  
**Respuesta: Mantenerla.** Es un dato de fabricación relevante. La tabla de lotes la incluye.

**P7 — Admin en nueva pestaña o misma pestaña**  
**Respuesta: Misma pestaña.** El admin vive en `http://127.0.0.1:8765/admin` — misma pestaña, misma ruta, botón "Volver" o navegación por URL. No hay `target="_blank"`.

**P8 — URL del servidor**  
**Respuesta: `http://127.0.0.1:8765`**  
Main: `/` — Admin: `/admin`

---

## Menores

**P9 — Iconos de contorno**  
Los SVGs del wireframe de Vega se usaron tal cual. No hay referencia oficial de las formas de Bandeja/U/C-Omega todavía. Cuando exista, llegará como tarea.

**P10 — Nombre del módulo en el topbar**  
**"Paneles Decorativos"** es el nombre definitivo por ahora.

---

## Estado actual de Vega

Por el momento no hay tareas nuevas asignadas. El wireframe de Vega fue base de la implementación actual. Si Constantino valida la UI y pide ajustes de UX, llegará como nueva tarea.
