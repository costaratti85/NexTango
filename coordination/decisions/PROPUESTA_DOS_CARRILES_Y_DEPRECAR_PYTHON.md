# PROPUESTA — Dos carriles de trabajo + deprecar la rama Python

**Estado:** 🟡 PROPUESTA — **NO implementada.** Para aprobación de Constantino antes de tocar nada.
**Autora:** Nova · **Fecha:** 2026-07-21
**Origen:** rumbo estratégico definido por Constantino

---

## 1. Dos carriles de trabajo

De acá en más, cada tarea vive en **uno** de dos carriles. Esto no es burocracia: es para no volver a mezclar "lo que le sirve hoy" con "el sistema que algún día lo reemplaza" — que es de donde salieron varias vueltas (la página de precios, el modelo de clientes).

### 🟢 Carril "YA" — empalmar lo nuevo con lo viejo

**Objetivo:** que lo que construimos **le sirva HOY**, encajando en cómo trabaja Constantino ahora mismo.

**Cómo trabaja hoy (su realidad, que el carril YA respeta tal cual):**
- Su agenda de clientes es **una carpeta con un Excel por cliente**.
- Dentro de cada Excel, **cada hoja es un presupuesto**.
- El "cliente" **es simplemente el nombre del Excel** donde pega.

**Qué hace el "Programa YA":**
- **NO pregunta qué cliente es.** El cliente no existe en este carril — es el nombre del Excel, y eso lo maneja Constantino, no el sistema.
- **Genera la información** — cálculo/cotización + datos de la pieza/panel — en un formato que Constantino **copia y pega** en los presupuestos y órdenes de trabajo que **ya usa**.
- Se mide por una sola cosa: **¿le ahorró trabajo hoy?**

### 🔵 Carril "LARGO PLAZO" — el sistema que reemplaza los Excels

**Objetivo:** el sistema que algún día **reemplaza** la carpeta de Excels.

Acá va **todo el modelo de clientes** que veníamos hablando, y que **NO va en el carril YA**:
- Agenda de clientes en **ERPNext**, por nombre.
- **Tabla de CUITs habituales** por cliente.
- Al **facturar**: elegir entre CUIT habitual o **"consumidor final"** sin CUIT.
- El **presupuesto NO pide CUIT ni documento** (el documento es cosa de la factura, no del presupuesto).

Se mide por otra cosa: **¿nos acerca a jubilar los Excels?** No tiene que servir hoy — tiene que ser correcto para el día que reemplace.

### La regla que separa los carriles

> Si una tarea **pregunta por el cliente / CUIT / identidad fiscal** → es **LARGO PLAZO**.
> Si una tarea **produce algo que Constantino copia y pega hoy** → es **YA**.

---

## 2. Deprecar la rama Python

### La decisión propuesta

**Deprecar el sistema standalone en Python** que precedió a ERPNext. Hoy **ERPNext funciona igual o mejor** que lo desarrollado en Python, y ya encontramos evidencia de que parte de ese Python estaba **muerto** (el modelo de precios `pricing_sync` / `sync_from_tango`, inerte).

### 🔴 DISTINCIÓN CRÍTICA — no todo lo que es Python se depreca

Esto es exactamente el tipo de decisión donde un agente puede **pasarse de la raya** (como con `DECISION_017`) y archivar algo que está **vivo**. Antes de aprobar, hay que separar tres cosas que son todas "Python":

| Categoría | Ejemplos | ¿Se depreca? |
|---|---|---|
| **A. Standalone que ERPNext ya reemplazó** | el viejo programa de precios que se corría a mano, `pricing_sync/`/`sync_from_tango.py` (ya inerte) | ✅ **SÍ** — es lo que la decisión apunta |
| **B. Python que ERPNext LLAMA en producción** | el **motor standalone de Panel Decorativo** (`Programas_hechos/Panel Decorativo/main.py`) — lo importa `panel_sales_local_app.py` y **sirve el panel HOY** | ❌ **NO** — está vivo, es el que corre |
| **C. Herramientas standalone propias, fuera de la app** | **CostADCAM** (postprocesador G-code), 1DNest, conversores DXF, OCR | ❌ **NO** — son herramientas nuestras válidas (`DECISION_002` §2, `DECISION_004`) |

**"Deprecar la rama Python" = deprecar la categoría A.** Las B y C **no se tocan**: B porque está en el camino de producción, C porque son herramientas legítimas que nunca fueron "el sistema a reemplazar".

⚠️ **Verificación previa obligatoria antes de archivar cualquier cosa:** confirmar que no esté importada/llamada desde la app ERPNext viva. El motor de Panel Decorativo es el ejemplo de por qué: parece "un Python standalone más", pero es lo que sirve la pantalla.

### Cómo archivar SIN borrar historia

- **No `git rm` a secas.** Mover el código de categoría A a una carpeta `deprecated/` (o `archive/`) dentro del repo, con un `README` que explique **qué era, por qué se deprecó, y qué lo reemplaza en ERPNext**.
- La historia de git **se preserva** (mover ≠ borrar; los commits siguen).
- Un **tag git** `pre-erpnext-python-final` en el último commit donde el standalone estaba vivo, para poder volver a mirarlo si hace falta.
- Marcar las tasks asociadas (`TASK_003/006_TANGO_PRICE_CACHE`, etc.) como **obsoletas**, no borrarlas — consistente con el "por ahora no borren nada".

Sigue vigente que **nada se archiva sin tu OK** y sin la verificación de la tabla de arriba.

---

## 3. Estructura de ramas / organización

### Opción propuesta: **carriles por etiqueta, no por rama nueva**

No propongo ramas git nuevas para los carriles. Las ramas ya tienen dueño (`erpnext`, `feat/<agente>`), y partir por "YA/largo plazo" a nivel git duplicaría worktrees sin ganancia — el mismo agente toca los dos carriles.

En cambio:
- **Un campo `carril` en cada tarea de `queue.json`**: `YA` | `LARGO_PLAZO` | `INFRA`.
- Un doc `coordination/CARRILES.md` con la definición y la lista viva de qué hay en cada uno.
- El foco de sprint se declara por carril ("este sprint, todo YA salvo X").

*Alternativa si preferís separación dura:* una rama `largo-plazo` donde vive el modelo de clientes/facturación mientras no se activa, para que no se mezcle con lo productivo. Cuesta más mantenimiento. **Recomiendo la etiqueta**; la rama solo si querés aislamiento físico.

### Clasificación de las tareas abiertas hoy

| Tarea | Carril | Nota |
|---|---|---|
| Fix tileo X / patrones (Philo) | 🟢 **YA** | genera el panel que Constantino usa hoy |
| Thumbnails (backfill Philo + autogen) | 🟢 **YA** | |
| Diálogo "Actualizar patrón" compacto | 🟢 **YA** | |
| Fix caché `load_patterns` | 🟢 **YA** | |
| Página de precios editable (carga manual) | 🟢 **YA** | es carga del vendedor para copiar/pegar |
| Limpieza PriceCache + fuente única de precios | 🟢 **YA** | (y toca la categoría A del Python muerto) |
| Simulador de movimiento / cálculo de recursos (Punto) | 🟢 **YA** | alimenta la **cotización** que se copia/pega |
| Contrato DXF postprocesador (CostADCAM) | 🟢 **YA** | categoría C — herramienta viva |
| **Agenda de clientes en ERPNext** | 🔵 **LARGO PLAZO** | |
| **CUITs habituales + consumidor final** | 🔵 **LARGO PLAZO** | |
| **Tango: 15 renames de clientes** (`\n`) | 🔵 **LARGO PLAZO** | es data de clientes → del modelo futuro. Refuerza dejarlo pospuesto |
| **MES / estados por pieza (Lechu)** | 🔵 **LARGO PLAZO** | sigue en pausa |
| **Nido — compilador de lote** | 🔵 **LARGO PLAZO** | depende del modelo de piezas de MES |
| **OCR proveedores** | 🔵 **LARGO PLAZO** | escribe a Tango/ERPNext/stock; parte clave del sistema futuro |
| Relevamiento pricing/comercial (Orbit) | ⚙️ **INFRA** | transversal |
| Lectura Brújula / DECISION_017 | ⚙️ **INFRA** | transversal |
| Deprecación rama Python (esta propuesta) | ⚙️ **INFRA** | |
| Copia canónica del deploy | ⚙️ **INFRA** | resuelto |

**Lectura de conjunto:** casi todo lo activo hoy es **YA**. Todo lo que está **en pausa** cae en **LARGO PLAZO** — lo cual **valida las pausas que ya pusiste**: no estabas frenando trabajo urgente, estabas separando carriles sin tener el nombre todavía.

---

## 4. Qué apruebo yo y qué te toca a vos

- **Estructura de carriles (etiqueta vs rama), forma de archivar el Python, clasificación de tareas** → decisión de **organización**, la propongo yo y la puedo ejecutar apenas apruebes el enfoque.
- **La definición de negocio de cada carril** (qué es YA, qué es largo plazo, el modelo de clientes/CUIT) → es **tuya**, ya la definiste, acá solo la asiento.
- **El OK para archivar la categoría A del Python** → tuyo, tras validar la tabla de la §2.

**Nada de esto se ejecuta hasta tu aprobación.** Cuando apruebes, lo primero que hago es la verificación de qué Python está vivo (categoría B), antes de mover un solo archivo.
