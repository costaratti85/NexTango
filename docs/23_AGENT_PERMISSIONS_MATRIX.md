# Agent Permissions Matrix

| Agente | Puede cambiar | No puede cambiar | Debe consultar |
|---|---|---|---|
| Nova | Roadmap, prioridades, contratos | Codigo sin issue/tarea | Cambios de alcance |
| Atlas | Integraciones, boundaries, arquitectura | Core ERPNext, core Tango | Conflictos entre sistemas |
| Forge | App Frappe, DocTypes, workflows ERPNext | Core ERPNext | Campos maestros sensibles |
| Tango | Adaptadores Tango, schemas, cache precios | Contabilidad real sin sandbox | Escritura real en Tango |
| Punto | Presets, DXF pieza, geometria | Nesting y G-code | Cambios de parametros industriales |
| Nido | Lotes, estados pieza, handoff CypCut | CAM propio | Cambios en postprocesador existente |
| Gemu | Corte lineal, barras, sobrantes | Chapa/nesting | Reglas de remanentes |
| Vega | UX vendedor/taller/totem | Reglas de negocio | Cambios que afecten operacion humana |
| Prisma | Tests, fixtures, DoD | Reglas de negocio sin validar | Casos ambiguos |
| Orbit | CI, scripts, repo | Logica industrial | Secretos / infraestructura real |
| Security | Permisos, auditoria, portal gate | Pricing/produccion | Exposicion publica |

Toda decision automatica debe dejar rastro auditable.
