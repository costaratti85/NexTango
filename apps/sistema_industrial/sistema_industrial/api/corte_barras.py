"""Endpoints para la página de corte de barras (corte-barras).

URL base: /api/method/sistema_industrial.api.corte_barras.

Endpoints:
    calcular(bar_len, cuts_json, price_per_bar, price_per_meter, kerf_mm)
    item_query(...)  — autocomplete del selector de Producto (01-/02-)
"""
import json

try:
    import frappe
    from frappe.utils import cint
    _whitelist = frappe.whitelist
except ImportError:
    frappe = None
    cint = int

    def _whitelist(**_kw):
        def deco(fn):
            return fn
        return deco


from sistema_industrial.cutting.nest_1d import calculate_purchase_plan


@_whitelist()
def item_query(doctype, txt, searchfield, start, page_length, filters=None, **kwargs):
    """Autocomplete de Item para el selector de Producto en corte-barras —
    solo perfiles (01-) y caños (02-).

    VEGA_REVISION_CORTE_BARRAS: el get_query original armaba
    {filters: [AND de 2 like], or_filters: true} para pedir un OR entre
    "item_code like 01-%" y "like 02-%" — pero search_link/search_widget
    (frappe/desk/search.py) no aceptan un parámetro or_filters (confirmado:
    TypeError). El resultado real era 0 resultados siempre (o error de
    servidor), el selector de producto no funcionaba. No hay forma de
    expresar el OR con el "filters" simple de Frappe sin incluir también
    otros prefijos reales del maestro (04-/05-/06-/07-/50-/etc.), así que
    se resuelve con SQL directo como query function.
    """
    like_txt = f"%{txt}%" if txt else "%"
    return frappe.db.sql(
        """
        select name, item_name
        from `tabItem`
        where disabled = 0
          and (name like %(txt)s or item_name like %(txt)s)
          and (name like '01-%%' or name like '02-%%')
        order by name
        limit %(start)s, %(page_length)s
        """,
        {"txt": like_txt, "start": cint(start), "page_length": cint(page_length)},
    )


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
