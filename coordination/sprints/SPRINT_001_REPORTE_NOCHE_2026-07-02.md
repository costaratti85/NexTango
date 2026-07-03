# Sprint 001 — Reporte consolidado de la noche (2026-07-01 → 02)

**De:** Nova
**Para:** Constantino
**Estado general:** Las dos herramientas principales (Panel Decorativo y Plegados/Bandeja) están migradas a Frappe con backend + frontend completos, desplegadas y parcialmente verificadas en el servidor. En una noche se completó lo planificado para ~2 semanas del sprint.

---

## 1. Qué se construyó esta noche (11 entregas)

| # | Agente | Entrega | Estado en servidor |
|---|---|---|---|
| 1 | Atlas | Items ERPNext (BANDEJA, SRV-CORTE-LASER, SRV-PLEGADO) + Price List "Precio Standard" | ✅ vivo |
| 2 | Punto | Backend Fase 1: 4 doctypes (Material Corte, Precios Globales, Presupuesto Panel + líneas), 6 roles, api/materiales, api/paneles, migración | ✅ vivo |
| 3 | Vega | CSS bundle + Desk Page **panel-decorativo** completa (factores en vivo, DXF descarga directa) | ✅ vivo |
| 4 | Vega | Cliente → Link a Customer con typeahead + galería de patrones auto-activable | ✅ vivo |
| 5 | Punto | api/patrones (contrato de Vega) + 11 thumbnails | ✅ vivo |
| 6 | Punto | Backend plegados: doctype SI Pedido Plegado + api/plegados completa | ✅ vivo |
| 7 | Vega | Desk Page **plegados-complejos** completa (desglose por componente de la fórmula) | ✅ vivo |
| 8 | Punto+Vega | Fix campo `cantidad` + costo unitario/total | ✅ vivo y testeado |
| 9 | Cybelec | Zoom centrado en pliegue + Guardar DXF como... + corrección empírica de ángulo (extra) | ✅ (app local iPad) |
| 10 | Atlas | Push de clientes Tango→ERPNext (upsert por si_tango_code, 14/14 tests, smoke test idempotente) | ✅ código listo, run masivo pendiente |
| 11 | Forge | 4 ciclos de deploy + 3 fixes de infraestructura (patches.txt, autoname Floats, permisos nginx) + test end-to-end | ✅ |

**Verificación funcional más importante:** Forge creó un pedido real vía API (`BAN-2026-00001`, cantidad 3) y la matemática del modelo de factores dio exacta. El motor de bandeja funciona en el servidor.

## 2. Para probar hoy

- **Panel Decorativo:** `http://190.190.190.20/app/panel-decorativo`
- **Plegados:** `http://190.190.190.20/app/plegados-complejos`
- **Materiales (admin):** Desk → SI Material Corte (28 cargados)
- **Precios globales:** Desk → SI Precios Globales
- Login: administrator (o usuarios con roles `SI *`)

**Antes de probar costos, cargá:** `precio_por_plegado` (SI Precios Globales) y `precio_plegar_por_kg` (por material) — están en $0 porque no existían en el sistema viejo. Sin eso, el componente plegado cotiza $0.

## 3. Pendientes al cierre de la noche

| Pendiente | Owner | Estado |
|---|---|---|
| Copiar `daily_prices.json` al servidor + re-migrar → `precio_por_kg` reales | Forge | instrucción enviada (MSG_015), sin confirmar |
| Prueba live de `api.paneles.calcular` (plegados ya PASS; paneles usa el motor legacy) | Forge | ídem |
| Copiar 5 patrones DXF desde `//190.190.190.9/Ventas/` al servidor | Forge | ídem — hasta entonces la galería los muestra "no disponibles" |
| Verificar Quotation contra Customer (bug `is_billing_contact`) | Forge | probablemente resuelto por los migrates, sin confirmar |
| Aclarar 28 vs 30 materiales migrados | Forge | ídem |
| **Run masivo de 8.426 clientes** | Tango | reasignado (Atlas bloqueado por SI_NEXUS_KEY) |
| Planning doc de Tango | Tango | debe desde ayer |

## 4. Decisiones que solo vos podés tomar

1. **Valores de `precio_plegar_por_kg` (por material) y `precio_por_plegado`** — hoy $0. ¿Cuánto valen?
2. **SI_NEXUS_KEY:** no está documentado en el repo; Atlas no pudo correr el sync. Si Tango tampoco lo ejecuta, necesitamos que proveas el token — y sugiero documentarlo en `coordination/SERVIDOR_ERPNEXT.md` como el resto de las credenciales.
3. **Validación del motor de recursos** (Punto, MSG_045): las velocidades de corte (ej: hierro 0.56mm → 180 mm/s; inox 2.5mm → 43 mm/s) y tiempos de perforación no tienen fuente documentada. Ahora que el precio se construye sobre estos números, ¿los validamos contra la máquina real (pesar piezas, cronometrar)?
4. **Cybelec — corrección empírica:** hoy es por-pieza. ¿La preferís pegada al juego de útiles + espesor?

## 5. Incidencias de coordinación (para el registro)

- Forge necesitó 3 insistencias para pasar de deploys estructurales a verificación funcional — cuando lo hizo, la calidad fue excelente (bug de autoname diagnosticado de raíz).
- Atlas entregó una task fuera de plan (api/presupuestos sobre el servidor standalone deprecado) — redirigido; la parte ERPNext se conserva.
- Tango fue el único agente sin actividad en toda la noche.

— Nova
