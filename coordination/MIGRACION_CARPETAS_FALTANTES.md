# Carpetas / paths que el equipo necesita y HOY no puede acceder

**De:** Nova · **Para:** Constantino · **Fecha:** 2026-07-13
**Objetivo:** que Constantino decida, por cada una, si **la copia al Ubuntu server** o **la comparte desde la Windows**.

---

## ✅ ACTUALIZACIÓN 2026-07-14 — La Windows sale de la cancha del equipo
Constantino aclaró que **la Windows `.15` es su máquina PERSONAL**, no parte del sistema. **Los agentes NUNCA acceden a la Windows** ni montan el disco viejo `\\190.190.190.15\c`. El `NT_STATUS_LOGON_FAILURE` **ya no importa — descartado.**

**Cómo llegan ahora los archivos de la Windows (#1–#5, #9):** **Constantino los copia a la Mint por su cuenta**, cuando pueda. El código standalone va a `Programas_hechos/` en git (DECISION_004); datos/exe al share. → Esas filas dejan de ser tarea del equipo; el equipo solo **espera** que Constantino deje los archivos.

**Sigue vigente para el equipo:** solo lo que vive en la red del sistema — `#6` calibración y `#7` planos (ya operativos por Samba), `#8` Ventas (a confirmar).

---

## ~~⚠ Bloqueo transversal~~ (RESUELTO/DESCARTADO — ver arriba)
~~El share del disco viejo `\\190.190.190.15\c`~~ — ya no aplica: la Windows es personal, el equipo no la toca.

---

## Tabla de decisión

| # | Carpeta / path que falta | Agente(s) | Para qué | Dónde vive hoy | ¿Lectura o L/E? | Recomendación |
|---|---|---|---|---|---|---|
| 1 | Proyecto **CostADCAM Claude** (`\Python\CostADCAM Claude\`: `cam_core_v9.py`, `nesting_coedge.py`, `exporters\gcode_exporter.py`, el `.exe` 57 MB) | Postprocesador | Validar los 3 bugs corregidos + probar nesting/G-code. Es su proyecto activo | Windows vieja → `\\190.190.190.15\c\Python\CostADCAM Claude\` | **Lectura-escritura** (lo edita) | **Copiar local** (o seguir en un entorno Windows dedicado — es proyecto externo al repo) |
| 2 | **VBA/Excel** del flujo pedido-Tango (`TangoAPI_VBA.bas`, `TangoAPI.xlam`, `PRESUPUESTO_PLANTILLA.xlsm`, `fix_plantilla.py`) | PedidoExcel | Continuar el botón "cargar pedido a Tango". El 70% de la lógica ya está en el `.bas` | OneDrive → `\\190.190.190.15\c\Users\vendo\OneDrive\Documentos\Costa\Claude\` | **L/E** si sigue VBA; **solo lectura** si se reescribe en Python | **Depende de decisión VBA-vs-Python** (pendiente tuya). Si Python: basta compartir para leer de referencia |
| 3 | **`ocr_transferencias.pyw`** (conciliación Mercado Pago / Hierros Ratti) | OCR-MELI | Ejecutar/editar la herramienta de conciliación bancaria | OneDrive → `\\190.190.190.15\c\Users\vendo\OneDrive\Documentos\Costa\Claude\Cloud Code OCR Mercadopago\` | **Lectura-escritura** | **Copiar local** (además pendiente aclarar scope Mercadolibre vs Mercado Pago) |
| 4 | **Clave SSH privada** (`id_rsa`/`id_ed25519`) | Punto (y todo el que deba SSH al server) | Subir DXF a `/home/costa/planos/`, verificar deploys, correr scripts remotos | Windows vieja → `\\190.190.190.15\c\Users\vendo\.ssh\` | **Lectura** (copiar una vez) | **Copiar local** a `~/.ssh/` (es credencial, no carpeta de trabajo) |
| 5 | **`tools/generate_version_stamp.py`** (el generador; el consumidor `window.SI_VERSION` sí sobrevivió) | Forge | Cache-busting en cada deploy — hoy está roto sin él | A ubicar: Windows vieja / scratchpad viejo (no está en el repo) | **Lectura** (recuperar → se commitea al repo) | **Recuperar y commitear** al repo. Si no aparece, Forge lo recrea |
| 6 | **`\calibracion_laser\`** (`bateria_calibracion.dxf` + paneles de muestra) | Punto | Insumo de la calibración del modelo láser (T = A·cut + B·travel + C·pierce) | Server → `\\190.190.190.20\planos\calibracion_laser\` | **Lectura** | **Basta compartir** el share `planos` a la Mint (ya vive en el server) |
| 7 | **`\planos\`** (DXF históricos, patrones, calibración) | Punto, Nido, Postprocesador, Vega (galería) | Leer DXF reales para CAM/CAM-preview, patrones de la galería | Server → `\\190.190.190.20\planos\` | **Lectura** (el alta de patrones la hace la app en el server) | **Basta compartir/montar** el share a la Mint |
| 8 | **`\\190.190.190.9\Ventas\`** (5 patrones DXF históricos) | Punto / Forge | Patrones históricos de la galería | Otro equipo de la red → `\\190.190.190.9\Ventas\` | **Lectura** | **A confirmar** si ya se copiaron al server; si no, compartir o copiar los 5 DXF |
| 9 | **`index.html` original del standalone de plegado** (fix #6, pre-migración) | Cybelec | Cotejo final de la re-sincronización (ya cerrada por otra vía) | Windows vieja → `\\190.190.190.15\c\...` (ruta a confirmar) | **Lectura** | **Opcional** — la verificación ya se hizo byte-a-byte contra erpnext. Solo si querés doble-check |

---

## Resumen para decidir rápido

**Basta COMPARTIR (solo lectura, viven en un server de la red):**
- `#6` calibración láser y `#7` planos → compartir/montar `\\190.190.190.20\planos` en la Mint.
- `#8` Ventas → confirmar si ya está en el server; si no, compartir `\\190.190.190.9\Ventas`.

**Conviene COPIAR local (proyectos que se editan / credenciales):**
- `#1` CostADCAM (Postproc), `#3` OCR (OCR-MELI), `#4` clave SSH (Punto).

**Depende de una decisión previa tuya:**
- `#2` VBA pedido-Excel → según VBA-vs-Python.
- `#5` version stamp → recuperar del disco viejo o recrear.

**Requisito para acceder a todo lo del disco viejo (`#1–#5, #9`):** primero **arreglar la credencial/nombre del share** `\\190.190.190.15\c` (hoy da logon failure).

> Nota: el **entorno Python** de Punto (`ezdxf`, `paramiko`, `pip`) NO es una carpeta a compartir — se reinstala. Ya se avanzó (commit `e3dc73f` dejó `.env.example` + `requirements`).

*Si querés, confirmo por sus canales las rutas marcadas "a confirmar" (#5 version stamp, #8 Ventas, #9 index.html) antes de que decidas.*
