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


def write_rectangles_dxf(path: Path, rectangles: list[DxfRect]) -> Path:
    entities: list[str] = []
    for r in rectangles:
        entities += _line(r.x, r.y, r.x + r.width, r.y)
        entities += _line(r.x + r.width, r.y, r.x + r.width, r.y + r.height)
        entities += _line(r.x + r.width, r.y + r.height, r.x, r.y + r.height)
        entities += _line(r.x, r.y + r.height, r.x, r.y)
        if r.label:
            entities += _text(r.x, r.y - 25, r.label)
    content = ["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path
