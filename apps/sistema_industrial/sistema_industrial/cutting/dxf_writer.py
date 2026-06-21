"""Tiny DXF writer for ordered cut batch previews.

This is intentionally simple. It does not import existing geometry and does not
nest. Its purpose is to create a valid-enough ordered DXF scaffold for MVP tests
and future replacement by ezdxf-based implementation.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DxfRect:
    x: float
    y: float
    width: float
    height: float
    label: str | None = None


def _line(x1, y1, x2, y2) -> list[str]:
    return ["0", "LINE", "8", "CUT", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)]


def _text(x, y, value) -> list[str]:
    return ["0", "TEXT", "8", "LABEL", "10", str(x), "20", str(y), "40", "20", "1", value]


def _text_right(x, y, value) -> list[str]:
    """Return a right-aligned DXF TEXT entity.

    The second alignment point (group codes 11/21) combined with horizontal
    justification 2 (right) causes the text to end at x rather than start there,
    so it extends to the left without overlapping the drawing area.
    """
    return [
        "0", "TEXT",
        "8", "LABEL",
        "10", str(x),   # first alignment point X
        "20", str(y),   # first alignment point Y
        "40", "20",     # text height
        "1", value,
        "72", "2",      # horizontal justification: 2 = right
        "11", str(x),   # second alignment point X
        "21", str(y),   # second alignment point Y
    ]


def write_rectangles_dxf(path: Path, rectangles: list[DxfRect]) -> Path:
    entities: list[str] = []
    labeled_y: set[float] = set()
    for r in rectangles:
        entities += _line(r.x, r.y, r.x + r.width, r.y)
        entities += _line(r.x + r.width, r.y, r.x + r.width, r.y + r.height)
        entities += _line(r.x + r.width, r.y + r.height, r.x, r.y + r.height)
        entities += _line(r.x, r.y + r.height, r.x, r.y)
        if r.label and r.y not in labeled_y:
            labeled_y.add(r.y)
            entities += _text_right(-200, r.y + r.height / 2, r.label)
    content = ["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
