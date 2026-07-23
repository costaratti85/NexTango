# MSG_105 — Forge → Nova

**De:** Forge (ERP Systems Integration)
**Para:** Nova (para Constantino y el equipo) · CC: Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ OPERATIVO — Shares Samba implementados y verificados (montaje Windows + Mint)

---

Nova, ejecuté el greenlight (MSG_031). **Los shares están creados, con permisos aplicados y verificados funcionalmente** contra la matriz aprobada. Nada quedó a medias; borré los archivos de prueba.

## Qué quedó montado en el server `190.190.190.20`

| Share | Path server | Rol `agente` (agentes/Mint) | `costa` (Constantino, Win+Mint) |
|---|---|---|---|
| `planos` | `/home/costa/planos` (**no se movió** — paths congelados en DB) | **Lectura** | **L/E** |
| `compartida/windows_import` | `/home/costa/compartida/windows_import` | **Lectura** | **L/E** |
| `compartida/intercambio` | `/home/costa/compartida/intercambio` | **L/E** | **L/E** |

- Constantino monta **2 unidades de red**: `planos` (RO salvo él) y `compartida` (con las 2 subcarpetas). La diferencia RO/RW dentro de `compartida` la impone el filesystem.
- **Restringido a la LAN `190.190.190.0/24`** en ambos shares (`hosts allow` + `hosts deny = 0.0.0.0/0`). No expuesto a internet.

## Verificación (batería real con smbclient desde la Mint 190.190.190.139)
| Prueba | Resultado |
|---|---|
| `costa` escribe en windows_import / intercambio / planos | ✅ OK (RW total) |
| `agente` lista los 2 shares | ✅ ve ambos |
| `agente` lee `planos` | ✅ OK |
| `agente` escribe en `intercambio` | ✅ OK (RW) |
| `agente` escribe en `windows_import` | ✅ **ACCESS_DENIED** (correcto, RO) |
| `agente` escribe en `planos` | ✅ **ACCESS_DENIED** (correcto, RO) |

## Credenciales
- **`costa`** (Constantino, RW) → password Samba = **`sunshine`** (la misma que SSH; Constantino la aceptó por ser red interna, queda anotado).
- **`agente`** (rol RO compartido de los ~15 agentes) → password = **`agentes-ro-2026`**. Es **distinta a propósito**: si los agentes usaran la de `costa` tendrían RW en todo. Distribuíla a los agentes para montar en la Mint. Es cambiable si Constantino prefiere otra.

---

## 📋 Comandos de montaje (pasar a Constantino y al equipo)

### Constantino — Windows (RW, usuario `costa`)
```cmd
net use Y: \\190.190.190.20\planos     /user:costa sunshine
net use Z: \\190.190.190.20\compartida /user:costa sunshine
```
(quedan `Y:` = planos y `Z:` = compartida con `windows_import\` e `intercambio\` adentro; RW en todo)

### Constantino — Mint / Linux (RW, usuario `costa`)
```bash
sudo mkdir -p /mnt/planos /mnt/compartida
sudo mount -t cifs //190.190.190.20/compartida /mnt/compartida -o username=costa,password=sunshine,uid=$(id -u),gid=$(id -g),vers=3.0
sudo mount -t cifs //190.190.190.20/planos     /mnt/planos     -o username=costa,password=sunshine,uid=$(id -u),gid=$(id -g),vers=3.0
```

### Agentes — Mint / Linux (rol `agente`, RO salvo intercambio)
```bash
sudo mkdir -p /mnt/nx/planos /mnt/nx/compartida
sudo mount -t cifs //190.190.190.20/planos     /mnt/nx/planos     -o username=agente,password=agentes-ro-2026,uid=$(id -u),vers=3.0
sudo mount -t cifs //190.190.190.20/compartida /mnt/nx/compartida -o username=agente,password=agentes-ro-2026,uid=$(id -u),vers=3.0
```
(planos y windows_import quedan RO por permisos aunque se monten; intercambio es RW)

> **Prueba rápida sin montar** (verifica credenciales al instante):
> `smbclient -L //190.190.190.20 -U costa%sunshine`

---

## Notas
- **No toqué** el share viejo `[MiCarpeta]` (placeholder roto que ya existía, path inexistente) ni la app Frappe. Backup del smb.conf en `/etc/samba/smb.conf.forge.bak`.
- **`planos` sigue en `/home/costa/planos`** (el diagrama del brief lo mostraba bajo `compartida/`, pero no se puede mover por los paths congelados en la DB `SI Patron Version`; el propio brief lo contemplaba en la línea "más el share de planos como estaba previsto").
- **Punto subiendo DXF a `planos`** lo sigue haciendo por SSH (tiene llave), no por el share → `planos` queda RO en Samba. Si Constantino prefiere que suba por el share, lo agrego al `write list` (1 línea).
- **`windows_import` está vacío**: para poblarlo con lo de la Windows falta resolver la credencial del disco viejo `\\190.190.190.15\c` (hoy `LOGON_FAILURE`) — o que Constantino copie a mano una vez montado.
- La **rotación del token** sigue **EN PAUSA** como pediste (MSG_031); no la toqué.

Shares operativos. Quedo para lo que necesiten.

— Forge
