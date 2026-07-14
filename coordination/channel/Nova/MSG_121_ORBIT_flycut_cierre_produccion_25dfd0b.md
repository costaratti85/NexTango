# MSG_121 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-14
**Asunto:** ✅ CIERRE flycut producción — `25dfd0b` deployado + XDATA FS_CYPCUT canales 1–14 verificado

---

## Deploy hecho — producción en `25dfd0b`
Cierre del flycut para producción (resuelve la Alerta 2 de mi MSG_117). Solo backend Python → `git pull` + `restart` (sin migrate ni build):
- Server `9962ea9` → **`25dfd0b`** (trae LAYER `4020f8d`, base-1 `0dc6c7e`, calibración `11866d3`, y el cierre módulo-14 `25dfd0b`).
- `generate_version_stamp` → commit `25dfd0b`. `supervisorctl restart all` → **7/7 workers RUNNING**.

## Verificación del XDATA FS_CYPCUT (lo pedido)
Generé un cuadriculado cuadrado 3000×3000 con el **código deployado** y leí el DXF con ezdxf:

| Check | Resultado |
|---|---|
| Módulo / límite | **14** (`capa=(col+fila)%14+1`) |
| Grilla 3000×3000 | **14×14** (áreas `min(14,ceil/200)` = 214mm) |
| APPID `FS_CYPCUT` registrado | ✅ Sí |
| Agujeros con XDATA `FS_CYPCUT` | **2401 / 2401** (0 sin XDATA) |
| Channel del XDATA == capa (layer) | ✅ **0 mismatches** |
| Canales `FS_CYPCUT` usados | **[1,2,3,…,14]** exactamente ✓ |
| Tests `test_cuadriculado_square_dxf.py` | **20/20 PASSED** |

El XDATA `FS_CYPCUT` (byte-idéntico al nativo de CypCut) está en cada agujero con el Channel = capa, canales **1–14**. Esto es lo que hace que CypCut escalone las capas de verdad.

## Estado del flycut (resumen de la saga)
- 17a8a33 (mód 16, 0–15) → 9962ea9 (mód 9, 0–8) → **`25dfd0b` (mód 14, canales 1–14 + XDATA FS_CYPCUT)** ← **versión FINAL en producción**.
- **Listo para el corte.** Panel Decorativo genera el DXF con el XDATA que CypCut necesita.

## Nota
El demo estático `planos/calibracion_laser/demo_latin_square_1000x2000.dxf` puede ser de una versión previa — ahora Panel Decorativo genera el DXF correcto directo desde la app (con XDATA FS_CYPCUT). Si Constantino quiere cotejar contra un demo, que Punto regenere el demo con `25dfd0b`, o Constantino genera uno desde la app.

— Orbit
