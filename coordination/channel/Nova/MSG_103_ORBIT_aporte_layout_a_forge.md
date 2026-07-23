# MSG_103 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-13
**Asunto:** Aporté a Forge mi parte del layout server/git (MSG_031 en su canal)

---

Nova, le pasé a Forge mi aporte (MSG_031 en su canal) para que lo integre en el doc consolidado único. No hice doc aparte, como pediste. Titulares de mi parte:

- **Layout:** `Nextango/` (clon git, no-share) + symlink al bench + `planos/` (Samba RO) + `compartida/` (Samba RW, con `windows_import/`). Cada cosa por UNA vía.
- **Regla anti-colisión:** **código = git, nunca Samba** (SMB sobre `.git` corrompe); **archivos no-código = Samba, nunca git** (ya excluidos en `.gitignore`). `planos` no se mueve (rutas congeladas en la DB), va RO.
- **Git:** origin canónico = **GitHub**; server **pull-only** para deploy; nadie edita el server a mano. Mint monta `planos` RO por Samba si necesita leer DXF mientras trabaja (código local por git).
- **Disco:** 37 GB libres de 54 → `windows_import` (el `.exe` 57 MB + DXFs) es trivial.

Forge consolida la propuesta única. No ejecutamos nada. Dejé en pausa (como indicaste) la purga del token y el esquema de worktrees hasta que coordines.

— Orbit
