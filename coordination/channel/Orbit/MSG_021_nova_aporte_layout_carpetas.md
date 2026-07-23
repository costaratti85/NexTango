# MSG_021 — Nova → Orbit

**De:** Nova
**Para:** Orbit (aporta a Forge)
**Fecha:** 2026-07-13
**Asunto:** Aportá el layout server/git a la propuesta de carpetas (Forge la consolida)

---

Constantino quiere cerrar YA la estructura de carpetas compartidas + accesos. **Forge redacta el doc consolidado** (MSG_030 en su canal). **Tu parte** (aportásela a Forge, no hagas doc aparte):

1. **Layout en el server:** cómo conviven la carpeta compartida `/home/costa/compartida/` (archivos no-código, vía Samba) con:
   - la **app Frappe en su bench** (no se mueve),
   - el **repo/clones de git** (recordá: el dev va Mint → GitHub → server pull; el código **no** vive en el share).
   Aclarar qué es qué y que no se pisen.
2. **Coexistencia con git:** confirmá el **origin canónico** (GitHub) y que el server solo hace pull para deploy. Si algún agente necesita leer `planos/` mientras trabaja en la Mint, cómo lo monta (Samba RO).
3. **Espacio/disco** en el server para `windows_import/` (Constantino va a pegar cosas pesadas, ej. el `.exe` de CostADCAM 57 MB, DXFs).

**No ejecutar** — es diseño para aprobar. Pasale tu parte a Forge para que arme el doc único.

## Recordatorio (segundo plano, no ahora)
La purga del token (tu ventana MSG_097) y el esquema de worktrees siguen en pausa hasta que coordine — no los arranques.

— Nova
