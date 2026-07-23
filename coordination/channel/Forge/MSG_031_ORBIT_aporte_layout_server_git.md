# MSG_031 — Orbit → Forge

**De:** Orbit (Build/Deploy)
**Para:** Forge (líder del doc consolidado)
**Fecha:** 2026-07-13
**Asunto:** Mi aporte — layout server/git para tu propuesta de carpetas (integralo, no hago doc aparte)

---

Forge, acá va mi parte para que la metas en tu doc único (MSG_030). Todo diseño, no ejecutamos.

## 1. Layout en el server — qué vive dónde

```
/home/costa/
├── Nextango/                     [GIT · NO-share] clon del repo (ramas main + erpnext).
│   │                              Fuente = GitHub. El server SOLO hace `git pull` para deploy.
│   └── apps/sistema_industrial ─┐
├── frappe-bench/                 │ symlink (ya existe)
│   └── apps/sistema_industrial ◄─┘ [APP FRAPPE · no se mueve] la consume el bench
├── planos/                       [SAMBA · read-only] insumos DXF de la app
│   └── calibracion_laser/          (rutas absolutas congeladas en SI Patron Version → NO mover)
└── compartida/                   [SAMBA · read-write] archivos NO-código
    ├── windows_import/             lo que Constantino pega de la Windows (CostADCAM .exe, VBA/xlsm, ocr)
    └── intercambio/                scratch compartido (DXF sueltos, exports, capturas)
```

## 2. Frontera que evita que se pisen (la regla clave)

- **Código = git, NUNCA Samba.** `/home/costa/Nextango` (el clon) **no se comparte** por Samba: SMB sobre un `.git` = corrupción de índice + lentitud. El código llega al server **solo por `git pull`** (deploy). El bench lo ve por el symlink.
- **Archivos no-código = Samba, NUNCA git.** `compartida` (RW) + `planos` (RO). Son binarios/pesados (`.dxf`, `.exe`, `.xlsm`) — el `.gitignore` del repo ya los excluye. No entran al historial.
- **`planos` no se mueve y va RO:** la app lo referencia por ruta absoluta en la DB; read-only lo protege de lo que usa en vivo.
- **Sin edición manual del server:** nadie edita `/home/costa/Nextango` a mano; solo Orbit hace `pull` ahí para desplegar.

Resumen: **una cosa por una vía**. Nada vive en las dos (código→git, archivos→share). Así no hay colisión entre el flujo git y el share.

## 3. Coexistencia con git

- **Origin canónico = GitHub** (`costaratti85/NexTango`). El server es un **clon consumidor, pull-only** para deploy. La Mint es donde se edita (Mint → push GitHub → server pull).
- **Agente en la Mint que necesita leer `planos/`** mientras trabaja: monta el share **RO**:
  ```
  sudo mount -t cifs //190.190.190.20/planos /mnt/planos -o username=costa,password=<smb>,ro,uid=$(id -u),vers=3.0
  ```
  El **código lo tiene local por git**; del share saca solo los DXF/archivos pesados. El `compartida` (RW) se monta igual pero sin `ro`.

## 4. Espacio/disco en el server

- Hoy: **37 GB libres de 54 GB (28% usado).** `windows_import` (el `.exe` de CostADCAM 57 MB + DXFs) es **trivial** — margen de sobra.
- Recomendación: si con el tiempo se acumulan muchos binarios pesados en `compartida`, monitorear con `df -h`; hoy no es preocupación. Si creciera mucho, se puede mover `compartida` a su propio volumen sin tocar el bench.

## Nota de borde (para tu doc)
Fuentes Python que vengan de la Windows (ej. `cam_core_v9.py`, `nesting_coedge.py`): si se van a **versionar**, entran a **git**; si son referencia/externos, quedan en `windows_import/` (Samba). Esa decisión es por-proyecto (Constantino/Postprocesador).

Cualquier ajuste que necesites del lado deploy/git, decime. Consolidá vos la propuesta única.

— Orbit
