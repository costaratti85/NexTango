**De:** OCR (satélite)
**Para:** Nova (cc Dispatch / Constantino)
**Fecha:** 2026-07-23
**Asunto:** 🔒 Limpieza del token Tango en texto plano — zona OCR hecha; footprint fuera de scope reportado (sin tocar)
**Nota:** en ningún punto de este reporte se transcribe el valor del token.

---

## A. Qué hice (zona OCR — autorizado)

### OCR Proveedores — `/home/costa/Python/OCR Proveedores`
| Archivo | Hallazgo | Acción |
|---|---|---|
| `Token.txt` | archivo que era **solo el secreto** | ✅ **BORRADO** (`rm`) |
| `api.py` (línea 4) | token **hardcodeado** `TOKEN = "<secreto>"` | ✅ **REDACTADO** → `import os` + `TOKEN = os.environ.get("APP_INSTANCE_ID", "")` |

### OCR Mercado Pago — `/home/costa/Claude/Cloud Code OCR Mercadopago` (OCR relacionado)
Mismo token, hardcodeado. Redactado a entorno (`APP_INSTANCE_ID`):
| Archivo | Línea | Acción |
|---|---|---|
| `ocr_transferencias.pyw` | 29 (`TANGO_TOKEN`) | ✅ REDACTADO → `os.environ.get("APP_INSTANCE_ID", "")` |
| `consulta_facturas.py` | 5 (`TOKEN`) | ✅ REDACTADO + `import os` agregado |
| `consulta_nexo.py` | 4 (`TOKEN`) | ✅ REDACTADO + `import os` agregado |
| `ocr_transferencias.pyw.bak_20260720` | 29 | ✅ REDACTADO (mi backup del fix previo; el token quedó fuera, el respaldo del fix se conserva) |

**Verificado:** `grep` del valor en ambas zonas OCR → **0 rastros**. Sintaxis (`ast.parse`) de los 4 archivos de código → **OK**.

> El token **no era usado** por `ocr_claude.py` (la app OCR canónica); en `api.py` sí (script de prueba que postea a Tango). Ahora todos leen la clave por `APP_INSTANCE_ID`, sin valor pegado.

## B. Footprint FUERA de mi rol — reportado, NO tocado

El token aparece también en **tooling Tango que NO es OCR** (no lo modifiqué; no es mi zona):
- `/home/costa/Python/Tango Extractor Bajas Stock/.env`
- `/home/costa/Python/tools/tango_probe_articulos.py`
- `/home/costa/Claude/consulta_cliente.py`, `consulta_cuenta.py`, `consultar_talonarios.py`, `consulta_articulos.py`, `probar_facturador.py`, `CONTEXTO_API_TANGO.md`
- `/home/costa/Claude/zip_extraido/proyecto_tango_ratti/` → `descubrir_api_tango.py`, `crear_pedido_prueba.py`, `buscar_cliente.py`, `probar_metodos_api.py`, `prueba_api_articulos.py`, `ModuloTangoAPI.bas`
- `/home/costa/Claude/Repositorios Tango Software/.env`

## C. ⚠️ El token está en el REPO Nextango y en el HISTORIAL de git — NO reescribí historia

- **Working-tree del repo:** el valor **todavía aparece** en archivos de **otros agentes** (no OCR, no míos): `coordination/dispatch/queue.json` y varios mensajes de canal de **Orbit / Tango / Forge / Nova** (justamente los de la campaña de rotación/purga: `MSG_012_TANGO_purga_historial_token`, `MSG_095_TANGO_token_eliminado`, `MSG_105/106_ORBIT_verificacion_tokens`, etc.). **No los toqué** — no es mi rol editar canales ajenos.
- **Historial de git:** el token aparece en **9 commits** (`git log -S`). **NO reescribí la historia** (como pediste, eso lo decide Constantino a la mañana).
- **🔴 Dato de seguridad importante:** el repo tiene **remoto en GitHub** (`origin → github.com/costaratti85/NexTango`). Si ese remoto ya recibió push del historial, el token **ya está publicado** allí; borrarlo del working-tree no lo saca del historial remoto. Dado que Tango no puede rotar el token (devuelve siempre el mismo), esto es un riesgo que amerita decisión de Constantino (¿repo privado? ¿purga de historial + force-push coordinada por Orbit? ¿el token da acceso a algo sensible?).

## Resumen
✅ Zona OCR (Proveedores + Mercado Pago) limpia de token en texto plano, con clave por entorno.
📋 Footprint no-OCR + repo + historial git: reportado, intacto.
⛔ No reescribí git ni edité archivos de otros roles.

— OCR
