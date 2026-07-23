"""La etiqueta de cantidad («×N») debe quedar a 200 mm del borde inferior del panel.

El panel se coloca con su borde inferior en current_row_y (0 para el primer
grupo). arrange_cad_result_items estampa:
  - row_label  (N°/material) en current_row_y + 150  (ARRIBA del borde) -> intacta
  - quantity_label («×N»)     en current_row_y - 200  (200 mm ABAJO del borde)
El MTEXT usa ancla top-right, así que el tope del texto queda a esa distancia.
"""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

LEGACY = Path(__file__).resolve().parents[1] / "Programas_hechos" / "Panel Decorativo"
sys.path.insert(0, str(LEGACY))

from layout import cad_result_layout as L  # noqa: E402
from geometry.sheet_outline import create_sheet_outline  # noqa: E402
from geometry.text_label import TextLabel  # noqa: E402


def _fake_item(quantity, width=550.0, height=1500.0):
    # geometría mínima: el contorno de la chapa (borde inferior en y=0 local)
    return SimpleNamespace(
        material="Chapa doble decapada",
        thickness=0.7,
        quantity=quantity,
        geometry_items=[create_sheet_outline(0, 0, width, height)],
        occupied_width=width,
        occupied_height=height,
    )


def _labels(output_items):
    return [it for it in output_items if isinstance(it, TextLabel)]


def test_quantity_label_a_200mm_del_borde_inferior():
    out = L.arrange_cad_result_items([_fake_item(quantity=3)])
    qty = next(l for l in _labels(out) if l.text.startswith("x"))
    # primer (único) grupo -> current_row_y = 0 -> borde inferior del panel en y=0
    assert qty.text == "x3"
    assert qty.y == -200          # 200 mm por debajo del borde inferior
    assert L.QUANTITY_LABEL_Y_OFFSET == -200


def test_numero_material_label_no_se_movio():
    """La etiqueta de material/número (N°) sigue 150 mm ARRIBA del borde (intacta)."""
    out = L.arrange_cad_result_items([_fake_item(quantity=1)])
    row = next(l for l in _labels(out) if not l.text.startswith("x"))
    assert row.y == 150           # sin cambios


def test_espaciado_entre_grupos_no_cambia_por_mover_la_etiqueta():
    """La clearance de fila quedó decoplada de la posición de la etiqueta (300)."""
    assert L.ROW_LABEL_CLEARANCE == 300
