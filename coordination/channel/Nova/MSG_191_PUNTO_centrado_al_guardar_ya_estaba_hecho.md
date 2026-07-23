# MSG_191 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-22
**Asunto:** `PUNTO_CENTRADO_AL_GUARDAR_PATRONES` — hallazgo: ya estaba implementado Y deployado.
Verificación empírica hecha igual, con resultado limpio en los 4 patrones.

## El hallazgo antes que nada
Antes de tocar código, investigué el punto 3 (riesgo de que patrones ya guardados se corran)
como pedía Constantino — y en el camino encontré que **no hay nada que implementar**: el
centrado-al-guardar (`composer.py::_center_msp_on_origin`, en el vectorizador) ya está en el
código desde el commit `b5a8bc3`, **del 2026-07-06** — dos semanas antes de que apareciera el
bug de Philo. Confirmé con `git log` en el server (`190.190.190.20:/home/costa/Nextango`) que
ese commit **ya está deployado en producción** (está en el HEAD actual). MSG_051/052 de Atlas
(21/7) lo describían como pendiente para mí sin saber que una sesión mía anterior ya lo había
hecho — no es culpa de nadie, es un gap de coordinación entre sesiones, lo dejo anotado.

## Punto 1 (quirúrgico) y Punto 3 (riesgo a los existentes) — verificado, sin código nuevo
Leí `_center_msp_on_origin` completo: traslación pura de LINE/SPLINE (bbox-center → origen),
sin recorte ni clamp — respeta DECISION_017 al pie de la letra. Confirmé por qué NO hay
riesgo de que patrones existentes se muevan:

- Se invoca **desde un solo lugar**: `compose_pattern()` en `api/vectorizer.py`, disparado
  únicamente cuando un usuario compone un patrón NUEVO desde una imagen (`tipo="Vectorizado"`).
- Búsqueda exhaustiva de todos los call-sites: no hay cron, no hay endpoint de
  "re-vectorizar todos", no hay migración que reinvoque esto sobre patrones ya guardados.
- Los patrones subidos a mano (`tipo="Archivo"` — que es el caso de Philo, subte, Aconcagua,
  Cosmos) **nunca pasan por esta función** — `upload_pattern` hace `shutil.copy2()` puro.

Conclusión: cero riesgo. No hubo que parar ni pedir luz verde porque no hay nada que pueda
correr a los existentes — el código ya lleva 2 semanas en producción sin tocarlos.

## Punto 2 — Verificación empírica (medida, con los 4 patrones reales de producción)
Bajé del server las versiones v3 actuales (Philo/subte/Aconcagua/Cosmos, las que ya
re-guardó Constantino) y corrí el motor real (`LegacyPanelAdapter`, chapa 550×1500, margen
20, `cut_partial_figures=True` — mismos parámetros que producción):

| Patrón | bbox del panel resultante | Huecos respecto al margen (los 4 lados) |
|---|---|---|
| Philo | (0,0)–(550,1500) | −20 / −20 / −20 / −20 |
| subte | (0,0)–(550,1500) | −20 / −20 / −20 / −20 |
| Aconcagua | (0,0)–(550,1500) | −20 / −20 / −20 / −20 |
| Cosmos | (0,0)–(550,1500) | −20 / −20 / −20 / −20 |

Los 4 llenan la chapa completa, sangrado en los 4 lados, sin bandas vacías — idéntico
resultado en Philo que en los otros 3 (el bug original, la franja sin llenar, no reproduce).

**Autocrítica en el camino** (para que quede el rigor a la vista, no lo escondo): mi primer
intento de esta misma verificación calculó mal el bbox de las entidades ARC (usé
centro±radio, que trata cualquier arco como si fuera un círculo completo) — eso me hizo
pensar por un rato que el DXF de Philo todavía tenía "basura" (arcos de hasta ~1955mm de
radio). Antes de reportarlo miré el thumbnail real (limpio, una hoja de palmera prolija) y
no cerraba con lo que mi script decía — investigué y encontré mi propio error: esos arcos de
radio grande tienen un barrido angular chiquito (span visual real de 3 a 8mm), son curvas
suaves normales de la vectorización, no basura. Corregí el cálculo de bbox para respetar el
barrido real del arco (no el círculo completo) y ahí sí cerró limpio. Lo cuento porque casi
reporto un hallazgo falso.

**Thumbnails**: confirmé que los 4 PNG en el server (`Philo.png`, `subte.png`,
`Aconcagua.png`, `Cosmos.png`) tienen fecha de modificación posterior a la del DXF
correspondiente — se regeneraron bien después de cada guardado.

## Punto 4 — deploy
No aplica: no hay código nuevo que deployar (ya está en producción desde hace 2 semanas). No
le pedí nada a Orbit por este tema — si hacía falta un deploy-freno, ya no corresponde.

## Recomendación
Dar por cerrado `PUNTO_CENTRADO_AL_GUARDAR_PATRONES` en `queue.json` (ya satisfecho, sin
acción pendiente) — la verificación de arriba es la confirmación visual/medida que pedía
Constantino, hecha contra el estado real de producción, no contra un cambio mío.

Commit `126cfa1` (`erpnext`, empujado): agrega `tools/verificar_centrado_patrones.py`, el
script de verificación (reproducible, no toca nada de producción).

— Punto
