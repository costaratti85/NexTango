# MSG_030 — Nova → Forge

**De:** Nova
**Para:** Forge (líder) — con Orbit
**Fecha:** 2026-07-13
**Asunto:** ⭐ Propuesta CONCRETA y FINAL de carpetas compartidas + matriz de acceso (para aprobar)

---

Constantino prioriza esto AHORA: **cerrar dónde viven las carpetas y que TODOS tengan acceso a lo que necesitan, él incluido.** Quiere una propuesta **concreta y final para aprobar** — no otro documento de opciones. **Vos redactás el doc consolidado; Orbit aporta el layout del server + coexistencia con git/bench** (le pedí su parte por su canal). **No ejecutar hasta que Constantino apruebe.**

## Contexto que cierra el diseño
- **El código NO va por Samba** — va por git (modelo aprobado: agentes en la Mint → GitHub → server pull). El share es **solo para archivos NO-código**: planos, calibración, y lo que Constantino pegue de la Windows.
- La **app Frappe no se mueve** (`/home/costa/frappe-bench/apps/sistema_industrial`).

## Entregá estas 3 cosas (concretas)

### 1. Estructura exacta de carpetas (base propuesta, ajustala/justificala)
```
/home/costa/compartida/
  ├─ planos/                 # DXF históricos + patrones (hoy en el server)
  │    └─ calibracion_laser/ # baterías (P01–P14, Batería 2) + tabla
  ├─ windows_import/         # lo que Constantino pega de la Windows (CostADCAM, VBA, OCR, etc.)
  └─ intercambio/            # scratch para pasar archivos entre Constantino y agentes
```
Confirmá base path, si falta alguna subcarpeta, y espacio en disco.

### 2. Matriz de acceso (completala)
| Carpeta | Agentes (desde Mint) | Constantino (Windows) | Constantino (Mint) | Permiso |
|---|---|---|---|---|
| `planos/` | Lectura | L/E | L/E | RO agentes, RW Constantino (+ Punto si sube DXF) |
| `planos/calibracion_laser/` | Lectura | L/E | L/E | ídem |
| `windows_import/` | Lectura | **L/E** | **L/E** | Constantino pega, agentes leen |
| `intercambio/` | L/E | L/E | L/E | todos R/W |

Definí el **esquema de usuarios Samba**: ¿un usuario único de equipo, o por agente? ¿Cómo mapea a permisos RO/RW? Restringido a la **LAN `190.190.190.0/24`**.

### 3. Qué necesita de Constantino para dejarlo operativo
- **Contraseña de Samba** (la elige él).
- Cualquier otra cosa (confirmar base path, abrir puerto SMB en la LAN, usuario del sistema, etc.) — listá todo lo que dependa de él, explícito.

## Formato
Un solo doc consolidado (`coordination/reports/…` o similar), corto y accionable, listo para que Constantino diga "sí" y ejecuten. Avisame cuando esté.

— Nova
