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


def _pieza_ang_a_str(pieza):
    """Formatea una pieza angular como texto para la orden de trabajo.

    Ángulos en convención máquina (0°=recto, máx 60°) — se muestran tal cual,
    sin conversión (el usuario los ingresó ya en esta convención).
    Si izq==0 y der==0 (corte recto en ambos extremos), muestra solo el largo.
    """
    largo, izq, der, cara, disp = pieza[0], pieza[1], pieza[2], pieza[3], pieza[4]
    txt = _fmt_num(largo)
    if izq == 0 and der == 0:
        return txt
    return f"{txt} ({_fmt_num(izq)}{disp}{_fmt_num(der)}){_fmt_num(cara)}"


def _patron_ang_a_str(patron):
    """Agrupa piezas angulares iguales: '2 x 1000 (45//0)80 + 1 x 800'."""
    conteo = Counter(tuple(p) for p in patron)
    partes = []
    for pieza_tuple, cantidad in sorted(conteo.items(), key=lambda x: -x[0][0]):
        s = _pieza_ang_a_str(pieza_tuple)
        if cantidad > 1:
            partes.append(f"{cantidad} x {s}")
        else:
            partes.append(s)
    return " + ".join(partes)


def _generar_texto_salida(result, bar_len, tipo_material, medida, angular=False):
    """Genera el texto tab-separated para pegar en la planilla Excel de presupuesto.

    Formato idéntico al programa original 1DnestOut.py (generar_plan_excel):
      {qty}\\t{tipo}\\t{medida}\\tx {bar_len}
      \\t{qty} a {patron}\\t\\t
      1\\t{tipo}\\t{medida}\\tx {pieza}   ← tramos sueltos
    """
    if result.error:
        return result.error

    tipo_str = tipo_material or "—"
    medida_str = medida or "—"
    lines = []

    # ── Barras enteras ─────────────────────────────────────────────────────────
    for p in result.bar_patterns:
        if angular:
            detalle = f"{p.count} a {_patron_ang_a_str(p.pieces)}"
        else:
            detalle = f"{p.count} a {_patron_a_str(p.pieces)}"
        lines.append(
            f"{p.count}\t{tipo_str}\t{medida_str}\tx {_fmt_num(bar_len)}"
        )
        lines.append(f"\t{detalle}\t\t")

    # ── Tramos sueltos ─────────────────────────────────────────────────────────
    for pieza in result.tramo_pieces:
        if angular:
            largo_mm = pieza[0]
            pieza_str = _pieza_ang_a_str(pieza)
        else:
            largo_mm = pieza
            pieza_str = _fmt_num(largo_mm)
        lines.append(f"1\t{tipo_str}\t{medida_str}\tx {pieza_str}")

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
    # name (código): prefijo — "01-02-03" solo matchea códigos que EMPIEZAN con eso,
    # así la jerarquía 01→01-02→01-02-03 se resuelve a medida que el usuario tipea más.
    # item_name: substring — el nombre libre puede buscarse en cualquier posición.
    prefix_txt = f"{txt}%" if txt else "%"
    substr_txt = f"%{txt}%" if txt else "%"
    # Frappe puede pasar page_length chico (5) en make_control standalone —
    # forzamos mínimo 20 para que aparezcan todos los que matchean el prefijo.
    effective_page_length = max(cint(page_length) or 20, 20)
    return frappe.db.sql(
        """
        select name, item_name
        from `tabItem`
        where disabled = 0
          and (name like %(prefix_txt)s or item_name like %(substr_txt)s)
          and (name like '01-%%' or name like '02-%%')
        order by name
        limit %(start)s, %(page_length)s
        """,
        {
            "prefix_txt": prefix_txt,
            "substr_txt": substr_txt,
            "start": cint(start),
            "page_length": effective_page_length,
        },
    )


@_whitelist()
def calcular(bar_len, cuts_json, tipo_material="", medida="",
             price_per_bar=0, price_per_meter=0, kerf_mm=2.0, angular=False):
    """
    Calcula el plan de compra mixto (barras enteras + tramos sueltos).

    Args:
        bar_len:         Largo de barra en mm.
        cuts_json:       Modo recto: [[qty, largo], ...].
                         Modo angular: [[qty, largo, izq, der, cara, disp], ...].
        tipo_material:   Texto libre (ej. "Caño").
        medida:          Texto libre (ej. "80 x 80 x 1.6").
        price_per_bar:   Precio de una barra entera (0 = modo no disponible).
        price_per_meter: Precio por metro lineal de tramo suelto (0 = modo no disponible).
        kerf_mm:         Ancho de sierra en mm (default 2).
        angular:         Si True, procesa cortes angulares (cada corte tiene izq/der/cara/disp).

    Returns:
        dict con campos de PurchasePlanResult + texto_salida + angular flag.
    """
    bar_len = float(bar_len)
    kerf_mm = float(kerf_mm)
    price_per_bar = float(price_per_bar)
    price_per_meter = float(price_per_meter)
    # bool("false") == True en Python (string no vacío = truthy) — parseo explícito
    angular = str(angular).strip().lower() in ("1", "true", "yes", "on")
    cuts_raw = json.loads(cuts_json)

    if angular:
        cuts = [(c[0], c[1], c[2], c[3], c[4], c[5]) for c in cuts_raw]
    else:
        cuts = [(int(q), float(l)) for q, l in cuts_raw]

    result = calculate_purchase_plan(
        bar_len=bar_len,
        cuts=cuts,
        price_per_bar=price_per_bar,
        price_per_meter=price_per_meter,
        kerf_mm=kerf_mm,
        angular=angular,
    )

    return {
        "error": result.error,
        "angular": angular,
        "full_bars": result.full_bars,
        "full_bar_cost": result.full_bar_cost,
        "tramo_total_mm": result.tramo_total_mm,
        "tramo_total_meters": result.tramo_total_meters,
        "tramo_cost": result.tramo_cost,
        "total_cost": result.total_cost,
        "global_efficiency_pct": result.global_efficiency_pct,
        "bar_patterns": [
            {
                "pieces": [list(pc) if isinstance(pc, tuple) else pc for pc in p.pieces],
                "count": p.count,
                "used_mm": p.used_mm,
                "waste_mm": p.waste_mm,
                "efficiency_pct": p.efficiency_pct,
            }
            for p in result.bar_patterns
        ],
        "tramo_pieces": [
            list(pc) if isinstance(pc, tuple) else pc
            for pc in result.tramo_pieces
        ],
        "texto_salida": _generar_texto_salida(result, bar_len, tipo_material, medida, angular),
    }
