# PUNTO_TASK_025 — Etiqueta de material en DXF: formato abreviado + justificación derecha

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Normal

---

## Cambios requeridos en el DXF generado

### 1. Formato abreviado del material

La etiqueta que define el material/espesor de la fila en el DXF debe usar el formato abreviado que rige en todo el sistema:

| Material | Formato |
|---|---|
| Hierro (DD, LAF, etc.) | `N°{calibre}` — ej: `N°18` |
| Galvanizada | `Galv N°{calibre}` — ej: `Galv N°18` |
| Inox 304 | `Inox 304 {espesor}mm` — ej: `Inox 304 1.25mm` |
| Inox 430 | `Inox 430 {espesor}mm` — ej: `Inox 430 1.25mm` |

La familia del material y si usa calibre o mm debe leerse de `material_table.json`. Si el campo no existe, agregarlo.

### 2. Justificación del texto

El texto de la etiqueta debe cambiar de `justify: "left"` a `justify: "right"`.

---

## Reporte

Dejar reporte en `coordination/reports/PUNTO_TASK_025_REPORT.md` y mensaje en `coordination/channel/Nova/`.
