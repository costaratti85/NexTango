#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONVERSOR DXF: SPLINES A ARCOS - CON CAPA ROJA
------------------------------------------------
Convierte splines en arcos y líneas, y los coloca en una capa nueva (ROJO)
sin eliminar las splines originales.
"""

import os
import sys
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.ttk import Progressbar
import threading
import time

try:
    import ezdxf
    from ezdxf.colors import RGB
except ImportError:
    print("❌ Error: La librería 'ezdxf' no está instalada.")
    print("   Instálala con: pip install ezdxf")
    sys.exit(1)


# ============================================================================
#                         EXCEPCIONES
# ============================================================================

class _SaveBlocked(Exception):
    """Raised when doc.saveas fails with PermissionError (file open elsewhere).
    Carries the converted doc so the work is not lost."""
    def __init__(self, doc, output_path, converted_count, total_arcs, total_lines):
        super().__init__(str(output_path))
        self.doc = doc
        self.output_path = output_path
        self.converted_count = converted_count
        self.total_arcs = total_arcs
        self.total_lines = total_lines


# ============================================================================
#                         FUNCIONES DE CONVERSIÓN
# ============================================================================

def normalize_path(path):
    if not path:
        return path
    path = path.strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    if path.startswith("'") and path.endswith("'"):
        path = path[1:-1]
    path = path.replace('\\\\\\\\', '//')
    path = path.replace('\\\\', '//')
    path = path.replace('\\', '/')
    path = os.path.normpath(path)
    return path


def _fit_arc_through_endpoints(points, tolerance):
    """Circle fit that EXACTLY passes through points[0] and points[-1].

    Unlike Kasa (which minimises average radial distance and does NOT
    guarantee the circle passes through the boundary points), this
    constrains the centre to lie on the perpendicular bisector of the
    chord p0→pn.  Parameterising the centre as

        centre = midpoint(p0,pn) + t * perp_direction
        radius  = half_chord * sqrt(1 + t²)

    the optimal t that minimises the interior-point residuals is found
    analytically (closed form).  Because each arc starts and ends at
    exact points on the circle, consecutive arcs share the same physical
    endpoint and produce a gap-free chain.

    Returns (cx, cy, r, start_deg, end_deg, n) or None.
    """
    n = len(points)
    if n < 2:
        return None
    p0 = points[0];  pn = points[-1]

    mx = (p0.x + pn.x) * 0.5;  my = (p0.y + pn.y) * 0.5
    dx = (pn.x - p0.x) * 0.5;  dy = (pn.y - p0.y) * 0.5
    chord_sq = dx * dx + dy * dy
    if chord_sq < 1e-12:
        return None        # coincident endpoints

    if n == 2:
        return None        # no interior points → emit a line instead

    # Optimal t: minimise Σ (dist_i − R)² for interior points.
    # dist_i² − R²  =  Ai + t·Bi   (linear in t)
    # → t_opt = −Σ(Ai·Bi) / Σ(Bi²)
    sum_AB = 0.0;  sum_B2 = 0.0
    for p in points[1:-1]:
        u = p.x - mx;  v = p.y - my
        Ai = u * u + v * v - chord_sq
        Bi = 2.0 * (u * dy - v * dx)
        sum_AB += Ai * Bi
        sum_B2 += Bi * Bi
    t = (-sum_AB / sum_B2) if sum_B2 > 1e-12 else 0.0

    cx = mx - t * dy
    cy = my + t * dx
    r  = math.sqrt(chord_sq * (1.0 + t * t))

    if r < 0.001 or r > 100000.0:
        return None

    # Tolerance check: only interior points (endpoints are exact by construction)
    max_err = 0.0
    for p in points[1:-1]:
        err = abs(math.sqrt((p.x - cx) ** 2 + (p.y - cy) ** 2) - r)
        if err > max_err:
            max_err = err
    if max_err > tolerance:
        return None

    # Arc direction: CCW from p0 through the midpoint sample to pn
    a1 = math.atan2(p0.y - cy, p0.x - cx)
    am = math.atan2(points[n // 2].y - cy, points[n // 2].x - cx)
    a3 = math.atan2(pn.y - cy, pn.x - cx)
    if a3 < a1:
        a3 += 2 * math.pi
    if am < a1:
        am += 2 * math.pi
    if am > a3:
        a1, a3 = a3, a1
        a1 -= 2 * math.pi

    # Angular containment check.
    # Each intermediate point must lie within the arc's angular range [a1, a3]
    # (CCW), with a 10° slack for floating-point noise.
    #
    # Two wrap-around fixes are needed to handle arcs whose angular range
    # straddles the ±180° boundary:
    #   (A) Upper fix: if a normalised angle still sits above a3+slack (because
    #       it ended up on the far side of ±180°), subtract 2π once more.
    #   (B) Lower fix: if after (A) the angle is below a1−slack it means a
    #       genuine direction-flip has occurred (the point is outside the arc on
    #       the low side) — reject the fit.  Without this lower-bound check the
    #       containment loop only verifies the upper bound, letting wrongly-
    #       directed arcs (330° instead of 30°) pass silently.
    #
    # Note: we do NOT add a blanket span>180° guard here. Tips and sharp bends
    # legitimately need arcs spanning up to ~180°, and the upper+lower bound
    # pair correctly rejects the actual direction-flip cases without over-firing.
    ANG_SLACK = math.radians(10)
    for p in points[1:-1]:
        a = math.atan2(p.y - cy, p.x - cx)
        while a < a1 - ANG_SLACK:
            a += 2 * math.pi
        while a > a1 + 2 * math.pi + ANG_SLACK:
            a -= 2 * math.pi
        if a > a3 + ANG_SLACK:     # (A) upper wrap-around fix
            a -= 2 * math.pi
        if a > a3 + ANG_SLACK:     # still above → genuinely outside arc
            return None
        if a < a1 - ANG_SLACK:     # (B) lower bound: below range after (A)
            return None            #     → direction-flip, reject

    return (cx, cy, r, math.degrees(a1), math.degrees(a3), n)


def fit_arc_to_points(points, tolerance):
    """Kasa least-squares circle fit with angular containment check.

    Returns (cx, cy, r, start_deg, end_deg, n) or None.

    Beyond checking that each point is within *tolerance* of the circle,
    this also verifies that every intermediate point falls inside the arc's
    angular range (from start to end, CCW).  This rejects cases where Kasa
    finds the right circle but the arc takes the long way around, producing
    a 280° arc instead of the correct 80° one.
    """
    n = len(points)
    if n < 3:
        return None
    try:
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        sx = sum(xs); sy = sum(ys)
        sxx = sum(x*x for x in xs); syy = sum(y*y for y in ys)
        sxy = sum(x*y for x, y in zip(xs, ys))
        sx3 = sum(x**3 for x in xs); sy3 = sum(y**3 for y in ys)
        sxxy = sum(x*x*y for x, y in zip(xs, ys))
        sxyy = sum(x*y*y for x, y in zip(xs, ys))
        A = 2*(sx*sx - n*sxx); B = 2*(sx*sy - n*sxy); C = 2*(sy*sy - n*syy)
        D = sx*sxx - n*sx3 + sx*syy - n*sxyy
        E = sy*sxx - n*sxxy + sy*syy - n*sy3
        det = A*C - B*B
        if abs(det) < 1e-10:
            return None
        cx = (D*C - B*E) / det
        cy = (A*E - B*D) / det
        r = math.sqrt(sum((x-cx)**2 + (y-cy)**2 for x, y in zip(xs, ys)) / n)
        if r < 0.001 or r > 100000:
            return None
        max_err = max(abs(math.sqrt((x-cx)**2 + (y-cy)**2) - r) for x, y in zip(xs, ys))
        if max_err > tolerance:
            return None

        # Determine arc direction: CCW from p1 through pm to p3
        p1 = points[0]; pm = points[n//2]; p3 = points[-1]
        a1 = math.atan2(p1.y - cy, p1.x - cx)
        am = math.atan2(pm.y - cy, pm.x - cx)
        a3 = math.atan2(p3.y - cy, p3.x - cx)
        if a3 < a1:
            a3 += 2*math.pi
        if am < a1:
            am += 2*math.pi
        if am > a3:
            a1, a3 = a3, a1
            a1 -= 2*math.pi

        # Angular containment check — same logic as _fit_arc_through_endpoints.
        # Upper fix (A): wrap-around for arcs near ±180°.
        # Lower fix (B): rejects direction-flip arcs (330° instead of 30°).
        ANG_SLACK = math.radians(10)
        for p in points[1:-1]:
            a = math.atan2(p.y - cy, p.x - cx)
            while a < a1 - ANG_SLACK:
                a += 2 * math.pi
            while a > a1 + 2 * math.pi + ANG_SLACK:
                a -= 2 * math.pi
            if a > a3 + ANG_SLACK:     # (A) upper wrap-around fix
                a -= 2 * math.pi
            if a > a3 + ANG_SLACK:
                return None
            if a < a1 - ANG_SLACK:     # (B) lower bound after (A)
                return None

        return (cx, cy, r, math.degrees(a1), math.degrees(a3), n)
    except Exception:
        return None


def _curvature_at(points, i):
    """Approximate curvature (rad/mm) at interior index i via the direction
    change between the two chords meeting at that point."""
    dx1 = points[i].x - points[i - 1].x
    dy1 = points[i].y - points[i - 1].y
    dx2 = points[i + 1].x - points[i].x
    dy2 = points[i + 1].y - points[i].y
    l1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
    l2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
    if l1 < 1e-9 or l2 < 1e-9:
        return 0.0
    cos_a = (dx1 * dx2 + dy1 * dy2) / (l1 * l2)
    cos_a = max(-1.0, min(1.0, cos_a))
    return math.acos(cos_a) / ((l1 + l2) * 0.5)


def _signed_curvature_at(points, i):
    """Signed curvature at interior index i.

    Positive = left turn (CCW), Negative = right turn (CW).
    The sign indicates which side of the curve the centre of curvature is on.
    """
    dx1 = points[i].x - points[i - 1].x
    dy1 = points[i].y - points[i - 1].y
    dx2 = points[i + 1].x - points[i].x
    dy2 = points[i + 1].y - points[i].y
    l1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
    l2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
    if l1 < 1e-9 or l2 < 1e-9:
        return 0.0
    cross = dx1 * dy2 - dy1 * dx2   # z-component of v1 × v2
    cos_a = (dx1 * dx2 + dy1 * dy2) / (l1 * l2)
    cos_a = max(-1.0, min(1.0, cos_a))
    unsigned_k = math.acos(cos_a) / ((l1 + l2) * 0.5)
    return unsigned_k if cross >= 0 else -unsigned_k


def _find_curvature_valleys(points, min_peak_ratio=2.0):
    """Return point indices at valleys in the curvature profile.

    When a spline has multiple distinct arc domains (e.g. a gentle large arc
    followed by a tight spiral), its curvature profile has peaks (at the
    centre of each domain) and valleys (at the transitions between them).
    Splitting the point list at those valleys ensures each sub-segment has
    exactly ONE curvature peak, so _fit_rolling can anchor its initial circle
    there and grow correctly outward toward lower-curvature regions.

    A valley is only returned when both adjacent peaks are at least
    *min_peak_ratio* times higher than the valley — this filters noise-level
    undulations from genuine arc-domain boundaries.
    """
    n = len(points)
    if n < 6:
        return []

    # Raw curvature at each interior point
    raw = [_curvature_at(points, i) for i in range(1, n - 1)]
    # raw[j] is curvature at point index j+1

    # 3-point moving average to suppress numerical noise from dense flattening
    curv = raw[:]
    for j in range(1, len(raw) - 1):
        curv[j] = (raw[j - 1] + raw[j] + raw[j + 1]) / 3.0

    # Collect all local maxima (peaks) and minima (valleys)
    peaks   = []   # (value, point_index)
    valleys = []   # (value, point_index)
    for j in range(1, len(curv) - 1):
        if curv[j] >= curv[j - 1] and curv[j] >= curv[j + 1]:
            peaks.append((curv[j], j + 1))
        elif curv[j] <= curv[j - 1] and curv[j] <= curv[j + 1]:
            valleys.append((curv[j], j + 1))

    if len(peaks) < 2:
        return []   # only one curvature domain — no valley split needed

    # Keep only valleys where both neighbouring peaks are significantly higher:
    # that confirms a genuine arc-domain boundary rather than noise.
    splits = []
    for v_val, v_idx in valleys:
        safe_v = max(v_val, 1e-9)
        left_peaks  = [p for p, i in peaks if i < v_idx]
        right_peaks = [p for p, i in peaks if i > v_idx]
        if not left_peaks or not right_peaks:
            continue
        if (max(left_peaks) / safe_v >= min_peak_ratio and
                max(right_peaks) / safe_v >= min_peak_ratio):
            splits.append(v_idx)

    return sorted(splits)


def _find_hard_nodes(points, threshold_rad_mm=0.5):
    """Return sorted list of indices where curvature jumps sharply.

    A jump in curvature between consecutive interior points signals that the
    second derivative is discontinuous there — i.e. the first derivative
    (tangent direction) may also be discontinuous, indicating a corner or tip.
    These points are always treated as segment boundaries so no single arc
    ever crosses them.
    """
    n = len(points)
    if n < 4:
        return []
    nodes = []
    k_prev = _curvature_at(points, 1)
    for i in range(2, n - 1):
        k_curr = _curvature_at(points, i)
        if abs(k_curr - k_prev) > threshold_rad_mm:
            nodes.append(i)
        k_prev = k_curr
    return nodes


def _find_inflection_points(points, min_k_threshold=0.005):
    """Return indices where the signed curvature changes sign (inflection points).

    At an inflection point the centre of curvature jumps from one side of the
    curve to the other.  No single arc can span an inflection correctly —
    a Kasa fit on a crossing-inflection segment places the circle centre on
    whatever side has more points, which is geometrically wrong for the other
    half.  These points are therefore always treated as mandatory split
    boundaries.

    min_k_threshold — ignore near-zero curvature (< this value) when detecting
    sign changes, to avoid false positives from discretisation noise on
    nearly-straight stretches.
    """
    n = len(points)
    if n < 4:
        return []

    raw = [_signed_curvature_at(points, i) for i in range(1, n - 1)]
    # raw[j] → signed curvature at points[j + 1]

    # 3-point moving average to suppress discretisation noise
    sk = raw[:]
    for j in range(1, len(raw) - 1):
        sk[j] = (raw[j - 1] + raw[j] + raw[j + 1]) / 3.0

    inflections = []
    for j in range(1, len(sk)):
        k_prev = sk[j - 1]   # curvature at points[j]
        k_curr = sk[j]        # curvature at points[j + 1]
        # Require both sides to have meaningful curvature to avoid noise
        if abs(k_prev) < min_k_threshold or abs(k_curr) < min_k_threshold:
            continue
        if k_prev * k_curr < 0:   # genuine sign reversal
            # Split at whichever index is closer to curvature = 0
            if abs(k_prev) <= abs(k_curr):
                inflections.append(j)       # points index j
            else:
                inflections.append(j + 1)   # points index j + 1

    return sorted(set(inflections))


def _fit_rolling(points, fit_tol, min_sagitta_mm,
                 modelspace, layer_name, arcs, lines):
    """Fit *points* as ARC/LINE by growing outward from the peak curvature.

    Algorithm (follows the user's 'draw from high curvature to low' idea):
    1. Fast path: try fitting the whole segment as one arc.
    2. Find the interior point with the highest curvature (the tightest bend /
       tip). This is the *seed* — the most important point to capture accurately.
    3. Start a 3-point arc window centred on the seed (always fits).
    4. Grow the window right by one point at a time while Kasa+angular check
       still accepts. Then grow left the same way.
    5. Emit the maximum-extent arc centred on the seed.
    6. Recurse on the left remainder [0..lo] and right remainder [hi..n-1],
       each with their own seed and growing step.

    This guarantees that the highest-curvature region is always the interior
    of an arc — never a split boundary — so arcs fit the tight bends first
    and connect outward into the lower-curvature regions.
    """
    n = len(points)
    if n < 2:
        return
    if n == 2:
        try:
            ln = modelspace.add_line(points[0], points[1])
            ln.dxf.layer = layer_name
            lines.append(ln)
        except Exception:
            pass
        return

    chord = math.sqrt((points[-1].x - points[0].x) ** 2
                      + (points[-1].y - points[0].y) ** 2)
    if chord < 0.001:
        return

    # Fast path: whole segment fits as one arc AND curvature is nearly constant.
    # Use the endpoint-constrained fit so the arc passes exactly through
    # points[0] and points[-1] (required for gap-free chain continuity).
    # Guard with max_k_ratio so high-variation segments are never collapsed.
    _fp_max_k_ratio = 1.5
    result = _fit_arc_through_endpoints(points, fit_tol)
    if result is not None and n >= 4:
        _fp_k = [_curvature_at(points, i) for i in range(1, n - 1)]
        _fp_kr = max(_fp_k) / max(min(_fp_k), 1e-9) if _fp_k else 1.0
        if _fp_kr <= _fp_max_k_ratio:
            _emit_arc_or_line(result, points[0], points[-1],
                              modelspace, layer_name, min_sagitta_mm, arcs, lines)
            return
        result = None   # reject fast path — fall through to growing algorithm
    elif result is not None:   # n < 4: fast path always OK (trivially constant curvature)
        _emit_arc_or_line(result, points[0], points[-1],
                          modelspace, layer_name, min_sagitta_mm, arcs, lines)
        return

    # Find the interior point with the highest curvature
    best_k = -1.0
    i_peak = n // 2
    for i in range(1, n - 1):
        k = _curvature_at(points, i)
        if k > best_k:
            best_k = k
            i_peak = i

    # For a monotone-curvature segment the global peak sits at one of the two
    # endpoint-adjacent positions (index 1 or n-2).  Starting there forces all
    # growth in a single direction and anchors the circle at the extreme end —
    # which produces arcs whose centres diverge from the original curve in the
    # low-curvature flank.  Using the midpoint instead gives a circle that is
    # centred inside the segment and can grow symmetrically in both directions,
    # yielding a much better fit for the gentle-arc portion.
    if i_peak == 1 or i_peak == n - 2:
        i_seed = n // 2   # monotone: anchor at centre, not at the curvature extreme
    else:
        i_seed = i_peak   # genuine interior peak: use it

    # Initial 3-point window centred on seed (always fits — 3 pts define a circle)
    lo = max(0, i_seed - 1)
    hi = min(n - 1, i_seed + 1)

    # Maximum allowed ratio of max/min curvature within a single arc window.
    # A circular arc has constant curvature; large variation means the window
    # spans geometrically different regions that need separate arcs.
    max_k_ratio = 1.5

    def _k_ratio_ok(window):
        """True if curvature variation within window is within max_k_ratio."""
        m = len(window)
        if m < 4:
            return True
        k_vals = [_curvature_at(window, j) for j in range(1, m - 1)]
        if not k_vals:
            return True
        k_max_w = max(k_vals)
        k_min_w = min(k_vals)
        return k_max_w / max(k_min_w, 1e-9) <= max_k_ratio

    # Grow RIGHT: extend hi while the endpoint-constrained arc still fits
    while hi + 1 < n:
        new_window = points[lo:hi + 2]
        if _fit_arc_through_endpoints(new_window, fit_tol) is None:
            break
        if not _k_ratio_ok(new_window):
            break
        hi += 1

    # Grow LEFT: extend lo while the endpoint-constrained arc still fits
    while lo - 1 >= 0:
        new_window = points[lo - 1:hi + 1]
        if _fit_arc_through_endpoints(new_window, fit_tol) is None:
            break
        if not _k_ratio_ok(new_window):
            break
        lo -= 1

    # Emit the maximum-extent arc centred on the seed.
    # The endpoint-constrained fit guarantees this arc starts/ends exactly at
    # points[lo] and points[hi] — the same physical locations used by the
    # left and right recursive calls — so the full chain is gap-free.
    main_result = _fit_arc_through_endpoints(points[lo:hi + 1], fit_tol)
    if main_result is not None:
        _emit_arc_or_line(main_result, points[lo], points[hi],
                          modelspace, layer_name, min_sagitta_mm, arcs, lines)
    else:
        # Arc fit failed for the main window — emit a straight line so the
        # endpoints points[lo]..points[hi] are never silently dropped.
        # This happens for nearly-collinear 3-point windows near corners.
        try:
            ln = modelspace.add_line(points[lo], points[hi])
            ln.dxf.layer = layer_name
            lines.append(ln)
        except Exception:
            pass

    # Recurse on remainders (each with their own seed)
    if lo > 0:
        _fit_rolling(points[:lo + 1], fit_tol, min_sagitta_mm,
                     modelspace, layer_name, arcs, lines)
    if hi < n - 1:
        _fit_rolling(points[hi:], fit_tol, min_sagitta_mm,
                     modelspace, layer_name, arcs, lines)


def _arc_sagitta(radius, span_deg):
    """Maximum deviation of arc from its chord (mm)."""
    return radius * (1.0 - math.cos(math.radians(span_deg / 2.0)))


def _emit_arc_or_line(result, p_start, p_end, modelspace, layer_name,
                      min_sagitta_mm, arcs, lines):
    """Decide arc vs line from a fit result; append to arcs or lines."""
    cx, cy, radius, start_angle, end_angle, _ = result
    # end_angle > start_angle always (fit_arc_to_points guarantees this)
    span = end_angle - start_angle
    sagitta = _arc_sagitta(radius, span)
    if sagitta < min_sagitta_mm:
        try:
            line = modelspace.add_line(p_start, p_end)
            line.dxf.layer = layer_name
            lines.append(line)
        except Exception:
            pass
    else:
        # Normalise angles to [0, 360) so that DXF viewers that do not accept
        # negative angles display the arc correctly.  We keep end = start + span
        # (rather than normalising end separately) so that arcs crossing 0°/360°
        # are stored unambiguously as a positive sweep.
        start_norm = start_angle % 360.0
        end_norm = start_norm + span
        try:
            new_arc = modelspace.add_arc(
                center=(cx, cy, 0),
                radius=radius,
                start_angle=start_norm,
                end_angle=end_norm,
            )
            new_arc.dxf.layer = layer_name
            arcs.append(new_arc)
        except Exception:
            pass


def discretize_and_convert_spline(spline_entity, modelspace, layer_name,
                                  flatten_tol=0.01, fit_tol=0.5,
                                  min_sagitta_mm=0.01):
    """Convert a SPLINE entity to ARC and LINE entities in *layer_name*.

    flatten_tol  – max chord-deviation when discretising (mm). Smaller = more
                   points = better arc recognition for tight curves.
    fit_tol      – max residual allowed in the Kasa circle fit (mm).
    min_sagitta_mm – arcs whose sagitta is below this are emitted as lines
                     (the curve is so flat it is indistinguishable from a chord).
    """
    arcs = []
    lines = []

    try:
        points = []
        if hasattr(spline_entity, 'flattening'):
            try:
                points = list(spline_entity.flattening(flatten_tol))
            except Exception:
                pass
        if not points:
            try:
                points = list(spline_entity.vertices())
            except Exception:
                pass
        if not points:
            try:
                pts = list(spline_entity.control_points())
                if len(pts) >= 2:
                    points = list(pts)
            except Exception:
                pass

        if not points or len(points) < 3:
            return [], []

        max_points = 2000
        if len(points) > max_points:
            step = max(1, len(points) // max_points)
            last = points[-1]
            points = points[::step]
            if points[-1] is not last:
                points = list(points) + [last]

        # Phase 1 — hard nodes: abrupt jumps in curvature (second-derivative
        # discontinuities) that signal corners or tips with potentially
        # discontinuous tangent directions.  No arc ever crosses these.
        hard_nodes = _find_hard_nodes(points)

        # Phase 2 — valley splits: local minima of the unsigned curvature
        # profile that separate distinct arc domains (e.g. gentle large arc
        # vs tight spiral).
        valley_splits = _find_curvature_valleys(points)

        # Phase 3 — inflection points: where the signed curvature changes sign.
        # At an inflection the centre of curvature jumps sides; any single arc
        # spanning an inflection will have its Kasa circle on the wrong side for
        # at least half the points, producing grossly wrong geometry.
        inflection_pts = _find_inflection_points(points)

        # Merge all split points and process each sub-segment independently
        split_indices = sorted(set(
            [0] + hard_nodes + valley_splits + inflection_pts + [len(points) - 1]
        ))
        for seg_idx in range(len(split_indices) - 1):
            i_start = split_indices[seg_idx]
            i_end   = split_indices[seg_idx + 1]
            if i_end > i_start:
                seg = points[i_start:i_end + 1]
                _fit_rolling(seg, fit_tol, min_sagitta_mm,
                             modelspace, layer_name, arcs, lines)

    except Exception as e:
        print(f"   Error en discretizacion: {e}")

    return arcs, lines


def process_lwpolyline(polyline, modelspace, layer_name):
    arcs = []
    lines = []
    
    try:
        vertices = list(polyline.vertices())
        if len(vertices) < 2:
            return [], []
        
        is_closed = polyline.closed
        
        for i in range(len(vertices)):
            current = vertices[i]
            next_idx = (i + 1) % len(vertices) if is_closed else i + 1
            
            if next_idx >= len(vertices):
                break
            
            next_vertex = vertices[next_idx]
            
            p1 = current[0] if isinstance(current, tuple) else current
            p2 = next_vertex[0] if isinstance(next_vertex, tuple) else next_vertex
            
            if len(current) > 4:
                bulge = current[4]
            else:
                bulge = 0
            
            if bulge == 0:
                line = modelspace.add_line(p1, p2)
                line.dxf.layer = layer_name
                lines.append(line)
            else:
                try:
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    chord_length = math.sqrt(dx*dx + dy*dy)
                    
                    if chord_length < 0.001:
                        continue
                    
                    radius = abs(chord_length / (2 * math.sin(2 * math.atan(bulge))))
                    perp_x = -dy / chord_length
                    perp_y = dx / chord_length
                    sagitta = radius * math.cos(2 * math.atan(bulge))
                    
                    center_x = (p1.x + p2.x) / 2 + perp_x * sagitta
                    center_y = (p1.y + p2.y) / 2 + perp_y * sagitta
                    
                    angle1 = math.atan2(p1.y - center_y, p1.x - center_x)
                    angle2 = math.atan2(p2.y - center_y, p2.x - center_x)
                    
                    start_angle = math.degrees(angle1)
                    end_angle = math.degrees(angle2)
                    
                    if bulge < 0:
                        start_angle, end_angle = end_angle, start_angle
                    
                    new_arc = modelspace.add_arc(
                        center=(center_x, center_y, 0),
                        radius=abs(radius),
                        start_angle=start_angle,
                        end_angle=end_angle
                    )
                    new_arc.dxf.layer = layer_name
                    arcs.append(new_arc)
                except:
                    line = modelspace.add_line(p1, p2)
                    line.dxf.layer = layer_name
                    lines.append(line)
    except Exception as e:
        print(f"   ❌ Error procesando LWPOLYLINE: {e}")
    
    return arcs, lines


def convert_dxf_with_progress(input_file, output_file, tolerance=0.01, status_callback=None, progress_callback=None):
    input_file = normalize_path(input_file)
    output_file = normalize_path(output_file)
    
    if not os.path.exists(input_file):
        if status_callback:
            status_callback(f"❌ Error: El archivo no existe")
        return -1
    
    if status_callback:
        status_callback("📖 Leyendo archivo DXF...")
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            doc = ezdxf.read(f)
    except:
        with open(input_file, 'r', encoding='latin-1') as f:
            doc = ezdxf.read(f)
    
    modelspace = doc.modelspace()
    
    # Limpiar entidades previas en ARCOS_CONVERTIDOS (evita duplicados si el archivo ya fue convertido)
    existing = [e for e in modelspace if e.dxf.get('layer', '') == 'ARCOS_CONVERTIDOS']
    for e in existing:
        modelspace.delete_entity(e)

    # Crear una nueva capa en ROJO (color 1 = rojo en AutoCAD)
    try:
        # Verificar si la capa ya existe
        if 'ARCOS_CONVERTIDOS' not in doc.layers:
            new_layer = doc.layers.new('ARCOS_CONVERTIDOS')
            new_layer.color = 1  # Rojo
            if status_callback:
                status_callback("🆕 Capa 'ARCOS_CONVERTIDOS' creada (color ROJO)")
        else:
            # Asegurar que la capa existente sea roja
            doc.layers.get('ARCOS_CONVERTIDOS').color = 1
            if status_callback:
                status_callback("🔄 Capa 'ARCOS_CONVERTIDOS' ya existía, configurada a ROJO")
    except Exception as e:
        if status_callback:
            status_callback(f"⚠️ Error al crear capa: {e}")
    
    # Contar splines y polilíneas con curvas
    spline_count = 0
    polyline_count = 0
    all_splines = []
    all_polylines = []
    
    for entity in modelspace:
        try:
            et = entity.dxftype()
            if et == 'SPLINE':
                spline_count += 1
                all_splines.append(entity)
            elif et == 'LWPOLYLINE':
                has_arc = False
                try:
                    for v in entity.vertices():
                        if len(v) > 4 and v[4] != 0:
                            has_arc = True
                            break
                except:
                    pass
                if has_arc:
                    polyline_count += 1
                    all_polylines.append(entity)
        except:
            pass
    
    if status_callback:
        status_callback(f"📊 Splines: {spline_count}, Polilíneas con curvas: {polyline_count}")
    
    converted_count = 0
    total_arcs = 0
    total_lines = 0

    total_to_process = spline_count + polyline_count
    processed = 0

    # Capa destino
    target_layer = 'ARCOS_CONVERTIDOS'

    # Conjunto de capas que contienen splines/polilíneas — usado luego para
    # identificar las LINE entities que forman parte del mismo dibujo.
    source_layers = set()
    for e in all_splines + all_polylines:
        try:
            source_layers.add(e.dxf.layer)
        except Exception:
            pass

    # Lista de endpoints físicos de cada cadena convertida (x, y).
    # Con _fit_arc_through_endpoints cada cadena comienza y termina EXACTAMENTE
    # en el primer/último punto discretizado de la spline original.
    # Las LINE entities vecinas serán re-dibujadas usando estos puntos como
    # nuevos extremos para mantener la continuidad perfecta.
    converted_endpoints = []   # list of (x, y)

    def _collect_spline_endpoints(entity):
        """Agrega los endpoints físicos de la spline a converted_endpoints."""
        try:
            pts = list(entity.flattening(tolerance))
            if len(pts) >= 2:
                converted_endpoints.append((pts[0].x, pts[0].y))
                converted_endpoints.append((pts[-1].x, pts[-1].y))
        except Exception:
            pass

    # Convertir splines
    for entity in all_splines:
        processed += 1
        if progress_callback:
            progress_callback(processed, total_to_process)
        if status_callback:
            status_callback(f"🔄 SPLINE {processed}/{total_to_process}...")

        _collect_spline_endpoints(entity)
        arcs, lines = discretize_and_convert_spline(
            entity, modelspace, target_layer, flatten_tol=tolerance)
        if arcs or lines:
            converted_count += 1
            total_arcs += len(arcs)
            total_lines += len(lines)
            if status_callback:
                status_callback(f"   OK {len(arcs)} arcos, {len(lines)} lineas")
        else:
            if status_callback:
                status_callback(f"   Sin resultado")

    # Convertir polilíneas con curvas
    for entity in all_polylines:
        processed += 1
        if progress_callback:
            progress_callback(processed, total_to_process)
        if status_callback:
            status_callback(f"🔄 LWPOLYLINE {processed}/{total_to_process}...")

        arcs, lines = process_lwpolyline(entity, modelspace, target_layer)
        if arcs or lines:
            converted_count += 1
            total_arcs += len(arcs)
            total_lines += len(lines)
            if status_callback:
                status_callback(f"   ✅ {len(arcs)} arcos, {len(lines)} líneas")
        else:
            if status_callback:
                status_callback(f"   ⚠️ No se pudo convertir")

    # Redibujar LINE entities que conectan entidades convertidas.
    # Cada extremo de la línea original se reemplaza por el endpoint convertido
    # más cercano (dentro de un umbral de 0.1 mm); si ningún endpoint está cerca
    # se usa el extremo original sin modificar.
    # Umbral pequeño: los endpoints correctos tienen dist=0.0, los vértices libres
    # (apex de puntas) están a 0.5–1.0 mm → no deben snappearse.
    def _snap(x, y, threshold=0.1):
        best_d2 = threshold * threshold
        bx, by = x, y
        for ex, ey in converted_endpoints:
            d2 = (x - ex) ** 2 + (y - ey) ** 2
            if d2 < best_d2:
                best_d2 = d2
                bx, by = ex, ey
        return bx, by

    src_lines = [e for e in modelspace
                 if e.dxftype() == 'LINE' and e.dxf.layer in source_layers]

    copied_lines = 0
    for ln in src_lines:
        try:
            sx, sy = ln.dxf.start.x, ln.dxf.start.y
            ex, ey = ln.dxf.end.x,   ln.dxf.end.y
            sx, sy = _snap(sx, sy)
            ex, ey = _snap(ex, ey)
            new_ln = modelspace.add_line((sx, sy, 0), (ex, ey, 0))
            new_ln.dxf.layer = target_layer
            copied_lines += 1
            total_lines += 1
        except Exception:
            pass

    if copied_lines and status_callback:
        status_callback(f"   📐 {copied_lines} líneas rectas redirijidas a nodos convertidos")

    # NO ELIMINAMOS las splines originales, las dejamos para comparar
    
    if status_callback:
        status_callback(f"💾 Guardando archivo...")
    
    # Guardar el archivo
    try:
        doc.saveas(output_file)
    except PermissionError:
        # File locked by another app — raise so the GUI can offer save-as / retry
        raise _SaveBlocked(doc, output_file, converted_count, total_arcs, total_lines)
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Error al guardar: {e}")
        return -1
    
    if status_callback:
        status_callback(f"✅ ¡COMPLETADO! {converted_count} curvas → {total_arcs} arcos, {total_lines} líneas")
        status_callback(f"📌 Las splines originales se conservan en sus capas originales")
        status_callback(f"📌 Los nuevos arcos/líneas están en la capa 'ARCOS_CONVERTIDOS' (ROJO)")
    
    return converted_count


# ============================================================================
#                         INTERFAZ GRÁFICA
# ============================================================================

class DXFConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor DXF: Splines a Arcos (Capa ROJA)")
        self.root.geometry("800x650")
        
        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.tolerance = tk.DoubleVar(value=0.01)
        self.is_running = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Título
        titulo = tk.Label(self.root, text="CONVERSOR DXF - SPLINES A ARCOS", 
                         font=("Arial", 16, "bold"), fg="#2c3e50")
        titulo.pack(pady=10)
        
        # Subtítulo
        subtitulo = tk.Label(self.root, text="Los arcos convertidos se guardan en capa ROJA (sin eliminar originales)", 
                            font=("Arial", 10), fg="#e74c3c")
        subtitulo.pack(pady=5)
        
        # --- Archivo de entrada ---
        frame1 = tk.LabelFrame(self.root, text="1. Archivo de entrada", padx=10, pady=10)
        frame1.pack(pady=5, padx=20, fill="x")
        
        tk.Entry(frame1, textvariable=self.input_file_path, state='readonly', width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(frame1, text="Examinar", command=self.select_input, bg="#3498db", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # --- Parámetros ---
        frame2 = tk.LabelFrame(self.root, text="2. Parámetros", padx=10, pady=10)
        frame2.pack(pady=5, padx=20, fill="x")
        
        tk.Label(frame2, text="Tolerancia (mm):").pack(side=tk.LEFT, padx=5)
        tk.Spinbox(frame2, from_=0.001, to=5.0, increment=0.005,
                  textvariable=self.tolerance, width=12, format="%.3f").pack(side=tk.LEFT, padx=5)
        tk.Label(frame2, text="(0.01mm recomendado | 0.1mm rapido)", font=("Arial", 8), fg="#7f8c8d").pack(side=tk.LEFT, padx=10)
        
        # --- Archivo de salida ---
        frame3 = tk.LabelFrame(self.root, text="3. Archivo de salida", padx=10, pady=10)
        frame3.pack(pady=5, padx=20, fill="x")
        
        tk.Entry(frame3, textvariable=self.output_file_path, state='readonly', width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(frame3, text="Guardar", command=self.select_output, bg="#2ecc71", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # --- Progreso ---
        frame4 = tk.LabelFrame(self.root, text="4. Progreso", padx=10, pady=10)
        frame4.pack(pady=5, padx=20, fill="both", expand=True)
        
        self.progress = Progressbar(frame4, orient="horizontal", length=750, mode="determinate")
        self.progress.pack(pady=5, fill="x")
        
        self.status_text = tk.Text(frame4, height=12, font=("Consolas", 9), state='disabled')
        self.status_text.pack(pady=5, fill="both", expand=True)
        
        scroll = tk.Scrollbar(frame4, orient="vertical", command=self.status_text.yview)
        scroll.pack(side=tk.RIGHT, fill="y")
        self.status_text.config(yscrollcommand=scroll.set)
        
        # --- BOTÓN CONVERTIR ---
        self.convert_btn = tk.Button(
            self.root,
            text="🔄 CONVERTIR",
            command=self.start_conversion,
            bg="#e67e22",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=50,
            pady=15
        )
        self.convert_btn.pack(pady=15)
        
        # --- Estado ---
        self.status_label = tk.Label(self.root, text="✅ Listo", font=("Arial", 10), fg="#27ae60")
        self.status_label.pack(pady=5)
    
    def select_input(self):
        path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
        if path:
            self.input_file_path.set(path)
            base = os.path.splitext(path)[0]
            self.output_file_path.set(f"{base}_convertido.dxf")
            self.add_status(f"📂 Cargado: {os.path.basename(path)}")
    
    def select_output(self):
        if not self.input_file_path.get():
            messagebox.showwarning("Atención", "Primero selecciona un archivo de entrada")
            return
        path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF files", "*.dxf")])
        if path:
            self.output_file_path.set(path)
    
    def add_status(self, msg):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, msg + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
        self.root.update()
    
    def update_progress(self, current, total):
        if total > 0:
            pct = int((current / total) * 100)
            self.progress['value'] = pct
            self.root.update()
    
    def update_status(self, msg):
        self.status_label.config(text=msg[:70])
        self.add_status(msg)
        self.root.update()
    
    def start_conversion(self):
        if self.is_running:
            return
        
        if not self.input_file_path.get():
            messagebox.showerror("Error", "Selecciona un archivo de entrada")
            return
        
        if not self.output_file_path.get():
            messagebox.showerror("Error", "Especifica un archivo de salida")
            return
        
        self.is_running = True
        self.convert_btn.config(state='disabled', text="⏳ TRABAJANDO...")
        self.progress['value'] = 0
        
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state='disabled')
        
        thread = threading.Thread(target=self.run_conversion, daemon=True)
        thread.start()
    
    def run_conversion(self):
        try:
            start_time = time.time()
            result = convert_dxf_with_progress(
                self.input_file_path.get(),
                self.output_file_path.get(),
                self.tolerance.get(),
                status_callback=self.update_status,
                progress_callback=self.update_progress
            )
            elapsed = time.time() - start_time
            self.root.after(0, lambda r=result, e=elapsed: self.finish_conversion(r, e))
        except _SaveBlocked as sb:
            elapsed = time.time() - start_time
            self.root.after(0, lambda e=sb, t=elapsed: self._handle_save_blocked(e, t))
        except Exception as ex:
            import traceback
            error_msg = str(ex) + "\n" + traceback.format_exc()
            self.root.after(0, lambda msg=error_msg: self.error_conversion(msg))
    
    @staticmethod
    def _next_available_path(path):
        """Return path_v2.dxf, path_v3.dxf … until one that doesn't exist."""
        base, ext = os.path.splitext(path)
        i = 2
        while True:
            candidate = f"{base}_v{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
            i += 1

    def _do_save(self, doc, path, converted_count, total_arcs, total_lines, elapsed):
        """Try to save *doc* to *path*. On success update UI; on error show msg."""
        try:
            doc.saveas(path)
            self.output_file_path.set(path)
            self.add_status(f"✅ Guardado en: {os.path.basename(path)}")
            self.status_label.config(
                text=f"✅ {converted_count} curvas en {elapsed:.1f}s", fg="#27ae60")
            self.progress['value'] = 100
            messagebox.showinfo(
                "¡Listo!",
                f"✅ {converted_count} curvas convertidas en {elapsed:.1f}s\n\n"
                f"{total_arcs} arcos, {total_lines} líneas\n"
                f"Guardado en: {os.path.basename(path)}"
            )
        except PermissionError:
            messagebox.showerror(
                "Archivo bloqueado",
                f"Tampoco se pudo guardar en:\n{os.path.basename(path)}\n\n"
                "Cerrá el archivo en el CAD e intentá de nuevo."
            )
            self.status_label.config(text="❌ No se pudo guardar", fg="#e74c3c")
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))
            self.status_label.config(text="❌ Error al guardar", fg="#e74c3c")

    def _handle_save_blocked(self, exc, elapsed):
        """Called in the main thread when doc.saveas failed with PermissionError."""
        self.is_running = False
        self.convert_btn.config(state='normal', text="🔄 CONVERTIR")

        blocked_path = exc.output_path
        suggested   = self._next_available_path(blocked_path)
        blocked_name  = os.path.basename(blocked_path)
        suggested_name = os.path.basename(suggested)

        # Custom dialog — three choices
        dlg = tk.Toplevel(self.root)
        dlg.title("Archivo bloqueado")
        dlg.resizable(False, False)
        dlg.grab_set()  # modal

        tk.Label(
            dlg,
            text=(
                f"No se pudo guardar:\n{blocked_name}\n\n"
                "El archivo está abierto en otra aplicación.\n"
                "La conversión está lista — elegí cómo guardarla:"
            ),
            justify=tk.LEFT, padx=20, pady=12
        ).pack()

        btn_frame = tk.Frame(dlg, pady=10)
        btn_frame.pack()

        def on_suggested():
            dlg.destroy()
            self._do_save(exc.doc, suggested,
                          exc.converted_count, exc.total_arcs, exc.total_lines, elapsed)

        def on_retry():
            dlg.destroy()
            self._do_save(exc.doc, blocked_path,
                          exc.converted_count, exc.total_arcs, exc.total_lines, elapsed)

        def on_choose():
            dlg.destroy()
            new_path = filedialog.asksaveasfilename(
                initialdir=os.path.dirname(blocked_path),
                initialfile=suggested_name,
                defaultextension=".dxf",
                filetypes=[("DXF files", "*.dxf")]
            )
            if new_path:
                self._do_save(exc.doc, new_path,
                              exc.converted_count, exc.total_arcs, exc.total_lines, elapsed)
            else:
                self.add_status(
                    "⚠️ Guardado cancelado. El resultado se descarta.")
                self.status_label.config(text="⚠️ Guardado cancelado", fg="#f39c12")

        tk.Button(
            btn_frame, text=f"Guardar como {suggested_name}",
            command=on_suggested, bg="#27ae60", fg="white", width=32, pady=6
        ).grid(row=0, column=0, padx=8, pady=4)

        tk.Button(
            btn_frame, text=f"Reintentar con {blocked_name}",
            command=on_retry, bg="#2980b9", fg="white", width=32, pady=6
        ).grid(row=1, column=0, padx=8, pady=4)

        tk.Button(
            btn_frame, text="Elegir otro nombre...",
            command=on_choose, bg="#7f8c8d", fg="white", width=32, pady=6
        ).grid(row=2, column=0, padx=8, pady=4)

        dlg.update_idletasks()
        # Center over parent
        x = self.root.winfo_x() + (self.root.winfo_width()  - dlg.winfo_width())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

    def finish_conversion(self, result, elapsed):
        self.is_running = False
        self.convert_btn.config(state='normal', text="🔄 CONVERTIR")
        
        if result >= 0:
            if result == 0:
                messagebox.showinfo("Completado", "No se encontraron curvas para convertir")
                self.status_label.config(text="⚠️ No hay curvas para convertir", fg="#f39c12")
            else:
                messagebox.showinfo(
                    "¡Éxito!", 
                    f"✅ {result} curvas convertidas en {elapsed:.1f} segundos\n\n"
                    f"📌 Los nuevos arcos/líneas están en la capa 'ARCOS_CONVERTIDOS' (ROJO)\n"
                    f"📌 Las splines originales se conservan"
                )
                self.status_label.config(text=f"✅ {result} curvas convertidas en {elapsed:.1f}s", fg="#27ae60")
                self.progress['value'] = 100
        else:
            self.status_label.config(text="❌ Error en conversión", fg="#e74c3c")
    
    def error_conversion(self, msg):
        self.is_running = False
        self.convert_btn.config(state='normal', text="🔄 CONVERTIR")
        self.status_label.config(text=f"❌ Error en conversión", fg="#e74c3c")
        self.add_status(f"❌ ERROR: {msg}")
        messagebox.showerror("Error", f"Error en la conversión:\n\n{msg[:500]}")


# ============================================================================
#                         PUNTO DE ENTRADA
# ============================================================================

def main():
    root = tk.Tk()
    app = DXFConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()