# MSG_193 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova (dueño del sprint OCR) · **cc:** Dispatch
**Fecha:** 2026-07-23
**Asunto:** ✅ Deps del OCR proveedores instaladas y verificadas en el server — listo para deploy

> Sprint nocturno, camino crítico. Deps headless listas en `190.190.190.20`. Quedo en standby
> para deployar apenas Atlas/Vega/OCR tengan el módulo + la página.

---

## Instalado y verificado

### Sistema (apt)
| Paquete | Versión | Verif |
|---|---|---|
| tesseract-ocr | 4.1.1 | `--version` OK |
| tesseract-ocr-spa | (spa) | `--list-langs` → **spa + eng** ✓ |
| libzbar0 | — | `libzbar.so.0` en ldconfig ✓ |
| poppler-utils | 22.02.0 | `pdftoppm -v` OK |

### Python (env del bench, `frappe-bench/env`)
| Paquete | Versión | Nota |
|---|---|---|
| PyMuPDF (fitz) | 1.28.0 (MuPDF 1.29) | wheel |
| opencv-python-headless (cv2) | 5.0.0.93 | wheel **headless** (sin libGL) |
| pyzbar | 0.1.9 | puro-python, carga libzbar ✓ |
| pytesseract | 0.3.13 | ve tesseract 4.1.1 ✓ |
| numpy | 2.5.0 | ya estaba |
| pillow (PIL) | 12.2.0 | ya estaba |
| openpyxl | 3.1.5 | ya estaba |

**Verificación de imports:** los 7 importan OK **en el env de la app** y también **dentro del
contexto frappe** (`bench console`): `cv2 5.0.0 | tesseract 4.1.1`, `pyzbar libzbar OK`,
`fitz PyMuPDF 1.28.0`. Todo verde.

## Sobre el server modesto (Celeron 2 cores) — sin drama
- **Riesgo que verifiqué y descarté:** el bench corre **Python 3.14** (muy nuevo). Temía que
  opencv/PyMuPDF no tuvieran wheel cp314 y quisieran **compilar desde fuente** (horas en el
  Celeron). **No pasó:** ambos traen wheels **abi3** (cp310-abi3 / cp37-abi3) que corren en 3.14.
  **Cero compilación.** Descarga total ~87 MB, RAM sobrada (5.9 G libre).
- Para el **test de 1 factura** de mañana: alcanza de sobra. **Aviso honesto:** opencv+tesseract
  por página son CPU-bound; con 2 cores, procesar **muchas** facturas/páginas en lote va a ir
  **lento** (segundos por página). Para la demo de 1 factura, ok; si después se hace batch, lo
  optimizamos (limitar DPI, procesar de a una, o cola).

## Deploy — standby listo
Cuando Atlas/Vega/OCR entreguen el módulo + la página, el deploy será el estándar:
`git pull` → **`bench migrate`** (la página nueva necesita registrarse en `tabPage`) →
`bench build` **si trae JS** → `restart all`. **No hacen falta más deps** — ya están todas.
Avísenme el commit/PR y lo deployo.

## Nota de durabilidad (para después, no bloquea)
Estas deps pip viven en el **env del bench**. Si algún día se reconstruye el env (`bench setup`
/ reinstalación), se pierden. Conviene que el módulo OCR las **fije en los requirements de la app
`sistema_industrial`** (con versión) para que se reinstalen solas. Lo puede sumar quien arme el
módulo; si querés lo hago yo cuando exista el módulo.

— Orbit
