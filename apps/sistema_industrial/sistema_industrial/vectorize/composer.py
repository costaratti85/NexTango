"""Compose DXF from selected vectorizer entities.

Converts SVG path data into DXF entities:
  - Cubic Bézier (C command from potrace) → SPLINE entity, degree=3, clamped
    knot vector [0,0,0,0,1,1,1,1], 4 control points. Mathematically exact.
  - Quadratic Bézier (Q) → elevated to cubic → SPLINE.
  - Straight segments (M, L, H, V, Z) → LINE entity.

SPLINE entities can be processed by convert_splines() (same as AutoCAD DXFs).

Coordinate conversion:
  path units → display units: multiply by transform_scale (typically 0.1)
  display units → mm: multiply by escala_display (mm/display_unit, from calibration)
  Combined: mm = path_coord × transform_scale × escala_display

Y-axis: SVG Y points down, DXF Y points up. For hole patterns that tile
uniformly this rarely matters; operators can mirror in CypCut if needed.
"""
import math
import re
from pathlib import Path

# Clamped knot vector for a single cubic Bézier segment (degree 3, 4 control points).
_CUBIC_KNOTS = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]

# Tangent discontinuity threshold between consecutive Bézier segments.
# When the angle between the exit tangent of segment N and the entry tangent of
# segment N+1 exceeds this value, the junction is treated as a hard corner.
_CORNER_DEG = 25.0
# Fraction of each Bézier to keep as a smooth SPLINE at a corner.
# The tail (segment N) and head (segment N+1) each lose (1 - _CLIP_FRAC) of
# their length to a straight LINE, eliminating the "early-turn" control point
# influence that potrace adds when fitting smooth curves across physical corners.
_CLIP_FRAC = 0.87


def _add_cubic_spline(msp, p0, p1, p2, p3, layer: str) -> None:
    """Add one cubic Bézier as a DXF SPLINE entity (exact, no approximation)."""
    sp = msp.add_spline(dxfattribs={"layer": layer})
    sp.dxf.degree = 3
    sp.knots = _CUBIC_KNOTS
    sp.control_points = [
        (p0[0], p0[1], 0.0),
        (p1[0], p1[1], 0.0),
        (p2[0], p2[1], 0.0),
        (p3[0], p3[1], 0.0),
    ]


def _de_casteljau_split(p0, p1, p2, p3, t):
    """Split cubic Bézier at parameter t (De Casteljau algorithm).

    Returns (first, second), each a 4-tuple of (x,y) points.
    first  covers [0, t].
    second covers [t, 1].
    """
    def _lp(a, b):
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    q01 = _lp(p0, p1)
    q12 = _lp(p1, p2)
    q23 = _lp(p2, p3)
    q012 = _lp(q01, q12)
    q123 = _lp(q12, q23)
    q0123 = _lp(q012, q123)
    return (p0, q01, q012, q0123), (q0123, q123, q23, p3)


def _vec_angle_deg(v1, v2):
    """Angle in degrees between two 2D vectors (0–180)."""
    n1 = math.hypot(v1[0], v1[1])
    n2 = math.hypot(v2[0], v2[1])
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def _parse_path_segments(d: str, scale: float) -> list:
    """Parse SVG path d into a flat list of scaled absolute-coordinate segments.

    Returns a list of:
      ("line",  (x0,y0), (x1,y1))
      ("cubic", (x0,y0), (x1,y1), (x2,y2), (x3,y3))

    Q/q are elevated to cubic. Zero-length lines are dropped.
    All coordinates are multiplied by scale.
    """
    tok_re = re.compile(
        r"[MmLlCcQqZzHhVv]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
    )
    tokens = tok_re.findall(d)
    segs = []
    cx = cy = sx = sy = 0.0
    cmd = None
    i = 0

    def sc(x, y):
        return x * scale, y * scale

    def consume(n):
        nonlocal i
        vals = [float(tokens[i + k]) for k in range(n)]
        i += n
        return vals

    def _add_line(x0, y0, x1, y1):
        p0, p1 = sc(x0, y0), sc(x1, y1)
        if abs(p1[0] - p0[0]) > 1e-9 or abs(p1[1] - p0[1]) > 1e-9:
            segs.append(("line", p0, p1))

    def _add_cubic(x0, y0, x1, y1, x2, y2, x3, y3):
        segs.append(("cubic", sc(x0, y0), sc(x1, y1), sc(x2, y2), sc(x3, y3)))

    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"[a-zA-Z]", tok):
            cmd = tok; i += 1
        if i >= len(tokens):
            break

        if cmd == "M":
            x, y = consume(2); cx, cy = x, y; sx, sy = cx, cy; cmd = "L"
        elif cmd == "m":
            dx, dy = consume(2); cx, cy = cx+dx, cy+dy; sx, sy = cx, cy; cmd = "l"
        elif cmd == "L":
            x, y = consume(2); _add_line(cx, cy, x, y); cx, cy = x, y
        elif cmd == "l":
            dx, dy = consume(2); _add_line(cx, cy, cx+dx, cy+dy); cx, cy = cx+dx, cy+dy
        elif cmd == "H":
            x, = consume(1); _add_line(cx, cy, x, cy); cx = x
        elif cmd == "h":
            dx, = consume(1); _add_line(cx, cy, cx+dx, cy); cx += dx
        elif cmd == "V":
            y, = consume(1); _add_line(cx, cy, cx, y); cy = y
        elif cmd == "v":
            dy, = consume(1); _add_line(cx, cy, cx, cy+dy); cy += dy
        elif cmd == "C":
            x1, y1, x2, y2, x, y = consume(6)
            _add_cubic(cx, cy, x1, y1, x2, y2, x, y); cx, cy = x, y
        elif cmd == "c":
            dx1, dy1, dx2, dy2, dx, dy = consume(6)
            _add_cubic(cx, cy, cx+dx1, cy+dy1, cx+dx2, cy+dy2, cx+dx, cy+dy)
            cx, cy = cx+dx, cy+dy
        elif cmd == "Q":
            qx1, qy1, x, y = consume(4)
            pc1x = cx + 2/3*(qx1-cx); pc1y = cy + 2/3*(qy1-cy)
            pc2x = x + 2/3*(qx1-x); pc2y = y + 2/3*(qy1-y)
            _add_cubic(cx, cy, pc1x, pc1y, pc2x, pc2y, x, y); cx, cy = x, y
        elif cmd == "q":
            dqx1, dqy1, dx, dy = consume(4)
            qx1, qy1 = cx+dqx1, cy+dqy1; x, y = cx+dx, cy+dy
            pc1x = cx + 2/3*(qx1-cx); pc1y = cy + 2/3*(qy1-cy)
            pc2x = x + 2/3*(qx1-x); pc2y = y + 2/3*(qy1-y)
            _add_cubic(cx, cy, pc1x, pc1y, pc2x, pc2y, x, y); cx, cy = x, y
        elif cmd in ("Z", "z"):
            _add_line(cx, cy, sx, sy); cx, cy = sx, sy
        else:
            while i < len(tokens) and not re.match(r"[a-zA-Z]", tokens[i]):
                i += 1

    return segs


def _split_at_corners(segments: list) -> list:
    """Clip Bézier segments at sharp tangent junctions.

    For each pair of consecutive cubic segments where the angle between
    the exit tangent of segment N and the entry tangent of segment N+1
    exceeds _CORNER_DEG, both segments are clipped:

      - Tail of N  (last 1-_CLIP_FRAC of the curve) → LINE to corner point
      - Head of N+1 (first 1-_CLIP_FRAC of the curve) → LINE from corner point

    This removes the "early-turn" shape that smooth-preset Béziers develop
    when potrace places control points to create tangent continuity across
    what is physically a sharp corner — one side was contaminating the other.
    The clip uses De Casteljau so the main Bézier portion is geometrically exact.

    Non-cubic segments between consecutive cubics reset the adjacency chain.
    """
    n = len(segments)
    clip_tail = [False] * n
    clip_head = [False] * n

    for idx in range(n - 1):
        if segments[idx][0] != "cubic" or segments[idx + 1][0] != "cubic":
            continue
        # Exit tangent of segment idx: direction from P2 to P3
        p2 = segments[idx][3]    # second control point
        p3 = segments[idx][4]    # endpoint = startpoint of next
        # Entry tangent of segment idx+1: direction from P3 to P4
        p4 = segments[idx + 1][2]  # first control point of next segment
        exit_v  = (p3[0] - p2[0], p3[1] - p2[1])
        entry_v = (p4[0] - p3[0], p4[1] - p3[1])
        if _vec_angle_deg(exit_v, entry_v) > _CORNER_DEG:
            clip_tail[idx]     = True
            clip_head[idx + 1] = True

    result = []
    for idx, seg in enumerate(segments):
        if seg[0] != "cubic" or (not clip_tail[idx] and not clip_head[idx]):
            result.append(seg)
            continue

        _, p0, p1, p2, p3 = seg
        need_head = clip_head[idx]
        need_tail = clip_tail[idx]
        cp0, cp1, cp2, cp3 = p0, p1, p2, p3   # working control points

        if need_head:
            # Split off the first (1-_CLIP_FRAC) as a straight LINE stub.
            head_t = 1.0 - _CLIP_FRAC           # e.g. 0.13 when _CLIP_FRAC=0.87
            stub_h, rest_h = _de_casteljau_split(cp0, cp1, cp2, cp3, head_t)
            result.append(("line", stub_h[0], stub_h[3]))
            cp0, cp1, cp2, cp3 = rest_h
            # The remaining portion spans [head_t, 1]; re-parametrize tail_t
            # so it still clips the last (1-_CLIP_FRAC) of the ORIGINAL curve:
            # In the new [0,1] of rest_h, (1 - head_t - (1 - _CLIP_FRAC)) / (1 - head_t)
            #   = (2*_CLIP_FRAC - 1) / _CLIP_FRAC
            tail_t = (2.0 * _CLIP_FRAC - 1.0) / _CLIP_FRAC  # ≈ 0.851 when _CLIP_FRAC=0.87
        else:
            tail_t = _CLIP_FRAC

        if need_tail:
            main_t, stub_t = _de_casteljau_split(cp0, cp1, cp2, cp3, tail_t)
            result.append(("cubic", *main_t))
            result.append(("line", stub_t[0], stub_t[3]))
        else:
            result.append(("cubic", cp0, cp1, cp2, cp3))

    return result


def _add_path_to_msp(msp, d: str, scale: float, layer: str) -> None:
    """Parse SVG path d and add LINE/SPLINE entities to modelspace.

    C/c → SPLINE (exact cubic Bézier, degree=3, clamped knots)
    Q/q → elevated to cubic → SPLINE
    M/m, L/l, H/h, V/v, Z/z → LINE

    Consecutive Bézier segments with a tangent junction angle exceeding
    _CORNER_DEG are clipped at _CLIP_FRAC: the tail/head near the corner
    is replaced with a straight LINE. This prevents the arc fitter from
    rounding across a hard corner regardless of which potrace preset was used.
    """
    segments = _parse_path_segments(d, scale)
    segments = _split_at_corners(segments)
    for seg in segments:
        if seg[0] == "line":
            _, p0, p1 = seg
            msp.add_line(p0, p1, dxfattribs={"layer": layer})
        elif seg[0] == "cubic":
            _, p0, p1, p2, p3 = seg
            _add_cubic_spline(msp, p0, p1, p2, p3, layer)


def _center_msp_on_origin(msp) -> None:
    """Translate all LINE/SPLINE entities in msp so their combined bbox is centered on (0,0).

    The vectorizer writes coordinates in image space (origin at image corner).
    This ensures the resulting DXF pattern has (0,0) at its geometric center,
    which is required for symmetric tiling in the panel motor.
    """
    all_x: list = []
    all_y: list = []
    for entity in msp:
        et = entity.dxftype()
        if et == "LINE":
            all_x.extend([entity.dxf.start.x, entity.dxf.end.x])
            all_y.extend([entity.dxf.start.y, entity.dxf.end.y])
        elif et == "SPLINE":
            for cp in entity.control_points:
                all_x.append(cp[0])
                all_y.append(cp[1])

    if not all_x or not all_y:
        return

    cx = (min(all_x) + max(all_x)) / 2.0
    cy = (min(all_y) + max(all_y)) / 2.0
    if abs(cx) <= 1e-6 and abs(cy) <= 1e-6:
        return

    for entity in msp:
        et = entity.dxftype()
        if et == "LINE":
            s = entity.dxf.start
            e = entity.dxf.end
            entity.dxf.start = (s.x - cx, s.y - cy, 0.0)
            entity.dxf.end = (e.x - cx, e.y - cy, 0.0)
        elif et == "SPLINE":
            entity.control_points = [
                (cp[0] - cx, cp[1] - cy, 0.0)
                for cp in entity.control_points
            ]


def compose_dxf(
    manifest: dict,
    selected_items: list,
    escala_display: float,
    output_path: Path,
) -> None:
    """Compose DXF from selected entities, each with its own preset.

    Args:
        manifest: dict loaded from manifest.json
        selected_items: list of {entity_id: str, preset: str}, e.g.
            [{"entity_id": "e0", "preset": "Fino"},
             {"entity_id": "e7", "preset": "Ultra-Fino"}]
            Every item may use a different preset — the entity is looked up
            in the preset named by its own "preset" key.
        escala_display: mm per SVG display unit (from calibration line)
        output_path: destination .dxf path
    """
    import ezdxf

    # Build per-preset lookup: preset_name → {entity_id → entity dict}
    presets_by_name: dict = {}
    for p in manifest.get("presets", []):
        presets_by_name[p["name"]] = {
            "transform_scale": p.get("transform_scale", 0.1),
            "entities_by_id": {e["id"]: e for e in p.get("entities", [])},
        }

    layer = "CUT"
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    doc.layers.new(layer, dxfattribs={"color": 1})

    for item in selected_items:
        entity_id = item.get("entity_id") or item.get("id")
        preset_name = item.get("preset")
        preset_info = presets_by_name.get(preset_name)
        if preset_info is None:
            continue
        entity = preset_info["entities_by_id"].get(entity_id)
        if entity is None:
            continue
        mm_factor = preset_info["transform_scale"] * escala_display
        try:
            _add_path_to_msp(msp, entity["d"], scale=mm_factor, layer=layer)
        except Exception:
            continue

    # Center bbox on origin so the pattern file itself has (0,0) at its center.
    # Without this, patterns open in CypCut/viewers with the origin offset to
    # one corner, matching the raw image coordinates from the vectorizer.
    _center_msp_on_origin(msp)

    doc.saveas(str(output_path))


def compose_dxf_legacy(
    manifest: dict,
    preset_name: str,
    selected_ids: list,
    escala_display: float,
    output_path: Path,
) -> None:
    """Backward-compatible wrapper: one preset for all entities."""
    items = [{"entity_id": eid, "preset": preset_name} for eid in selected_ids]
    compose_dxf(manifest, items, escala_display, output_path)
