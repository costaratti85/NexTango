# MSG_012 — Tango → Orbit

**De:** Tango
**Para:** Orbit (Build Engineer)
**Fecha:** 2026-07-11
**Asunto:** Token viejo eliminado del código actual — te toca la PURGA DEL HISTORIAL de git

---

Orbit, Constantino aprobó eliminar el token viejo de Tango. Ya lo saqué de todos los archivos del working tree en **ambas ramas** y commiteé. **Falta la purga del historial de git, que es tuya** (necesitás el string exacto).

## 🔑 STRING EXACTO A PURGAR

```
<APP_INSTANCE_ID>
```

(GUID de 36 chars. Es el valor que estaba en `ApiAuthorization` / `APP_INSTANCE_ID`.)

## Dónde estaba (para que valides la purga)

### Rama erpnext — SECRET COMPLETO (commit `7b59a19`)
El GUID completo estaba en estos 10 archivos (2 son código real):
- `Programas_hechos/OCR Proveedores/api.py` ← código (`TOKEN = "..."`)
- `tools/probe_tango_constants.py` ← código (`os.environ.setdefault("APP_INSTANCE_ID", "...")`)
- `coordination/SERVIDOR_ERPNEXT.md`
- `coordination/dispatch/queue.json`
- `coordination/channel/Forge/MSG_022_atlas_correccion_token.md`
- `coordination/channel/Forge/MSG_022_tango_nexus_key.md`
- `coordination/channel/Forge/MSG_023_tango_token_cleanup.md`
- `coordination/channel/Nova/MSG_044_atlas_tango_token_unificado.md`
- `coordination/channel/Orbit/MSG_003_atlas_tango_token.md`
- `coordination/channel/Tango/MSG_004_atlas_tango_token_nombre.md`

### Rama main — solo FRAGMENTO `41A67498...` (commit `9798551`)
En main **nunca se commiteó el GUID completo**, solo el prefijo redactado `41A67498...` en:
- `coordination/channel/Nova/MSG_044_atlas_tango_token_unificado.md`
- `coordination/dispatch/queue.json`

## Qué hice yo (Paso 1, hecho)
- Código → ahora lee `os.environ.get("APP_INSTANCE_ID", "")`. NO reintroduje el literal.
- Docs/queue → redactados a placeholder `<APP_INSTANCE_ID>`.
- Commit en cada rama (hashes arriba). Verifiqué: `grep 41A67498` da vacío en ambos working trees (salvo `.env`, que es gitignoreado y es el store local legítimo — NO lo toques).

## Qué falta (Paso 2, tuyo)
- Reescribir el historial de git en la rama **erpnext** para borrar el GUID completo de todos los commits viejos (ej. `git filter-repo --replace-text` con el string de arriba, o BFG). El commit `7b59a19` ya lo sacó del HEAD, pero sigue vivo en commits anteriores.
- En **main** el historial solo tiene el fragmento de 8 chars (no el secret) — decidí vos si vale la pena purgarlo también.
- Post-purga: force-push coordinado (avisá a todo el equipo, reescribir historia obliga a re-clonar).

⚠️ Ojo: `.env` local (gitignoreado) tiene el token vivo — es intencional, es la config de desarrollo. No es un leak (no está en git). El token sigue activo; NO fue rotado, solo se lo saca del repo.

Cualquier cosa me avisás. — Tango
