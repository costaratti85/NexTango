# -*- coding: utf-8 -*-
"""
Motor de optimización de corte lineal 1D.

Extraído de Programas_hechos/1DNest/1DnestOut.py — solo cortes rectos (angular no es prioridad).
No importa tkinter ni ninguna dependencia de GUI.

Uso:
    from sistema_industrial.cutting.nest_1d import calculate_plan

    result = calculate_plan(
        bar_len=6000,
        cuts=[(3, 1500), (2, 800), (5, 400)],
        kerf_mm=2.0,
    )
    print(result.bars_needed, result.total_saw_operations)
"""

from collections import Counter
import random
from dataclasses import dataclass, field


# ── Tipos de resultado ────────────────────────────────────────────────────────

@dataclass
class BarPattern:
    pieces: list          # largos de piezas en mm (ordenados desc)
    count: int            # cuántas barras usan este patrón
    used_mm: float        # material neto usado (piezas + kerfs internos)
    waste_mm: float       # sobrante al final de la barra
    efficiency_pct: float


@dataclass
class CuttingPlanResult:
    bars_needed: int
    total_saw_operations: int  # un corte de sierra por pieza
    total_waste_mm: float
    global_efficiency_pct: float
    patterns: list             # list[BarPattern], ordenados por frecuencia desc
    error: str = ""            # vacío si OK; mensaje de error si algo falló


# ── Helpers internos ──────────────────────────────────────────────────────────

def _normalizar(b):
    return tuple(sorted(b, reverse=True))


def _largo_ocupado(bin_piezas, kerf_mm):
    """Material consumido por un bin: piezas + (n-1) kerfs internos."""
    n = len(bin_piezas)
    return sum(bin_piezas) + max(0, n - 1) * kerf_mm


def _fits(bar_len, bin_piezas, new_piece, kerf_mm):
    """True si new_piece cabe en bin_piezas sin exceder bar_len."""
    k = len(bin_piezas)
    # k cortes internos ya existentes + 1 nuevo corte para separar la nueva pieza
    return sum(bin_piezas) + new_piece + k * kerf_mm <= bar_len


# ── Algoritmos de bin-packing ─────────────────────────────────────────────────

def _first_fit(bar_len, pieces, kerf_mm):
    bins = []
    for p in pieces:
        placed = False
        for b in bins:
            if _fits(bar_len, b, p, kerf_mm):
                b.append(p)
                placed = True
                break
        if not placed:
            bins.append([p])
    return [list(_normalizar(b)) for b in bins]


def _best_fit(bar_len, pieces, kerf_mm):
    bins = []
    for p in pieces:
        mejor_idx = None
        menor_resto = None
        for i, b in enumerate(bins):
            if _fits(bar_len, b, p, kerf_mm):
                resto = bar_len - (_largo_ocupado(b, kerf_mm) + p + len(b) * kerf_mm)
                if menor_resto is None or resto < menor_resto:
                    menor_resto = resto
                    mejor_idx = i
        if mejor_idx is None:
            bins.append([p])
        else:
            bins[mejor_idx].append(p)
    return [list(_normalizar(b)) for b in bins]


def _worst_fit(bar_len, pieces, kerf_mm):
    bins = []
    for p in pieces:
        mejor_idx = None
        mayor_resto = None
        for i, b in enumerate(bins):
            if _fits(bar_len, b, p, kerf_mm):
                resto = bar_len - _largo_ocupado(b, kerf_mm)
                if mayor_resto is None or resto > mayor_resto:
                    mayor_resto = resto
                    mejor_idx = i
        if mejor_idx is None:
            bins.append([p])
        else:
            bins[mejor_idx].append(p)
    return [list(_normalizar(b)) for b in bins]


# ── Ordenamiento de piezas ────────────────────────────────────────────────────

def _ordenar(pieces, modo):
    if modo == "desc":
        return sorted(pieces, reverse=True)
    if modo == "asc":
        return sorted(pieces)
    if modo == "por_frecuencia":
        conteo = Counter(pieces)
        return sorted(pieces, key=lambda x: (-conteo[x], -x))
    if modo == "alternado":
        ordenadas = sorted(pieces, reverse=True)
        resultado, izq, der = [], 0, len(ordenadas) - 1
        while izq <= der:
            resultado.append(ordenadas[izq]); izq += 1
            if izq <= der:
                resultado.append(ordenadas[der]); der -= 1
        return resultado
    return list(pieces)


# ── Generador de variantes + puntuación ───────────────────────────────────────

def _generar_variantes(bar_len, piezas, kerf_mm):
    variantes = []
    for modo in ("desc", "asc", "alternado", "por_frecuencia"):
        p = _ordenar(piezas, modo)
        variantes.append(_first_fit(bar_len, p, kerf_mm))
        variantes.append(_best_fit(bar_len, p, kerf_mm))
        variantes.append(_worst_fit(bar_len, p, kerf_mm))

    rnd = random.Random(12345)
    base = list(piezas)
    for _ in range(200):
        shuffled = base[:]
        rnd.shuffle(shuffled)
        variantes.append(_first_fit(bar_len, shuffled, kerf_mm))
        variantes.append(_best_fit(bar_len, shuffled, kerf_mm))

    return variantes


def _puntuar(bar_len, bins, kerf_mm):
    patrones = Counter(_normalizar(b) for b in bins)
    grupos_repetidos = sum(1 for c in patrones.values() if c > 1)
    mayor_grupo = max(patrones.values()) if patrones else 0
    desperdicio = sum(bar_len - _largo_ocupado(b, kerf_mm) for b in bins)
    return (
        len(bins),
        len(patrones),
        -mayor_grupo,
        -grupos_repetidos,
        desperdicio,
    )


def _elegir_mejor(bar_len, piezas, kerf_mm):
    variantes = _generar_variantes(bar_len, piezas, kerf_mm)
    mejor, mejor_score = None, None
    for bins in variantes:
        score = _puntuar(bar_len, bins, kerf_mm)
        if mejor is None or score < mejor_score:
            mejor, mejor_score = bins, score
    return mejor


# ── API pública ───────────────────────────────────────────────────────────────

def calculate_plan(
    bar_len: float,
    cuts: list,
    kerf_mm: float = 2.0,
) -> CuttingPlanResult:
    """
    Calcula el plan de corte óptimo.

    Args:
        bar_len:  Largo de barra estándar en mm (ej. 6000).
        cuts:     Lista de tuplas (cantidad: int, largo: float) en mm.
                  Ej: [(3, 1500), (2, 800)]
        kerf_mm:  Ancho de corte de sierra en mm (default 2).

    Returns:
        CuttingPlanResult con barras, cortes, desperdicio y patrones.
        Si hay error (pieza > barra), result.error contiene el mensaje.
    """
    if not cuts:
        return CuttingPlanResult(
            bars_needed=0,
            total_saw_operations=0,
            total_waste_mm=0,
            global_efficiency_pct=0,
            patterns=[],
            error="La lista de cortes está vacía.",
        )

    piezas = []
    for qty, length in cuts:
        if length > bar_len:
            return CuttingPlanResult(
                bars_needed=0,
                total_saw_operations=0,
                total_waste_mm=0,
                global_efficiency_pct=0,
                patterns=[],
                error=(
                    f"Una pieza de {length:.0f} mm es más larga "
                    f"que la barra de {bar_len:.0f} mm."
                ),
            )
        piezas.extend([float(length)] * qty)

    bins = _elegir_mejor(bar_len, piezas, kerf_mm)

    freq = Counter(_normalizar(b) for b in bins)
    patrones = []
    for patron_tuple, count in sorted(freq.items(), key=lambda x: -x[1]):
        patron = list(patron_tuple)
        used = _largo_ocupado(patron, kerf_mm)
        waste = bar_len - used
        patrones.append(BarPattern(
            pieces=patron,
            count=count,
            used_mm=round(used, 2),
            waste_mm=round(waste, 2),
            efficiency_pct=round(used / bar_len * 100, 1),
        ))

    total_piezas = len(piezas)
    total_bars = len(bins)
    total_waste = sum(bar_len - _largo_ocupado(b, kerf_mm) for b in bins)
    material_neto = sum(_largo_ocupado(b, kerf_mm) for b in bins)
    material_total = total_bars * bar_len

    return CuttingPlanResult(
        bars_needed=total_bars,
        total_saw_operations=total_piezas,
        total_waste_mm=round(total_waste, 2),
        global_efficiency_pct=round(material_neto / material_total * 100, 1),
        patterns=patrones,
    )


# ── Modelo de compra mixto ────────────────────────────────────────────────────

@dataclass
class PurchasePlanResult:
    """Resultado del plan de compra con modelo mixto barras + tramos sueltos."""
    full_bars: int
    full_bar_cost: float
    tramo_total_mm: float          # suma de piezas que van como tramos sueltos
    tramo_total_meters: float      # ídem en metros
    tramo_cost: float
    total_cost: float
    bar_patterns: list             # list[BarPattern] — solo de barras enteras
    tramo_pieces: list             # list[float] — largos en mm de piezas sueltas
    global_efficiency_pct: float   # sobre barras enteras (0 si no hay barras)
    error: str = ""


def calculate_purchase_plan(
    bar_len: float,
    cuts: list,
    price_per_bar: float,
    price_per_meter: float,
    kerf_mm: float = 2.0,
) -> PurchasePlanResult:
    """
    Calcula el plan de compra óptimo con modelo mixto.

    Para cada grupo de piezas que caben en una barra, elige la opción más barata:
    - Comprar la barra entera (costo = price_per_bar)
    - Comprar cada pieza de ese grupo como tramo suelto (costo = sum_mm / 1000 * price_per_meter)

    Args:
        bar_len:         Largo de barra estándar en mm (ej. 6000).
        cuts:            Lista de (cantidad: int, largo: float) en mm.
        price_per_bar:   Precio de una barra entera.
        price_per_meter: Precio por metro lineal de tramo suelto.
        kerf_mm:         Ancho de sierra en mm (default 2).

    Returns:
        PurchasePlanResult con desglose barras enteras + tramos sueltos + costo total.
    """
    if not cuts:
        return PurchasePlanResult(
            full_bars=0, full_bar_cost=0,
            tramo_total_mm=0, tramo_total_meters=0, tramo_cost=0, total_cost=0,
            bar_patterns=[], tramo_pieces=[], global_efficiency_pct=0,
            error="La lista de cortes está vacía.",
        )

    piezas = []
    for qty, length in cuts:
        if length > bar_len:
            return PurchasePlanResult(
                full_bars=0, full_bar_cost=0,
                tramo_total_mm=0, tramo_total_meters=0, tramo_cost=0, total_cost=0,
                bar_patterns=[], tramo_pieces=[], global_efficiency_pct=0,
                error=(
                    f"Una pieza de {length:.0f} mm es más larga "
                    f"que la barra de {bar_len:.0f} mm."
                ),
            )
        piezas.extend([float(length)] * qty)

    bins = _elegir_mejor(bar_len, piezas, kerf_mm)

    bar_bins = []
    tramo_pieces = []

    for b in bins:
        cost_tramo = sum(b) / 1000.0 * price_per_meter
        if price_per_bar <= cost_tramo:
            bar_bins.append(b)
        else:
            tramo_pieces.extend(b)

    # Patrones de barras enteras
    freq = Counter(_normalizar(b) for b in bar_bins)
    bar_patterns = []
    for patron_tuple, count in sorted(freq.items(), key=lambda x: -x[1]):
        patron = list(patron_tuple)
        used = _largo_ocupado(patron, kerf_mm)
        waste = bar_len - used
        bar_patterns.append(BarPattern(
            pieces=patron,
            count=count,
            used_mm=round(used, 2),
            waste_mm=round(waste, 2),
            efficiency_pct=round(used / bar_len * 100, 1),
        ))

    full_bars = len(bar_bins)
    full_bar_cost = round(full_bars * price_per_bar, 2)
    tramo_total_mm = round(sum(tramo_pieces), 2)
    tramo_total_meters = round(tramo_total_mm / 1000.0, 4)
    tramo_cost = round(tramo_total_meters * price_per_meter, 2)
    total_cost = round(full_bar_cost + tramo_cost, 2)

    if bar_bins:
        neto = sum(_largo_ocupado(b, kerf_mm) for b in bar_bins)
        global_eff = round(neto / (full_bars * bar_len) * 100, 1)
    else:
        global_eff = 0.0

    return PurchasePlanResult(
        full_bars=full_bars,
        full_bar_cost=full_bar_cost,
        tramo_total_mm=tramo_total_mm,
        tramo_total_meters=tramo_total_meters,
        tramo_cost=tramo_cost,
        total_cost=total_cost,
        bar_patterns=bar_patterns,
        tramo_pieces=sorted(tramo_pieces, reverse=True),
        global_efficiency_pct=global_eff,
    )
