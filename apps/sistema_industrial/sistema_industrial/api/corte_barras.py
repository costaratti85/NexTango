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


from collections import Counter

from sistema_industrial.cutting.nest_1d import calculate_purchase_plan


def _fmt_num(n):
    """Formato numérico igual al original: enteros sin decimal, decimales con coma."""
    if float(n) == int(float(n)):
        return str(int(float(n)))
    return str(round(float(n), 2)).replace(".", ",")


def _patron_a_str(patron):
    """'6 x 950' o '2 x 2,250 + 1 x 1,000' — agrupa piezas iguales."""
    conteo = Counter(patron)
    partes = []
    for largo, cantidad in sorted(conteo.items(), key=lambda x: -x[0]):
        if cantidad > 1:
            partes.append(f"{cantidad} x {_fmt_num(largo)}")
        else:
            partes.append(_fmt_num(largo))
    return " + ".join(partes)


def _generar_texto_salida(result, bar_len, tipo_material, medida):
    """Genera el texto tab-separated compatible con el formato del programa original.

    Barras enteras → bloque cantidad/patrón.
    Tramos sueltos → una línea por pieza (formato original: línea suelta).
    Resumen arriba: 1 línea con total barras + material + largo.
    """
    if result.error:
        return result.error

    lines = []

    # ── Resumen ────────────────────────────────────────────────────────────────
    total_barras = result.full_bars
    resumen_parts = []
    if total_barras:
        resumen_parts.append(f"{total_barras} barra{'s' if total_barras != 1 else ''}")
    if result.tramo_pieces:
        n_tramos = len(result.tramo_pieces)
        resumen_parts.append(f"{n_tramos} pieza{'s' if n_tramos != 1 else ''} sueltas")
    resumen = " + ".join(resumen_parts) if resumen_parts else "Sin resultado"
    tipo_str = tipo_material or "—"
    medida_str = medida or "—"
    lines.append(
        f"RESUMEN\t{tipo_str}\t{medida_str}\t"
        f"x {_fmt_num(bar_len)} mm\t{resumen}"
    )
    lines.append("")

    # ── Barras enteras ─────────────────────────────────────────────────────────
    for p in result.bar_patterns:
        detalle = f"{p.count} a {_patron_a_str(p.pieces)}"
        lines.append(
            f"{p.count}\t{tipo_str}\t{medida_str}\tx {_fmt_num(bar_len)}"
        )
        lines.append(f"\t{detalle}\t\t")

    # ── Tramos sueltos ─────────────────────────────────────────────────────────
    for largo_mm in result.tramo_pieces:
        lines.append(f"1\t{tipo_str}\t{medida_str}\tx {_fmt_num(largo_mm)}")

    return "\n".join(lines)


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
def calcular(bar_len, cuts_json, tipo_material="", medida="",
             price_per_bar=0, price_per_meter=0, kerf_mm=2.0):
    """
    Calcula el plan de compra mixto (barras enteras + tramos sueltos).

    Args:
        bar_len:         Largo de barra en mm.
        cuts_json:       JSON con lista [[qty, length_mm], ...].
        tipo_material:   Texto libre (ej. "Caño").
        medida:          Texto libre (ej. "80 x 80 x 1.6").
        price_per_bar:   Precio de una barra entera (0 = modo no disponible).
        price_per_meter: Precio por metro lineal de tramo suelto (0 = modo no disponible).
        kerf_mm:         Ancho de sierra en mm (default 2).

    Returns:
        dict con campos de PurchasePlanResult + texto_salida (formato tab-separated original).
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
        "texto_salida": _generar_texto_salida(result, bar_len, tipo_material, medida),
    }
