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
import re
from pathlib import Path

# Clamped knot vector for a single cubic Bézier segment (degree 3, 4 control points).
_CUBIC_KNOTS = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]


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


def _add_path_to_msp(msp, d: str, scale: float, layer: str) -> None:
    """Parse SVG path d and add LINE/SPLINE entities directly to modelspace.

    C/c → SPLINE (exact cubic Bézier, degree=3, clamped knots)
    Q/q → elevated to cubic → SPLINE
    M/m, L/l, H/h, V/v, Z/z → LINE
    """
    tok_re = re.compile(
        r"[MmLlCcQqZzHhVv]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
    )
    tokens = tok_re.findall(d)

    cx = cy = sx = sy = 0.0
    cmd = None
    i = 0

    def consume(n):
        nonlocal i
        vals = [float(tokens[i + k]) for k in range(n)]
        i += n
        return vals

    def sc(x, y):
        """Apply scale to a point."""
        return x * scale, y * scale

    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"[a-zA-Z]", tok):
            cmd = tok
            i += 1

        if cmd == "M":
            x, y = consume(2)
            cx, cy = x, y
            sx, sy = cx, cy
            cmd = "L"
        elif cmd == "m":
            dx, dy = consume(2)
            cx, cy = cx + dx, cy + dy
            sx, sy = cx, cy
            cmd = "l"

        elif cmd == "L":
            x, y = consume(2)
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(x, y)
            if abs(x1 - x0) > 1e-9 or abs(y1 - y0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cx, cy = x, y
        elif cmd == "l":
            dx, dy = consume(2)
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(cx + dx, cy + dy)
            if abs(x1 - x0) > 1e-9 or abs(y1 - y0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cx, cy = cx + dx, cy + dy

        elif cmd == "H":
            x, = consume(1)
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(x, cy)
            if abs(x1 - x0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cx = x
        elif cmd == "h":
            dx, = consume(1)
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(cx + dx, cy)
            if abs(x1 - x0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cx += dx

        elif cmd == "V":
            y, = consume(1)
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(cx, y)
            if abs(y1 - y0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cy = y
        elif cmd == "v":
            dy, = consume(1)
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(cx, cy + dy)
            if abs(y1 - y0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cy += dy

        elif cmd == "C":
            x1, y1, x2, y2, x, y = consume(6)
            _add_cubic_spline(
                msp,
                sc(cx, cy), sc(x1, y1), sc(x2, y2), sc(x, y),
                layer,
            )
            cx, cy = x, y
        elif cmd == "c":
            dx1, dy1, dx2, dy2, dx, dy = consume(6)
            _add_cubic_spline(
                msp,
                sc(cx, cy),
                sc(cx + dx1, cy + dy1),
                sc(cx + dx2, cy + dy2),
                sc(cx + dx, cy + dy),
                layer,
            )
            cx, cy = cx + dx, cy + dy

        elif cmd == "Q":
            # Elevate quadratic Bézier to cubic: Pc1 = P0 + 2/3*(P1-P0), Pc2 = P3 + 2/3*(P1-P3)
            qx1, qy1, x, y = consume(4)
            pc1x = cx + 2/3 * (qx1 - cx)
            pc1y = cy + 2/3 * (qy1 - cy)
            pc2x = x + 2/3 * (qx1 - x)
            pc2y = y + 2/3 * (qy1 - y)
            _add_cubic_spline(
                msp,
                sc(cx, cy), sc(pc1x, pc1y), sc(pc2x, pc2y), sc(x, y),
                layer,
            )
            cx, cy = x, y
        elif cmd == "q":
            dqx1, dqy1, dx, dy = consume(4)
            qx1, qy1 = cx + dqx1, cy + dqy1
            x, y = cx + dx, cy + dy
            pc1x = cx + 2/3 * (qx1 - cx)
            pc1y = cy + 2/3 * (qy1 - cy)
            pc2x = x + 2/3 * (qx1 - x)
            pc2y = y + 2/3 * (qy1 - y)
            _add_cubic_spline(
                msp,
                sc(cx, cy), sc(pc1x, pc1y), sc(pc2x, pc2y), sc(x, y),
                layer,
            )
            cx, cy = x, y

        elif cmd in ("Z", "z"):
            x0, y0 = sc(cx, cy)
            x1, y1 = sc(sx, sy)
            if abs(x1 - x0) > 1e-9 or abs(y1 - y0) > 1e-9:
                msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": layer})
            cx, cy = sx, sy

        else:
            while i < len(tokens) and not re.match(r"[a-zA-Z]", tokens[i]):
                i += 1


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
