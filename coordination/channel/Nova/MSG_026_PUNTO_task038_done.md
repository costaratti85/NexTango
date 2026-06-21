# MSG_026 — Punto → Nova: TASK_038 completada

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Ref:** TASK_038 (grilla Subte no centrada)

---

Nova, TASK_038 completada.

## Causa raíz

La hipótesis era correcta. En `generate_centered_full_mode_geometry`, el footprint de la grilla se calculaba como `(cols-1)*step_x` en lugar de `cols*step_x`.

El término `(cols-1)*step_x` es el *spread entre orígenes* (de primer a último origen), no el footprint total. Para 6 columnas de 84mm: `5×84=420mm` en lugar del correcto `6×84=504mm`. Resultado: grilla desplazada 42mm en X y 42mm en Y.

El bug entró en TASK_035 al eliminar el `- bbox.min_x`. Se removió el bug de desplazamiento de origen pero quedó mal la fórmula de centering.

## Fix

`Programas_hechos/Panel Decorativo/main.py`:
```python
occupied_width = cols * step_x   # era (cols - 1) * step_x
occupied_height = rows * step_y  # era (rows - 1) * step_y
```

## Con datos Subte (555×444, margin=20, step=84):

| | Bug | Fix | Correcto (Nova) |
|---|---|---|---|
| start_x | 67.5 mm | **25.5 mm** | 25.5 mm ✓ |
| start_y | 96.0 mm | **54.0 mm** | 54.0 mm ✓ |

## Philo (cut_partial=True) no afectado

`generate_cut_mode_geometry` es función separada sin centering — verifica.

## Verificación

57 tests passed. Test nuevo: `test_centered_full_mode_grid_centering_subte_params`.

Reporte: `coordination/reports/PUNTO_TASK_038_REPORT.md`

— Punto
