"""Compose DXF from vectorizer run output.

Converts selected SVG paths (cubic bezier curves from potrace) into
LINE entities in a single DXF file with layer CUT (CypCut-compatible).

Y-axis note: SVG has Y pointing down; DXF Y points up. For decorative
hole patterns the orientation rarely matters, so we keep SVG coordinates
as-is. The operator can mirror in CypCut if needed.
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


def _path_d_to_segments(d: str, steps: int = 20):
    """Convert SVG path d attribute to list of (x0, y0, x1, y1) line segments.

    Handles M, L, H, V, C, Q, Z and their lowercase (relative) variants.
    potrace SVG output uses primarily M, C, Z — others included for robustness.
    """
    tok_pattern = re.compile(
        r"[MmLlCcQqZzHhVv]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
    )
    tokens = tok_pattern.findall(d)

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
        # Implicit repeat if still numeric — cmd stays

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
            segs.append((cx, cy, x, y))
            cx, cy = x, y
        elif cmd == "l":
            dx, dy = consume(2)
            segs.append((cx, cy, cx + dx, cy + dy))
            cx, cy = cx + dx, cy + dy
        elif cmd == "H":
            x, = consume(1)
            segs.append((cx, cy, x, cy))
            cx = x
        elif cmd == "h":
            dx, = consume(1)
            segs.append((cx, cy, cx + dx, cy))
            cx += dx
        elif cmd == "V":
            y, = consume(1)
            segs.append((cx, cy, cx, y))
            cy = y
        elif cmd == "v":
            dy, = consume(1)
            segs.append((cx, cy, cx, cy + dy))
            cy += dy
        elif cmd == "C":
            x1, y1, x2, y2, x, y = consume(6)
            pts = _cubic_bezier_pts((cx, cy), (x1, y1), (x2, y2), (x, y), steps)
            for j in range(len(pts) - 1):
                segs.append((*pts[j], *pts[j + 1]))
            cx, cy = x, y
        elif cmd == "c":
            dx1, dy1, dx2, dy2, dx, dy = consume(6)
            pts = _cubic_bezier_pts(
                (cx, cy),
                (cx + dx1, cy + dy1),
                (cx + dx2, cy + dy2),
                (cx + dx, cy + dy),
                steps,
            )
            for j in range(len(pts) - 1):
                segs.append((*pts[j], *pts[j + 1]))
            cx, cy = cx + dx, cy + dy
        elif cmd == "Q":
            x1, y1, x, y = consume(4)
            pts = _quadratic_bezier_pts((cx, cy), (x1, y1), (x, y), steps)
            for j in range(len(pts) - 1):
                segs.append((*pts[j], *pts[j + 1]))
            cx, cy = x, y
        elif cmd == "q":
            dx1, dy1, dx, dy = consume(4)
            pts = _quadratic_bezier_pts(
                (cx, cy), (cx + dx1, cy + dy1), (cx + dx, cy + dy), steps
            )
            for j in range(len(pts) - 1):
                segs.append((*pts[j], *pts[j + 1]))
            cx, cy = cx + dx, cy + dy
        elif cmd in ("Z", "z"):
            if abs(cx - sx) > 1e-6 or abs(cy - sy) > 1e-6:
                segs.append((cx, cy, sx, sy))
            cx, cy = sx, sy
        else:
            # Unknown command — skip until next letter
            while i < len(tokens) and not re.match(r"[a-zA-Z]", tokens[i]):
                i += 1

    return segs


def compose_dxf(manifest: dict, selecciones: list, output_path: Path) -> None:
    """Write a DXF composed from selected figura/variante combinations.

    selecciones: [{"figura_id": "fig_0", "preset": "Fino"}, ...]
    """
    import ezdxf

    sel_map = {s["figura_id"]: s["preset"] for s in selecciones}

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    doc.layers.new("CUT", dxfattribs={"color": 1})

    for figura in manifest.get("figuras", []):
        fid = figura["figura_id"]
        if fid not in sel_map:
            continue
        preset_name = sel_map[fid]
        variante = next(
            (v for v in figura.get("variantes", []) if v["preset"] == preset_name),
            None,
        )
        if not variante or not variante.get("d"):
            continue

        try:
            segs = _path_d_to_segments(variante["d"])
        except Exception:
            continue

        for x0, y0, x1, y1 in segs:
            msp.add_line((x0, y0), (x1, y1), dxfattribs={"layer": "CUT"})

    doc.saveas(str(output_path))
