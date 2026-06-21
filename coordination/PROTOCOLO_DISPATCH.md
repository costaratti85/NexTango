# Protocolo de activación del equipo — Dispatch

**Versión:** 1.0  
**Fecha:** 2026-06-17  
**Autor:** Nova

---

## Roles

| Rol | Responsabilidad |
|---|---|
| **Constantino** | Define qué se necesita. Habla solo con Nova. |
| **Nova** | PM. Escucha a Constantino, parte el trabajo, delega, controla, reporta. |
| **Dispatch** | Orquestador técnico. Lee la cola de activaciones de Nova y envía mensajes a las sesiones del equipo. |
| **Agentes** (Punto, Atlas, Vega, etc.) | Ejecutan tareas. Leen su inbox, trabajan, escriben el report. |

---

## Estructura de directorios

```
coordination/
  inbox/          # Tareas pendientes (Nova escribe, agentes leen)
  reports/        # Reportes de tareas completadas (agentes escriben, Nova lee)
  dispatch/
    queue.json    # Cola de activaciones (Nova escribe, Dispatch lee y limpia)
    sessions.json # Session IDs del equipo (referencia permanente)
```

---

## Session IDs del equipo

Ver `coordination/dispatch/sessions.json`.

---

## Flujo completo

```
Constantino → Nova → [escribe inbox + queue] → Dispatch → Agente
                                                              ↓
Nova ← Dispatch ← [detecta report file] ←──────────── Agente escribe report
  ↓
Constantino
```

### Paso a paso

1. **Constantino le pide algo a Nova**

2. **Nova hace el PM work:**
   - Parte la tarea en ítems concretos
   - Escribe el brief en `coordination/inbox/AGENTE_TASK_XXX_DESCRIPCION.md`
   - Actualiza `coordination/dispatch/queue.json` con la activación pendiente

3. **Dispatch lee `queue.json`** (polling periódico o trigger manual):
   - Ve que hay una entrada pendiente para Punto
   - Envía el mensaje de activación a la sesión de Punto
   - Elimina la entrada de `queue.json` (marca como despachado)

4. **Punto despierta, lee su inbox, trabaja**

5. **Punto termina:**
   - Escribe `coordination/reports/PUNTO_TASK_XXX_REPORT.md`
   - El archivo nuevo es la señal de "done"

6. **Dispatch detecta el report nuevo** (polling sobre `coordination/reports/`):
   - Envía mensaje a Nova: "Nova, Punto terminó TASK_XXX."

7. **Nova lee el report, evalúa, reporta a Constantino**

---

## Formato de `queue.json`

Nova escribe en este archivo cuando hay agentes que activar. Dispatch lo lee, procesa, y limpia.

```json
{
  "pending": [
    {
      "agent": "Punto",
      "session_id": "local_fdd69f9d-3224-4e94-b8e9-c4ba5ae7d6ec",
      "tasks": ["PUNTO_TASK_017", "PUNTO_TASK_018"],
      "queued_at": "2026-06-17T21:30:00"
    }
  ],
  "dispatched": []
}
```

Cuando Dispatch procesa una entrada, la mueve de `pending` a `dispatched` con un campo `dispatched_at`.

---

## Mensaje de activación (Dispatch → Agente)

Simple y genérico. El agente lee su propio inbox para los detalles.

```
[Agente], tenés tareas nuevas asignadas. Leé tu inbox en `coordination/inbox/` 
y trabajá en las tareas pendientes en orden de prioridad.

Al terminar cada tarea, escribí el reporte en `coordination/reports/` 
siguiendo el formato [AGENTE]_TASK_XXX_REPORT.md.
```

---

## Detección de "done" por Dispatch

Dispatch hace polling sobre `coordination/reports/`. Cuando aparece un archivo nuevo:
- Extrae el agente y el número de tarea del nombre del archivo
- Notifica a Nova via `send_message` a la sesión de Nova

**No se requiere ningún archivo "done" adicional** — el report file ES la señal.

---

## Naming conventions

| Tipo | Formato | Ejemplo |
|---|---|---|
| Inbox | `AGENTE_TASK_NNN_DESCRIPCION.md` | `PUNTO_TASK_017_NAVBAR_Y_ADMIN.md` |
| Report | `AGENTE_TASK_NNN_REPORT.md` | `PUNTO_TASK_017_REPORT.md` |
| Queue entry (agent field) | Nombre del agente en mayúsculas | `"Punto"` |

---

## Qué hace Nova (resumen)

✅ Escuchar a Constantino  
✅ Escribir briefs en `coordination/inbox/`  
✅ Actualizar `coordination/dispatch/queue.json`  
✅ Leer reports cuando Dispatch avisa  
✅ Reportar a Constantino  

❌ No escribe código  
❌ No ejecuta comandos  
❌ No toca archivos fuera de `coordination/`, `docs/`, `memory/`  
