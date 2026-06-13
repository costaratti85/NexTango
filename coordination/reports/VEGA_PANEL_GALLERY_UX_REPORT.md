# VEGA — Panel Gallery UX Wireframe Report

**Agente:** Vega (UI/UX)  
**Fecha:** 2026-06-12  
**Estado:** Entregado — pendiente validación de Constantino

---

## Archivos entregados

| Archivo | Descripción |
|---|---|
| `coordination/wireframes/panel_gallery_main.html` | Ventana principal del vendedor — flujo de 3 pasos + lista de lotes |
| `coordination/wireframes/panel_gallery_admin.html` | Ventana de administración de patrones |

Ambos son HTML estáticos que se pueden abrir directamente en el browser sin servidor.

---

## Decisiones de diseño

### Navegación entre ventanas

Se optó por una **barra de navegación superior fija** presente en ambas ventanas. El topbar incluye:

- Links de navegación principal (Paneles Decorativos / Corte Lineal / Pedidos) — anticipando que el sistema va a tener más módulos
- En la ventana de vendedor: un botón "⚙ Administrar patrones" en el extremo derecho que abre la ventana admin en una nueva pestaña
- En la ventana admin: un badge "Admin" y un botón "← Volver al catálogo" que regresa al flujo principal

La decisión de abrir el admin en pestaña separada (no modal, no página en la misma tab) es intencional: el vendedor puede tener el catálogo abierto en una pestaña mientras edita patrones en otra.

### Flujo de 3 pasos (ventana principal)

Se implementó como **3 tarjetas (cards) apiladas verticalmente** en lugar de pasos que se ocultan/muestran con transición. Razones:

1. Para el wireframe estático no hay JS funcional, así que mostrar los 3 pasos a la vez permite evaluar todo el flujo en una sola pantalla
2. En implementación, Punto puede elegir entre: (a) mostrar/ocultar con `display:none` y scroll automático, o (b) mantenerlos visibles pero con los pasos 2 y 3 deshabilitados hasta que el anterior esté completo

El **indicador de pasos (stepper)** en la parte superior comunica visualmente en qué etapa está el usuario. Las burbujas tienen tres estados: activo (azul relleno), completado (azul claro con borde), pendiente (gris).

### Tarjetas de patrón

- Tamaño 170px de ancho con thumbnail de 150×150px (según spec)
- Los placeholders usan SVGs inline minimalistas que dan una pista visual del patrón (círculos para tresbolillo, rombos para rombo, etc.) en lugar de cuadrados grises planos — mejora la legibilidad del wireframe y da a Constantino una idea de cómo se verán con imágenes reales
- El estado "seleccionado" usa borde azul + fondo tenue + indicador "✓ Seleccionado" — consistente con el color de acento del sistema
- En el wireframe, Tresbolillo ya aparece preseleccionado para mostrar el estado visual

### Contorno exterior

- "Rectángulo simple" aparece como opción activa (borde + fondo azul)
- Las 3 opciones deshabilitadas tienen `opacity: 0.5` y `cursor: not-allowed` más una etiqueta "Próximamente" en itálica
- Los iconos de contorno son SVGs simples geométricos — suficientes para comunicar la forma sin necesitar assets externos

### Formulario de parámetros

- **Margen mm** tiene su propia fila (no comparte fila con otro campo) para darle visibilidad visual — el brief lo marcó como "importante que sea visible"
- **Modo de distribución** usa un toggle segmentado (dos opciones en una fila, sin radio buttons tradicionales) — más compacto y visualmente claro para una elección binaria
- Los **bloques condicionales** (DXF offset / Tresbolillo params) se muestran ambos en el wireframe con una nota en itálica explicando que son condicionales. El borde punteado y el fondo diferenciado los distingue visualmente del formulario base
- Todos los inputs usan la misma altura y estilo — consistencia visual

### Tabla de lotes

- Columna "Margen" agregada respecto al spec original — parecía importante mostrarla dado que es un parámetro de fabricación clave
- Las filas de ejemplo incluyen datos realistas (materiales, medidas) para que Constantino pueda validar el layout con contenido real
- El botón "GENERAR DXF" está en el extremo derecho de una fila que también muestra el conteo total — le da contexto antes de la acción

### Ventana admin — tabla de patrones

- La columna de preview usa thumbnails de 80×80px con el mismo estilo SVG placeholder que la galería
- Los badges de tipo (Nativo / DXF) y visibilidad (Público / Privado) usan colores semánticos: azul para nativo/sistema, cálido para DXF/usuario, verde para público, naranja para privado
- Tresbolillo no tiene botón "Borrar" — solo "Editar". En su lugar aparece el texto en gris "No se puede borrar" para que quede explícito en el wireframe (en producción podría ser un tooltip)
- Los patrones DXF tienen ambos botones: "Editar" y "Borrar"

### Formulario de carga de patrón

- El campo de archivo usa el patrón "input deshabilitado + botón Examinar a la derecha" — diseño estándar que hace obvio que hay que clickear el botón para seleccionar un archivo
- El bloque condicional de clientes usa fondo amarillo suave + borde punteado naranja — diferente al azul de los bloques condicionales del form principal para que visualmente sean reconocibles como dos tipos distintos de condicionalidad
- **Área de feedback**: se muestran los 3 estados (cargando / éxito / error) apilados en el wireframe, con nota explicando que en producción solo uno será visible. Esto permite evaluar el diseño de los tres estados en una sola revisión

---

## Preguntas para Constantino antes de que Punto implemente

### Críticas (bloquean la implementación)

**P1 — Flujo de pasos: ¿esconder o deshabilitar?**  
¿Los pasos 2 y 3 deben estar ocultos hasta que el anterior se complete, o deben estar visibles pero deshabilitados (greyed out)? Esconder es más limpio; deshabilitar deja ver hacia dónde va el flujo. El wireframe los muestra todos visibles.

**P2 — Campos condicionales: ¿ambos o uno?**  
El wireframe muestra los dos bloques condicionales (DXF offset + Tresbolillo params) simultáneamente con notas. En producción solo uno debe mostrarse según el patrón elegido. Confirmar: ¿si el patrón es Tresbolillo, el bloque DXF offset no aparece? ¿Y viceversa?

**P3 — Offset DXF: ¿va en el admin o en el formulario del vendedor?**  
El offset X/Y del DXF actualmente aparece en ambos lugares: en el admin (al cargar el patrón) y en el formulario del vendedor (paso 3). ¿Es correcto que el vendedor pueda ajustarlo por lote, o el offset es un parámetro fijo del patrón que solo configura el admin?

**P4 — Visibilidad de patrones: ¿quién es "el cliente"?**  
El campo "Código(s) de cliente" en el admin asume que hay un concepto de cliente en el sistema y que el código Tango identifica al cliente. ¿Es así? ¿O la visibilidad privada aún no tiene implementación definida y debería omitirse del wireframe por ahora?

### Importantes (afectan el diseño pero no lo bloquean)

**P5 — Preview de patrón al cargar DXF**  
¿El "preview" que genera el sistema es una imagen raster (PNG/JPG) del DXF, o una visualización vectorial en el browser? Esto afecta cómo se muestra en la tabla de patrones.

**P6 — Columna "Margen" en la tabla de lotes**  
Agregué esta columna porque me pareció fabricación-crítica. ¿La querés o prefieren una tabla más compacta sin ella?

**P7 — Navegación: ¿ventana admin en nueva pestaña o misma pestaña?**  
El wireframe la abre en nueva pestaña (`target="_blank"`). ¿Están de acuerdo con eso o prefieren que sea la misma pestaña con botón "Volver"?

**P8 — ¿Existe ya una URL base para el servidor local?**  
¿El servidor corre en `localhost:8000`, `localhost:5000` u otro puerto? Esto no afecta el wireframe estático pero Punto lo necesita para definir las rutas.

### Menores (se pueden resolver después)

**P9 — Iconos de contorno**  
Los SVGs de los contornos (Bandeja, U, C/Omega) son aproximaciones mías. ¿Tienen referencia visual de cómo son exactamente esas formas en la práctica de la empresa?

**P10 — Nombre del módulo en el topbar**  
Usé "Paneles Decorativos" como nombre de la sección. ¿Es ese el nombre definitivo o puede cambiar?

---

## Lo que NO está en el wireframe (fuera de scope de este entregable)

- Modales de confirmación (ej. confirmar borrado de patrón)
- Estados de error en los inputs del formulario (campo requerido vacío, valor fuera de rango)
- Versión mobile / responsive (el brief dice solo desktop por ahora)
- Integración con el sistema de cotización ERPNext (botón "Generar cotización" posterior al DXF)
- Gestión de usuarios / autenticación (quién tiene acceso al admin)
