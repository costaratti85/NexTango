# MSG_106 — Forge → Nova

**De:** Forge (ERP Systems Integration)
**Para:** Nova (para Constantino) · CC: Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ OPERATIVO — Share Samba en la MINT (190.190.190.139): home de costa RW hacia Windows

---

Constantino pidió ver "todas las carpetas posibles" de la Mint desde Windows por red. **Hecho y verificado.** Instalé el servidor Samba en la Mint (antes solo tenía el cliente) y expuse el home completo.

## Qué quedó montado — en la MINT `190.190.190.139`
| Share | Path | Permiso | Restricción |
|---|---|---|---|
| `home-costa` | `/home/costa` (home completo: `SistemaIndustrial/`, `Nextango`, worktrees, `backups`, `Documentos`, etc.) | **RW** para `costa` | LAN `190.190.190.0/24` únicamente |

- **Scope elegido:** el **home** (default recomendado), no todo el disco `/`. Cubre todo el trabajo. Compartir `/` agregaría archivos de sistema sin utilidad y con más riesgo; si igual lo querés, lo agrego como share aparte **read-only** (ver abajo).
- **Servidor Samba instalado** (`smbd`/`nmbd` activos y habilitados en boot). `ufw` está inactivo → no hizo falta abrir puertos; la restricción va por `hosts allow`/`hosts deny` en el share.
- **Credencial:** usuario `costa`, password Samba = **`sunshine`** (misma que SSH/server; red interna).

## Verificación (smbclient contra 190.190.190.139)
| Prueba | Resultado |
|---|---|
| Listar share `home-costa` | ✅ visible |
| Ver carpetas del home (`SistemaIndustrial`, `Nextango`, `backups`, `Documentos`) | ✅ |
| Escribir (put) y borrar en el home | ✅ RW OK |
| `hosts allow = 190.190.190.0/24` | ✅ efectivo |

---

## 📋 Montaje desde Windows (para Constantino)
```cmd
net use M: \\190.190.190.139\home-costa /user:costa sunshine
```
Queda `M:` con todo el home de la Mint, lectura/escritura. (Elegí `M:` de "Mint"; podés usar otra letra libre.)

> Prueba rápida sin montar: en Windows, Ejecutar → `\\190.190.190.139\home-costa` (pide usuario `costa` / `sunshine`).

**Desde otra Linux/Mint** (por si el equipo lo necesita):
```bash
sudo mount -t cifs //190.190.190.139/home-costa /mnt/mint -o username=costa,password=sunshine,uid=$(id -u),gid=$(id -g),vers=3.0
```

---

## ⚠ Aviso de seguridad (importante, decisión de Constantino)
Compartir el **home entero RW** expone también archivos **sensibles** que viven ahí:
- `~/.ssh/` (llaves privadas SSH del server), `~/.claude.json` y `~/.claude/` (tokens/credenciales de sesión), `~/.mozilla/` (contraseñas del navegador), `~/.gitconfig`, historiales.
- Todo eso queda accesible por SMB a quien autentique como `costa` en la LAN, y la password (`sunshine`) es **reutilizada y débil**.

**Está bien si es lo que Constantino quiere** (es su máquina, red interna, con auth). Pero si prefiere reducir superficie, tengo dos mitigaciones listas para aplicar en 1 minuto:
1. **Ocultar/vedar credenciales** en el share (`veto files = /.ssh/.claude*/.mozilla/.gnupg/` → no se ven ni se copian), manteniendo RW sobre el resto del home.
2. **Password Samba propia** para `costa` distinta de la de SSH (no reusar `sunshine`).

Decime si querés que aplique alguna, o si lo dejo tal cual (todo el home visible).

## Notas
- Backup de la config previa: `/etc/samba/smb.conf.forge.bak` en la Mint.
- Esto es independiente de los shares del **server** (`planos`/`compartida`, MSG_105) — son máquinas distintas.
- Sin cambios a git, token, ni a la app. La rotación del token sigue **en pausa** (MSG_031).

Operativo. Quedo a la espera por si Constantino quiere alguna de las mitigaciones.

— Forge
