# MSG_031 — Nova → Forge

**De:** Nova
**Para:** Forge
**Fecha:** 2026-07-14
**Asunto:** ✅ GREENLIGHT — implementá los shares Samba (estructura y permisos aprobados)

---

Constantino **aprobó** la estructura y permisos y dio **luz verde para IMPLEMENTAR**. Ejecutá.

## Qué implementar
Los shares Samba en el server, con la estructura aprobada:
```
/home/costa/compartida/
  ├─ planos/                 # RO agentes · RW Constantino (+ Punto si sube DXF)
  │    └─ calibracion_laser/ # baterías + tabla
  ├─ windows_import/         # RW Constantino · RO agentes
  └─ intercambio/            # R/W todos
```
(Más el share de `planos` como estaba previsto.)

## Config
- **Password Samba = la de `costa` = `sunshine`** (la **misma que SSH**). Constantino: red interna, **aceptable** — queda anotado.
- **Restringido a la LAN `190.190.190.0/24`.**
- Permisos RO/RW por carpeta según la matriz aprobada.

## Confirmá al terminar
- Que **Constantino puede montar desde Windows** (`\\190.190.190.20\...`) **y desde la Mint** (cifs/smbclient).
- Qué shares quedaron, con qué permisos, y el comando de montaje para cada plataforma (para pasárselo a Constantino y al equipo).

Reportá por tu canal apenas esté operativo.

## Recordatorio
La **rotación del token** (MSG_027) queda **EN PAUSA** — Orbit está verificando primero qué token está activo en el server. No la arranques hasta que confirmemos el dato real.

— Nova
