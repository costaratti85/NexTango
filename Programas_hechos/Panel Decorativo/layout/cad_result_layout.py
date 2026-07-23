import json
from pathlib import Path

from geometry.transform_utils import (
    translate_items,
)

from geometry.text_label import TextLabel


HORIZONTAL_GAP = 200
VERTICAL_GAP = 500
# Etiqueta de cantidad («×N»): a 200 mm por debajo del borde inferior del panel
# (pedido de Constantino). El panel se coloca con su borde inferior en
# current_row_y y el MTEXT usa ancla top-right, así que el tope del texto queda
# exactamente a esta distancia del borde inferior. Antes eran 300 mm (muy lejos).
QUANTITY_LABEL_Y_OFFSET = -200
# Espacio reservado bajo el panel al calcular el salto de fila. Se mantiene en
# 300 (independiente de la posición de la etiqueta) para NO alterar el
# espaciado entre grupos de material al mover la etiqueta.
ROW_LABEL_CLEARANCE = 300
TEXT_HEIGHT = 100

_MATERIAL_TABLE_FILE = (
    Path(__file__).resolve().parent.parent / "material_table.json"
)
_MATERIAL_TABLE_CACHE = None


def _load_material_table():
    global _MATERIAL_TABLE_CACHE
    if _MATERIAL_TABLE_CACHE is None:
        try:
            with _MATERIAL_TABLE_FILE.open("r", encoding="utf-8") as f:
                _MATERIAL_TABLE_CACHE = json.load(f)
        except Exception:
            _MATERIAL_TABLE_CACHE = []
    return _MATERIAL_TABLE_CACHE


def _abbreviate_material(material, thickness):
    table = _load_material_table()
    thickness_mm = float(thickness)
    entry = next(
        (
            e for e in table
            if e.get("material") == material
            and abs(float(e.get("espesor_mm", 0)) - thickness_mm) < 0.001
        ),
        None,
    )
    if entry is None:
        return f"{thickness_mm:g}mm"
    familia = str(entry.get("familia", "")).lower()
    calibre = str(entry.get("calibre", "-")).strip()
    espesor = float(entry.get("espesor_mm", thickness_mm))
    if familia == "hierro":
        return f"N°{calibre}" if calibre and calibre != "-" else f"{espesor:g}mm"
    if familia == "galvanizada":
        return f"Galv N°{calibre}" if calibre and calibre != "-" else f"Galv {espesor:g}mm"
    if familia == "inox304":
        return f"Inox 304 {espesor:g}mm"
    if familia == "inox430":
        return f"Inox 430 {espesor:g}mm"
    return f"{espesor:g}mm"


def group_items(items):

    groups = {}

    for item in items:

        key = (
            item.material,
            item.thickness,
        )

        if key not in groups:
            groups[key] = []

        groups[key].append(item)

    return groups


def arrange_cad_result_items(items):

    output_items = []

    groups = group_items(items)

    current_row_y = 0

    for (material, thickness), group_items_list in groups.items():

        group_items_list.sort(
            key=lambda item: item.quantity,
            reverse=True,
        )

        row_label = TextLabel(
            _abbreviate_material(material, thickness),
            -200,
            current_row_y + 150,
            TEXT_HEIGHT,
            right_align=True,
        )

        output_items.append(row_label)

        current_x = 0
        max_height_in_row = 0

        for item in group_items_list:

            moved_geometry = translate_items(
                item.geometry_items,
                current_x,
                current_row_y,
            )

            output_items.extend(
                moved_geometry
            )

            quantity_label = TextLabel(
                f"x{item.quantity}",
                current_x + 150,
                current_row_y + QUANTITY_LABEL_Y_OFFSET,
                TEXT_HEIGHT,
                right_align=True,
            )

            output_items.append(
                quantity_label
            )

            current_x += (
                item.occupied_width
                + HORIZONTAL_GAP
            )

            max_height_in_row = max(
                max_height_in_row,
                item.occupied_height,
            )

        current_row_y -= (
            max_height_in_row
            + VERTICAL_GAP
            + ROW_LABEL_CLEARANCE
        )

    return output_items
