from config.settings import Settings
from config.pattern_library import PatternLibrary


def parse_sheet_size(text):

    text = text.lower().strip()
    parts = text.split("x")

    if len(parts) not in [2, 3]:
        raise Exception(
            f"Formato invalido: {text}"
        )

    width = float(parts[0])
    height = float(parts[1])

    if len(parts) == 3:
        quantity = int(parts[2])
    else:
        quantity = 1

    return width, height, quantity


def ask_dxf_file():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    filename = filedialog.askopenfilename(
        title="Seleccionar archivo DXF del patron",
        filetypes=[
            ("DXF files", "*.dxf"),
            ("Todos los archivos", "*.*"),
        ],
    )

    root.destroy()

    return filename


def ask_output_file():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    filename = filedialog.asksaveasfilename(
        title="Guardar DXF final",
        defaultextension=".dxf",
        filetypes=[
            ("DXF files", "*.dxf"),
            ("Todos los archivos", "*.*"),
        ],
    )

    root.destroy()

    return filename


def choose_pattern(settings):

    library = PatternLibrary()

    while True:

        print()
        print("BIBLIOTECA DE PATRONES")
        print()
        print("1 - Usar patron DXF existente")
        print("2 - Cargar patron DXF nuevo")
        print("3 - Borrar patron DXF")
        print("4 - Usar tresbolillo circular")
        print("5 - Salir")
        print()

        option = input("Opcion: ").strip()

        if option == "1":

            names = library.get_names()

            if not names:
                print("No hay patrones cargados.")
                continue

            print()
            print("Patrones disponibles:")

            for i, name in enumerate(names, start=1):
                print(f"{i} - {name}")

            index = int(input("Elegir patron: "))

            name = names[index - 1]
            data = library.get_pattern(name)

            settings.pattern_type = "dxf"
            settings.pattern_name = name
            settings.input_file = data["file_path"]
            settings.step_x = float(data["step_x"])
            settings.step_y = float(data["step_y"])

            return True

        elif option == "2":

            name = input("Nombre del patron: ").strip()

            if name == "":
                print("Nombre invalido.")
                continue

            file_path = ask_dxf_file()

            if file_path == "":
                print("No se selecciono archivo.")
                continue

            step_x = float(input("Step X del patron: "))
            step_y = float(input("Step Y del patron: "))

            library.add_pattern(
                name,
                file_path,
                step_x,
                step_y,
            )

            print("Patron guardado.")

        elif option == "3":

            names = library.get_names()

            if not names:
                print("No hay patrones para borrar.")
                continue

            print()
            print("Patrones disponibles:")

            for i, name in enumerate(names, start=1):
                print(f"{i} - {name}")

            index = int(input("Borrar patron: "))
            name = names[index - 1]

            confirm = input(
                f"Confirmar borrar '{name}'? s/n: "
            ).strip().lower()

            if confirm == "s":
                library.delete_pattern(name)
                print("Patron borrado.")

        elif option == "4":

            settings.pattern_type = "tresbolillo"
            settings.pattern_name = "Tresbolillo circular"

            settings.hole_diameter = float(
                input("Diametro del agujero: ")
            )

            settings.hole_distance = float(
                input("Distancia entre centros: ")
            )

            return True

        elif option == "5":

            return False

        else:

            print("Opcion invalida.")


def ask_batch_settings():

    settings = Settings()

    ok = choose_pattern(settings)

    if not ok:
        return None

    print()
    print("PATRON SELECCIONADO")
    print(settings.pattern_name)

    if settings.pattern_type == "dxf":

        print(settings.input_file)
        print(f"Step X: {settings.step_x}")
        print(f"Step Y: {settings.step_y}")

    else:

        print(f"Diametro: {settings.hole_diameter}")
        print(f"Distancia: {settings.hole_distance}")

    print()

    settings.material = input(
        "Material: "
    ).strip()

    settings.thickness = float(
        input("Espesor: ")
    )

    settings.margin = float(
        input("Margen sin perforar: ")
    )

    print()
    print("Modo de generacion")
    print("1 - Recortar figuras contra margen")
    print("2 - Solo figuras completas centradas")
    print()

    mode = input("Opcion: ").strip()

    settings.cut_partial_figures = (
        mode != "2"
    )

    print()
    print("Medidas de chapa")
    print("Una por linea")
    print("Formato: ancho x alto x cantidad")
    print("Ejemplo: 350x500x4")
    print("Linea vacia para terminar")
    print()

    while True:

        line = input("> ").strip()

        if line == "":
            break

        settings.sheet_sizes.append(
            parse_sheet_size(line)
        )

    if not settings.sheet_sizes:
        raise Exception(
            "No se cargaron medidas de chapa."
        )

    return settings


def ask_add_another_batch():

    print()
    print("¿Querés agregar más chapas con otro patrón?")
    print("1 - Sí, agregar otro patrón/lote")
    print("2 - No, finalizar pedido y guardar DXF")
    print()

    option = input("Opcion: ").strip()

    return option == "1"


def ask_continue():

    print()
    print("¿Querés iniciar un nuevo pedido?")
    print("1 - Sí, atender otro cliente")
    print("2 - No, finalizar programa")
    print()

    option = input("Opcion: ").strip()

    return option == "1"