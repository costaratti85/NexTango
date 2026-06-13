"""DXF entity validator for pattern uploads.

The legacy engine only handles LINE, ARC, and CIRCLE entities.
This module rejects DXF files that contain anything else before
they reach the engine, with a message specific enough for the
vendor to act on.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import ezdxf

SUPPORTED_TYPES = {"LINE", "ARC", "CIRCLE"}


@dataclass
class _UnsupportedEntity:
    entity_type: str
    location: str


class UnsupportedDXFEntitiesError(Exception):
    """Raised when a DXF file contains entities the engine cannot process."""

    def __init__(self, found: list[_UnsupportedEntity]) -> None:
        self.found = found
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        by_type: dict[str, list[str]] = {}
        for e in self.found:
            by_type.setdefault(e.entity_type, []).append(e.location)

        lines = ["El archivo contiene entidades no soportadas por el motor:"]
        for etype, locations in sorted(by_type.items()):
            count = len(locations)
            sample = ", ".join(locations[:3])
            suffix = f" (y {count - 3} más)" if count > 3 else ""
            lines.append(f"  - {etype}: {count}  en: {sample}{suffix}")
        lines.append(
            "Convertirlas a líneas, arcos o círculos en Inkscape antes de cargar."
        )
        return "\n".join(lines)


def _entity_location(entity) -> str:
    for attr in ("center", "insert", "start"):
        try:
            pt = getattr(entity.dxf, attr)
            return f"({pt.x:.1f}, {pt.y:.1f})"
        except Exception:
            pass
    try:
        pts = list(entity.control_points)
        if pts:
            return f"({pts[0][0]:.1f}, {pts[0][1]:.1f})"
    except Exception:
        pass
    return "posición no disponible"


def validate_dxf_entities(dxf_path: Path) -> None:
    """Scan *dxf_path* and raise if it contains unsupported entity types.

    Safe to call before adding a pattern to the library.  On success
    returns None; on failure raises UnsupportedDXFEntitiesError with a
    vendor-readable message.
    """
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    unsupported: list[_UnsupportedEntity] = []
    for entity in msp:
        dxftype = entity.dxftype()
        if dxftype not in SUPPORTED_TYPES:
            unsupported.append(
                _UnsupportedEntity(
                    entity_type=dxftype,
                    location=_entity_location(entity),
                )
            )

    if unsupported:
        raise UnsupportedDXFEntitiesError(unsupported)
