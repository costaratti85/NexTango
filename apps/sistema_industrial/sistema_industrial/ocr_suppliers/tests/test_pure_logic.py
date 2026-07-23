"""
Tests de la LÓGICA PURA del motor OCR (sin Frappe, sin binarios OCR).
Carga engine.py / item_matcher.py como un paquete sintético `ocrpkg` para que
resuelvan los imports relativos (`from .engine import ...`).

Ejecutar:  python3 test_pure_logic.py
"""
import base64
import json
import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
MODDIR = os.path.abspath(os.path.join(HERE, ".."))

# Paquete sintético para resolver imports relativos
_pkg = types.ModuleType("ocrpkg")
_pkg.__path__ = [MODDIR]
sys.modules["ocrpkg"] = _pkg


def _load(modname):
    full = f"ocrpkg.{modname}"
    spec = importlib.util.spec_from_file_location(full, os.path.join(MODDIR, f"{modname}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full] = mod
    spec.loader.exec_module(mod)
    return mod


engine = _load("engine")
item_matcher = _load("item_matcher")

fails = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALLA ") + msg)
    if not cond:
        fails.append(msg)


def _line(reader, text_words, y):
    words = []
    x = 50.0
    for t in text_words:
        w = 30.0 + len(t) * 12
        words.append(engine.WordBox(x, y, x + w, y + 20, t, 1))
        x += w + 40
    return reader.crear_linea(words)


def test_numeros():
    r = engine.FacturaTableReader()
    check(r.parse_decimal("1.234.567,89") == 1234567.89, "parse_decimal es-AR miles+decimales")
    check(r.parse_decimal("8,00") == 8.0, "parse_decimal coma decimal")
    check(r.es_numero("23.659,65") is True, "es_numero es-AR")
    check(r.es_numero("30-71251738-3") is False, "es_numero rechaza CUIT")
    check(r.is_cuit("30712517383") is True, "is_cuit 11 dígitos")
    check(r.is_cuit("12345678901") is False, "is_cuit prefijo inválido")


def test_qr_afip():
    r = engine.FacturaTableReader()
    payload = {"ver": 1, "fecha": "2026-04-27", "cuit": 30712517383, "ptoVta": 2,
               "tipoCmp": 1, "nroCmp": 201690, "importe": 456870.88}
    b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    d = r._parsear_url_afip("https://www.afip.gob.ar/fe/qr/?p=" + b64)
    check(d.get("cuit") == "30712517383", "QR: cuit")
    check(d.get("tipo") == "FACTURA A", "QR: tipoCmp 1 -> FACTURA A")
    check(d.get("numero_completo") == "0002-00201690", "QR: numero_completo con zfill")
    check(d.get("fuente") == "QR_AFIP", "QR: marca fuente")


def test_deteccion_texto():
    r = engine.FacturaTableReader()
    check(r.detectar_cuit_proveedor("CUIT: 30-71251738-3") == "30712517383", "detectar_cuit desde texto")
    check(r.detectar_tipo_comprobante("ORIGINAL FACTURA A") == "FACTURA A", "detectar tipo A")
    clave = r.clave_factura({"cuit_proveedor": "30712517383", "tipo": "FACTURA A",
                             "punto_venta": "2", "numero": "201690"})
    check(clave == "CUIT:30712517383|TIPO:FACTURA A|PV:0002|N:00201690", "clave_factura")


def test_parsing_lineas():
    r = engine.FacturaTableReader()
    l1 = _line(r, ["NERUNAF065", "8,00", "U", "RUEDA", "FIJA", "NARANJA", "65MM", "7.886,55", "21,00", "23.659,65"], 100)
    l2 = _line(r, ["NERUMCA030", "12,00", "U", "RUEDAS", "POLIPROPILENO", "FIJAS", "1.309,35", "21,00", "9.427,32"], 140)
    items, zonas = r.detectar_items([l1, l2])
    check(len(items) == 2, f"detectar_items encontró 2 renglones (encontró {len(items)})")
    if items:
        it = items[0]
        check(it["codigo_proveedor"] == "NERUNAF065", "línea: código proveedor")
        check("RUEDA" in it["descripcion"], "línea: descripción")
        check(it["cantidad"] == "8,00", "línea: cantidad")
        check(it["iva"] == "21,00", "línea: IVA detectado y separado")
        check(it["importe"] == "23.659,65", "línea: importe = último número")


def test_matching_engine():
    cat = engine.Catalogo()
    cat.cargar_desde_articulos([
        {"codigo": "54-00-00-00-062", "descripcion": "NERUNAF065 RUEDA FIJA NARANJA 65MM",
         "sinonimo": "NERUNAF065", "codigo_barras": "54000000062"},
    ])
    art, metodo, score = cat.buscar(codigo_proveedor="NERUNAF065", descripcion="RUEDA FIJA NARANJA 65MM")
    check(art is not None and art["codigo"] == "54-00-00-00-062", "engine: match por sinónimo exacto")
    check(score == 100, "engine: match score 100")


def test_match_lines_contrato_forge():
    """match_lines consumiendo catálogo en formato Forge build_item_catalog()."""
    catalog = [
        {"item_code": "54-00-00-00-062", "item_name": "NERUNAF065 RUEDA FIJA NARANJA 65MM",
         "description": "", "barcodes": ["54000000062"],
         "supplier_items": [{"supplier": "SUP-OB", "supplier_part_no": "NERUNAF065"}]},
        {"item_code": "54-00-00-00-025", "item_name": "NERUMCA030 RUEDAS POLIPROPILENO FIJAS CAMERA30MM",
         "description": "", "barcodes": [],
         "supplier_items": [{"supplier": "SUP-OB", "supplier_part_no": "NERUMCA030"}]},
    ]
    lineas = [
        {"codigo_proveedor": "NERUNAF065", "codigo_barras": "", "descripcion": "RUEDA FIJA NARANJA 65MM",
         "cantidad": 8.0, "precio_unitario": 7886.55, "raw_text": "x"},
        {"codigo_proveedor": "ZZZ999", "codigo_barras": "", "descripcion": "OBJETO FANTASMA INEXISTENTE",
         "cantidad": 1.0, "precio_unitario": 1.0, "raw_text": "y"},
    ]
    res = item_matcher.match_lines(lineas, catalog)
    check(res[0]["match"] is not None and res[0]["match"]["item_code"] == "54-00-00-00-062", "match_lines: matchea por código proveedor")
    check(res[0]["status"] == "verde" and res[0]["confianza"] == 100, "match_lines: status verde + confianza 100")
    check(res[0]["match"]["criterio"] == "codigo", "match_lines: criterio 'codigo'")
    check(res[0]["match"]["confidence"] == 1.0, "match_lines: confidence 0..1")
    check(res[1]["match"] is None and res[1]["status"] == "rojo", "match_lines: sin match -> rojo + match null")
    check(len(res) == 2, "match_lines: una entrada por línea")


if __name__ == "__main__":
    for fn in [test_numeros, test_qr_afip, test_deteccion_texto, test_parsing_lineas,
               test_matching_engine, test_match_lines_contrato_forge]:
        print(f"\n== {fn.__name__} ==")
        fn()
    print("\n" + ("TODOS OK" if not fails else f"{len(fails)} FALLAS: {fails}"))
    sys.exit(1 if fails else 0)
