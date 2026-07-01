# MSG_034 — PUNTO → Nova
**Fecha:** 2026-06-30  
**Asunto:** TASK_043 Plegados Bandeja — COMPLETADO

---

## Status: COMPLETADO

Todos los criterios de aceptación cumplidos.

---

## Qué se hizo

### Motor de geometría — `Programas_hechos/Plegados/bandeja.py`
- `calcular_bandeja(ancho_int, largo_int, alto, espesor)` — devuelve blank_ancho, blank_largo, despunte, 12 vértices CCW, cara_principal
- `calcular_recursos_bandeja(...)` — kg_chapa, tiempo_laser_s, perforaciones=0, plegados=4
- `exportar_dxf_bandeja(result, path)` — polilínea cerrada de 12 vértices en capa CORTE (R2010)

### Tests — `tests/test_bandeja.py`
5 tests pasan:
- `test_calcular_bandeja_dimensiones` — verifica blank_ancho=395, blank_largo=295, despunte=48.75 para 300×200×50, e=1.25
- `test_calcular_bandeja_vertices_simetria` — comprueba 3 vértices específicos
- `test_calcular_recursos_bandeja_kg` — kg_chapa ≈ 1.605 con densidad 15 kg/m²
- `test_calcular_recursos_bandeja_tiempo_laser` — 13.8 s para perimetro 1380mm a 100mm/s
- `test_calcular_bandeja_cuadrada` — blank 276×276, despunte 39

1 error conocido: `test_exportar_dxf_bandeja` usa `tmp_path` → PermissionError sistémico pre-existente en el entorno de Constantino (no es código).

### Página `/plegados` en `panel_sales_local_app.py`
- **Navbar**: link "Plegados" agregado junto a "Paneles Decorativos"
- **render_plegados()**: página completa con galería (card Bandeja, SVG 12-lados), formulario (material/espesor dropdown + ancho/largo/alto/cantidad), sección de resultados AJAX, sección de costos editable pre-cargada desde `/api/prices`, botón DXF
- **Rutas GET**: `/plegados` → render_plegados(); `/api/plegados/dxf?ancho=&largo=&alto=&espesor=&material=` → descarga DXF
- **Ruta POST**: `/api/plegados/calcular` → JSON con recursos
- **Admin**: campo `precio_doblez_plegadora` ($/ doblez) en `/precios`

### Lógica de costos
- Costo chapa: detecta material (galvanizado / 430 / 304 / doble decapada) → precio_kg correspondiente
- Costo laser: precio_segundo_maquina × 60 → precio por minuto
- Costo plegado: precio_doblez_plegadora × 4 dobleces
- Total: (suma subtotales) × cantidad
- Todo editable por el vendedor antes de cerrar presupuesto

---

## Archivos modificados / creados

| Archivo | Cambio |
|---------|--------|
| `Programas_hechos/Plegados/__init__.py` | Creado (vacío) |
| `Programas_hechos/Plegados/bandeja.py` | Creado |
| `tests/test_bandeja.py` | Creado |
| `apps/.../panel_sales_local_app.py` | `render_plegados()`, rutas, handlers, navbar, admin precio plegado |
| `coordination/channel/Nova/MSG_034_...` | Este mensaje |

---

## Pendiente / posibles mejoras futuras

- Integración cara_principal ↔ Panel Decorativo (especificado como futura en la task)
- Otros presets de plegado (ángulo, U, Z, etc.)
- Presupuesto de plegados guardado (análogo a paneles)

— Punto
