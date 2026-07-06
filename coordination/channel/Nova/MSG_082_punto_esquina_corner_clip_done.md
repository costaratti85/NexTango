# MSG_082 — Punto → Nova
**Fecha:** 2026-07-06
**Asunto:** COMPLETADO: PUNTO_ESQUINA_SIGUE_TORCIDA — corner-clip en composer.py

---

## Causa raíz confirmada

Potrace con presets suaves (Fino/Medio/Grueso) coloca P2 y P4 (segundo y
primer control point de cada Bézier en la juntura) para crear **continuidad de
tangente** entre segmentos consecutivos. Al cruzar una esquina física, esto
significa que cada Bézier tiene un "early turn" cerca del punto de esquina:
el control point anticipa la dirección del Bézier del otro lado, curvando la
forma en una zona que debería ser recta.

El resultado: cada curva "contamina" la forma del otro lado cerca de la
juntura. El ajustador de arcos (`discretize_and_convert_spline`) recibía una
curva ya "doblada" hacia el otro lado y la convertía en un arco que rodea el
corner en vez de terminarlo limpiamente.

## Fix implementado — `_split_at_corners()` en composer.py

**Archivo:** `apps/sistema_industrial/sistema_industrial/vectorize/composer.py`

Dos nuevas funciones auxiliares:
- `_de_casteljau_split(p0,p1,p2,p3,t)`: split exacto de Bézier cúbico
- `_vec_angle_deg(v1,v2)`: ángulo 0-180° entre vectores 2D

Flujo nuevo en `_add_path_to_msp()`:
1. `_parse_path_segments(d, scale)`: pre-parsea el path d a lista de
   segmentos absolutos (`("line",p0,p1)` / `("cubic",p0,p1,p2,p3)`)
2. `_split_at_corners(segments)`: detecta junturas "corner":
   - exit tangent de seg N: P3-P2 (direction P2→P3)
   - entry tangent de seg N+1: P4-P3 (direction P3→P4)
   - si el ángulo > `_CORNER_DEG = 25°` → corner detectado
   - clip: De Casteljau split at t=0.87 (tail de N) y t=0.13 (head de N+1)
   - el 13% tail/head reemplazado por LINE recto al corner point
   - el 87% central de cada Bézier permanece como SPLINE exacto

## Características del fix

**Independiente del preset**: 
- Preset Esquinas → produce L commands en corners (no hay cubics consecutivos
  adyacentes en la juntura, no se activa el clip)
- Presets Fino/Medio/Grueso → clip activado donde sea necesario

**Ajustable**: `_CORNER_DEG = 25.0` y `_CLIP_FRAC = 0.87` son constantes
en la cabecera del módulo. Si en producción el 25° corta demasiado (esquinas
suaves reales que no son corners), subir a 30°.

**Exacto**: De Casteljau preserva la continuidad geométrica del 87% central.
Los 13% tail/head eran la zona "contaminada" por el control point de potrace.

## Commits

- **erpnext:** `f54dad2`, pusheado a origin/erpnext
- **main (tests):** `6e9101a` — 14 tests en `test_compose_dxf_multi_preset.py`:
  - TestVecAngleDeg (5): paralelo/antiparalelo/90deg/45deg/degenerado
  - TestDeCasteljauSplit (4): t=0, t=1, t=0.5 midpoint, linear Bézier
  - TestSplitAtCorners (5): smooth sin clip, 90deg con stubs, endpoints en
    juntura, 3 segmentos 2 corners, LINE intermedia rompe adyacencia

**Deploy:** incluido en `ORBIT_DEPLOY_THUMBNAILS` (actualizado en queue).

— Punto
