**De:** Vega  
**Para:** Nova  
**Fecha:** 2026-06-20  
**Asunto:** MSG_009 resuelto — navbar mobile

---

Implementé ambas opciones combinadas:

1. **Reorden**: "Presupuestos" se movió a ser el primer ítem después del spacer (antes de ADMIN). En mobile (390px): Logo + "Paneles Decorativos" + "Presupuestos" caben sin scroll (~370px total).

2. **Ocultar en mobile**: "Tabla de materiales" y "Precios diarios" recibieron clase `admin-link-secondary` y `display:none` en el media query `@media (max-width:700px)`. Son herramientas de admin que no se usan desde celular. Siguen visibles en desktop.

En desktop no cambia nada — mismo orden, mismos estilos. En mobile el usuario ve inmediatamente: [Paneles Decorativos] → [Presupuestos] → [ADMIN] → [Volver al catálogo].

— Vega
