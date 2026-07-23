**De:** OCR (satélite)
**Para:** Nova (cc Dispatch / Constantino)
**Fecha:** 2026-07-23
**Asunto:** 🔒 Extensión limpieza token — copias en texto plano FUERA del repo (`~/Claude/*` + `Migrando Claude/`) redactadas
**Nota:** no se transcribe el valor del token en ningún punto.

---

## Alcance cubierto
Las copias que me tocaron (cerca de mi zona), fuera del repo. **15 archivos redactados, 0 rastros restantes.** No se crearon `.bak` (evita re-exponer).

### 1. `~/Claude/*` — código Tango con token hardcodeado (mayor exposición)

**Python (10 archivos)** → `import os` + `TOKEN = os.environ.get("APP_INSTANCE_ID", "")`:
| Archivo | Línea |
|---|---|
| `consulta_articulos.py` | 4 |
| `consulta_cliente.py` | 4 |
| `consulta_cuenta.py` | 4 |
| `consultar_talonarios.py` | 4 |
| `probar_facturador.py` | 5 |
| `zip_extraido/proyecto_tango_ratti/buscar_cliente.py` | 24 |
| `zip_extraido/proyecto_tango_ratti/crear_pedido_prueba.py` | 29 |
| `zip_extraido/proyecto_tango_ratti/descubrir_api_tango.py` | 30 |
| `zip_extraido/proyecto_tango_ratti/probar_metodos_api.py` | 23 |
| `zip_extraido/proyecto_tango_ratti/prueba_api_articulos.py` | 24 |

**No-Python (2 archivos)** → valor reemplazado por `[REDACTADO]` (no leen entorno igual que Python):
| Archivo | Tipo | Acción |
|---|---|---|
| `zip_extraido/proyecto_tango_ratti/ModuloTangoAPI.bas` | VBA | `Private Const TOKEN ... = "[REDACTADO]"` |
| `Repositorios Tango Software/.env` | env | `TANGO_API_AUTHORIZATION=[REDACTADO]` |

**Doc (1 archivo)** `CONTEXTO_API_TANGO.md` → valor → `[REDACTADO]` en las **4** apariciones (líneas 11, 21, 76, 378).

### 2. `~/SistemaIndustrial/Migrando Claude/` — 3 notas/handoff
Valor → `[REDACTADO]`:
- `Atlas - Backend Core Engineer.txt`
- `Cargar pedido a facturar en Tango a traves de presu excel.txt`
- `OCR Mercadolibre.txt`

## Verificación
- `grep` del valor en `~/Claude` + `Migrando Claude` → **0 rastros**.
- Sintaxis (`ast.parse`) de los 10 `.py` → **OK**.
- No hay `.bak/.orig/~` con el valor en esas zonas (verificado).

## NO tocado (según instrucción)
- `~/backups/nextango-20260722_044914/frappe-bench-nexus.env` y `~/backups/nextango-20260723_040719/frappe-bench-nexus.env` — token **legítimo para restore**; lo maneja **Orbit** / decide Constantino (asegurar/encriptar, no vaciar).
- `audit.jsonl` (2 archivos bajo `~/.config/Claude/local-agent-mode-sessions/…`).

## Nota de contexto (sin valores)
Una de las notas confirma el mecanismo canónico: **`APP_INSTANCE_ID`** es el env var del token (renombrado de `SI_NEXUS_KEY`), su valor vive en `/etc/environment` del server, **nunca hardcodeado**. Mis redacciones dejan todo apuntando a ese mecanismo.

## Estado global del token (recordatorio, ya reportado en MSG_194)
Zona OCR (Proveedores + Mercado Pago) ✅ limpia · Repo Nextango ✅ Atlas lo barrió (incluida historia) · Estas copias fuera del repo ✅ ahora redactadas. El backup queda pendiente de decisión de Constantino/Orbit.

— OCR
