"""Endpoints para la página de corte de barras (corte-barras).

URL base: /api/method/sistema_industrial.api.corte_barras.

Endpoints:
    calcular(bar_len, cuts_json, price_per_bar, price_per_meter, kerf_mm)
"""
import json

try:
    import frappe
    _whitelist = frappe.whitelist
except ImportError:
    frappe = None

    def _whitelist(**_kw):
        def deco(fn):
            return fn
        return deco


from sistema_industrial.cutting.nest_1d import calculate_purchase_plan


@_whitelist()
def calcular(bar_len, cuts_json, price_per_bar=0, price_per_meter=0, kerf_mm=2.0):
    """
    Calcula el plan de compra mixto (barras enteras + tramos sueltos).

    Args:
        bar_len:         Largo de barra en mm.
        cuts_json:       JSON con lista [[qty, length_mm], ...].
        price_per_bar:   Precio de una barra entera (puede ser 0 si no se cotiza).
        price_per_meter: Precio por metro lineal de tramo suelto.
        kerf_mm:         Ancho de sierra en mm (default 2).

    Returns:
        dict con los campos de PurchasePlanResult.
    """
    bar_len = float(bar_len)
    kerf_mm = float(kerf_mm)
    price_per_bar = float(price_per_bar)
    price_per_meter = float(price_per_meter)
    cuts = json.loads(cuts_json)

    result = calculate_purchase_plan(
        bar_len=bar_len,
        cuts=[(int(q), float(l)) for q, l in cuts],
        price_per_bar=price_per_bar,
        price_per_meter=price_per_meter,
        kerf_mm=kerf_mm,
    )

    return {
        "error": result.error,
        "full_bars": result.full_bars,
        "full_bar_cost": result.full_bar_cost,
        "tramo_total_mm": result.tramo_total_mm,
        "tramo_total_meters": result.tramo_total_meters,
        "tramo_cost": result.tramo_cost,
        "total_cost": result.total_cost,
        "global_efficiency_pct": result.global_efficiency_pct,
        "bar_patterns": [
            {
                "pieces": p.pieces,
                "count": p.count,
                "used_mm": p.used_mm,
                "waste_mm": p.waste_mm,
                "efficiency_pct": p.efficiency_pct,
            }
            for p in result.bar_patterns
        ],
        "tramo_pieces": result.tramo_pieces,
    }
