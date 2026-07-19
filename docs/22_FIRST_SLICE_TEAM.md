> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# First Slice Team

Primera rebanada: panel decorativo -> cotizacion ERPNext -> pieza pendiente -> lote DXF por espesor.

Equipo minimo operativo:
- Nova: direccion de proyecto y decisiones de alcance.
- Bruju: norte cultural y reglas de operacion.
- Atlas: integracion y arquitectura tecnica.
- Forge: ERPNext/Frappe y DocTypes.
- Tango: frontera Tango Gestion y precios maestros.
- Punto: presets, geometria y DXF de piezas.
- Nido: handoff CypCut, lotes y estados de corte.
- Prisma: QA, criterios de aceptacion y pruebas.
- Vega: interfaz vendedor / pantografista / futuro totem.
- Orbit: repo, entorno, CI y scripts.
- Security: permisos y bloqueo de portal publico hasta revision.

Regla: nadie reinventa ERP, Tango, Excel, nesting ni G-code.