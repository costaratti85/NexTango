import os
import re
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from dataclasses import dataclass
from typing import List
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
import fitz
import pytesseract

try:
    import cv2
except ImportError:
    cv2 = None


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


@dataclass
class WordBox:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    page: int


@dataclass
class LineBox:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    words: List[WordBox]
    score: int = 0


class AnalizadorFactura:
    def __init__(self):
        self.stop_words = [
            "total", "subtotal", "cae", "iva", "son pesos",
            "observaciones", "importe neto", "fecha de vto"
        ]

    def abrir_documento(self, ruta):
        ext = os.path.splitext(ruta)[1].lower()

        if ext == ".pdf":
            return self.leer_pdf(ruta)
        else:
            return self.leer_imagen(ruta)

    def leer_pdf(self, ruta):
        doc = fitz.open(ruta)
        paginas = []

        for page_index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_path = os.path.join(tempfile.gettempdir(), f"pagina_{page_index}.png")
            pix.save(img_path)

            img = Image.open(img_path)

            palabras = []
            for w in page.get_text("words"):
                x0, y0, x1, y1, text = w[:5]
                escala = 2
                palabras.append(
                    WordBox(
                        x0 * escala,
                        y0 * escala,
                        x1 * escala,
                        y1 * escala,
                        str(text),
                        page_index
                    )
                )

            paginas.append((img, palabras))

        return paginas

    def leer_imagen(self, ruta):
        img = Image.open(ruta)
        img_ocr = self.preparar_imagen(img)

        data = pytesseract.image_to_data(
            img_ocr,
            lang="spa",
            output_type=pytesseract.Output.DICT,
            config="--psm 6"
        )

        palabras = []

        for i, text in enumerate(data["text"]):
            text = str(text).strip()
            if not text:
                continue

            try:
                conf = int(float(data["conf"][i]))
            except:
                conf = -1

            if conf < 25:
                continue

            x = data["left"][i]
            y = data["top"][i]
            w = data["width"][i]
            h = data["height"][i]

            palabras.append(WordBox(x, y, x + w, y + h, text, 1))

        return [(img, palabras)]

    def preparar_imagen(self, img):
        img = img.convert("L")
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Contrast(img).enhance(2.2)
        return img

    def agrupar_lineas(self, palabras):
        palabras = sorted(palabras, key=lambda w: (w.y0, w.x0))
        lineas = []

        actual = []

        for palabra in palabras:
            if not actual:
                actual = [palabra]
                continue

            y_prom = sum(w.y0 for w in actual) / len(actual)

            if abs(palabra.y0 - y_prom) <= 8:
                actual.append(palabra)
            else:
                lineas.append(self.crear_linea(actual))
                actual = [palabra]

        if actual:
            lineas.append(self.crear_linea(actual))

        return lineas

    def crear_linea(self, palabras):
        palabras = sorted(palabras, key=lambda w: w.x0)
        return LineBox(
            x0=min(w.x0 for w in palabras),
            y0=min(w.y0 for w in palabras),
            x1=max(w.x1 for w in palabras),
            y1=max(w.y1 for w in palabras),
            text=" ".join(w.text for w in palabras),
            words=palabras
        )

    def es_numero(self, t):
        t = t.replace("$", "").strip()
        return bool(re.match(r"^-?\d{1,3}(\.\d{3})*,\d{2,4}$", t)) or bool(re.match(r"^-?\d+([,.]\d+)?$", t))

    def cantidad_columnas_visuales(self, linea):
        if len(linea.words) < 3:
            return 0

        gaps = 0

        for a, b in zip(linea.words, linea.words[1:]):
            if b.x0 - a.x1 > 25:
                gaps += 1

        return gaps + 1

    def puntuar_linea(self, linea):
        texto = linea.text.lower()

        if any(p in texto for p in self.stop_words):
            return -5

        numeros = sum(1 for w in linea.words if self.es_numero(w.text))
        columnas = self.cantidad_columnas_visuales(linea)

        score = 0

        if columnas >= 3:
            score += 2
        if columnas >= 5:
            score += 2
        if numeros >= 2:
            score += 2
        if numeros >= 4:
            score += 2
        if len(linea.words) >= 5:
            score += 1

        linea.score = score
        return score

    def detectar_zonas_tabla(self, lineas):
        for linea in lineas:
            self.puntuar_linea(linea)

        candidatas = [l for l in lineas if l.score >= 4]

        zonas = []

        if not candidatas:
            return []

        grupo = [candidatas[0]]

        for linea in candidatas[1:]:
            if linea.y0 - grupo[-1].y1 < 70:
                grupo.append(linea)
            else:
                zonas.append(grupo)
                grupo = [linea]

        if grupo:
            zonas.append(grupo)

        cajas = []

        for zona in zonas:
            if len(zona) < 2:
                continue

            cajas.append((
                min(l.x0 for l in zona),
                min(l.y0 for l in zona),
                max(l.x1 for l in zona),
                max(l.y1 for l in zona),
                zona
            ))

        return cajas

    def analizar(self, ruta):
        paginas = self.abrir_documento(ruta)
        resultados = []

        for num, (img, palabras) in enumerate(paginas, start=1):
            lineas = self.agrupar_lineas(palabras)
            zonas = self.detectar_zonas_tabla(lineas)
            debug_path = self.dibujar_debug(img, lineas, zonas, num)
            resultados.append((num, debug_path, lineas, zonas))

        return resultados

    def dibujar_debug(self, img, lineas, zonas, page_num):
        debug = img.convert("RGB")
        draw = ImageDraw.Draw(debug)

        for linea in lineas:
            if linea.score >= 4:
                draw.rectangle([linea.x0, linea.y0, linea.x1, linea.y1], outline="blue", width=2)
                draw.text((linea.x0, max(0, linea.y0 - 12)), f"S{linea.score}", fill="blue")

        for x0, y0, x1, y1, zona in zonas:
            draw.rectangle([x0, y0, x1, y1], outline="red", width=4)

        out = os.path.join(tempfile.gettempdir(), f"debug_factura_pagina_{page_num}.png")
        debug.save(out)
        return out


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador geométrico de facturas")
        self.root.geometry("1100x600")
        self.analizador = AnalizadorFactura()
        self.resultados = []

        self.crear_ui()

    def crear_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(top, text="Abrir factura PDF/imagen", command=self.abrir, width=25).pack(side="left", padx=5)
        tk.Button(top, text="Ver imagen debug", command=self.ver_debug, width=20).pack(side="left", padx=5)

        self.lbl = tk.Label(self.root, text="Sin archivo", anchor="w")
        self.lbl.pack(fill="x", padx=15)

        cols = ("pagina", "score", "texto")
        self.tabla = ttk.Treeview(self.root, columns=cols, show="headings", height=24)

        self.tabla.heading("pagina", text="Página")
        self.tabla.heading("score", text="Score")
        self.tabla.heading("texto", text="Línea candidata")

        self.tabla.column("pagina", width=80)
        self.tabla.column("score", width=80)
        self.tabla.column("texto", width=900)

        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

        nota = tk.Label(
            self.root,
            text="Azul = líneas con forma de tabla. Rojo = zona tabular probable.",
            fg="blue"
        )
        nota.pack(pady=5)

    def abrir(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar factura",
            filetypes=[
                ("Facturas", "*.pdf *.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
                ("Todos", "*.*")
            ]
        )

        if not ruta:
            return

        self.lbl.config(text=ruta)

        try:
            self.resultados = self.analizador.analizar(ruta)
            self.cargar_tabla()
            messagebox.showinfo("Listo", "Análisis terminado. Revisá las líneas y la imagen debug.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cargar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        for pagina, debug, lineas, zonas in self.resultados:
            for linea in lineas:
                if linea.score >= 4:
                    self.tabla.insert("", "end", values=(pagina, linea.score, linea.text))

    def ver_debug(self):
        if not self.resultados:
            messagebox.showerror("Error", "Primero analizá una factura.")
            return

        pagina, debug_path, lineas, zonas = self.resultados[0]

        try:
            os.startfile(debug_path)
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()