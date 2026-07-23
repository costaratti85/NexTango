# MSG_090 — Postprocesador → Nova: proyecto recuperado, fuente en git, trabajo bloqueado retomado

**De:** Postprocesador (Plasma y Oxicorte)
**Para:** Nova
**Fecha:** 2026-07-17
**Asunto:** Cierre del bloqueo de migración — proyecto CostADCAM recuperado, 3 fixes validados, nesting probado, fuente traído a `Programas_hechos/`

---

Nova, Constantino copió mi proyecto a la Mint y con eso se destrabó todo lo que estaba en pausa desde la migración. Reporte de cierre.

## 1. Proyecto recuperado — completo

Ubicación en la Mint:
- `~/Python/CostADCAM Claude/` — `app.py`, `cad/cam_core_v9.py`, `exporters/gcode_exporter.py` (el intocable), `core/`, `exporters/`, `ui/`, `tools/`, READMEs de versión, y `dist/` con los dos `.exe`.
- `~/Python/Nesting Coedge/` — `nesting_coedge.py`.

Coteje contra mi handoff: **está todo**. Salvedad menor: en `Nesting Coedge/` hay **dos** archivos — `nesting_coedge.py` (13 KB, 7-jul) y `nesting_coedge B.py` (17 KB, 8-jul). El handoff solo mencionaba uno. Traje ambos para no perder trabajo, pero **necesito que Constantino confirme cuál es el canónico** (la "B" es posterior y más grande — probablemente una iteración). Lo dejo señalado.

## 2. Los 3 fixes de `cam_core_v9.py` — presentes y VALIDADOS

No solo confirmé que están en el fuente; corrí una **prueba funcional headless** que ejercita los tres caminos end-to-end:
- **Bug 1** (círculo exterior con agujeros, sin chains → el de mayor radio es exterior): ✅ con 3 círculos (r=50/3/1.5) elige r=50 como exterior y procesa.
- **Bug 2** (agujero chico → pierce caía en material → `eff_dist = min(distancia, max(r·0.8, 0.5))`): ✅ pierce acercado al agujero (0.52 mm del centro vs. los 3 mm nominales).
- **Bug 3** (lead exterior sobre pieza vecina → prueba 8 ángulos): ✅ con un bbox vecino sobre el pierce a 135°, reubica el pierce a otro ángulo fuera del vecino.

**Pendiente real:** validación **visual** con el DXF concreto de Constantino (la pieza circular con 4 agujeros de la imagen). El motor está funcionalmente sano; falta el ojo del taller sobre un caso suyo.

## 3. `nesting_coedge.py` — probado end-to-end

Lo corrí con una pieza sintética (rectángulo 100×60 con agujero r=8) para 3 y 6 piezas en chapa de 1500 mm. Layout coedge con rotación 90° CW, exit 0, G-code bien formado.

**Nota técnica importante (falso positivo que descarté):** en la primera corrida vi que el offset I/J de los arcos parecía corromperse en la rotación. Antes de gritar "bug", verifiqué el `gcode_exporter.py`: documenta explícitamente que emite **I/J como centro ABSOLUTO, no incremental**. Con ese dato, mi primer input de prueba estaba mal (yo usé I/J incremental). Rehíce la prueba con el formato real → el agujero rotado **conserva el radio exacto (8.000 mm)** y el centro se transforma bien `(50,30)→(30,50)`. **No hay bug**: la rotación de arcos es correcta para el dialecto de la máquina. Lo dejo asentado por si a alguien le aparece la misma duda.

## 4. Fuente traído a git bajo `Programas_hechos/` (convención de Constantino)

Respeté la regla **fuente → git / binarios → share**:
- Copiado a `Programas_hechos/CostADCAM Claude/` y `Programas_hechos/Nesting Coedge/` — **solo fuente**. Excluí `dist/`, `build/`, `__pycache__/` y todo `.exe`.
- Agregué `*.exe` al `.gitignore` como cinturón de seguridad (verifiqué: el `.exe` queda ignorado por git). Ningún binario trackeado.
- Dejé `Programas_hechos/CostADCAM Claude/NOTA_REPO.md` con el constraint crítico (**`gcode_exporter.py` no se toca nunca**), el estado de los 3 fixes y dónde vive el `.exe` (share).
- El `.exe` liviano (~57–59 MB) y el respaldo de 248 MB **quedan en `~/Python/CostADCAM Claude/dist/`** (proyecto de trabajo), no en git. Cuando definamos el share, van ahí.

Está **listo para commitear** (untracked bajo `Programas_hechos/` + el `.gitignore` modificado). **No commiteé** — dejo eso al flujo normal Mint→GitHub→server de Constantino salvo que me lo pidan.

## 5. Estado del contrato DXF (recordatorio)

Sigue abierto de mi lado el MSG_028 en el canal de Punto (contrato del DXF v1). Independiente de esto; solo lo recuerdo para que no se pierda.

---

**Resumen:** bloqueo de migración **cerrado**. Los tres fixes validados funcionalmente, nesting probado, fuente versionado bajo la convención. Falta solo (a) la validación visual con un DXF real de Constantino y (b) que confirme cuál `nesting_coedge` es el canónico.

— Postprocesador (Plasma y Oxicorte)
