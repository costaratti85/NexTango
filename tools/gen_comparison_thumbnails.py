"""Genera dos thumbnails comparativos: figuras completas vs cortar en borde."""

import math
import os
import sys
from contextlib import redirect_stdout
from importlib import import_module
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "Programas_hechos" / "Panel Decorativo"
OUT_DIR = ROOT / "tools"

# Parametros del panel
WIDTH = 500.0
HEIGHT = 200.0
MARGIN = 20.0
DIAMETER = 20.0
DISTANCE = 30.0   # centro a centro


def run_motor(cut_partial: bool):
    legacy_path = str(LEGACY_DIR)
    prev_cwd = Path.cwd()
    inserted = legacy_path not in sys.path
    if inserted:
        sys.path.insert(0, legacy_path)
    os.chdir(LEGACY_DIR)
    try:
        for mod in [k for k in sys.modules if k.split(".")[0] in
                    ("config", "layout", "geometry", "main", "dxf", "models")]:
            del sys.modules[mod]

        settings_mod = import_module("config.settings")
        layout_mod = import_module("layout.cad_result_layout")
        main_mod = import_module("main")

        s = settings_mod.Settings()
        s.sheet_sizes = [(WIDTH, HEIGHT, 1)]
        s.margin = MARGIN
        s.pattern_type = "tresbolillo"
        s.pattern_name = "Tresbolillo"
        s.hole_diameter = DIAMETER
        s.hole_distance = DISTANCE
        s.cut_partial_figures = cut_partial

        buf = StringIO()
        with redirect_stdout(buf):
            items = main_mod.create_cad_result_items_from_batch(s)
            arranged = layout_mod.arrange_cad_result_items(items)
        return arranged
    finally:
        os.chdir(prev_cwd)
        if inserted:
            try:
                sys.path.remove(legacy_path)
            except ValueError:
                pass


def draw_panel(ax, arranged):
    color = "#1a1a2e"

    def _draw(geom):
        if hasattr(geom, "points"):
            pts = list(geom.points)
            if len(pts) >= 2:
                ax.plot([p[0] for p in pts], [p[1] for p in pts],
                        color=color, linewidth=0.8)
        elif hasattr(geom, "entities"):
            for e in geom.entities:
                _draw(e)
        elif hasattr(geom, "cx") and hasattr(geom, "radius"):
            span = geom.end_angle - geom.start_angle
            if span < 0:
                span += 360
            full = abs(span) >= 359.9
            a0 = math.radians(geom.start_angle)
            if full:
                n, total = 64, 2 * math.pi
            else:
                rad = math.radians(span) % (2 * math.pi)
                n = max(8, int(abs(rad) / (2 * math.pi) * 64))
                total = math.radians(span)
            angles = [a0 + total * i / n for i in range(n + 1)]
            ax.plot([geom.cx + math.cos(a) * geom.radius for a in angles],
                    [geom.cy + math.sin(a) * geom.radius for a in angles],
                    color=color, linewidth=0.8)
        elif hasattr(geom, "x1") and hasattr(geom, "x2"):
            ax.plot([geom.x1, geom.x2], [geom.y1, geom.y2],
                    color=color, linewidth=0.8)

    for item in arranged:
        _draw(item)

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_facecolor("white")


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    print("Corriendo motor — Figuras completas centradas...")
    centered = run_motor(cut_partial=False)
    print("Corriendo motor — Cortar en borde...")
    border = run_motor(cut_partial=True)

    # Imagen comparativa side-by-side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor("white")

    draw_panel(ax1, centered)
    ax1.set_title("Figuras completas centradas", fontsize=13, pad=10,
                  fontfamily="sans-serif")

    draw_panel(ax2, border)
    ax2.set_title("Cortar figuras en borde", fontsize=13, pad=10,
                  fontfamily="sans-serif")

    plt.tight_layout(pad=1.5)
    out = OUT_DIR / "comparacion_modos.png"
    fig.savefig(str(out), dpi=130, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Guardado: {out}")
