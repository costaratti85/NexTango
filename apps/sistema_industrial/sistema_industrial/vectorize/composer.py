"""Compose DXF from selected vectorizer entities.

Converts SVG path data (cubic bezier curves from potrace) into LINE entities
in a DXF file with layer CUT (CypCut-compatible).

Coordinate conversion:
  path units → display units: multiply by transform_scale (typically 0.1)
  display units → mm: multiply by escala_display (mm/display_unit, from calibration)
  Combined: mm = path_coord × transform_scale × escala_display

Y-axis: SVG Y points down, DXF Y points up. For hole patterns that tile
uniformly this rarely matters; operators can mirror in CypCut if needed.
"""
import re
from pathlib import Path


def _cubic_bezier_pts(p0, p1, p2, p3, steps=20):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0]
        y = u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def _quadratic_bezier_pts(p0, p1, p2, steps=20):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**2*p0[0] + 2*u*t*p1[0] + t**2*p2[0]
        y = u**2*p0[1] + 2*u*t*p1[1] + t**2*p2[1]
        pts.append((x, y))
    return pts


def _path_d_to_segments(d: str, scale: float = 1.0, steps: int = 20):
    """Convert SVG path d to list of (x0, y0, x1, y1) segments scaled to mm.

    Handles M, L, H, V, C, Q, Z and their lowercase (relative) variants.
    potrace output uses primarily M, C, Z.
    """
    tok_re = re.compile(
        r"[MmLlCcQqZzHhVv]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
    )
    tokens = tok_re.findall(d)

    segs = []
    cx = cy = sx = sy = 0.0
    cmd = None
    i = 0

    def consume(n):
        nonlocal i
        vals = [float(tokens[i + k]) for k in range(n)]
        i += n
        return vals

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
            segs.append((cx * scale, cy * scale, x * scale, y * scale))
            cx, cy = x, y
        elif cmd == "l":
            dx, dy = consume(2)
            segs.append((cx * scale, cy * scale, (cx + dx) * scale, (cy + dy) * scale))
            cx, cy = cx + dx, cy + dy
        elif cmd == "H":
            x, = consume(1)
            segs.append((cx * scale, cy * scale, x * scale, cy * scale))
            cx = x
        elif cmd == "h":
            dx, = consume(1)
            segs.append((cx * scale, cy * scale, (cx + dx) * scale, cy * scale))
            cx += dx
        elif cmd == "V":
            y, = consume(1)
            segs.append((cx * scale, cy * scale, cx * scale, y * scale))
            cy = y
        elif cmd == "v":
            dy, = consume(1)
            segs.append((cx * scale, cy * scale, cx * scale, (cy + dy) * scale))
            cy += dy
        elif cmd == "C":
            x1, y1, x2, y2, x, y = consume(6)
            pts = _cubic_bezier_pts((cx, cy), (x1, y1), (x2, y2), (x, y), steps)
            for j in range(len(pts) - 1):
                segs.append((pts[j][0] * scale, pts[j][1] * scale,
                              pts[j+1][0] * scale, pts[j+1][1] * scale))
            cx, cy = x, y
        elif cmd == "c":
            dx1, dy1, dx2, dy2, dx, dy = consume(6)
            pts = _cubic_bezier_pts(
                (cx, cy), (cx+dx1, cy+dy1), (cx+dx2, cy+dy2), (cx+dx, cy+dy), steps
            )
            for j in range(len(pts) - 1):
                segs.append((pts[j][0] * scale, pts[j][1] * scale,
                              pts[j+1][0] * scale, pts[j+1][1] * scale))
            cx, cy = cx + dx, cy + dy
        elif cmd == "Q":
            x1, y1, x, y = consume(4)
            pts = _quadratic_bezier_pts((cx, cy), (x1, y1), (x, y), steps)
            for j in range(len(pts) - 1):
                segs.append((pts[j][0] * scale, pts[j][1] * scale,
                              pts[j+1][0] * scale, pts[j+1][1] * scale))
            cx, cy = x, y
        elif cmd == "q":
            dx1, dy1, dx, dy = consume(4)
            pts = _quadratic_bezier_pts(
                (cx, cy), (cx+dx1, cy+dy1), (cx+dx, cy+dy), steps
            )
            for j in range(len(pts) - 1):
                segs.append((pts[j][0] * scale, pts[j][1] * scale,
                              pts[j+1][0] * scale, pts[j+1][1] * scale))
            cx, cy = cx + dx, cy + dy
        elif cmd in ("Z", "z"):
            if abs(cx - sx) > 1e-6 or abs(cy - sy) > 1e-6:
                segs.append((cx * scale, cy * scale, sx * scale, sy * scale))
            cx, cy = sx, sy
        else:
            while i < len(tokens) and not re.match(r"[a-zA-Z]", tokens[i]):
                i += 1

    return segs


def compose_dxf(
    manifest: dict,
    preset_name: str,
    selected_ids: list,
    escala_display: float,
    output_path: Path,
) -> None:
    """Compose DXF from selected entities of one preset.

    Args:
        manifest: dict loaded from manifest.json
        preset_name: e.g. "Fino"
        selected_ids: list of entity IDs, e.g. ["e0", "e3", "e7"]
        escala_display: mm per SVG display unit (from calibration line)
        output_path: destination .dxf path
    """
    import ezdxf

    preset = next((p for p in manifest.get("presets", []) if p["name"] == preset_name), None)
    if preset is None:
        raise ValueError(f"Preset '{preset_name}' no encontrado en el manifest")

    # path units → display units → mm
    transform_scale = preset.get("transform_scale", 0.1)
    mm_factor = transform_scale * escala_display

    selected = set(selected_ids)

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    doc.layers.new("CUT", dxfattribs={"color": 1})

    for entity in preset.get("entities", []):
        if entity["id"] not in selected:
            continue
        try:
            segs = _path_d_to_segments(entity["d"], scale=mm_factor)
        except Exception:
            continue
        for x0, y0, x1, y1 in segs:
            msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": "CUT"})

    doc.saveas(str(output_path))
