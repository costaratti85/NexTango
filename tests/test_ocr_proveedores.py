"""Tests del matcher de Items OCR y de la normalización (parte de Atlas).

El matcher es puro (sin frappe): se testea de punta a punta. La orquestación
Frappe (enqueue/cache/Purchase Receipt) es integración y se prueba en el server.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "sistema_industrial"))

from sistema_industrial.ocr_suppliers.item_matcher import (
    build_catalog, match_line, match_lines, normalizar, normalizar_codigo,
    AUTO_MIN,
)


CATALOGO = build_catalog([
    {"item_code": "BRC-HSS-6", "item_name": "Broca HSS 6mm cobalto",
     "barcodes": ["7790001234567"], "supplier_codes": ["AB-123"]},
    {"item_code": "BRC-HSS-8", "item_name": "Broca HSS 8mm cobalto"},
    {"item_code": "TORN-M6", "item_name": "Tornillo hexagonal M6 x 20",
     "barcodes": ["7790009999999"]},
    {"item_code": "CHAPA-DD-07", "item_name": "Chapa doble decapada 0.7mm"},
])


# ---------------------------------------------------------------- normalización

def test_normalizar_codigo_saca_separadores():
    assert normalizar_codigo("AB-123 ") == "ab123"
    assert normalizar_codigo("7790.001.234") == "7790001234"


def test_normalizar_texto():
    assert normalizar("Broca  HSS  6mm!!") == "broca hss 6mm"
    assert normalizar("Tornillÿ áéí") == "tornil aei" or normalizar("áéí") == "aei"


# ---------------------------------------------------------------- exactos

def test_match_codigo_barras_exacto():
    r = match_line({"codigo_barras": "7790001234567"}, CATALOGO)
    assert r["match"]["item_code"] == "BRC-HSS-6"
    assert r["match"]["reason"] == "Código de barras exacto"
    assert r["confianza"] == 100


def test_match_codigo_proveedor_exacto():
    r = match_line({"codigo_proveedor": "AB-123", "descripcion": "algo"}, CATALOGO)
    assert r["match"]["item_code"] == "BRC-HSS-6"
    assert r["match"]["score"] == 100


def test_match_fuzzy_por_descripcion():
    r = match_line({"descripcion": "broca hss 6 mm cobalto"}, CATALOGO)
    assert r["match"] is not None
    assert r["match"]["item_code"] == "BRC-HSS-6"
    assert r["confianza"] >= AUTO_MIN


def test_candidatos_ranqueados_y_topn():
    r = match_line({"descripcion": "broca hss cobalto"}, CATALOGO, top_n=3)
    codes = [c["item_code"] for c in r["candidatos"]]
    # las dos brocas deben aparecer como candidatas, ordenadas por score
    assert "BRC-HSS-6" in codes and "BRC-HSS-8" in codes
    scores = [c["score"] for c in r["candidatos"]]
    assert scores == sorted(scores, reverse=True)
    assert len(r["candidatos"]) <= 3


def test_sin_match_devuelve_candidatos_pero_no_sugerencia():
    # descripción pobre que no supera AUTO_MIN -> match None, pero puede haber candidatos
    r = match_line({"descripcion": "xyz articulo raro inexistente"}, CATALOGO)
    assert r["match"] is None
    assert r["confianza"] < AUTO_MIN


def test_nada_matchea_catalogo_vacio():
    r = match_line({"descripcion": "lo que sea"}, [])
    assert r["match"] is None and r["candidatos"] == [] and r["confianza"] == 0


# ---------------------------------------------------------------- match_lines

def test_match_lines_preserva_campos_y_agrega_idx():
    lineas = [
        {"codigo_barras": "7790001234567", "descripcion": "Broca", "cantidad": 10, "precio_unitario": 5.0},
        {"descripcion": "Tornillo hexagonal M6", "cantidad": 100, "precio_unitario": 1.0},
    ]
    out = match_lines(lineas, CATALOGO)
    assert len(out) == 2
    assert out[0]["idx"] == 0 and out[1]["idx"] == 1
    # campos originales preservados
    assert out[0]["cantidad"] == 10 and out[0]["precio_unitario"] == 5.0
    # matches
    assert out[0]["match"]["item_code"] == "BRC-HSS-6"
    assert out[1]["match"]["item_code"] == "TORN-M6"
    # estructura para Vega
    for l in out:
        assert set(["match", "confianza", "candidatos"]).issubset(l.keys())


def test_barcode_gana_a_fuzzy():
    # aunque la descripción apunte a otra cosa, el barcode exacto manda
    r = match_line({"codigo_barras": "7790009999999", "descripcion": "broca hss 6mm"}, CATALOGO)
    assert r["match"]["item_code"] == "TORN-M6"
    assert r["match"]["reason"] == "Código de barras exacto"


# ------------------------------------------------ FASE 2: payload de Item nuevo

from sistema_industrial.ocr_suppliers.item_builder import item_payload_nuevo  # noqa: E402


def test_item_payload_nuevo_completo():
    p = item_payload_nuevo("BUL-M8", "Bulón M8x40", "SUP-001", "PROV-99", "7791234567890",
                            "Ferretería", "unidad")
    assert p["doctype"] == "Item"
    assert p["item_code"] == "BUL-M8" and p["item_name"] == "Bulón M8x40"
    assert p["item_group"] == "Ferretería" and p["stock_uom"] == "unidad"
    assert p["supplier_items"] == [{"supplier": "SUP-001", "supplier_part_no": "PROV-99"}]
    assert p["barcodes"] == [{"barcode": "7791234567890"}]


def test_item_payload_nuevo_sin_barcode_ni_supplier():
    p = item_payload_nuevo("X1", "", None, "", "", "Ferretería", "Nos")
    assert p["item_name"] == "X1"            # item_name cae al item_code si falta
    assert p["barcodes"] == []               # sin barcode -> tabla vacía
    assert p["supplier_items"] == []         # sin supplier -> tabla vacía


def test_item_payload_item_name_se_trunca_a_140():
    largo = "D" * 200
    p = item_payload_nuevo("C1", largo, "S", "", "", "Ferretería", "Nos")
    assert len(p["item_name"]) == 140
