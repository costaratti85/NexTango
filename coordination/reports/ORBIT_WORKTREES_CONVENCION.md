# Convención de worktrees por agente (Mint)

**De:** Orbit (Build/Deploy) · **Fecha:** 2026-07-14
**Estado:** ACTIVO — montado sobre el repo ya purgado del token.

---

## Estructura (todos comparten UN solo `.git`, el de `Nextango/`)

```
/home/costa/SistemaIndustrial/
├── Nextango/              rama main     — COORDINACIÓN (MSG, queue.json). Compartido.
├── Nextango-erpnext/      rama erpnext  — base de código de referencia. NO editar a mano.
└── worktrees/
    ├── punto/     feat/punto
    ├── vega/      feat/vega
    ├── gemu/      feat/gemu
    ├── cybelec/   feat/cybelec
    ├── tango/     feat/tango
    └── atlas/     feat/atlas
```

Todos los worktrees nacieron de `erpnext` (HEAD `ffc462b`, ya sin el token en el historial).

## Flujo de trabajo por agente (código)

1. Trabajás en **tu** worktree `worktrees/<agente>/` (rama `feat/<agente>`). No pisás a nadie: cada uno su working tree.
2. `git add … && git commit`
3. `git push -u origin feat/<agente>`
4. `gh pr create --base erpnext --title "…"` (crear PR contra `erpnext`).
5. **Merge por integrador único** (Nova aprueba / Orbit mergea). `main` y `erpnext` no reciben push directo.
6. Deploy: tras el merge, Orbit hace `git pull` en el clon del server + `bench build`/`migrate`.

## Reglas

- **Coordinación** (MSG_*.md, `queue.json`) → se sigue haciendo en `Nextango/` (main), como hasta ahora. **Código** → en tu worktree `feat/<agente>`.
- **No editar** `Nextango-erpnext/` a mano (es la referencia limpia de erpnext) ni el clon del server.
- **Venv:** local en la Mint (nunca sobre SMB). Cada worktree puede crear su `.venv` o reusar `Nextango/.venv` (ezdxf/paramiko). Instalar libs nuevas → coordinar con Orbit (`requirements.txt`).
- **Sincronizar tu worktree** con lo último de erpnext: `git fetch origin && git rebase origin/erpnext` (o merge) dentro de tu worktree.

## Agregar un agente nuevo
```
cd /home/costa/SistemaIndustrial/Nextango
git worktree add -b feat/<nuevo> /home/costa/SistemaIndustrial/worktrees/<nuevo> erpnext
```

## Quién tiene worktree
Con worktree de código hoy: **punto, vega, gemu, cybelec, tango, atlas** (los que editan el repo).
Sin worktree (por ahora): Forge (infra/Samba), y proyectos Windows-nativos/standalone (Postprocesador `.exe`, PedidoExcel VBA, OCR) que se acceden por Samba, no se editan como código del repo. Se agregan on-demand con el comando de arriba.

— Orbit
