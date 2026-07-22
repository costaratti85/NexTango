# MSG_188 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** ✅ Deploy `488f5f4` productivo — Perfiles plegados: 3 ajustes de render (PR #9 de Vega)

---

## PR #9 mergeado + deployado
- **Merge:** PR #9 (`feat/vega-perfiles-render`, HEAD `4ba3d41`, 2 commits) → `origin/erpnext`.
  Merge commit **`488f5f4`** (`--admin`, base era `1b495d6` recién deployado → limpio).
- **Deploy** (copia canónica `/home/costa/Nextango`): `git merge --ff-only` → version stamp →
  **`bench build`** (es JS) → bump_page_cache → `clear-cache` → `restart all`. **Sin migrate.**
- Solo tocó **1 archivo, JS**: `page/perfiles_plegados/perfiles_plegados.js` (+37 / −9).

## Verificación
- **HEAD server = `488f5f4`** ✓ e **incluye `4ba3d41`** ✓.
- **7/7 servicios RUNNING**, **HTTP 301 estable** (no 502).
- **version_stamp servido = `488f5f4`** ✓ (build nuevo vivo + cache-busting activo).
- **JS servido con los cambios** ✓ — el page JS de Frappe se sirve vía `getpage`, que **lee el
  archivo del disco en cada request**; con HEAD `488f5f4` y working tree **limpio**, lo servido
  es exactamente el archivo verificado. Los **3 marcadores** están presentes:
  1. **Letras de nodo solo en "editar a mano"** (en vista normal son ruido).
  2. **Ángulos de 90° sin etiqueta** (`if(|ang−90|<0.5) continue;`).
  3. **Cotas del lado exterior, tamaño visible, con halo blanco** para no solaparse con los
     trazos (`paint-order="stroke" stroke="#ffffff" stroke-width="3"`; los trazos se dibujan
     primero y las cotas encima).

## Verificación visual (Constantino)
Abrir **Perfiles plegados**: en vista normal, sin letras de nodo y sin el "90°"; las cotas
legibles del lado de afuera con halo blanco. En modo "editar a mano" reaparecen las letras.

Cola: `ORBIT_DEPLOY_PERFILES_RENDER` marcada **completado**.

— Orbit
