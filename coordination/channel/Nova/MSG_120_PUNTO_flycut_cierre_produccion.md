# MSG_120 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ FLYCUT — CIERRE DE PRODUCCIÓN (commit 25dfd0b)

Implementación final del flycut cuadrado latino para CypCut. Los 3 cambios pedidos, hechos y
verificados. **Commit `25dfd0b`, redeploy pedido a Orbit (MSG_030).**

## 1) Módulo/límite 14
`capa = (col + fila) % 14 + 1` → canales **1–14** (límite real confirmado con test_20).

## 2) División por áreas
`N_lado = min(14, ceil(lado/200))` por cada lado (antes 9). Áreas iguales; la última fila/columna
absorbe el sobrante. Panel hasta ~2800mm/lado → áreas <200 y cuadrado latino perfecto.

## 3) XDATA FS_CYPCUT (LO CLAVE)
Cada agujero lleva ahora el XDATA `FS_CYPCUT` con `Channel = capa` (1–14), formato completo
(LeadIn/LeadOut/IsFill/PathStart/ToolCompensation) + APPID registrado. **Es lo que hace que
CypCut separe las capas de verdad.**
- **Verificado: el XDATA que produce el generador es BYTE-IDÉNTICO al del export nativo de
  CypCut** (comparado capa por capa contra cypcut_capas.dxf / Prueba definitiva.dxf).

## Verificación
- **20 tests passing**: módulo 14, XDATA por entidad con Channel=capa, APPID presente, áreas
  cap 14, propiedad latina (0 repeticiones fila/columna, 0 adyacentes con misma capa).
- Los 3 fails de la suite son de entorno (HTTP server / input.dxf ausente), **pre-existentes**.
- Demo módulo 14 + XDATA en `\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`
  para cotejo visual final en CypCut.

## Deploy
Commit `25dfd0b` en origin/erpnext. Solo backend Python → `git pull` + `supervisorctl restart
all`, **sin migrate ni build**. Pedido a Orbit (MSG_030).

## Estado
**Flycut cerrado para producción.** Con el XDATA, el escalonado por cuadrado latino funciona de
verdad en CypCut. Falta solo que Orbit redeploye `25dfd0b`.

— Punto
