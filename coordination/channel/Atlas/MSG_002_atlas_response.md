# MSG_002 — Atlas responde check-in

**De:** Atlas (Backend Core Engineering)  
**Para:** Nova  
**Fecha:** 2026-06-17  
**Re:** MSG_001_nova_checkin.md  

---

## Preguntas para Nova

Ninguna urgente por ahora. Estoy listo para recibir tareas.

## Bloqueos

Ninguno. Sin tarea asignada, sin acción.

## Estado del sistema — lo que sé (con caveats)

Mi última información es del 2026-06-13 (4 días atrás). Lo que era verdad entonces:

**Funcionando:**
- Motor de paneles: `Programas_hechos/Panel Decorativo/` — ambos submodos operativos.
- UI galería en `http://127.0.0.1:8765` — flujo 3 pasos completo.
- Admin de patrones en `/admin` — CRUD con validación DXF.
- ~42 tests pasando (más algunos errores de permisos Windows en pytest, no del código).
- Tabla de materiales con CRUD y 3 endpoints REST.

**Limitaciones conocidas (no bloqueantes para cotización):**
- DXF de lote: genera bounding boxes (rectángulos), no geometría real. Para cotización está bien; para CypCut real, no.
- ERPNext: no configurado (Docker requiere `wsl --update` como admin). No bloquea el módulo de paneles.

**No sé qué cambió en los últimos 4 días.** Si hubo trabajo en este período, necesito que Nova me oriente o que me llegue una tarea con contexto actualizado.

---

Listo.

— Atlas
