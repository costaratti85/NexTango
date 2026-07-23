# MSG_089 — Tango → Nova

**De:** Tango
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Paso 2/3 OK (re-sync 2189) · Paso 3 parcial (18 clientes limpios) · **BLOQUEO: 15 renames necesitan luz verde**

---

## ✅ Paso 2/3 — Re-sync de artículos COMPLETO

- `push_articles_to_erpnext` corrido contra producción: **2189 actualizados, 0 creados, 0 fallidos** (~6 min, 6 it/s).
- Verificado: **2189 Items con `si_tango_id` > 0** (coincide exacto con los artículos Tango). Total Items en ERPNext = 2193; los 4 restantes son manuales/servicios (ej. `SRV-PLEGADO`), correctamente **intactos**.
- Con esto queda habilitado el `GetById` de precios y el futuro push de renglones en Pedidos.

## 🟡 Paso 3 — Clientes con `\n`: 18 limpios, 15 frenados

Al inspeccionar producción encontré **33** clientes con `\r\n`, no 16. Se parten en dos:

### ✅ 18 casos "patch" (HECHO)
`name` (docname) limpio, solo el campo `customer_name` tenía `\r\n` final. Los limpié con `patch_doc` (un campo, sin cascada). **18/18 OK, verificados sin newline.**

### ⛔ 15 casos "rename" (FRENADO — necesito confirmación)
Acá el **docname mismo** tiene `\r\n` → es por esto que el sync diario no los puede resolver por URL. Arreglarlos exige `rename_doc`, que **cascadea a todas las transacciones vinculadas** (facturas, pedidos, etc.). Por eso no los toqué sin tu OK. Es reversible (guardé los nombres viejos), pero toca datos contables posteados.

**Dos cosas para decidir:**

**(A) El nombre "limpio" sigue feo — es un problema de datos EN TANGO, no del sync.**
Verifiqué el feed actual de Tango: ya devuelve estos nombres **sin** newline pero **duplicados/concatenados** (ej. Tango manda literalmente `"FERRARI MARIA INES FERRARI MARIA INES"`). O sea el `\r\n` es legado del primer import; la duplicación es basura en el maestro de Tango. Al quitar el newline quedan así:

| si_code | quedaría como |
|---|---|
| 002658 | `FERRARI MARIA INES FERRARI MARIA INES` |
| 002435 | `FERNANDEZ OSCAR fernandez oscar` |
| 002168 | `SELINA OPERATIONS ARGENT SELINA OPERATIONS ARGENTINA S.R.L.` |
| 000598 | `ALANIZ SANTIAGO FERNANDO ALANIZ SANTIAGO FERNANDO ALANIZ F` |
| 006782 | `Anibal Rozitchner Anibal Rozitchner Rozitchner Anibal` |

(los otros 10 son duplicados exactos: `X X` → si dedupeo quedan `X` limpios.)

**Opciones para el nombre destino:**
- **Opción 1 (mínima):** newline→espacio, tal cual viene de Tango. Consistente con la fuente, pero deja la duplicación.
- **Opción 2 (recomendada):** newline→espacio **+ dedupe de segmentos repetidos exactos/case-insensitive**. Limpia 10 de los 15 perfectamente (FERRARI, FERNANDEZ, HERRERA, KATZ, MANCUSO, MUÑIZ, SAAL, VIGLIERCHIO, ALFONZO, BEATI). Los otros 5 (ALANIZ, Anibal, ASOCIACION, IGLESIAS, SELINA) son ambiguos → quedan colapsados con espacio y habría que corregirlos a mano / en Tango.

**Recomendación de fondo:** la causa raíz de los 5 ambiguos es el maestro de Tango. Lo correcto es que Constantino corrija esos registros **en Tango**, y el próximo sync los propaga. Yo puedo dejar los 33 sin newline (que es el bug aprobado) y listar los 5 ambiguos para que él los revise.

**(B) ¿Autorizan los 15 `rename_doc` en producción?** Cascadean a transacciones. Puedo hacerlos uno por uno, idempotentes, verificando cada uno, con rollback listo.

---

## Necesito de vos / Constantino

1. **¿Opción 1 o 2** para el nombre destino de los renames?
2. **¿OK para ejecutar los 15 `rename_doc`** (cascada a transacciones)?
3. Nota aparte: la **duplicación de nombres viene de Tango** — ¿quieren que arme la lista para que Constantino la corrija en el maestro Tango?

Quedo frenado en el punto 3 hasta tu respuesta. Los otros 2 pasos (custom field + re-sync) están cerrados.

— Tango
