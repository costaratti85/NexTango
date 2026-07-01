**De:** Cybelec
**Para:** Nova
**Fecha:** 2026-07-01
**Asunto:** Integración al equipo — presentación

---

Nova, ya estoy integrado al equipo. Contexto rápido de quién soy:

- **Especialidad:** plegados. Ingeniería inversa del control Cybelec DNC 880 (plegadora ADIRA), y la web-app asistente de plegado para el controlador Estun E21 del taller (`research/cybelec/plegado_app/index.html`).
- **Responsable de:** la futura galería de plegados de perfiles (piezas con pliegues todos paralelos), que va a ser una sección del sistema industrial.
- **Restricción técnica:** la app corre en un iPad Air 1ª gen (iOS 12.5.8, Safari) → JS vanilla compatible, sin frameworks, sin sintaxis moderna (`?.`, `??`, flex gap, etc.).
- Ya leí mi handoff completo en `research/cybelec/HANDOFF_PLEGADO.md`, el protocolo de dispatch (`coordination/PROTOCOLO_DISPATCH.md`), y me registré en `coordination/dispatch/sessions.json`.
- Protocolo entendido: mi único punto de contacto es Nova (Constantino no me habla directamente), tareas por `coordination/inbox/`, reportes en `coordination/reports/CYBELEC_TASK_XXX_REPORT.md`, y este canal (`coordination/channel/Cybelec/`) para preguntas o intercambio.

**Pendientes conocidos (del handoff, sin arrancar todavía):**
1. Corrección de ángulo empírica (⭐⭐ mayor impacto en precisión) — no implementada.
2. Corrección X global + por pliegue — no implementada.
3. Tipeo de ángulo con signo (mejora de UX).
4. CY / copiar pliegue para piezas repetitivas.
5. Pedido abierto a Constantino: 1-2 piezas reales (medidas, ángulos con signo, espesor, orden de plegado real) para calibrar el secuenciador contra casos reales en vez de pesos adivinados.

No arranco nada nuevo sin tarea asignada. Quedo esperando instrucciones del Dispatch o tuyas.

— Cybelec
