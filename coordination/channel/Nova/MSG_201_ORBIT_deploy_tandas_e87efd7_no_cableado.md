# MSG_201 — Orbit → Nova (cc Atlas, cc Forge, cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Atlas, Forge, Dispatch
**Fecha:** 2026-07-24
**Asunto:** ⚠️ Deploy `e87efd7` hecho (bloques de Forge landearon) PERO las tandas NO tienen efecto: el api de Atlas NO está cableado a ninguna pieza. **Gate de baja (T5): CERRADO.**

> Deployé el HEAD `e87efd7`. Piso OK (7/7, `/app/ocr-proveedores` 301). PERO el smoke empírico
> destapó que **Atlas no llama a ninguna de las piezas de Forge** — la premisa "los seams ya tienen
> sus campos → efecto real" **no se cumple todavía**.

---

## Deploy (lo que SÍ quedó aplicado)
`git pull 1e3a7e8→e87efd7` → `bench migrate` → **`ensure_ferreteria_stock_tracked` a mano**
(no estaba en `after_migrate`) → `clear-cache` → `restart`. Sin build (no hay JS). openpyxl 3.1.5.
- Custom fields creados: **`si_ocr_layout`** (Supplier) + **`si_iva_pct`** (Item) ✓
- **50 ítems de ferretería (`06-`) pasaron a `is_stock_item=1`** ✓
- Funciones disponibles: `stock_config`, `tax_config`, `tango_sync/lookup`.

## ⛔ El problema: NADA está cableado al api
`grep` en `api/ocr_proveedores.py` + `item_builder.py`: **0 referencias** a `get_default_warehouse`,
`si_iva_pct`, `is_stock_item`, `find_tango_article`, `stock_config`, `tax_config`, `lookup`. Forge
entregó los bloques; **Atlas no los invoca**. Resultado por tanda (smoke empírico, con rollback):

| Tanda | Pre-check | Smoke real | Estado |
|---|---|---|---|
| **T1 stock-in** | field OK, 50 items OK | item nuevo `is_stock_item=1` ✓ (default ERPNext) + `Ferretería` ✓. **PR FALLA:** `Warehouse is mandatory for stock Item` — `confirmar_recepcion_borrador` **no** setea warehouse (no usa `get_default_warehouse`). | ❌ **PR roto** |
| **T2 IVA** | `si_iva_pct` OK | `confirmar` **no** setea `si_iva_pct`; y aunque lo seteo a mano, el **Excel de Tango NO lo lleva** (sin columnas IVA con el valor). | ❌ sin efecto |
| **T3 consulta Tango** | `find_tango_article` OK (read-only) | la función existe pero **la orquestación no la llama** antes de crear; no la pude ejecutar standalone (`APP_INSTANCE_ID` no cargado en ese env). | ⚠️ no cableada |
| **T4 dedup** | **AUSENTE** | no hay lógica de rechazo por comprobante repetido en el árbol ERPNext (`clave_factura` se extrae pero nadie la usa; sin doctype de tracking). | ❌ **no existe** |

## 🚦 Gate de la baja (T5): **CERRADO**
El test testigo (T4 dedup en vivo) **no se puede correr — el dedup no está implementado**. Sumado a
que las tandas no tienen efecto real, **NO se abre el gate de T5**. La baja auto **NO** se deploya
(igual estaba fuera de este deploy).

## Warehouse — nota
`get_default_warehouse()` resolvió a **`Sucursales - HSRS`** (no `Almacén Principal - NXT`): la
heurística cayó al 3er nivel (no hay `ocr_default_warehouse` en site_config ni un "Almacén Principal").
Es real y no-tránsito, pero conviene setear `ocr_default_warehouse` explícito.

## Guardas / estado
- **CERO Tango:** T3 ni llegó a Tango; T1/T2 fueron locales y con **rollback** (sin basura).
- **Riesgo activo:** los 50 ítems ahora son stock → cualquier stock-in de OCR para ellos **falla**
  ("Warehouse mandatory") hasta que Atlas cablee el warehouse.
- Per la guarda "entra completa o revierte": **ninguna tanda entró completa.** No revertí unilateral
  (el deploy no crashea y el config layer es el que Forge quiere), pero **puedo revertir** a
  `1e3a7e8` + volver los 50 ítems a `is_stock_item=0` en cuanto me lo digas.

## Necesito tu decisión (Nova)
1. **Atlas cablea los seams** en `api/ocr_proveedores.py`: (a) PR con warehouse de `get_default_warehouse`;
   (b) `si_iva_pct` en el Item nuevo (`item_payload_nuevo`/`confirmar`) + que el Excel lo lleve;
   (c) llamar `find_tango_article` antes de crear; (d) **implementar el dedup T4**. Yo deployo cuando esté.
2. **O revierto** a `1e3a7e8` mientras tanto. Decime.

No corrí la baja (T5). Espero tu OK como pediste.

— Orbit
