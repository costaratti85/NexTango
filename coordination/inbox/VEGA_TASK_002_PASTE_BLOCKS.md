# VEGA_TASK_002 — Bloques copy-paste para Presupuesto y OT

**Para:** Vega  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta — hace el sistema operativo desde hoy

---

## Objetivo

En la pantalla de resultados del panel decorativo, agregar dos secciones con bloques de texto listos para copiar y pegar en los documentos de trabajo existentes (presupuesto Excel y orden de trabajo).

---

## Bloque 1 — Para el Presupuesto

**Dónde se pega:** celda B25 del archivo `PRESUPUESTOS 1.XLS`  
**Formato:** tab-separado, una fila por ítem

```
{cant}[TAB]{descripcion}[TAB][TAB][TAB]{precio}
```

- B → cantidad
- C → descripción (D y E quedan vacíos — merged cells en el template)
- F → precio SIN IVA

**Descripción:**
```
Panel "{patron}" / {ancho} x {alto} / en {material_formateado}
```

**Formato del material:**
- Hierro (DD, LAF, etc.): `N°{calibre}` — ej: `N°18`
- Galvanizada: `Galv N°{calibre}` — ej: `Galv N°18`
- Inox 304: `Inox 304 {espesor}mm` — ej: `Inox 304 1.25mm`
- Inox 430: `Inox 430 {espesor}mm` — ej: `Inox 430 1.25mm`

La familia del material (hierro / galvanizada / inox304 / inox430) y si usa calibre o mm debe venir del `material_table.json`. Si no está ese campo, agregarlo.

**Ejemplo de salida:**
```
2	Panel "Philo" / 650 x 650 / en N°18			1250.50
```

---

## Bloque 2 — Para la Orden de Trabajo (OT)

**Dónde se pega:** columnas B–C de la hoja `ot1` del mismo archivo  
**Formato:** tab-separado, una fila por ítem

```
{cant}[TAB]{descripcion_ot}
```

**Descripción OT** = misma que presupuesto + nombre del DXF al final:
```
Panel "{patron}" / {ancho} x {alto} / en {material_formateado} / [{patron}.dxf]
```

**Ejemplo:**
```
2	Panel "Philo" / 650 x 650 / en N°18 / [Philo.dxf]
```

---

## UI

En la pantalla de resultados, agregar debajo del resultado actual:

1. **Sección "Para el Presupuesto"**
   - Textarea o bloque de texto con el contenido tab-separado
   - Botón "Copiar" que copia al portapapeles
   - Nota breve: "Pegar en celda B25 del presupuesto"

2. **Sección "Para la OT"**
   - Ídem
   - Nota: "Pegar en columna B de la OT"

El estilo debe ser consistente con el resto de la app (`_COMMON_CSS`).  
Usar `navigator.clipboard.writeText()` para el botón de copiar.

---

## Datos disponibles en el resultado actual

El motor ya entrega:
- Nombre del patrón
- Dimensiones (ancho × alto)
- Material y espesor
- Cantidad
- Precio calculado (SIN IVA)

---

## Archivos a modificar

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
- `Programas_hechos/Panel Decorativo/material_table.json` (si falta campo familia/calibre)

## Reporte

Dejar reporte en `coordination/reports/VEGA_TASK_002_REPORT.md` y mensaje en `coordination/channel/Nova/`.
