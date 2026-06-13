from geometry.transform_utils import (
    translate_items,
)

from geometry.text_label import TextLabel


HORIZONTAL_GAP = 200
VERTICAL_GAP = 500
LABEL_Y_OFFSET = -300
TEXT_HEIGHT = 100


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
            f"{material} {thickness} mm",
            0,
            current_row_y + 150,
            TEXT_HEIGHT,
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
                current_x,
                current_row_y + LABEL_Y_OFFSET,
                TEXT_HEIGHT,
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
            + abs(LABEL_Y_OFFSET)
        )

    return output_items