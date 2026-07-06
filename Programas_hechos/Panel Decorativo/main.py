from config.user_input import (
    ask_batch_settings,
    ask_add_another_batch,
    ask_output_file,
    ask_continue,
)

from dxf.importer import DXFImporter

from dxf.mixed_exporter import (
    MixedDXFExporter,
)

from geometry.discretizer import (
    Discretizer,
)

from geometry.entity_stitcher import (
    EntityStitcher,
)

from geometry.rect_clipper import (
    RectClipper,
)

from geometry.polyline_clipper import (
    PolylineClipper,
)

from geometry.polyline_closer import (
    PolylineCloser,
)

from geometry.sheet_outline import (
    create_sheet_outline,
)

from geometry.arc_rebuilder import (
    ArcRebuilder,
)

from geometry.tresbolillo_pattern import (
    create_tresbolillo_piece,
)

from geometry.cuadriculado_pattern import (
    create_cuadriculado_piece,
)

from layout.tile_classifier import (
    TileClassifier,
)

from layout.figure_variant_cache import (
    FigureVariantCache,
)

from layout.cad_result_layout import (
    arrange_cad_result_items,
)

from models.cad_result_item import (
    CADResultItem,
)


def process_border_figure(
    figure,
    xmin,
    ymin,
    xmax,
    ymax,
):

    discretizer = Discretizer(
        arc_step_degrees=5
    )

    loose_polys = discretizer.discretize_piece(
        figure
    )

    from geometry.polyline_stitcher import (
        PolylineStitcher,
    )

    stitcher = PolylineStitcher()

    contours = stitcher.stitch(
        loose_polys
    )

    rect_clipper = RectClipper(
        xmin,
        ymin,
        xmax,
        ymax,
    )

    poly_clipper = PolylineClipper(
        rect_clipper
    )

    clipped_polys = []

    for contour in contours:

        clipped = poly_clipper.clip_polyline(
            contour
        )

        clipped_polys.extend(clipped)

    closer = PolylineCloser(
        xmin,
        ymin,
        xmax,
        ymax,
    )

    closed_polys = closer.close_all(
        clipped_polys
    )

    rebuilder = ArcRebuilder(
        min_arc_points=2,
        tolerance=0.08,
    )

    return rebuilder.rebuild_all(
        closed_polys
    )


def load_pattern(settings):

    if settings.pattern_type == "dxf":

        importer = DXFImporter()

        piece = importer.load(
            settings.input_file
        )

        # Normalize bbox center to origin so tiling is symmetric on all 4 edges.
        # Without this, a pattern whose bbox is off-center tiles asymmetrically
        # (e.g. full figures on right/top, clipped figures on left/bottom).
        bbox = piece.bbox()
        if bbox is not None:
            cx = (bbox.min_x + bbox.max_x) / 2.0
            cy = (bbox.min_y + bbox.max_y) / 2.0
            if abs(cx) > 1e-6 or abs(cy) > 1e-6:
                piece = piece.translated(-cx, -cy)

        return (
            piece,
            settings.step_x,
            settings.step_y,
        )

    if settings.pattern_type == "tresbolillo":

        piece, step_x, step_y = (
            create_tresbolillo_piece(
                settings.hole_diameter,
                settings.hole_distance,
            )
        )

        return piece, step_x, step_y

    if settings.pattern_type == "cuadriculado":

        piece, step_x, step_y = create_cuadriculado_piece(
            settings.hole_shape,
            settings.hole_size,
            settings.step_x,
            settings.step_y,
        )

        return piece, step_x, step_y

    raise Exception(
        "Tipo de patron no soportado"
    )


def generate_cut_mode_geometry(
    base_figures,
    sheet_width,
    sheet_height,
    margin,
    step_x,
    step_y,
    variant_cache,
):

    output_items = []

    usable_width = sheet_width - margin * 2
    usable_height = sheet_height - margin * 2

    xmin = margin
    ymin = margin

    xmax = margin + usable_width
    ymax = margin + usable_height

    output_items.append(
        create_sheet_outline(
            0,
            0,
            sheet_width,
            sheet_height,
        )
    )

    classifier = TileClassifier(
        xmin,
        ymin,
        xmax,
        ymax,
    )

    cols = int(usable_width / step_x) + 3
    rows = int(usable_height / step_y) + 3

    for row in range(rows):

        for col in range(cols):

            dx = margin + col * step_x
            dy = margin + row * step_y

            for figure_index, figure in enumerate(
                base_figures
            ):

                moved = figure.translated(
                    dx,
                    dy,
                )

                bbox = moved.bbox()

                classification = (
                    classifier
                    .classify_bbox(bbox)
                )

                if classification == "outside":
                    continue

                cached_items = variant_cache.get(
                    figure_index,
                    figure,
                    classification,
                    dx,
                    dy,
                    xmin,
                    ymin,
                    xmax,
                    ymax,
                )

                output_items.extend(
                    cached_items
                )

    return output_items


def generate_centered_full_mode_geometry(
    original_piece,
    sheet_width,
    sheet_height,
    margin,
    step_x,
    step_y,
):

    output_items = []

    usable_width = sheet_width - margin * 2
    usable_height = sheet_height - margin * 2

    output_items.append(
        create_sheet_outline(
            0,
            0,
            sheet_width,
            sheet_height,
        )
    )

    bbox = original_piece.bbox()
    piece_w = bbox.max_x - bbox.min_x
    piece_h = bbox.max_y - bbox.min_y

    if piece_w > usable_width or piece_h > usable_height:
        return output_items

    cols = int(usable_width / step_x)
    rows = int(usable_height / step_y)

    # If the piece's visual content exceeds step_x (e.g. DXF tile with bleed),
    # the last tile would overhang. Reduce cols/rows until visual extent fits.
    while cols > 0 and (cols - 1) * step_x + piece_w > usable_width:
        cols -= 1
    while rows > 0 and (rows - 1) * step_y + piece_h > usable_height:
        rows -= 1

    if cols == 0 or rows == 0:
        return output_items

    # Center the full visual extent within the usable area.
    # Subtracting bbox.min_x corrects for DXF patterns whose content starts
    # left of the origin (i.e. bbox.min_x is negative).
    visual_width = (cols - 1) * step_x + piece_w
    visual_height = (rows - 1) * step_y + piece_h
    start_x = margin + (usable_width - visual_width) / 2 - bbox.min_x
    start_y = margin + (usable_height - visual_height) / 2 - bbox.min_y

    for row in range(rows):

        for col in range(cols):

            dx = start_x + col * step_x
            dy = start_y + row * step_y

            output_items.append(
                original_piece.translated(
                    dx,
                    dy,
                )
            )

    return output_items


def create_cad_result_items_from_batch(
    settings,
):

    original_piece, step_x, step_y = (
        load_pattern(settings)
    )

    entity_stitcher = EntityStitcher()

    base_figures = entity_stitcher.stitch(
        original_piece.entities
    )

    print()
    print("FIGURAS DETECTADAS:", len(base_figures))

    result_items = []

    variant_cache = FigureVariantCache(
        process_border_figure
    )

    for sheet_width, sheet_height, quantity in settings.sheet_sizes:

        print()
        print(
            f"CHAPA {sheet_width}x{sheet_height} x{quantity}"
        )

        if settings.cut_partial_figures:

            print("MODO: recorte contra margen")

            geometry_items = generate_cut_mode_geometry(
                base_figures,
                sheet_width,
                sheet_height,
                settings.margin,
                step_x,
                step_y,
                variant_cache,
            )

        else:

            print("MODO: figuras completas centradas")

            geometry_items = generate_centered_full_mode_geometry(
                original_piece,
                sheet_width,
                sheet_height,
                settings.margin,
                step_x,
                step_y,
            )

        item = CADResultItem(
            name=(
                f"{settings.pattern_name} "
                f"{sheet_width}x{sheet_height}"
            ),
            quantity=quantity,
            material=settings.material,
            thickness=settings.thickness,
            geometry_items=geometry_items,
            occupied_width=sheet_width,
            occupied_height=sheet_height,
            cut_length_mm=0,
            pierce_count=0,
            bend_count=0,
        )

        result_items.append(item)

    return result_items


def save_with_retry(
    exporter,
    output_items,
    output_file,
):

    while True:

        try:

            exporter.save(
                output_items,
                output_file,
            )

            print()
            print("DXF generado:")
            print(output_file)

            break

        except PermissionError:

            print()
            print("ERROR")
            print()
            print(
                "No se pudo sobrescribir el archivo DXF."
            )
            print()
            print("Posibles causas:")
            print(
                "- El archivo está abierto en otro programa"
            )
            print(
                "- El archivo tiene permisos de solo lectura"
            )
            print()
            print("Opciones:")
            print("1 - Reintentar")
            print("2 - Guardar con otro nombre")
            print("3 - Cancelar")
            print()

            option = input("Opcion: ").strip()

            if option == "1":
                continue

            if option == "2":

                new_file = ask_output_file()

                if new_file != "":
                    output_file = new_file

                continue

            print()
            print("Guardado cancelado.")
            break


def create_order():

    all_result_items = []

    while True:

        batch_settings = ask_batch_settings()

        if batch_settings is None:
            return None

        batch_items = create_cad_result_items_from_batch(
            batch_settings
        )

        all_result_items.extend(
            batch_items
        )

        if not ask_add_another_batch():
            break

    output_file = ask_output_file()

    if output_file == "":
        raise Exception(
            "No se eligio archivo de salida."
        )

    return all_result_items, output_file


def main():

    while True:

        order = create_order()

        if order is None:
            print()
            print("Programa finalizado.")
            break

        result_items, output_file = order

        arranged_items = arrange_cad_result_items(
            result_items
        )

        exporter = MixedDXFExporter()

        save_with_retry(
            exporter,
            arranged_items,
            output_file,
        )

        if not ask_continue():

            print()
            print("Programa finalizado.")
            break


if __name__ == "__main__":
    main()