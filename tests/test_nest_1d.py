"""Tests para el motor de optimización de corte lineal 1D (nest_1d.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "sistema_industrial"))

from sistema_industrial.cutting.nest_1d import (
    calculate_plan, CuttingPlanResult,
    calculate_purchase_plan, PurchasePlanResult,
)


# ── Casos básicos ─────────────────────────────────────────────────────────────

def test_lista_vacia():
    r = calculate_plan(6000, [])
    assert r.error != ""
    assert r.bars_needed == 0


def test_pieza_mas_larga_que_barra():
    r = calculate_plan(6000, [(1, 7000)])
    assert r.error != ""
    assert r.bars_needed == 0


def test_una_pieza_exacta():
    """Una pieza que ocupa la barra completa (sin kerf)."""
    r = calculate_plan(6000, [(1, 6000)], kerf_mm=0)
    assert r.error == ""
    assert r.bars_needed == 1
    assert r.total_saw_operations == 1
    assert r.total_waste_mm == 0.0
    assert r.global_efficiency_pct == 100.0


def test_dos_piezas_en_una_barra():
    """2 × 2500mm en barra de 6000mm, kerf=0: sobran 1000mm."""
    r = calculate_plan(6000, [(2, 2500)], kerf_mm=0)
    assert r.error == ""
    assert r.bars_needed == 1
    assert r.total_saw_operations == 2
    assert abs(r.total_waste_mm - 1000.0) < 1e-6


def test_kerf_fuerza_segunda_barra():
    """
    3 × 2000mm en barra de 6000mm con kerf=2mm.
    Material mínimo: 3×2000 + 2×2 = 6004mm > 6000mm → necesita 2 barras.
    """
    r = calculate_plan(6000, [(3, 2000)], kerf_mm=2)
    assert r.error == ""
    assert r.bars_needed == 2


def test_sin_kerf_tres_en_una():
    """3 × 2000mm sin kerf: caben exactamente en 6000mm."""
    r = calculate_plan(6000, [(3, 2000)], kerf_mm=0)
    assert r.error == ""
    assert r.bars_needed == 1


def test_kerf_default_2mm():
    """El kerf por defecto es 2mm."""
    r1 = calculate_plan(6000, [(3, 1990)])
    r2 = calculate_plan(6000, [(3, 1990)], kerf_mm=2)
    assert r1.bars_needed == r2.bars_needed
    assert r1.total_waste_mm == r2.total_waste_mm


def test_operaciones_sierra_igualan_total_piezas():
    """total_saw_operations siempre debe ser igual al total de piezas pedidas."""
    cuts = [(3, 1500), (2, 800), (5, 400)]
    total_piezas = sum(q for q, _ in cuts)
    r = calculate_plan(6000, cuts)
    assert r.error == ""
    assert r.total_saw_operations == total_piezas


def test_patrones_cubren_todas_las_barras():
    """La suma de count en los patrones debe igualar bars_needed."""
    r = calculate_plan(6000, [(7, 1200), (3, 900), (4, 600)], kerf_mm=2)
    assert r.error == ""
    assert sum(p.count for p in r.patterns) == r.bars_needed


def test_eficiencia_entre_0_y_100():
    r = calculate_plan(6000, [(5, 1100), (3, 750)], kerf_mm=2)
    assert r.error == ""
    assert 0 < r.global_efficiency_pct <= 100


def test_muchas_piezas_pequeñas():
    """Muchas piezas cortas deben agruparse bien, no una por barra."""
    r = calculate_plan(6000, [(20, 250)], kerf_mm=2)
    assert r.error == ""
    # Con kerf=2, 20 piezas de 250mm: mínimo teórico 2 barras
    # (20×250 + 19×2 = 5038mm en 1 barra es imposible: 5038 < 6000 → 1 barra)
    # Pero agrupa: 20×250 + 19×2 = 5038mm < 6000mm → todo en 1 barra
    assert r.bars_needed == 1


def test_resultado_inmutable_por_segunda_llamada():
    """Dos llamadas idénticas producen el mismo resultado (semilla fija)."""
    cuts = [(4, 1300), (3, 900)]
    r1 = calculate_plan(6000, cuts, kerf_mm=2)
    r2 = calculate_plan(6000, cuts, kerf_mm=2)
    assert r1.bars_needed == r2.bars_needed
    assert r1.total_waste_mm == r2.total_waste_mm


# ── Propiedades de los patrones ───────────────────────────────────────────────

def test_patron_piezas_ordenadas_desc():
    """Cada patrón tiene las piezas ordenadas de mayor a menor."""
    r = calculate_plan(6000, [(3, 1500), (2, 800), (4, 400)], kerf_mm=2)
    for p in r.patterns:
        assert p.pieces == sorted(p.pieces, reverse=True)


def test_patron_efficiency_coherente():
    """efficiency_pct de cada patrón es usado/bar_len × 100."""
    bar_len = 6000
    r = calculate_plan(bar_len, [(3, 1500), (2, 800)], kerf_mm=2)
    for p in r.patterns:
        expected = round(p.used_mm / bar_len * 100, 1)
        assert abs(p.efficiency_pct - expected) < 0.05


# ── Modelo de compra mixto ────────────────────────────────────────────────────

def test_compra_mixta_ejemplo_constantino():
    """
    7 piezas de 950mm → 1 barra (6×950=5700mm) + 1 tramo de 0.95m.
    Costo: 1×precio_barra + 0.95×precio_metro.
    NO 2 barras.
    """
    r = calculate_purchase_plan(
        bar_len=6000,
        cuts=[(7, 950)],
        price_per_bar=100.0,
        price_per_meter=20.0,
        kerf_mm=2,
    )
    assert r.error == ""
    assert r.full_bars == 1
    assert abs(r.tramo_total_meters - 0.95) < 0.001
    assert abs(r.total_cost - (100.0 + 0.95 * 20.0)) < 0.01


def test_compra_mixta_todo_barras():
    """Si price_per_bar <= cost_tramo para todos los bins → solo barras."""
    # 3 piezas de 1500mm = 4500mm en 1 barra; tramo costaría 4.5m × 30 = 135 > 100
    r = calculate_purchase_plan(6000, [(3, 1500)], price_per_bar=100.0, price_per_meter=30.0, kerf_mm=0)
    assert r.error == ""
    assert r.full_bars == 1
    assert r.tramo_total_mm == 0.0
    assert r.total_cost == 100.0


def test_compra_mixta_todo_tramos():
    """Si price_per_bar > cost_tramo para todos los bins → solo tramos."""
    # 1 pieza de 100mm; tramo = 0.1m × 20 = 2 < 100 → tramo
    r = calculate_purchase_plan(6000, [(1, 100)], price_per_bar=100.0, price_per_meter=20.0, kerf_mm=0)
    assert r.error == ""
    assert r.full_bars == 0
    assert r.full_bar_cost == 0.0
    assert abs(r.tramo_total_mm - 100.0) < 0.01
    assert abs(r.total_cost - 2.0) < 0.01


def test_compra_mixta_lista_vacia():
    r = calculate_purchase_plan(6000, [], price_per_bar=100, price_per_meter=20)
    assert r.error != ""
    assert r.total_cost == 0


def test_compra_mixta_pieza_mayor_que_barra():
    r = calculate_purchase_plan(6000, [(1, 7000)], price_per_bar=100, price_per_meter=20)
    assert r.error != ""
    assert r.full_bars == 0


def test_compra_mixta_total_cost_suma_correcta():
    """total_cost == full_bar_cost + tramo_cost siempre."""
    r = calculate_purchase_plan(6000, [(5, 1200), (3, 800)], price_per_bar=80, price_per_meter=15, kerf_mm=2)
    assert r.error == ""
    assert abs(r.total_cost - (r.full_bar_cost + r.tramo_cost)) < 0.01


def test_compra_mixta_tramo_pieces_ordenadas_desc():
    """tramo_pieces está ordenado de mayor a menor."""
    r = calculate_purchase_plan(6000, [(2, 300), (1, 900), (3, 150)], price_per_bar=10000, price_per_meter=1, kerf_mm=0)
    assert r.tramo_pieces == sorted(r.tramo_pieces, reverse=True)


def test_precio_barra_cero_fuerza_todo_tramos():
    """price_per_bar=0 → precio=0 como sentinel 'modo no disponible' → todo a tramos."""
    r = calculate_purchase_plan(6000, [(3, 1500)], price_per_bar=0, price_per_meter=20.0, kerf_mm=0)
    assert r.error == ""
    assert r.full_bars == 0
    assert r.full_bar_cost == 0.0
    # 3×1500mm = 4500mm = 4.5m × 20 = 90
    assert abs(r.tramo_total_meters - 4.5) < 0.001
    assert abs(r.total_cost - 90.0) < 0.01


def test_precio_metro_cero_fuerza_todo_barras():
    """price_per_meter=0 → modo no disponible → todo a barras enteras."""
    r = calculate_purchase_plan(6000, [(3, 1500)], price_per_bar=100.0, price_per_meter=0, kerf_mm=0)
    assert r.error == ""
    assert r.full_bars == 1
    assert r.tramo_total_mm == 0.0
    assert abs(r.full_bar_cost - 100.0) < 0.01
    assert abs(r.total_cost - 100.0) < 0.01


def test_ambos_precios_cero_solo_plan_barras():
    """Ambos=0 → sin precios, todo a barras, costo=0 (solo plan de corte)."""
    r = calculate_purchase_plan(6000, [(3, 1500)], price_per_bar=0, price_per_meter=0, kerf_mm=0)
    assert r.error == ""
    assert r.full_bars >= 1
    assert r.total_cost == 0.0


# ── Angular ───────────────────────────────────────────────────────────────────

def test_angular_recto_equivalente_a_modo_recto():
    """Piezas angulares con izq=der=0 deben dar el mismo resultado que modo recto."""
    # Recto
    r_recto = calculate_purchase_plan(
        6000, [(7, 950)], price_per_bar=5000, price_per_meter=900, kerf_mm=2,
    )
    # Angular con ángulos 0 (recto en ambos extremos)
    r_ang = calculate_purchase_plan(
        6000, [(7, 950, 0, 0, 0, '//')], price_per_bar=5000, price_per_meter=900,
        kerf_mm=2, angular=True,
    )
    assert r_ang.error == ""
    assert r_ang.full_bars == r_recto.full_bars
    assert r_ang.tramo_pieces.__len__() == r_recto.tramo_pieces.__len__()
    assert abs(r_ang.total_cost - r_recto.total_cost) < 0.01


def test_angular_piezas_distintos_angulos():
    """Piezas con ángulos distintos: la pieza angular tiene el largo correcto."""
    r = calculate_purchase_plan(
        6000, [(3, 1000, 45, 0, 80, '//'), (2, 800, 0, 30, 60, '\\')],
        price_per_bar=5000, price_per_meter=0,
        kerf_mm=2, angular=True,
    )
    assert r.error == ""
    assert r.full_bars >= 1
    # Las piezas en los patrones son tuplas de 5 elementos
    for patron in r.bar_patterns:
        for p in patron.pieces:
            assert len(p) == 5, "pieza angular debe tener 5 campos"
    # Piezas angulares distintas no deben mezclarse en el mismo "slot" de largo
    all_pieces = [p for pat in r.bar_patterns for p in pat.pieces]
    for p in all_pieces:
        largo, izq, der, cara, disp = p
        assert largo in (1000.0, 800.0)


def test_angular_tramo_suelto_precio_barra_cero():
    """angular + price_per_bar=0 → todo a tramos sueltos (piezas angulares)."""
    r = calculate_purchase_plan(
        6000, [(2, 1000, 45, 0, 80, '//'), (1, 800, 0, 0, 0, '//')],
        price_per_bar=0, price_per_meter=900,
        kerf_mm=2, angular=True,
    )
    assert r.error == ""
    assert r.full_bars == 0
    assert len(r.tramo_pieces) == 3
    # Ordenados por largo desc
    assert r.tramo_pieces[0][0] >= r.tramo_pieces[-1][0]


def test_angular_pieza_mas_larga_que_barra():
    """angular: pieza más larga que la barra → error."""
    r = calculate_purchase_plan(
        6000, [(1, 7000, 45, 0, 80, '//')],
        price_per_bar=5000, price_per_meter=900,
        kerf_mm=2, angular=True,
    )
    assert r.error != ""
    assert r.full_bars == 0


def test_angular_lista_vacia():
    r = calculate_purchase_plan(6000, [], price_per_bar=5000, price_per_meter=900, angular=True)
    assert r.error != ""
