# Análisis completo del sistema — SistemaIndustrial Nextango

**Preparado por:** Nova  
**Fecha:** 2026-06-11  
**Audiencia:** Constantino Ratti — para verificar que el sistema fue entendido correctamente

---

## A. Lo que el sistema debe lograr

La empresa fabrica piezas metálicas a medida. Tiene máquinas de corte (láser, plasma, oxicorte), plegadoras y probablemente guillotina. El negocio combina muchos tipos de recursos en un solo pedido: chapa por superficie, corte por metros, plegado por cantidad de dobleces, perfiles y barras por metro lineal, productos comerciales, tiempo de máquina.

Hoy ese conocimiento vive en las personas. El vendedor sabe cotizar porque tiene experiencia, no porque el sistema se lo diga. El pantografista sabe qué cortar porque conoce el taller, no porque haya una pantalla que lo guíe. El problema no es que la empresa funcione mal — es que eso no escala, no se puede auditar y es difícil de enseñar.

**Lo que el sistema debe hacer concretamente:**

1. **Cotizar rápido y bien.** El vendedor carga una pieza (panel decorativo, pieza paramétrica, perfil, pieza de biblioteca de cliente) y el sistema calcula automáticamente los recursos: cuánta chapa, cuántos metros de corte, cuántos pliegues, cuántas barras. Con esos recursos y los precios de Tango, arma una cotización en ERPNext.

2. **Organizar la producción por taller.** Cuando el pedido se confirma, el sistema genera piezas pendientes que el pantografista puede ver filtradas por material y espesor. Selecciona las que quiere cortar, el sistema compila un DXF ordenado que va a CypCut para nesting. Después del corte, el estado de cada pieza se actualiza.

3. **Registrar el avance en el taller.** El operario se identifica, elige su rol activo (láser, plegado, guillotina, almacén), ve sus tareas pendientes y registra avance parcial o completo.

4. **Mantener trazabilidad completa.** Para cualquier pieza, el sistema debe poder responder: quién la pidió, cuándo se cotizó, en qué lote se cortó, quién la cortó, si ya se plegó, si ya se entregó.

5. **Integrarse con Tango sin reemplazarlo.** Tango es el sistema fiscal y contable. El sistema sincroniza precios desde Tango, puede generar pedidos importables a Tango, y cuando Tango factura, actualiza el stock en ERPNext.

6. **Tres interfaces a futuro:** workstation del vendedor (interno), tótem para el cliente en la empresa, portal web externo (solo después de una revisión de seguridad).

**Lo que el sistema intencionalmente NO hace:**
- Nesting: lo hace CypCut
- G-code y secuencia de corte: los hace el postprocesador existente
- Contabilidad y facturación fiscal: los hace Tango
- Pricing: lo sigue calculando un humano en Excel; Tango es maestro de precios publicados

---

## B. Lo que está realmente construido hoy

### Funciona y está probado

| Componente | Qué hace | Dónde vive |
|---|---|---|
| Motor de paneles decorativos | Genera DXF real con tresbolillo o patrón DXF repetido, dos submodos (cortar/centrar) | `Programas_hechos/Panel Decorativo/` |
| Adapter al motor legacy | Llama al motor sin modificarlo, recibe resultado | `presets/legacy_panel_adapter.py` |
| Servicio de paneles | Normaliza parámetros, orquesta el adapter, genera outputs JSON | `presets/panel_service.py` |
| UI web local temporal | Formulario HTML + servidor HTTP para cargar paneles y ver cotización | `presets/panel_sales_local_app.py` en `http://127.0.0.1:8765` |
| Preset paramétrico (simple) | Calcula área m² y metros de corte perimetral (borde exterior) | `presets/panel_decorativo.py` |
| Cola de corte | Filtra piezas por material/espesor, expande cantidades | `cutting/cut_queue.py` |
| DXF batch compiler | Agrupa piezas pendientes, genera un DXF con los bounding boxes | `cutting/dxf_batch_compiler.py` |
| Price cache | Cache local de precios Tango, serializable a JSON | `pricing_sync/price_cache.py` |
| Quotation builder | Construye el payload JSON para crear una Quotation en ERPNext | `quoting/quotation_builder.py` |
| Manifiesto JSON | Registro de cada operación con trazabilidad básica | generado por `panel_service.py` |
| Modelos de dominio | `Money`, `PendingCutPart`, `ResourceQuantity`, `PresetQuotation`, etc. | `core/models.py` |
| Boundary Tango | Schemas, Protocol, FakeClient para tests | `tango_sync/` |
| Stock sync | Convierte facturas Tango en movimientos de stock (lógica) | `stock_sync/events.py` |
| DocTypes stub | Definiciones JSON de 6 DocTypes Frappe (no instalados aún) | `doctype/` |
| Tests | Suite completa que pasa — modelos, preset, cola de corte, DXF, price sync, stocks | `tests/` |

### Existe pero está incompleto o tiene problemas

| Componente | Problema |
|---|---|
| **Adapter apuntando al motor equivocado** | `legacy_panel_adapter.py` apunta a `Paneles decorativos funcionando/` — el motor canónico ahora está en `Programas_hechos/Panel Decorativo/` |
| **UI sin selector de submodo** | La UI no tiene campo para elegir entre "cortar en borde" y "figuras completas centradas" — `cut_partial_figures` existe en el modelo pero no está expuesto |
| **Campos `rows`/`columns` inútiles** | Están en el formulario pero el motor no los usa — confunden al usuario |
| **DXF batch = bounding boxes** | El `dxf_batch_compiler.py` genera rectángulos bounding box, no la geometría real de las piezas. Es útil para visualización pero no serviría para corte real |
| **Cálculo de recursos es estimativo** | `panel_decorativo.py` calcula metros de láser como `2 * (ancho + alto)` — eso es el borde exterior del panel, no los metros reales del patrón de agujeros |
| **Motor legacy no calcula cut_length y pierce_count** | El motor de `Programas_hechos/` setea `cut_length_mm=0` y `pierce_count=0` hardcodeados en `CADResultItem`. Los recursos de cotización no tienen estos datos reales |
| **App Frappe no instalada en ERPNext** | Los DocTypes son stubs JSON. No hay bench corriendo, no hay ERPNext al que conectar |
| **Linear cutting solo modelos** | `linear_cutting/models.py` tiene las estructuras pero no hay ninguna lógica, ni optimizador, ni integración |

### No existe

- Pantalla en ERPNext (la UI actual es el servidor local temporal)
- Integración real con Tango (hay Protocol y FakeClient, no cliente HTTP real)
- Flujo de producción por taller (operario, rol activo, avance)
- Flujo de piezas paramétricas (más allá del panel decorativo)
- Flujo de guillotina
- Flujo de plegado
- Biblioteca de piezas de cliente (solo modelo de datos)
- OCR de facturas de proveedor (módulo vacío)
- Portal de cliente (bloqueado intencionalmente hasta revisión de seguridad)

---

## C. La arquitectura tal como la entiendo

El sistema tiene cuatro capas que se comunican de maneras distintas:

```
┌─────────────────────────────────────────────────────────┐
│  ERPNext + App Frappe "sistema_industrial"               │
│                                                         │
│  Documentos ERPNext estándar que el sistema usa:        │
│    Quotation, Sales Order, Item, Stock Entry,           │
│    Work Order (futuro)                                  │
│                                                         │
│  DocTypes propios (SI_*):                               │
│    SI Preset, SI Cut Piece, SI Cut Batch,               │
│    SI Client Piece, SI Tango Price Cache,               │
│    SI Linear Cut Request                                │
│                                                         │
│  Lógica Python (módulos sistema_industrial):            │
│    presets/ → quoting/ → cutting/ → application/       │
│    pricing_sync/ ← tango_sync/ ← stock_sync/           │
└────────────┬────────────────────────┬───────────────────┘
             │                        │
    ┌────────▼────────┐    ┌──────────▼──────────┐
    │  MOTORES        │    │  SISTEMAS EXTERNOS   │
    │  ENCAPSULADOS   │    │                      │
    │                 │    │  Tango Gestión:       │
    │  Programas_     │    │  clientes, artículos,│
    │  hechos/Panel   │    │  precios, facturas,  │
    │  Decorativo/    │    │  comprobantes        │
    │  (Python 3.14,  │    │                      │
    │  motor real     │    │  Excel: pricing       │
    │  de geometría)  │    │  humano              │
    │                 │    │                      │
    │  Futuro: otros  │    │  CypCut: nesting      │
    │  motores en     │    │                      │
    │  Programas_     │    │  Postprocesador:      │
    │  hechos/        │    │  G-code y secuencia  │
    └─────────────────┘    └──────────────────────┘
```

**Regla de la carpeta Programas_hechos:** Constantino va a ir poniendo ahí los programas que ya funcionan y que deben incorporarse al sistema. El equipo los encapsula con un Adapter, no los reescribe. El motor canónico de paneles es `Programas_hechos/Panel Decorativo/`.

**Fuente de verdad por dominio:**

| Qué | Dueño |
|---|---|
| Clientes, proveedores, artículos | Tango |
| Precios publicados | Tango (Excel los calcula, Tango los publica) |
| Precios en cotización | ERPNext (copia sincronizada desde Tango) |
| Cotizaciones y pedidos operativos | ERPNext |
| Stock operativo | ERPNext |
| Facturas y comprobantes fiscales | Tango |
| DXF de piezas | SistemaIndustrial |
| Geometría de patrones | Motor legacy en Programas_hechos/ |

---

## D. Módulos y sus dueños

| Agente | Rol | Dominio técnico | Límite claro |
|---|---|---|---|
| **Nova** | Project Management | Coordinación, prioridades, contratos | No programa directo |
| **Atlas** | Frappe App Core | `core/`, `application/`, `erpnext_extensions/`, `hooks.py`, DocTypes | No configura ERPNext, no hace geometría |
| **Lechu** | ERPNext Manufacturing | Workstations, BOM, Work Orders, Job Cards, flujo de taller en ERPNext | No escribe Python de negocio |
| **Punto** | CAD & Preset Engine | `presets/`, motor legacy, LegacyPanelAdapter, nuevos presets | No hace nesting, no administra ERPNext |
| **Nido** | CypCut Bridge & Cut Queue | `cutting/` (queue, DXF compiler, repository), SI Cut Batch | No hace nesting ni CAM |
| **Tango** | Tango Integration | `tango_sync/`, `pricing_sync/`, `stock_sync/` | No crea DocTypes, no toca ERPNext salvo via boundary |
| **Gemu** | Linear Cutting | `linear_cutting/`, SI Linear Cut Request | No toca chapa ni nesting |
| **Vega** | Frappe UI | Form scripts, Print Formats, portal, dashboards | No escribe lógica Python |
| **Orbit** | DevOps & Infra | bench, CI/CD, `pyproject.toml`, deploy | Sin él ERPNext no existe |

**Regla de zoo (del documento original):** cada agente tiene su jaula. Si cruza la jaula, pide permiso primero.

---

## E. La rebanada actual de paneles

**Objetivo de la rebanada:** Panel decorativo → cotización en ERPNext, con DXF generado, recursos calculados y trazabilidad lista para taller.

### ✅ Qué está hecho

1. El motor de geometría en `Programas_hechos/Panel Decorativo/` genera DXF reales con tresbolillo o patrón DXF externo, con dos submodos (cortar en borde / figuras completas centradas).
2. El adapter conecta ese motor al sistema sin modificarlo.
3. La UI local muestra un formulario donde se carga el panel, se genera el DXF y aparece la cotización base.
4. Los outputs (DXF, panel_result.json, quotation_payload.json, cut_piece_payload.json, manifest.json) se generan correctamente.
5. La cola de corte puede recibir la pieza pendiente y generar un DXF de lote por material/espesor.

### ⚠️ Qué está roto o mal

1. **El adapter apunta al motor equivocado.** Usa `Paneles decorativos funcionando/` en lugar de `Programas_hechos/Panel Decorativo/`. Punto tiene que corregirlo.

2. **Faltan dos parámetros clave en la UI:**
   - Selector de submodo: "Cortar en borde" vs "Figuras completas centradas" (`cut_partial_figures`)
   - El campo "margen sin perforar" existe en el formulario como `margin_mm` pero el label no es claro. Debe decir exactamente qué es.

3. **Campos `rows` y `columns` están en la UI pero no hacen nada.** El motor los ignora. Hay que eliminarlos del formulario.

4. **Los recursos calculados son imprecisos.** `panel_decorativo.py` calcula metros de láser como el perímetro exterior del panel (2 × ancho + 2 × alto). Eso no es lo que se corta — lo que se corta es el patrón de agujeros, que puede ser centenares de metros más. El motor legacy tampoco calcula esto (hardcodea `cut_length_mm=0`). **Este es el gap más importante para la cotización real.**

5. **La cotización está en JSON, no en ERPNext.** No hay bench ni instancia ERPNext corriendo. El `quotation_payload.json` existe pero no se puede cargar en ERPNext todavía.

6. **El DXF de lote usa bounding boxes.** El `dxf_batch_compiler.py` no incluye la geometría real de los agujeros — dibuja el rectángulo exterior de cada pieza. Para cotizar está bien, para cortar no sirve. Esto es una simplificación intencional del MVP pero hay que tenerlo claro.

### ❌ Qué falta para completar la rebanada

- Corrección del adapter (apuntar a Programas_hechos)
- Agregar el selector de submodo a la UI
- Eliminar rows/columns del formulario
- Instalar la app en ERPNext real (bench) — sin esto, Constantino no puede ver la cotización en ERPNext
- UI de vendedor dentro de ERPNext (Vega) — el formulario local es una muleta temporal
- Investigar y resolver el cálculo de `cut_length_mm`: ¿el motor legacy puede calcularlo? ¿o hay que calcularlo desde la geometría generada?

---

## F. Decisiones tomadas y por qué

### Decisión principal: empezar de cero con NexTango

El repo original `Sistema-Industrial` (creado en mayo 2026) tomó un camino diferente:
- Intentó hacer nesting propio, G-code propio, CAM propio
- Construyó "autonomous orchestration infrastructure"
- Tenía 31+ documentos de arquitectura, muchos en estado DRAFT
- 11 branches de Codex generando código para nesting, CAD, CAM, event buses
- El equipo usaba 8 plataformas IA distintas (ChatGPT, DeepSeek, Gemini, Copilot, Qwen, Mistral, Claude, Mistral)

Ese camino estaba reinventando cosas que ya existen y funcionan (CypCut para nesting, el postprocesador para G-code). Había demasiada complejidad sin foco.

**Decisión (Constantino, junio 2026):** Restart limpio con NexTango, usando ERPNext como columna vertebral y eliminando lo que ya está resuelto externamente. Menos arquitectura, más rebanadas finas de punta a punta.

### Otras decisiones vinculantes

| Decisión | Motivo |
|---|---|
| App Frappe propia, no modificar core ERPNext | Permite actualizar ERPNext sin perder cambios propios |
| No hacer nesting ni CAM | CypCut y el postprocesador ya lo resuelven |
| Excel preservado como pricing humano | El flujo humano funciona y no debe romperse abruptamente |
| Tango via API, no via archivo | Integración más robusta y automática |
| Motores legacy encapsulados sin reescribir | Funcionan; reescribirlos es riesgo sin beneficio |
| Carpeta Programas_hechos/ como repositorio de motores | Permite incorporar nuevos programas de forma ordenada |

---

## G. Lo que falta para cada fase

### Fase actual (primera rebanada — panel decorativo)

- [ ] Corregir adapter → `Programas_hechos/Panel Decorativo/` (Punto)
- [ ] Agregar selector de submodo a la UI (Punto)
- [ ] Eliminar rows/columns del formulario (Punto)
- [ ] Instalar ERPNext + bench en el equipo local (Orbit)
- [ ] Instalar la app sistema_industrial en el bench (Orbit + Atlas)
- [ ] Primera pantalla del vendedor en ERPNext (Vega)
- [ ] Resolver cálculo real de cut_length_mm (Punto + Atlas)

### Fase 2 — ampliar presets y cotización

- [ ] Preset de pieza paramétrica simple (rectángulo con perforaciones libres) (Punto)
- [ ] Cotización multi-ítem en ERPNext (Atlas)
- [ ] Integración real con Tango API (Tango agent)
- [ ] Sync de precios Tango → ERPNext (Tango agent)
- [ ] Primera UI de taller: pantografista ve piezas pendientes por espesor (Lechu + Vega)

### Fase 3 — taller y producción

- [ ] Corte lineal con optimizador y regla del 65% (Gemu)
- [ ] Biblioteca de piezas de cliente: DXF fijos por carpeta de cliente (Atlas + Punto)
- [ ] Estados de pieza completos (14 estados) en ERPNext (Lechu + Atlas)
- [ ] Flujo de plegado: detección, tareas, agrupamiento por matriz (Lechu)
- [ ] Flujo de guillotina: detección automática de piezas rectangulares sin perforaciones (Nido + Lechu)
- [ ] OCR de facturas de proveedor (módulo dedicado)
- [ ] Trazabilidad completa: log auditado por usuario/rol

### Fase 4 — interfaces externas

- [ ] Portal de cliente / tótem (post-revisión de seguridad)
- [ ] Reportes de producción para dirección
- [ ] Roles dinámicos en ERPNext (usuario elige rol activo)

---

## H. Riesgos e inconsistencias que identifico

### Riesgo alto

**1. ERPNext existe pero está virgen y no está corriendo.**
Hay una instancia Docker de ERPNext (`erpnext.local:8080`) pero está prácticamente sin configurar — no tiene la app sistema_industrial instalada, no tiene DocTypes, ni datos. Adicionalmente Docker Desktop no puede arrancar porque WSL necesita actualización (`wsl --update` como administrador resuelve eso). El equipo aún no llegó a esta etapa intencionalmente — primero se está construyendo el código y la arquitectura. Cuando ERPNext sea el siguiente hito, Orbit instala bench + la app, y desde ahí se trabaja en contexto real.

**2. Los cálculos de recursos no son los reales.**
El `panel_decorativo.py` calcula metros de láser como el borde exterior del panel. Para un panel de 300×200 son 1 metro. Pero un panel con tresbolillo de agujeros de 20mm puede tener 50, 100 metros de corte real. El motor legacy tampoco lo calcula (hardcodea 0). La cotización que genera el sistema hoy subestimaría masivamente el costo de corte.

**3. El adapter apunta al motor equivocado.**
`legacy_panel_adapter.py` apunta a `Paneles decorativos funcionando/` pero el motor canónico está en `Programas_hechos/Panel Decorativo/`. Esto significa que el sistema está usando el motor anterior, no el que Constantino indicó como fuente de verdad.

### Riesgo medio

**4. Dos piezas de código con propósito solapado.**
`panel_decorativo.py` (preset simple, calcula recursos paramétricos) y `legacy_panel_adapter.py` (llama al motor real) hacen cosas distintas pero relacionadas. Para la cotización se usa el preset simple con métricas incorrectas, y el motor real solo se usa para generar el DXF. A largo plazo esto debería unificarse: los recursos cotizados deben venir del motor real (que sí conoce la geometría real).

**5. DocTypes sin instalar.**
Hay 6 DocTypes definidos como stubs JSON pero ninguno está instalado en ERPNext. No se puede desarrollar ni probar el flujo ERPNext sin un bench.

**6. Equipo nuevo en documentación vieja.**
Los docs `docs/09_ENGINEERING_ORG.md` y `docs/29_AGENT_ZOO.md` mencionan "Forge" como agente activo pero el equipo tiene "Lechu". Si algún agente lee esos docs para orientarse, va a encontrar inconsistencias.

### Inconsistencias menores

- El DXF de lote usa bounding boxes, no geometría real. Está bien documentado como limitación del MVP, pero si alguien lo manda a CypCut como está, el nesting no tendría las formas reales.
- `rows` y `columns` existen en el formulario, el modelo y el adapter, pero el motor no los usa. Son campos fantasma que confunden.
- El `Paneles decorativos funcionando/` sigue existiendo pero ya tiene un sucesor. No está claro cuándo se puede eliminar.
- La UI local (`http://127.0.0.1:8765`) es una muleta temporal. No hay fecha ni plan para moverlo a ERPNext.
- `linear_cutting/models.py` define estructuras de datos pero no tiene ninguna lógica. La regla del 65% (si la última barra supera 65% del largo estándar, cotizar barra entera) no está ni documentada en el código.

---

## I. Preguntas y sugerencias propias

**1. ¿Cuándo se instala ERPNext?**
Este es el bloqueante más importante del proyecto. Todo el sistema apunta a ERPNext pero sin un bench instalado no hay contexto real para probar. Mi sugerencia: que Orbit instale bench + ERPNext en el entorno local como primer hito, antes de que Vega diseñe ninguna pantalla.

**2. ¿Cómo se calculan los metros reales de corte?**
El motor legacy genera la geometría completa de los agujeros/patrón. Es técnicamente posible calcular el perímetro real de todos los contornos a partir de las figuras generadas. ¿Queremos que el motor legacy devuelva eso, o lo calculamos en un paso posterior? Esta decisión afecta directamente la precisión de la cotización.

**3. ¿Qué pasa con el repo original Sistema-Industrial?**
Tiene 11 branches de Codex con nesting, CAM, G-code, autonomous infrastructure. ¿Se archiva? ¿Se extrae algo de ahí? Hay código valioso en los módulos CAD (geometría, DTOs) que podría ser referencia para Punto, aunque la decisión de no reimplementar nesting/CAM está clara.

**4. ¿Las piezas de cliente son DXF fijos en carpetas?**
Entendí que la biblioteca de piezas de cliente incluye DXF fijos por cliente (un panel específico que ese cliente pide repetido). ¿Cómo se organiza esa carpeta? ¿Por cliente/pieza? ¿Quién la mantiene? Este flujo puede ser el segundo más importante después del panel, porque acelera enormemente la cotización de clientes recurrentes.

**5. Sugerencia: calcular cut_length desde el motor.**
Una mejora de alto valor con esfuerzo moderado: en lugar de que el motor devuelva `cut_length_mm=0`, calcular el perímetro total de todas las figuras generadas (suma de longitudes de todos los segmentos en `geometry_items`). Eso daría una cotización de metros de corte real y diferenciaría enormemente al sistema de una simple hoja de cálculo.

**6. Sugerencia: el DXF de lote debería incluir la geometría real.**
El `dxf_batch_compiler.py` compila piezas como rectángulos bounding box. Para que CypCut pueda hacer nesting real, el DXF debería incluir la geometría real del patrón, no el bounding box. Esto requiere que el motor devuelva el DXF individual de cada pieza y el compilador los ensamble. No es para el MVP, pero es la diferencia entre un demo y un sistema que sirve para producción real.

---

## Resumen ejecutivo para Constantino

**El sistema entiende correctamente el negocio.** La arquitectura elegida (ERPNext + app Frappe propia + motores encapsulados + integraciones sin reemplazar lo que funciona) es sólida y pragmática.

**El estado actual es una base, no un producto.** El motor de paneles funciona y genera DXF reales. La cotización se genera. Los tests pasan. Pero todo vive en un servidor local temporal, ERPNext no está instalado, y los cálculos de recursos son estimativos.

**Los tres problemas más urgentes son:**
1. Instalar ERPNext (Orbit) — sin esto nada puede probarse en contexto real
2. Corregir el adapter al motor correcto (Punto) — ahora mismo usa el motor viejo
3. Agregar el selector de submodo a la UI (Punto) — falta un parámetro fundamental del panel

**Los dos gaps más importantes a mediano plazo son:**
1. Calcular los metros reales de corte del patrón — la cotización actual es inexacta
2. Conectar los DXF reales al batch compiler — hoy el lote tiene bounding boxes, no geometría

El equipo conoce el dominio y la dirección es correcta. La clave ahora es instalar la plataforma y hacer que la primera rebanada llegue a una pantalla de ERPNext.
