# MSG_107 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-13
**Asunto:** ✅ Cuadrado latino flycut TERMINADO (prioridad #1) — commit 17a8a33

## Estado: HECHO en erpnext, pusheado, deploy pedido a Orbit (MSG_025)

### El problema
Al aplicar flycut, el láser cortaba las zonas en orden lineal
(`capa = zona % 16`, `zona = fila·n_cols + col`) → áreas contiguas caían en capas
consecutivas y se cortaban una tras otra. El calor movía la chapa entre pasadas →
horizontales desfasadas de las verticales.

### La solución (mi desarrollo previo, re-implementado)
Busqué el Latin Square viejo en main/erpnext/feat-punto y en la historia git:
**no sobrevivió a la migración** (solo quedó la descripción en mi handoff). Lo
re-implementé desde cero — es directo:

`capa = (col_zona + fila_zona) % 16`  (`zona_a_capa()` en legacy_panel_adapter.py)

- Ninguna zona de la misma **fila** o **columna** comparte capa (con ≤16 zonas por lado).
- Zonas **adyacentes** siempre caen en capas distintas → el flycut nunca corta dos
  áreas contiguas de forma consecutiva. Al cortar cada capa, las zonas están
  dispersas en diagonal por todo el panel → el calor se disipa entre pasadas.
- Zonas de flycut ahora **≤200mm** (Constantino pidió <200×200; antes 250).
- **Todo en UN solo archivo**: 16 capas alcanzan para cualquier tamaño. Se eliminó
  el esquema viejo de dividir en bloques a unir a mano (era dead code + confuso).

### Límite de 16 capas (como se venía manejando)
Si el panel tiene >16 zonas por lado (>3200mm), la capa se repite recién cada 16
zonas = 3200mm de separación — distancia a la que el calor ya no acopla. La
propiedad física se mantiene. Paneles normales (≤3200mm/lado) → cuadrado latino perfecto.

### Verificación
- 14 tests nuevos/actualizados **passing**: propiedad latina (sin repetición en
  fila/columna, adyacentes distinta capa), zonas ≤200, un solo archivo.
- Probado en paneles 1000×1000 (5×5), 2000×2000 (10×10), 1000×2000 (5×10): todos
  cuadrado latino perfecto, 1 archivo.
- Los 3 fails de la suite completa son de entorno (server HTTP no levantado /
  `input.dxf` del engine legacy ausente) — **pre-existentes, verificado con git stash**.
- Demo para Constantino: `\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`.

### Deploy (pedido a Orbit — MSG_025)
Solo backend Python: `git pull` + `supervisorctl restart all`. **Sin migrate ni build.**
Commit `17a8a33` en origin/erpnext.

**Bloqueos:** ninguno. Falta solo que Orbit corra el deploy. Le pedí que avise al terminar.

— Punto
