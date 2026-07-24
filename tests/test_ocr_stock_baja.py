"""Tests puros de las piezas finales del motor OCR/stock:
baja de stock (filtros+dedup+HWM), consulta a Tango, check de catálogo, IVA default 21.
No requieren frappe (los módulos son puros)."""
import os
import sys

_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial"))
if _APP not in sys.path:
    sys.path.insert(0, _APP)

from sistema_industrial.stock_sync import baja
from sistema_industrial.ocr_suppliers import tango_lookup, engine


def _doc(numero, fecha, doc_id, cae_ok=True, nc=False, lineas=None):
    return {"tipo": "NC" if nc else "FAC", "letra": "A", "punto_venta": "0001", "numero": numero,
            "cae": "x" if cae_ok else "", "cae_autorizado": cae_ok, "fecha": fecha, "doc_id": doc_id,
            "es_nota_credito": nc, "lineas": lineas or [{"item_code": "06-1", "cantidad": 10, "es_mercaderia": True}]}


def test_baja_filtros_signo_dedup_hwm():
    docs = [
        _doc("00000001", "2026-07-20", "d1",
             lineas=[{"item_code": "06-1", "cantidad": 10, "es_mercaderia": True},
                     {"item_code": "SERV", "cantidad": 1, "es_mercaderia": False}]),
        _doc("00000002", "2026-07-21", "d2", nc=True,
             lineas=[{"item_code": "06-1", "cantidad": 3, "es_mercaderia": True}]),
        _doc("00000003", "2026-07-22", "d3", cae_ok=False),
    ]
    res = baja.procesar_ventas(docs)
    movs = {(m.item_code, m.quantity_delta) for m in res["movimientos"]}
    assert ("06-1", -10.0) in movs        # venta -> salida
    assert ("06-1", 3.0) in movs          # NC -> entrada
    assert all(m.item_code != "SERV" for m in res["movimientos"])  # no-mercadería excluida
    audit = {a["clave"]: a for a in res["auditoria"]}
    assert audit["FAC-A-0001-00000003"]["motivo"] == "sin_cae"
    assert res["hwm_nuevo"] == {"fecha": "2026-07-22", "doc_id": "d3"}
    # 2da corrida con HWM+claves: nada nuevo
    res2 = baja.procesar_ventas(docs, hwm=res["hwm_nuevo"], claves_procesadas=set(res["claves_nuevas"]))
    assert res2["movimientos"] == []
    # neto por item
    assert {x["item_code"]: x["qty_delta"] for x in baja.stock_entry_items(res["movimientos"])}["06-1"] == -7.0


def test_consulta_tango_y_catalogo():
    class Art:
        code, description, barcode, uom, tango_id = "06-1", "Electrodo", None, "Nos", 2007

    class C:
        def get_article_by_code(self, c):
            return Art() if c == "06-1" else None

    assert tango_lookup.consultar_articulo_en_tango("06-1", C())["existe"] is True
    assert tango_lookup.consultar_articulo_en_tango("ZZZ", C())["existe"] is False
    assert tango_lookup.consultar_articulo_en_tango("06-1", object())["existe"] is None  # no bloquea
    h = tango_lookup.check_catalogo([{"item_code": "a", "item_name": "X", "barcodes": ["779"],
                                      "supplier_items": [{"supplier_part_no": "P1"}]}])
    assert h["items"] == 1 and h["con_barcode"] == 1 and h["ok"]


def test_iva_default_21():
    r = engine.FacturaTableReader()
    it = {"iva": "", "_y0": 100}
    r._asignar_iva([it], [engine.LineBox(0, 100, 100, 120, "COSA 9,00", [])], "SIN IVA")
    assert it["iva_pct"] == 21.0 and it["needs_review"] is True and it["iva_fuente"] == "default_21"


if __name__ == "__main__":
    test_baja_filtros_signo_dedup_hwm()
    test_consulta_tango_y_catalogo()
    test_iva_default_21()
    print("TODOS OK")
