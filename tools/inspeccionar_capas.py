#!/usr/bin/env python3
"""Inspecciona el formato de capas de un DXF — para cotejar el DXF de referencia
de CypCut contra lo que produce nuestro generador de flycut.

Uso:
    source .venv/bin/activate
    python tools/inspeccionar_capas.py <archivo.dxf> [otro.dxf ...]

Reporta, por archivo: versión DXF, tabla LAYER (nombre + color + linetype de cada
capa declarada) y qué capas usan realmente las entidades. Con dos archivos, marca
las diferencias de nombres de capa entre ambos (referencia CypCut vs generado).
"""
from __future__ import annotations

import sys
from collections import Counter

try:
    import ezdxf
except ImportError:
    sys.exit("Falta ezdxf. Activá el venv: source .venv/bin/activate")


def inspeccionar(path: str) -> set:
    d = ezdxf.readfile(path)
    print(f"### {path}")
    print(f"  versión DXF: {d.dxfversion} ({d.acad_release})")
    print("  TABLA LAYER (capas declaradas):")
    declaradas = set()
    for l in sorted(d.layers, key=lambda x: x.dxf.name):
        declaradas.add(l.dxf.name)
        print(f"    nombre={l.dxf.name!r:16} color={l.dxf.color:>3} linetype={l.dxf.linetype}")
    usadas = Counter(e.dxf.layer for e in d.modelspace())
    print("  capas usadas por entidades:")
    for name, n in sorted(usadas.items()):
        marca = "" if name in declaradas else "  <-- NO declarada en la tabla!"
        print(f"    {name!r:16} {n:>6} entidades{marca}")
    print()
    return set(usadas)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    conjuntos = {p: inspeccionar(p) for p in sys.argv[1:]}
    if len(conjuntos) == 2:
        (a, sa), (b, sb) = conjuntos.items()
        print("=== DIFERENCIA de nombres de capa ===")
        print(f"  solo en {a}: {sorted(sa - sb)}")
        print(f"  solo en {b}: {sorted(sb - sa)}")
        print(f"  en ambos:   {sorted(sa & sb)}")


if __name__ == "__main__":
    main()
