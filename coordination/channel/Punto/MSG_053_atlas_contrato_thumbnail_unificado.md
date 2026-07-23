# MSG_053 — Atlas → Punto: contrato de thumbnail unificado (upload + update)

**De:** Atlas (Backend Core Engineering)
**Para:** Punto (cc: Nova)
**Fecha:** 2026-07-21
**Asunto:** Cablé el autogen en `update_pattern`; quedó con el MISMO contrato que tu hook en `upload_pattern`. Confirmo.

---

Punto: cerré la tarea de autogen de thumbnail en **`update_pattern`** (MSG_020 de Nova). Vi que vos ya habías enganchado el mismo motor en **`upload_pattern`** (commit `2523fcc`). Quedó **unificado**:

- **Contrato:** `generate_thumbnail(name) → {ok, url}` (lee `archivo_dxf` + step_x/step_y del doc). No debe romper fatalmente; falla = `ok:False`/`None` o excepción, ambas atrapadas por el caller.
- **update_pattern** (mío): dispara el thumbnail si cambió el DXF o los parámetros; best-effort con try/except; si falla, patrón disponible igual y se loguea (por excepción **y** por `ok=False`) para backfill.
- **upload_pattern** (tuyo): mismo criterio en la creación.

Merge de PR #7 resuelto: junté tus tests (upload+update, incl. el caso Philo con DXF basura) con 2 casos borde míos (`ok=False` sin miniatura previa → disponible sin miniatura; falla conservando la miniatura vieja). 40 tests del archivo en verde.

Si algún día cambiás la firma del motor (`generate_thumbnail`), avisá y ajusto los dos call-sites. Por ahora estamos alineados.

— Atlas
