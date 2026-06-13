# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import random
import re


def formato_numero(n):
    if float(n).is_integer():
        return str(int(n))
    return str(round(n, 2)).replace(".", ",")


def normalizar_disp(disp):
    disp = str(disp).strip().upper()
    if disp in ["X", "CRUZADO", "CRUZADOS"]:
        return "X"
    if disp in ["/\\", "/"]:
        return "/\\"
    if disp in ["\\/", "\\"]:
        return "\\/"
    if disp in ["\\\\"]:
        return "\\\\"
    return "//"


def normalizar_bin_recto(b):
    return tuple(sorted(b, reverse=True))


def largo_ocupado_recto(patron):
    return sum(patron)


def pieza_recta_a_str(largo):
    return formato_numero(largo)


def patron_a_str_recto(patron):
    conteo = Counter(patron)
    items = sorted(conteo.items(), key=lambda x: x[0], reverse=True)
    partes = []

    for largo, cantidad in items:
        largo_txt = pieza_recta_a_str(largo)
        if cantidad > 1:
            partes.append(f"{cantidad} x {largo_txt}")
        else:
            partes.append(largo_txt)

    return " + ".join(partes)


def normalizar_bin_angular(b):
    return tuple(sorted(b, key=lambda x: (-x[0], x)))


def largo_pieza_angular(pieza):
    return pieza[0]


def largo_ocupado_angular(patron):
    return sum(largo_pieza_angular(p) for p in patron)


def pieza_angular_base_a_str(pieza):
    largo, izq, der, cara, disp = pieza
    largo_txt = formato_numero(largo)

    if izq == 0 and der == 0:
        return largo_txt

    disp = normalizar_disp(disp)

    return (
        f"{largo_txt} "
        f"({formato_numero(izq)}{disp}{formato_numero(der)})"
        f"{formato_numero(cara)}"
    )


def patron_a_str_angular(patron):
    conteo = Counter(patron)
    items = sorted(conteo.items(), key=lambda x: (-x[0][0], x[0]))
    partes = []

    for pieza, cantidad in items:
        pieza_txt = pieza_angular_base_a_str(pieza)
        partes.append(f"{cantidad} x {pieza_txt}")

    return " + ".join(partes)


def first_fit(bar_len, pieces, largo_pieza, largo_ocupado, normalizar):
    bins = []

    for p in pieces:
        placed = False

        for b in bins:
            if largo_ocupado(b) + largo_pieza(p) <= bar_len:
                b.append(p)
                placed = True
                break

        if not placed:
            bins.append([p])

    return [list(normalizar(b)) for b in bins]


def best_fit(bar_len, pieces, largo_pieza, largo_ocupado, normalizar):
    bins = []

    for p in pieces:
        mejor_idx = None
        menor_resto = None

        for i, b in enumerate(bins):
            usado = largo_ocupado(b)

            if usado + largo_pieza(p) <= bar_len:
                resto = bar_len - (usado + largo_pieza(p))

                if menor_resto is None or resto < menor_resto:
                    menor_resto = resto
                    mejor_idx = i

        if mejor_idx is None:
            bins.append([p])
        else:
            bins[mejor_idx].append(p)

    return [list(normalizar(b)) for b in bins]


def worst_fit(bar_len, pieces, largo_pieza, largo_ocupado, normalizar):
    bins = []

    for p in pieces:
        mejor_idx = None
        mayor_resto = None

        for i, b in enumerate(bins):
            usado = largo_ocupado(b)

            if usado + largo_pieza(p) <= bar_len:
                resto_actual = bar_len - usado

                if mayor_resto is None or resto_actual > mayor_resto:
                    mayor_resto = resto_actual
                    mejor_idx = i

        if mejor_idx is None:
            bins.append([p])
        else:
            bins[mejor_idx].append(p)

    return [list(normalizar(b)) for b in bins]


def ordenar_piezas(pieces, modo, angular=False):
    if angular:
        clave_desc = lambda x: (-x[0], x)
        clave_asc = lambda x: (x[0], x)
        largo = lambda x: x[0]
    else:
        clave_desc = lambda x: -x
        clave_asc = lambda x: x
        largo = lambda x: x

    if modo == "desc":
        return sorted(pieces, key=clave_desc)

    if modo == "asc":
        return sorted(pieces, key=clave_asc)

    if modo == "por_frecuencia":
        conteo = Counter(pieces)
        return sorted(pieces, key=lambda x: (-conteo[x], -largo(x), x))

    if modo == "alternado":
        ordenadas = sorted(pieces, key=clave_desc)
        resultado = []
        izq = 0
        der = len(ordenadas) - 1

        while izq <= der:
            resultado.append(ordenadas[izq])
            izq += 1

            if izq <= der:
                resultado.append(ordenadas[der])
                der -= 1

        return resultado

    return list(pieces)


def generar_variantes(bar_len, piezas, angular=False):
    variantes = []
    modos = ["desc", "asc", "alternado", "por_frecuencia"]

    if angular:
        largo_pieza = largo_pieza_angular
        largo_ocupado = largo_ocupado_angular
        normalizar = normalizar_bin_angular
    else:
        largo_pieza = lambda x: x
        largo_ocupado = largo_ocupado_recto
        normalizar = normalizar_bin_recto

    for modo in modos:
        piezas_ordenadas = ordenar_piezas(piezas, modo, angular=angular)

        variantes.append(first_fit(bar_len, piezas_ordenadas, largo_pieza, largo_ocupado, normalizar))
        variantes.append(best_fit(bar_len, piezas_ordenadas, largo_pieza, largo_ocupado, normalizar))
        variantes.append(worst_fit(bar_len, piezas_ordenadas, largo_pieza, largo_ocupado, normalizar))

    rnd = random.Random(12345)
    piezas_base = list(piezas)

    for _ in range(200):
        piezas_random = piezas_base[:]
        rnd.shuffle(piezas_random)

        variantes.append(first_fit(bar_len, piezas_random, largo_pieza, largo_ocupado, normalizar))
        variantes.append(best_fit(bar_len, piezas_random, largo_pieza, largo_ocupado, normalizar))

    return variantes


def puntuar_plan(bar_len, bins, angular=False):
    if angular:
        normalizar = normalizar_bin_angular
        largo_ocupado = largo_ocupado_angular
    else:
        normalizar = normalizar_bin_recto
        largo_ocupado = largo_ocupado_recto

    cantidad_barras = len(bins)
    patrones = Counter(normalizar(b) for b in bins)
    cantidad_patrones = len(patrones)
    desperdicio_total = sum(bar_len - largo_ocupado(b) for b in bins)

    grupos_repetidos = sum(1 for _, cant in patrones.items() if cant > 1)
    mayor_grupo = max(patrones.values()) if patrones else 0

    return (
        cantidad_barras,
        cantidad_patrones,
        -mayor_grupo,
        -grupos_repetidos,
        desperdicio_total
    )


def elegir_mejor_plan(bar_len, piezas, angular=False):
    variantes = generar_variantes(bar_len, piezas, angular=angular)
    mejor = None
    mejor_score = None

    for bins in variantes:
        score = puntuar_plan(bar_len, bins, angular=angular)

        if mejor is None or score < mejor_score:
            mejor = bins
            mejor_score = score

    return mejor


def pieza_suelta_a_str(pieza, angular=False):
    if angular:
        return pieza_angular_base_a_str(pieza)

    return pieza_recta_a_str(pieza)


def patron_a_str(patron, angular=False):
    if angular:
        return patron_a_str_angular(patron)

    return patron_a_str_recto(patron)


def largo_ocupado(patron, angular=False):
    if angular:
        return largo_ocupado_angular(patron)

    return largo_ocupado_recto(patron)


def normalizar_bin(b, angular=False):
    if angular:
        return normalizar_bin_angular(b)

    return normalizar_bin_recto(b)


def largo_pieza(pieza, angular=False):
    if angular:
        return largo_pieza_angular(pieza)

    return pieza


def generar_plan_excel(bar_len, piezas, tipo_material, medida, eficiencia_minima=65, angular=False):
    if not piezas:
        return "No hay piezas."

    for p in piezas:
        if largo_pieza(p, angular=angular) > bar_len:
            return (
                f"Error: hay una pieza de {formato_numero(largo_pieza(p, angular=angular))} mm "
                f"que es más larga que la barra de {formato_numero(bar_len)} mm."
            )

    bins = elegir_mejor_plan(bar_len, piezas, angular=angular)
    freq = Counter(normalizar_bin(b, angular=angular) for b in bins)

    patrones_ordenados = sorted(
        freq.items(),
        key=lambda x: (-x[1], -largo_ocupado(list(x[0]), angular=angular), x[0])
    )

    lineas = []

    for patron_tuple, cantidad_barras in patrones_ordenados:
        patron = list(patron_tuple)
        usado = largo_ocupado(patron, angular=angular)
        eficiencia = (usado / bar_len) * 100 if bar_len > 0 else 0

        if eficiencia >= eficiencia_minima:
            detalle = f"{cantidad_barras} a {patron_a_str(patron, angular=angular)}"

            lineas.append(
                f"{cantidad_barras}\t{tipo_material}\t{medida}\tx {formato_numero(bar_len)}"
            )

            lineas.append(
                f"\t{detalle}\t\t"
            )

        else:
            for _ in range(cantidad_barras):
                piezas_sueltas = sorted(
                    patron,
                    key=lambda x: -largo_pieza(x, angular=angular)
                )

                for pieza in piezas_sueltas:
                    lineas.append(
                        f"1\t{tipo_material}\t{medida}\tx {pieza_suelta_a_str(pieza, angular=angular)}"
                    )

    return "\n".join(lineas)


def interpretar_pieza_angular(texto):
    texto = texto.strip()

    match_angular = re.match(
        r"^([\d.,]+)\s*\(\s*([\d.,]+)\s*(//|\\\\|/\\|\\/|X)\s*([\d.,]+)\s*\)\s*([\d.,]+)\s*$",
        texto,
        re.IGNORECASE
    )

    if match_angular:
        largo = float(match_angular.group(1).replace(",", "."))
        izq = float(match_angular.group(2).replace(",", "."))
        disp = normalizar_disp(match_angular.group(3))
        der = float(match_angular.group(4).replace(",", "."))
        cara = float(match_angular.group(5).replace(",", "."))
        return (largo, izq, der, cara, disp)

    match_recto = re.match(r"^([\d.,]+)$", texto)

    if match_recto:
        largo = float(match_recto.group(1).replace(",", "."))
        return (largo, 0.0, 0.0, 0.0, "//")

    return None


def interpretar_plan_de_corte(texto, angular=False):
    cortes = Counter()
    lineas = texto.splitlines()
    i = 0

    while i < len(lineas):
        linea_original = lineas[i]

        if not linea_original.strip():
            i += 1
            continue

        # Caso salida tabulada para Excel
        if "\t" in linea_original:
            columnas = linea_original.split("\t")

            # Fila detalle: primera columna vacía, segunda contiene "4 a ..."
            if len(columnas) >= 2 and columnas[0].strip() == "":
                linea = columnas[1].strip()
                i += 1

            # Fila cabecera o corte suelto: Cantidad | Tipo | Medida | x Largo
            elif len(columnas) >= 4:
                # Si la línea siguiente es detalle, esta fila es cabecera de barras enteras.
                # Entonces NO se releva como corte.
                if i + 1 < len(lineas):
                    siguiente = lineas[i + 1]
                    sig_cols = siguiente.split("\t")

                    if (
                        "\t" in siguiente
                        and len(sig_cols) >= 2
                        and sig_cols[0].strip() == ""
                        and re.match(r"^\s*\d+\s*a\s*", sig_cols[1].strip(), re.IGNORECASE)
                    ):
                        i += 1
                        continue

                # Si no tiene detalle debajo, es corte suelto y sí se releva.
                try:
                    cantidad = int(columnas[0].strip())
                    largo_txt = columnas[3].strip()

                    largo_txt = re.sub(
                        r"^\s*x\s*",
                        "",
                        largo_txt,
                        flags=re.IGNORECASE
                    )

                    if angular:
                        pieza = interpretar_pieza_angular(largo_txt)
                    else:
                        pieza = float(largo_txt.replace(",", "."))

                    cortes[pieza] += cantidad
                    i += 1
                    continue

                except:
                    i += 1
                    continue

            else:
                i += 1
                continue

        else:
            linea = linea_original.strip()
            i += 1

        match_barras = re.match(
            r"^\s*(\d+)\s*a\s*(.+)$",
            linea,
            re.IGNORECASE
        )

        if not match_barras:
            continue

        cantidad_barras = int(match_barras.group(1))
        contenido = match_barras.group(2)

        partes = contenido.split("+")

        for parte in partes:
            parte = parte.strip()

            if not parte:
                continue

            # Acepta "2x1500" y "2 x 1500"
            match_multi = re.match(
                r"^\s*(\d+)\s*x\s*(.+)$",
                parte,
                re.IGNORECASE
            )

            if match_multi:
                cant_pieza = int(match_multi.group(1))
                texto_pieza = match_multi.group(2).strip()
            else:
                cant_pieza = 1
                texto_pieza = parte

            if angular:
                pieza = interpretar_pieza_angular(texto_pieza)
            else:
                match_recto = re.match(r"^([\d.,]+)$", texto_pieza.strip())
                pieza = float(match_recto.group(1).replace(",", ".")) if match_recto else None

            if pieza is not None:
                cortes[pieza] += cantidad_barras * cant_pieza

    if angular:
        lista = sorted(cortes.items(), key=lambda x: (-x[0][0], x[0]))
    else:
        lista = sorted(cortes.items(), key=lambda x: -x[0])

    return [(cant, pieza) for pieza, cant in lista]


class TablaEditable:
    def __init__(self, parent, columnas, ancho_cols=None, angular=False):
        self.parent = parent
        self.columnas = columnas
        self.angular = angular
        self.entradas = []
        self.filas = 0
        self.ancho_cols = ancho_cols or [10] * len(columnas)

        self.frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(self.frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.frame,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame.pack(fill="both", expand=True)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.header_frame = ttk.Frame(self.scrollable_frame)
        self.header_frame.pack(fill="x")

        for i, col in enumerate(columnas):
            label = ttk.Label(
                self.header_frame,
                text=col,
                font=("TkDefaultFont", 10, "bold"),
                relief="ridge"
            )
            label.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
            self.header_frame.columnconfigure(i, weight=1)

        self.filas_frame = ttk.Frame(self.scrollable_frame)
        self.filas_frame.pack(fill="x")

        self.agregar_fila()

    def destruir(self):
        self.frame.destroy()

    def refrescar_binds(self):
        for fila_idx, fila in enumerate(self.entradas):
            for col_idx, widget in enumerate(fila):
                widget.bind(
                    "<Tab>",
                    lambda e, r=fila_idx, c=col_idx: self._tab_pressed(e, r, c)
                )
                widget.bind(
                    "<Return>",
                    lambda e, r=fila_idx, c=col_idx: self._enter_pressed(e, r, c)
                )

    def crear_widget_celda(self, row_frame, col_nombre, ancho):
        if col_nombre == "Disp":
            widget = ttk.Combobox(
                row_frame,
                width=ancho,
                values=["//", "\\\\", "/\\", "\\/", "X"],
                state="readonly"
            )
            widget.set("//")
            return widget

        return ttk.Entry(row_frame, width=ancho)

    def agregar_fila(self, valores=None):
        row_frame = ttk.Frame(self.filas_frame)
        row_frame.pack(fill="x", pady=1)

        entradas_fila = []

        for i, col in enumerate(self.columnas):
            widget = self.crear_widget_celda(row_frame, col, self.ancho_cols[i])
            widget.grid(row=0, column=i, sticky="ew", padx=1)

            if valores and i < len(valores):
                if isinstance(widget, ttk.Combobox):
                    widget.set(normalizar_disp(valores[i]))
                else:
                    widget.insert(0, str(valores[i]))

            entradas_fila.append(widget)
            row_frame.columnconfigure(i, weight=1)

        self.entradas.append(entradas_fila)
        self.filas += 1
        self.refrescar_binds()

        if entradas_fila:
            entradas_fila[0].focus_set()

    def _tab_pressed(self, event, fila, col):
        if col < len(self.columnas) - 1:
            self.entradas[fila][col + 1].focus_set()
        else:
            if fila == self.filas - 1:
                self.agregar_fila()

            self.entradas[fila + 1][0].focus_set()

        return "break"

    def _enter_pressed(self, event, fila, col):
        if fila == self.filas - 1:
            self.agregar_fila()

        self.entradas[fila + 1][col].focus_set()
        return "break"

    def eliminar_fila(self):
        if self.filas > 1:
            row_frame = self.entradas[-1][0].master
            row_frame.destroy()
            self.entradas.pop()
            self.filas -= 1
            self.refrescar_binds()

    def borrar_todo(self):
        while self.filas > 1:
            self.eliminar_fila()

        for widget in self.entradas[0]:
            if isinstance(widget, ttk.Combobox):
                widget.set("//")
            else:
                widget.delete(0, tk.END)

        self.entradas[0][0].focus_set()

    def obtener_datos(self, angular=False):
        datos = []

        for fila in self.entradas:
            try:
                cant_txt = fila[0].get().strip()
                largo_txt = fila[1].get().strip().replace(",", ".")

                cant = int(cant_txt) if cant_txt else 0
                largo = float(largo_txt) if largo_txt else 0

                if cant <= 0 or largo <= 0:
                    continue

                if angular:
                    izq_txt = fila[2].get().strip().replace(",", ".")
                    der_txt = fila[3].get().strip().replace(",", ".")
                    cara_txt = fila[4].get().strip().replace(",", ".")
                    disp_txt = fila[5].get().strip()

                    izq = float(izq_txt) if izq_txt else 0
                    der = float(der_txt) if der_txt else 0
                    cara = float(cara_txt) if cara_txt else 0
                    disp = normalizar_disp(disp_txt)

                    datos.append((cant, (largo, izq, der, cara, disp)))
                else:
                    datos.append((cant, largo))

            except:
                pass

        return datos

    def cargar_lista_cortes(self, lista, angular=False):
        self.borrar_todo()
        primera = True

        for cant, pieza in lista:
            if angular:
                largo, izq, der, cara, disp = pieza
                valores = [
                    cant,
                    formato_numero(largo),
                    formato_numero(izq),
                    formato_numero(der),
                    formato_numero(cara),
                    normalizar_disp(disp)
                ]
            else:
                valores = [
                    cant,
                    formato_numero(pieza)
                ]

            if primera:
                for i, valor in enumerate(valores):
                    widget = self.entradas[0][i]
                    if isinstance(widget, ttk.Combobox):
                        widget.set(normalizar_disp(valor))
                    else:
                        widget.insert(0, str(valor))
                primera = False
            else:
                self.agregar_fila(valores)

    def pegar_desde_portapapeles(self, root, angular=False):
        try:
            texto = root.clipboard_get()
            lineas = texto.strip().splitlines()

            if not lineas:
                return

            for linea in lineas:
                partes = linea.strip().split()

                try:
                    if angular:
                        if len(partes) >= 6:
                            cant = int(partes[0])
                            largo = float(partes[1].replace(",", "."))
                            izq = float(partes[2].replace(",", "."))
                            der = float(partes[3].replace(",", "."))
                            cara = float(partes[4].replace(",", "."))
                            disp = normalizar_disp(partes[5])

                            if cant > 0 and largo > 0:
                                self.agregar_fila([
                                    cant,
                                    formato_numero(largo),
                                    formato_numero(izq),
                                    formato_numero(der),
                                    formato_numero(cara),
                                    disp
                                ])

                        elif len(partes) >= 5:
                            cant = int(partes[0])
                            largo = float(partes[1].replace(",", "."))
                            izq = float(partes[2].replace(",", "."))
                            der = float(partes[3].replace(",", "."))
                            cara = float(partes[4].replace(",", "."))

                            if cant > 0 and largo > 0:
                                self.agregar_fila([
                                    cant,
                                    formato_numero(largo),
                                    formato_numero(izq),
                                    formato_numero(der),
                                    formato_numero(cara),
                                    "//"
                                ])

                        elif len(partes) >= 2:
                            cant = int(partes[0])
                            largo = float(partes[1].replace(",", "."))

                            if cant > 0 and largo > 0:
                                self.agregar_fila([
                                    cant,
                                    formato_numero(largo),
                                    "0",
                                    "0",
                                    "0",
                                    "//"
                                ])

                    else:
                        if len(partes) >= 2:
                            cant = int(partes[0])
                            largo = float(partes[1].replace(",", "."))

                            if cant > 0 and largo > 0:
                                self.agregar_fila([cant, formato_numero(largo)])

                        elif len(partes) == 1:
                            largo = float(partes[0].replace(",", "."))

                            if largo > 0:
                                self.agregar_fila([1, formato_numero(largo)])

                except:
                    pass

            messagebox.showinfo("Pegado", "Datos agregados correctamente.")

        except:
            messagebox.showerror("Error", "No se pudo leer el portapapeles.")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizador de Corte")
        self.root.geometry("1050x700")

        self.modo_angulos = tk.BooleanVar(value=False)

        frame_config = ttk.LabelFrame(root, text="Configuración")
        frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_config, text="Largo de barra estándar (mm)").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.largo_barra_entry = ttk.Entry(frame_config, width=18)
        self.largo_barra_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=3)
        self.largo_barra_entry.insert(0, "6000")

        ttk.Label(frame_config, text="Tipo de material").grid(row=0, column=1, sticky="w", padx=5, pady=3)
        self.tipo_material_entry = ttk.Entry(frame_config, width=22)
        self.tipo_material_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        self.tipo_material_entry.insert(0, "Caño")

        ttk.Label(frame_config, text="Medida").grid(row=0, column=2, sticky="w", padx=5, pady=3)
        self.medida_entry = ttk.Entry(frame_config, width=28)
        self.medida_entry.grid(row=1, column=2, sticky="ew", padx=5, pady=3)
        self.medida_entry.insert(0, "80 x 80 x 1.6")

        ttk.Label(frame_config, text="Eficiencia mínima (%)").grid(row=0, column=3, sticky="w", padx=5, pady=3)
        self.eficiencia_entry = ttk.Entry(frame_config, width=12)
        self.eficiencia_entry.grid(row=1, column=3, sticky="ew", padx=5, pady=3)
        self.eficiencia_entry.insert(0, "65")

        ttk.Checkbutton(
            frame_config,
            text="Cortes en ángulos",
            variable=self.modo_angulos,
            command=self.cambiar_modo
        ).grid(row=1, column=4, sticky="w", padx=10, pady=3)

        frame_config.grid_columnconfigure(0, weight=1)
        frame_config.grid_columnconfigure(1, weight=1)
        frame_config.grid_columnconfigure(2, weight=2)

        self.frame_tabla = ttk.LabelFrame(root, text="Piezas necesarias")
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)

        self.tabla = None
        self.crear_tabla()

        frame_botones = ttk.Frame(root)
        frame_botones.pack(pady=5)

        ttk.Button(
            frame_botones,
            text="Borrar todo",
            command=self.borrar_todo
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Pegar desde Excel",
            command=self.pegar_desde_excel
        ).pack(side="left", padx=5)

        ttk.Button(
            frame_botones,
            text="Calcular lista de cortes",
            command=self.calcular_lista_de_cortes
        ).pack(side="left", padx=5)

        ttk.Button(
            root,
            text="Calcular plan de corte",
            command=self.calcular
        ).pack(pady=5)

        frame_resultado = ttk.LabelFrame(root, text="Salida para Excel / Entrada para calcular lista")
        frame_resultado.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_resultado = tk.Text(
            frame_resultado,
            wrap="none",
            height=10,
            font=("Courier", 10)
        )

        scroll_y = ttk.Scrollbar(
            frame_resultado,
            orient="vertical",
            command=self.text_resultado.yview
        )

        scroll_x = ttk.Scrollbar(
            frame_resultado,
            orient="horizontal",
            command=self.text_resultado.xview
        )

        self.text_resultado.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.text_resultado.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_resultado.grid_rowconfigure(0, weight=1)
        frame_resultado.grid_columnconfigure(0, weight=1)

    def crear_tabla(self):
        if self.tabla is not None:
            self.tabla.destruir()

        if self.modo_angulos.get():
            columnas = ["Cantidad", "Largo", "Izq", "Der", "Cara", "Disp"]
            anchos = [10, 12, 8, 8, 8, 8]
            angular = True
        else:
            columnas = ["Cantidad", "Largo"]
            anchos = [10, 15]
            angular = False

        self.tabla = TablaEditable(
            self.frame_tabla,
            columnas=columnas,
            ancho_cols=anchos,
            angular=angular
        )

    def cambiar_modo(self):
        self.crear_tabla()
        self.text_resultado.delete(1.0, tk.END)

    def borrar_todo(self):
        self.tabla.borrar_todo()
        self.text_resultado.delete(1.0, tk.END)

    def pegar_desde_excel(self):
        self.tabla.pegar_desde_portapapeles(
            self.root,
            angular=self.modo_angulos.get()
        )

    def calcular(self):
        try:
            bar_len = float(self.largo_barra_entry.get().replace(",", "."))

            if bar_len <= 0:
                raise ValueError

        except:
            messagebox.showerror("Error", "Ingrese un largo de barra válido (>0)")
            return

        try:
            eficiencia_minima = float(self.eficiencia_entry.get().replace(",", "."))

            if eficiencia_minima < 0 or eficiencia_minima > 100:
                raise ValueError

        except:
            messagebox.showerror("Error", "Ingrese una eficiencia mínima válida entre 0 y 100.")
            return

        tipo_material = self.tipo_material_entry.get().strip()
        medida = self.medida_entry.get().strip()

        if not tipo_material:
            messagebox.showerror("Error", "Ingrese el tipo de material.")
            return

        if not medida:
            messagebox.showerror("Error", "Ingrese la medida del material.")
            return

        angular = self.modo_angulos.get()
        datos = self.tabla.obtener_datos(angular=angular)

        if not datos:
            messagebox.showwarning(
                "Sin datos",
                "Agregue al menos una fila con cantidad y largo positivos."
            )
            return

        piezas = []

        for cant, pieza in datos:
            piezas.extend([pieza] * cant)

        resultado = generar_plan_excel(
            bar_len=bar_len,
            piezas=piezas,
            tipo_material=tipo_material,
            medida=medida,
            eficiencia_minima=eficiencia_minima,
            angular=angular
        )

        self.text_resultado.delete(1.0, tk.END)
        self.text_resultado.insert(tk.END, resultado)

    def calcular_lista_de_cortes(self):
        texto = self.text_resultado.get(1.0, tk.END).strip()

        if not texto:
            messagebox.showwarning(
                "Sin datos",
                "Pegue un plan de corte en el cuadro inferior."
            )
            return

        angular = self.modo_angulos.get()
        lista = interpretar_plan_de_corte(texto, angular=angular)

        if not lista:
            messagebox.showwarning(
                "Sin datos",
                "No se pudo interpretar ningún corte."
            )
            return

        self.tabla.cargar_lista_cortes(lista, angular=angular)

        messagebox.showinfo(
            "Lista calculada",
            "La lista de cortes fue cargada correctamente."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()