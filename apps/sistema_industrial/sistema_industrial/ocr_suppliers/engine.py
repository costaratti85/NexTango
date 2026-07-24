"""
Motor OCR de facturas de proveedor — PORT server-side headless de la V9
(`ocr_claude.py` de escritorio) a la app Frappe.

Qué se portó (fiel a la V9):
  - Lectura de PDF (texto nativo PyMuPDF) e imagen (Tesseract) + preproceso OpenCV.
  - Detección de "texto ilegible" (fix Emapi) → cae a OCR por vocabulario de factura.
  - QR AFIP: decodificación (pyzbar/cv2) + parseo de la URL → CUIT/tipo/nº/fecha/importe.
  - Parsing espacial de líneas → ítems (código proveedor, descripción, cantidad, precio, IVA).
  - Aprendizaje de layout por proveedor (zona de ítems como % de página).
  - Matching multicriterio contra el catálogo (código proveedor / barras / descripción).

Qué cambió respecto de la V9:
  - SIN tkinter / sin openpyxl / sin GUI. Es una librería pura.
  - Los imports pesados (PIL, fitz, pytesseract, numpy, cv2, pyzbar) son PEREZOSOS:
    el módulo importa sin ellos y la lógica de texto/matching es testeable sin OCR.
  - El catálogo ya NO se levanta de un .xls → se carga desde ERPNext (ver `catalog.py`).
  - La persistencia del aprendizaje (layout/equivalencias/qr_cache) se inyecta vía un
    "store" (ver `stores.py`); si no hay DocTypes todavía, degrada a memoria (aprende
    de cero en cada corrida, igual funciona).

NO escribe nada en Tango/ERPNext. Devuelve datos para revisión humana (Regla 8).
"""
from __future__ import annotations

import os
import re
import json
import base64
import unicodedata
import tempfile
from dataclasses import dataclass
from difflib import SequenceMatcher

APP_VERSION = "V9.0-erpnext"
UMBRAL_CONFIANZA_DEFAULT = 82


# ─────────────────────────────────────────────────────────────────────────────
#  Cajas espaciales
# ─────────────────────────────────────────────────────────────────────────────
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
    words: list
    score: int = 0


# ─────────────────────────────────────────────────────────────────────────────
#  Normalización de texto (idéntica a V9)
# ─────────────────────────────────────────────────────────────────────────────
class Normalizador:
    def quitar_acentos(self, texto):
        texto = unicodedata.normalize("NFD", str(texto))
        return "".join(c for c in texto if unicodedata.category(c) != "Mn")

    def normalizar(self, texto):
        if texto is None:
            return ""
        texto = self.quitar_acentos(str(texto).upper().strip())
        reemplazos = {
            "P/ACERO": "ACERO", "P ACERO": "ACERO", "PACERO": "ACERO",
            "P/ ACERO": "ACERO", "P/INOX": "INOX", "P INOX": "INOX",
            "INOXIDABLE": "INOX", "C/": "CON ", "S/": "SIN ",
            "MM.": "MM", "M.M.": "MM",
        }
        for a, b in reemplazos.items():
            texto = texto.replace(a, b)
        for ch in ["/", "-", ",", ".", "(", ")", "[", "]", "_", ":"]:
            texto = texto.replace(ch, " ")
        return re.sub(r"\s+", " ", texto).strip()

    def tokens(self, texto):
        return [t for t in self.normalizar(texto).split() if len(t) >= 2]


# ─────────────────────────────────────────────────────────────────────────────
#  Catálogo + matching multicriterio (idéntico a V9, pero alimentado desde ERPNext)
# ─────────────────────────────────────────────────────────────────────────────
class Catalogo(Normalizador):
    def __init__(self):
        self.articulos = []

    def cargar_desde_articulos(self, articulos):
        """Recibe una lista de dicts con keys: codigo, descripcion, desc_adic,
        sinonimo, codigo_barras. Calcula los campos normalizados de matching.
        (En la V9 esto salía de un .xls; ahora sale de ERPNext — ver catalog.py.)"""
        self.articulos = []
        for a in articulos:
            art = {
                "codigo": str(a.get("codigo", "") or "").strip(),
                "descripcion": str(a.get("descripcion", "") or "").strip(),
                "desc_adic": str(a.get("desc_adic", "") or "").strip(),
                "sinonimo": str(a.get("sinonimo", "") or "").strip(),
                "codigo_barras": str(a.get("codigo_barras", "") or "").strip(),
            }
            if not art["codigo"] and not art["descripcion"]:
                continue
            art["_codigo_n"] = self.normalizar(art["codigo"])
            art["_descripcion_n"] = self.normalizar(art["descripcion"])
            art["_sinonimo_n"] = self.normalizar(art["sinonimo"])
            art["_codigo_barras_n"] = self.normalizar(art["codigo_barras"])
            art["_texto_completo_n"] = self.normalizar(
                f"{art['codigo']} {art['descripcion']} {art['desc_adic']} {art['sinonimo']} {art['codigo_barras']}"
            )
            self.articulos.append(art)
        return len(self.articulos)

    def similitud(self, a, b):
        a = self.normalizar(a)
        b = self.normalizar(b)
        if not a or not b:
            return 0
        return int(SequenceMatcher(None, a, b).ratio() * 100)

    def score_tokens(self, a, b):
        ta, tb = set(self.tokens(a)), set(self.tokens(b))
        if not ta or not tb:
            return 0
        return int((len(ta.intersection(tb)) / len(ta)) * 100)

    def buscar(self, codigo_proveedor="", codigo_barras="", descripcion="", umbral=UMBRAL_CONFIANZA_DEFAULT):
        """Mejor artículo. Retorna (art|None, metodo, score)."""
        return self._buscar_interno(codigo_proveedor, codigo_barras, descripcion, umbral)

    def buscar_candidatos(self, codigo_proveedor="", codigo_barras="", descripcion="", top=5):
        cp = self.normalizar(codigo_proveedor)
        cb = self.normalizar(codigo_barras)
        desc = self.normalizar(descripcion)
        resultados = []
        if cb:
            for art in self.articulos:
                if art["_codigo_barras_n"] and art["_codigo_barras_n"] == cb:
                    resultados.append((art, "Codigo de barras exacto", 100))
        if cp:
            for art in self.articulos:
                if art["_codigo_n"] == cp:
                    resultados.append((art, "Codigo Tango exacto", 100))
            for art in self.articulos:
                if art["_sinonimo_n"] and art["_sinonimo_n"] == cp:
                    resultados.append((art, "Sinonimo exacto", 99))
            for art in self.articulos:
                if cp in art["_descripcion_n"]:
                    resultados.append((art, "Codigo proveedor en descripcion", 96))
                elif cp in art["_texto_completo_n"]:
                    resultados.append((art, "Codigo proveedor contenido", 94))
        if desc:
            scored = []
            for art in self.articulos:
                score = max(self.similitud(desc, art["_descripcion_n"]),
                            self.score_tokens(desc, art["_descripcion_n"]))
                if score >= 50:
                    scored.append((art, "Similitud descripcion", score))
            scored.sort(key=lambda x: -x[2])
            resultados.extend(scored[:top * 2])
        vistos = {}
        for art, metodo, score in resultados:
            cod = art["codigo"]
            if cod not in vistos or score > vistos[cod][2]:
                vistos[cod] = (art, metodo, score)
        ordenados = sorted(vistos.values(), key=lambda x: -x[2])
        return ordenados[:top]

    def _buscar_interno(self, codigo_proveedor="", codigo_barras="", descripcion="", umbral=UMBRAL_CONFIANZA_DEFAULT):
        cp = self.normalizar(codigo_proveedor)
        cb = self.normalizar(codigo_barras)
        desc = self.normalizar(descripcion)
        if cb:
            for art in self.articulos:
                if art["_codigo_barras_n"] and art["_codigo_barras_n"] == cb:
                    return art, "Codigo de barras exacto", 100
        if cp:
            for art in self.articulos:
                if art["_codigo_n"] == cp:
                    return art, "Codigo Tango exacto", 100
            for art in self.articulos:
                if art["_sinonimo_n"] and art["_sinonimo_n"] == cp:
                    return art, "Sinonimo exacto", 100
            for art in self.articulos:
                if cp in art["_descripcion_n"]:
                    return art, "Codigo proveedor en descripcion", 96
            for art in self.articulos:
                if cp in art["_texto_completo_n"]:
                    return art, "Codigo proveedor contenido", 94
        mejor, mejor_score = None, 0
        if desc:
            for art in self.articulos:
                score = max(self.similitud(desc, art["_descripcion_n"]),
                            self.score_tokens(desc, art["_descripcion_n"]))
                if score > mejor_score:
                    mejor, mejor_score = art, score
            if mejor and mejor_score >= umbral:
                return mejor, "Similitud descripcion", mejor_score
        return None, "", 0


# ─────────────────────────────────────────────────────────────────────────────
#  Lector de facturas (PDF/imagen/QR/líneas/layout) — headless
# ─────────────────────────────────────────────────────────────────────────────
class FacturaTableReader:
    _PALABRAS_FACTURA = {
        "factura", "remito", "total", "subtotal", "cantidad", "precio", "importe",
        "fecha", "cuit", "iva", "neto", "codigo", "descripcion", "proveedor",
        "cliente", "srl", "s.a", "s.r.l", "responsable", "inscripto", "pesos",
        "unitario", "descuento", "original", "duplicado", "numero", "venta",
        "compra", "stock", "articulo", "producto", "unidad", "bulto", "caja",
        "the", "and", "invoice", "date", "item", "unit", "price",
        "emapi", "orange", "blue", "import", "export", "ferreteria", "metalurgica",
    }

    def __init__(self, base=None, logfn=None):
        # `base` = store de aprendizaje (layout/qr_cache). Ver stores.py.
        self._base = base
        self._logfn = logfn
        self.stop_words = [
            "total", "subtotal", "cae", "iva 21", "iva 10", "iva 27",
            "son pesos", "observaciones", "importe neto", "fecha de vto",
        ]

    def _log(self, msg):
        if self._logfn:
            try:
                self._logfn(str(msg))
            except Exception:
                pass

    # ---- imports perezosos de libs pesadas -------------------------------------
    @staticmethod
    def _pil():
        from PIL import Image, ImageOps, ImageEnhance  # noqa
        return Image, ImageOps, ImageEnhance

    @staticmethod
    def _np():
        import numpy as np
        return np

    @staticmethod
    def _fitz():
        import fitz
        return fitz

    @staticmethod
    def _tess():
        import pytesseract
        cmd = os.environ.get("TESSERACT_CMD")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
        return pytesseract

    @staticmethod
    def _cv2():
        try:
            import cv2
            return cv2
        except Exception:
            return None

    # ---- CUIT ------------------------------------------------------------------
    def is_cuit(self, text):
        clean = str(text).strip()
        if re.fullmatch(r"\d{2}-\d{8}-\d", clean):
            return True
        digits = re.sub(r"\D", "", clean)
        return len(digits) == 11 and digits[:2] in ["20", "23", "24", "27", "30", "33", "34"]

    def normalizar_cuit(self, cuit):
        return re.sub(r"\D", "", str(cuit or ""))

    # ---- lectura de documento --------------------------------------------------
    def abrir_documento(self, ruta):
        ext = os.path.splitext(ruta)[1].lower()
        return self.leer_pdf(ruta) if ext == ".pdf" else self.leer_imagen(ruta)

    def _texto_es_legible(self, palabras_raw):
        if not palabras_raw:
            return False
        muestra = [str(w[4]).strip().lower() for w in palabras_raw[:120] if str(w[4]).strip()]
        if not muestra:
            return False
        con_cid = sum(1 for t in muestra if "(cid:" in t)
        if con_cid / len(muestra) > 0.15:
            return False
        con_no_ascii = sum(
            1 for t in muestra
            if len(t) > 0 and sum(1 for c in t if ord(c) > 127) / len(t) > 0.5
        )
        if con_no_ascii / len(muestra) > 0.25:
            return False
        encontradas = set()
        for t in muestra:
            t_limpio = re.sub(r"[^a-z.]", "", t)
            if t_limpio in self._PALABRAS_FACTURA:
                encontradas.add(t_limpio)
        return len(encontradas) > 0

    def leer_pdf(self, ruta):
        fitz = self._fitz()
        Image, _, _ = self._pil()
        doc = fitz.open(ruta)
        paginas = []
        for page_index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_path = os.path.join(tempfile.gettempdir(), f"_ocrsup_pagina_{page_index}.png")
            pix.save(img_path)
            img = Image.open(img_path)
            palabras_raw = page.get_text("words")
            if self._texto_es_legible(palabras_raw):
                palabras = []
                for w in palabras_raw:
                    x0, y0, x1, y1, text = w[:5]
                    text = str(text).strip()
                    if text:
                        palabras.append(WordBox(x0 * 2, y0 * 2, x1 * 2, y1 * 2, text, page_index))
            else:
                self._log(f"pag {page_index}: texto ilegible -> OCR (fix Emapi)")
                palabras = self._ocr_sobre_imagen(img, page_index)
            paginas.append((img, palabras))
        return paginas

    def _ocr_sobre_imagen(self, img, page_num):
        pytesseract = self._tess()
        img_ocr = self.preparar_imagen(img)
        try:
            data = pytesseract.image_to_data(img_ocr, lang="spa",
                                              output_type=pytesseract.Output.DICT, config="--psm 6")
        except Exception:
            data = pytesseract.image_to_data(img_ocr, output_type=pytesseract.Output.DICT, config="--psm 6")
        return self._words_desde_tess(data, page_num)

    def leer_imagen(self, ruta):
        Image, _, _ = self._pil()
        pytesseract = self._tess()
        img = Image.open(ruta)
        img_ocr = self.preparar_imagen(img)
        try:
            data = pytesseract.image_to_data(img_ocr, lang="spa",
                                              output_type=pytesseract.Output.DICT, config="--psm 6")
        except Exception:
            data = pytesseract.image_to_data(img_ocr, output_type=pytesseract.Output.DICT, config="--psm 6")
        return [(img, self._words_desde_tess(data, 1))]

    def _words_desde_tess(self, data, page_num):
        palabras = []
        for i, text in enumerate(data["text"]):
            text = str(text).strip()
            if not text:
                continue
            try:
                conf = int(float(data["conf"][i]))
            except Exception:
                conf = -1
            if conf < 25:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            palabras.append(WordBox(x, y, x + w, y + h, text, page_num))
        return palabras

    def preparar_imagen(self, img):
        img = img.convert("RGB")
        if self._cv2() is not None:
            return self._preparar_imagen_cv2(img)
        return self._preparar_imagen_pillow(img)

    def _preparar_imagen_pillow(self, img):
        _, ImageOps, ImageEnhance = self._pil()
        img = img.convert("L")
        img = ImageOps.autocontrast(img)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        img = ImageEnhance.Contrast(img).enhance(2.2)
        return img

    def _preparar_imagen_cv2(self, img_pil):
        cv2 = self._cv2()
        np = self._np()
        Image, _, _ = self._pil()
        arr = np.array(img_pil)
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if w < 1000:
            factor = 1800 / w
            gray = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)
        gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        gray = self._deskew_cv2(gray)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, blockSize=31, C=10)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        return Image.fromarray(binary)

    def _deskew_cv2(self, gray):
        cv2 = self._cv2()
        np = self._np()
        try:
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)
            if lines is None or len(lines) < 5:
                return gray
            angles = []
            for line in lines[:40]:
                theta = line[0][1]
                angle = np.degrees(theta) - 90
                if -15 < angle < 15:
                    angles.append(angle)
            if not angles:
                return gray
            median_angle = float(np.median(angles))
            if abs(median_angle) < 0.3:
                return gray
            h, w = gray.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            return gray

    # ---- agrupación espacial ---------------------------------------------------
    def agrupar_lineas(self, palabras):
        palabras = sorted(palabras, key=lambda w: (w.y0, w.x0))
        lineas, actual = [], []
        for p in palabras:
            if not actual:
                actual = [p]
                continue
            y_prom = sum(w.y0 for w in actual) / len(actual)
            if abs(p.y0 - y_prom) <= 8:
                actual.append(p)
            else:
                lineas.append(self.crear_linea(actual))
                actual = [p]
        if actual:
            lineas.append(self.crear_linea(actual))
        return lineas

    def crear_linea(self, palabras):
        palabras = sorted(palabras, key=lambda w: w.x0)
        return LineBox(
            min(w.x0 for w in palabras), min(w.y0 for w in palabras),
            max(w.x1 for w in palabras), max(w.y1 for w in palabras),
            " ".join(w.text for w in palabras), palabras,
        )

    # ---- números es-AR ---------------------------------------------------------
    def parse_decimal(self, t):
        t = str(t).replace("$", "").replace(" ", "").strip()
        if not t:
            return None
        if re.match(r"^-?\d{1,3}(\.\d{3})*,\d+$", t):
            t = t.replace(".", "").replace(",", ".")
        elif re.match(r"^-?\d+,\d+$", t):
            t = t.replace(",", ".")
        try:
            return float(t)
        except Exception:
            return None

    def es_numero(self, t):
        t = str(t).replace("$", "").strip()
        if self.is_cuit(t):
            return False
        return bool(re.match(r"^-?\d{1,3}(\.\d{3})*,\d{2,4}$", t)) or bool(re.match(r"^-?\d+([,.]\d+)?$", t))

    def cantidad_columnas(self, linea):
        if len(linea.words) < 3:
            return 0
        gaps = 0
        for a, b in zip(linea.words, linea.words[1:]):
            if b.x0 - a.x1 > 25:
                gaps += 1
        return gaps + 1

    def puntuar_linea(self, linea):
        text = linea.text.lower()
        if any(self.is_cuit(w.text) for w in linea.words):
            linea.score = -10
            return linea.score
        if any(p in text for p in self.stop_words):
            linea.score = -5
            return linea.score
        nums = sum(1 for w in linea.words if self.es_numero(w.text))
        cols = self.cantidad_columnas(linea)
        score = 0
        if cols >= 3: score += 2
        if cols >= 5: score += 2
        if nums >= 2: score += 2
        if nums >= 4: score += 2
        if len(linea.words) >= 5: score += 1
        linea.score = score
        return score

    def detectar_zonas(self, lineas):
        for l in lineas:
            self.puntuar_linea(l)
        candidatas = [l for l in lineas if l.score >= 4]
        if not candidatas:
            return []
        grupos, grupo = [], [candidatas[0]]
        for l in candidatas[1:]:
            if l.y0 - grupo[-1].y1 < 75:
                grupo.append(l)
            else:
                grupos.append(grupo)
                grupo = [l]
        grupos.append(grupo)
        zonas = []
        for g in grupos:
            if len(g) < 2:
                continue
            zonas.append((min(l.x0 for l in g), min(l.y0 for l in g),
                          max(l.x1 for l in g), max(l.y1 for l in g), g))
        return zonas

    def detectar_items(self, lineas):
        zonas = self.detectar_zonas(lineas)
        items = []
        for x0, y0, x1, y1, grupo in zonas:
            for linea in grupo:
                if linea.score < 4 or any(self.is_cuit(w.text) for w in linea.words):
                    continue
                item = self.linea_a_item(linea)
                if item:
                    items.append(item)
        return items, zonas

    def linea_a_item(self, linea):
        codigo_proveedor = ""
        descripcion_parts = []
        numeros_detectados = []
        for w in linea.words:
            t = w.text.strip()
            if self.is_cuit(t):
                return None
            if self.es_numero(t):
                numeros_detectados.append(t)
                continue
            if not codigo_proveedor and re.match(r"^[A-Z0-9][A-Z0-9.\-/]{2,}$", t, re.IGNORECASE):
                codigo_proveedor = t[:15]
                continue
            if t.upper() in ["U", "UN", "KG", "M", "L", "%"]:
                continue
            if re.match(r"^-?\d+([,.]\d+)?%?$", t):
                continue
            descripcion_parts.append(t)

        vals = [(n, self.parse_decimal(n)) for n in numeros_detectados]
        vals = [(n, v) for n, v in vals if v is not None]

        iva = ""
        if len(vals) >= 4:
            posibles = [(n, v) for n, v in vals
                        if abs(v - 21.0) < 0.01 or abs(v - 10.5) < 0.01 or abs(v - 27.0) < 0.01 or abs(v - 0.0) < 0.01]
            if posibles:
                no_cero = [x for x in posibles if abs(x[1]) > 0.01]
                elegido = no_cero[0] if no_cero else posibles[0]
                iva = elegido[0]
                vals = [x for x in vals if x[0] != elegido[0]]

        cantidad = vals[0][0] if vals else ""
        precio = vals[-2][0] if len(vals) >= 2 else ""
        importe = vals[-1][0] if vals else ""
        descripcion = re.sub(r"\s+", " ", " ".join(descripcion_parts)).replace(" /", "").replace("/", "").strip()

        if not descripcion and not codigo_proveedor:
            return None

        advertencia = self.validar_calculo(cantidad, precio, importe)
        return {
            "usar": True, "existe_tango": "No", "accion": "Alta artículo", "codigo_tango": "",
            "descripcion": descripcion[:50], "desc_adic": "", "codigo_proveedor": codigo_proveedor[:15],
            "sinonimo": codigo_proveedor[:15], "codigo_barras": "",
            "cantidad": cantidad, "precio": precio, "importe": importe,
            "iva": iva, "advertencia": advertencia, "tipo": "Simple", "escala": "No usa",
            "linea_detectada": linea.text, "score": linea.score, "coincidencia": "", "match_score": 0,
            "_y0": linea.y0,
        }

    def validar_calculo(self, cantidad, precio, importe):
        c, p, i = self.parse_decimal(cantidad), self.parse_decimal(precio), self.parse_decimal(importe)
        if c is None or p is None or i is None:
            return ""
        tolerancia = max(1.0, abs(i) * 0.01)
        if abs((c * p) - i) > tolerancia:
            return "Revisar cantidad/precio/importe"
        return "OK"

    # ---- texto de encabezado ---------------------------------------------------
    def extraer_texto_documento(self, ruta):
        ext = os.path.splitext(ruta)[1].lower()
        Image, _, _ = self._pil()
        pytesseract = self._tess()
        if ext == ".pdf":
            try:
                fitz = self._fitz()
                doc = fitz.open(ruta)
                palabras_raw = doc[0].get_text("words") if len(doc) > 0 else []
                if self._texto_es_legible(palabras_raw):
                    return "\n".join(page.get_text("text") for page in doc)
                textos = []
                for page in doc:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_path = os.path.join(tempfile.gettempdir(), "_ocrsup_texto_tmp.png")
                    pix.save(img_path)
                    img = self.preparar_imagen(Image.open(img_path))
                    try:
                        textos.append(pytesseract.image_to_string(img, lang="spa"))
                    except Exception:
                        textos.append(pytesseract.image_to_string(img))
                return "\n".join(textos)
            except Exception as e:
                self._log(f"extraer_texto_documento ERROR: {e}")
                return ""
        try:
            img = self.preparar_imagen(Image.open(ruta))
            try:
                return pytesseract.image_to_string(img, lang="spa")
            except Exception:
                return pytesseract.image_to_string(img)
        except Exception:
            return ""

    def detectar_proveedor(self, texto):
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]
        for l in lineas[:20]:
            may = l.upper()
            if "S.R.L" in may or "SRL" in may or "S.A" in may or " SA" in may:
                return l
        for l in lineas[:10]:
            if len(l) > 4 and not re.search(r"\d{2}/\d{2}/\d{2,4}", l):
                return l
        return ""

    def detectar_cuit_proveedor(self, texto):
        for patron in [
            r"CUIT\s*[:\-]?\s*(\d{2}[-\s]?\d{8}[-\s]?\d)",
            r"C\.?U\.?I\.?T\.?\s*[:\-]?\s*(\d{2}[-\s]?\d{8}[-\s]?\d)",
        ]:
            for m in re.findall(patron, texto, re.IGNORECASE):
                cuit = self.normalizar_cuit(m)
                if len(cuit) == 11 and cuit[:2] in ["20", "23", "24", "27", "30", "33", "34"]:
                    return cuit
        m = re.search(r"\b((?:20|23|24|27|30|33|34)\d{9})\b", texto)
        return m.group(1) if m else ""

    def detectar_tipo_comprobante(self, texto):
        may = texto.upper()
        if "FACTURA" in may:
            if re.search(r"FACTURA\s*A", may) or re.search(r"\bCOD\.?\s*0?1\b", may): return "FACTURA A"
            if re.search(r"FACTURA\s*B", may) or re.search(r"\bCOD\.?\s*0?6\b", may): return "FACTURA B"
            if re.search(r"FACTURA\s*C", may) or re.search(r"\bCOD\.?\s*0?11\b", may): return "FACTURA C"
            return "FACTURA"
        if "REMITO" in may:
            return "REMITO"
        return ""

    def detectar_numero_comprobante(self, texto):
        patrones = [
            r"Punto\s+de\s+Venta\s*[:\-]?\s*(\d{4,5}).{0,80}?Comp\.?\s*Nro\.?\s*[:\-]?\s*(\d{6,8})",
            r"Pto\.?\s*Vta\.?\s*[:\-]?\s*(\d{4,5}).{0,80}?Nro\.?\s*[:\-]?\s*(\d{6,8})",
            r"(?:FACTURA|REMITO)\s*(?:N[°º]?)?\s*[:\-]?\s*(\d{4,5})[-\s]?(\d{6,8})",
            r"\b(\d{4,5})[-\s](\d{6,8})\b",
        ]
        for p in patrones:
            m = re.search(p, texto, re.IGNORECASE | re.DOTALL)
            if m:
                pv, nro = m.group(1).zfill(4), m.group(2).zfill(8)
                return pv, nro, f"{pv}-{nro}"
        return "", "", ""

    def detectar_fecha(self, texto):
        m = re.search(r"(?:Fecha\s+de\s+Emisi[oó]n|Fecha)\s*[:\-]?\s*(\d{1,2}/\d{1,2}/\d{2,4})", texto, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", texto)
        return m.group(1) if m else ""

    def detectar_total(self, texto):
        posibles = re.findall(r"(?:TOTAL|Total)\s*[:$ ]+\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})", texto)
        return posibles[-1] if posibles else ""

    def clave_factura(self, datos):
        cuit = self.normalizar_cuit(datos.get("cuit_proveedor", ""))
        proveedor = str(datos.get("proveedor", "")).strip().upper()
        tipo = str(datos.get("tipo", "")).strip().upper()
        punto = str(datos.get("punto_venta", "")).strip().zfill(4) if datos.get("punto_venta") else ""
        numero = str(datos.get("numero", "")).strip().zfill(8) if datos.get("numero") else ""
        if cuit and punto and numero:
            return f"CUIT:{cuit}|TIPO:{tipo}|PV:{punto}|N:{numero}"
        if proveedor and punto and numero:
            return f"PROV:{re.sub(r'\\s+', ' ', proveedor)}|TIPO:{tipo}|PV:{punto}|N:{numero}"
        return f"ARCHIVO:{datos.get('archivo', '')}"

    # ---- QR AFIP ---------------------------------------------------------------
    def leer_qr_afip(self, ruta):
        try:
            Image, _, _ = self._pil()
            ext = os.path.splitext(ruta)[1].lower()
            if ext == ".pdf":
                fitz = self._fitz()
                doc = fitz.open(ruta)
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                img_path = os.path.join(tempfile.gettempdir(), "_ocrsup_qr.png")
                pix.save(img_path)
                img = Image.open(img_path).convert("RGB")
            else:
                img = Image.open(ruta).convert("RGB")
            return self._decodificar_qr(img)
        except Exception as e:
            self._log(f"leer_qr_afip ERROR: {e}")
            return {}

    def _decodificar_qr(self, img):
        url = None
        np = self._np()
        try:
            from pyzbar import pyzbar
            codigos = pyzbar.decode(np.array(img))
            for c in codigos:
                if c.type == "QRCODE":
                    url = c.data.decode("utf-8", errors="ignore")
                    break
            if not url:
                Image, _, _ = self._pil()
                img_big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
                for c in pyzbar.decode(np.array(img_big)):
                    if c.type == "QRCODE":
                        url = c.data.decode("utf-8", errors="ignore")
                        break
        except ImportError:
            pass
        except Exception as e:
            self._log(f"_decodificar_qr pyzbar error: {e}")

        if not url and self._cv2() is not None:
            try:
                cv2 = self._cv2()
                img_gray = np.array(img.convert("L"))
                val, _, _ = cv2.QRCodeDetector().detectAndDecode(img_gray)
                if val:
                    url = val
            except Exception as e:
                self._log(f"_decodificar_qr cv2 error: {e}")

        if not url:
            return {}
        return self._parsear_url_afip(url)

    def _parsear_url_afip(self, url):
        """Parsea la URL del QR de AFIP: https://www.afip.gob.ar/fe/qr/?p=BASE64JSON"""
        try:
            if "?p=" in url:
                b64 = url.split("?p=")[1].split("&")[0]
            elif url.strip().startswith("{"):
                return self._normalizar_datos_qr(json.loads(url))
            else:
                return {}
            b64 = b64 + "=" * (-len(b64) % 4)
            datos_json = json.loads(base64.b64decode(b64).decode("utf-8"))
            return self._normalizar_datos_qr(datos_json)
        except Exception as e:
            self._log(f"_parsear_url_afip error: {e}")
            return {}

    def _normalizar_datos_qr(self, d):
        TIPOS_COMPROBANTE = {
            1: "FACTURA A", 2: "NOTA DEBITO A", 3: "NOTA CREDITO A",
            6: "FACTURA B", 7: "NOTA DEBITO B", 8: "NOTA CREDITO B",
            11: "FACTURA C", 12: "NOTA DEBITO C", 13: "NOTA CREDITO C",
            51: "FACTURA M", 201: "FACTURA DE EXPORTACION",
        }
        try:
            cuit = str(d.get("cuit", "")).replace("-", "").strip()
            pv = str(d.get("ptoVta", "")).zfill(4)
            nro = str(d.get("nroCmp", "")).zfill(8)
            tipo_cod = int(d.get("tipoCmp", 0))
            tipo = TIPOS_COMPROBANTE.get(tipo_cod, f"COMPROBANTE {tipo_cod}")
            return {
                "cuit": cuit, "punto_venta": pv, "numero": nro,
                "numero_completo": f"{pv}-{nro}", "tipo": tipo,
                "fecha": str(d.get("fecha", "")), "importe_total": str(d.get("importe", "")),
                "fuente": "QR_AFIP",
            }
        except Exception as e:
            self._log(f"_normalizar_datos_qr error: {e}")
            return {}

    # ---- encabezado + análisis completo ---------------------------------------
    def detectar_datos_factura(self, ruta):
        archivo = os.path.basename(ruta)
        datos_qr = self.leer_qr_afip(ruta)
        cuit_qr = datos_qr.get("cuit", "")

        layout = None
        if cuit_qr and self._base is not None:
            layout = self._base.obtener_layout(cuit_qr)

        texto = self.extraer_texto_documento(ruta)
        proveedor = self.detectar_proveedor(texto)
        cuit = cuit_qr or self.detectar_cuit_proveedor(texto)
        tipo = datos_qr.get("tipo") or self.detectar_tipo_comprobante(texto)
        pv = datos_qr.get("punto_venta") or ""
        nro = datos_qr.get("numero") or ""
        completo = datos_qr.get("numero_completo") or ""
        fecha = datos_qr.get("fecha") or self.detectar_fecha(texto)
        total = datos_qr.get("importe_total") or self.detectar_total(texto)

        if not pv or not nro:
            pv2, nro2, completo2 = self.detectar_numero_comprobante(texto)
            pv = pv or pv2
            nro = nro or nro2
            completo = completo or completo2

        if cuit and (not proveedor) and self._base is not None:
            cache = self._base.obtener_qr_cache(cuit)
            if cache:
                proveedor = cache["proveedor"]

        partes = []
        if proveedor: partes.append(proveedor[:30])
        if completo: partes.append(completo)
        if fecha: partes.append(fecha)
        etiqueta = " | ".join(partes) if partes else archivo

        datos = {
            "archivo": archivo, "ruta": ruta,
            "proveedor": proveedor, "cuit_proveedor": cuit,
            "tipo": tipo, "punto_venta": pv, "numero": nro,
            "numero_completo": completo, "fecha": fecha,
            "total": total, "etiqueta": etiqueta,
            "_layout": layout, "_datos_qr": datos_qr,
            "_texto": texto,
        }
        datos["clave"] = self.clave_factura(datos)
        return datos

    # ---- IVA por renglón (alícuota) --------------------------------------------
    # Alícuotas de IVA argentinas que reconocemos.
    _IVA_RATES = (21.0, 10.5, 27.0)

    def _match_rate(self, v):
        """Devuelve la alícuota (21.0/10.5/27.0) si v matchea una, si no None."""
        if v is None:
            return None
        for r in self._IVA_RATES:
            if abs(v - r) < 0.05:
                return r
        return None

    def _rates_en_texto(self, texto):
        """Alícuotas mencionadas en el texto del comprobante (contexto IVA/%/gravado)."""
        up = (texto or "").upper()
        rates = set()
        if re.search(r"10[.,]5\s*%", up) or re.search(r"(IVA|AL[IÍ]C|GRAVAD)[^\n]{0,25}10[.,]5", up):
            rates.add(10.5)
        if re.search(r"\b21([.,]0+)?\s*%", up) or re.search(r"(IVA|AL[IÍ]C|GRAVAD)[^\n]{0,25}\b21\b", up):
            rates.add(21.0)
        if re.search(r"\b27([.,]0+)?\s*%", up) or re.search(r"(IVA|AL[IÍ]C|GRAVAD)[^\n]{0,25}\b27\b", up):
            rates.add(27.0)
        return rates

    def _marcadores_alicuota(self, lineas):
        """Líneas que parecen encabezado/subtotal de una alícuota (formato agrupado).
        Devuelve [(y0, rate)] ordenado por y0."""
        out = []
        for l in lineas:
            t = l.text.upper()
            if not (("IVA" in t) or ("ALIC" in t) or ("GRAVAD" in t) or ("%" in t)):
                continue
            for r, pat in ((10.5, r"10[.,]5"), (27.0, r"\b27\b|27[.,]0"), (21.0, r"\b21\b|21[.,]0")):
                if re.search(pat, t):
                    out.append((l.y0, r))
                    break
        return sorted(out, key=lambda x: x[0])

    def _rate_por_bloque(self, y, markers):
        """Alícuota del bloque en el que cae el renglón (asume encabezado arriba)."""
        if y is None or not markers:
            return None
        arriba = [(my, r) for my, r in markers if my <= y]
        if arriba:
            return arriba[-1][1]
        return markers[0][1]

    def _asignar_iva(self, items, lineas, texto):
        """Asigna `iva_pct` + `needs_review` a cada item.
        (a) columna por línea → confiable. (b) alícuota única en el doc → confiable.
        (c) multi-alícuota agrupada → best-guess por bloque + needs_review.
        (d) indeterminado → default 21 + needs_review (Constantino: default 21)."""
        rates_doc = self._rates_en_texto(texto)
        markers = self._marcadores_alicuota(lineas)
        rates_marker = {r for _, r in markers}
        solo = (rates_doc | rates_marker) & set(self._IVA_RATES)
        unica = next(iter(solo)) if len(solo) == 1 else None
        for item in items:
            y = item.pop("_y0", None)
            per = self._match_rate(self.parse_decimal(item.get("iva", ""))) if item.get("iva") else None
            if per in self._IVA_RATES:
                item["iva_pct"], item["iva_fuente"], item["needs_review"] = per, "linea", False
            elif unica is not None:
                item["iva_pct"], item["iva_fuente"], item["needs_review"] = unica, "alicuota_unica", False
            elif len(rates_marker) >= 2:
                item["iva_pct"] = self._rate_por_bloque(y, markers)
                item["iva_fuente"], item["needs_review"] = "agrupado", True
            else:
                # Default 21% (alícuota general) pero marcado para que el humano confirme.
                item["iva_pct"], item["iva_fuente"], item["needs_review"] = 21.0, "default_21", True

    def analizar(self, ruta, aprender=True):
        """Analiza una factura y extrae los renglones. Devuelve (items, zonas_debug, datos).
        `aprender` controla si persiste el layout aprendido en el store."""
        datos = self.detectar_datos_factura(ruta)
        layout = datos.get("_layout")
        cuit = datos.get("cuit_proveedor", "")
        fuente_qr = bool(datos.get("_datos_qr"))

        paginas = self.leer_pdf(ruta) if ruta.lower().endswith(".pdf") else self.leer_imagen(ruta)
        debug = []
        items = []

        for img, palabras in paginas:
            page_w, page_h = img.size
            # Líneas de TODA la página: necesarias para detectar marcadores de alícuota
            # (subtotales/encabezados por IVA) aunque estemos en modo dirigido (zona).
            lineas_full = self.agrupar_lineas(palabras)
            if layout and layout.get("veces_procesado", 0) >= 2:
                palabras_zona = self._filtrar_zona(
                    palabras, page_w, page_h,
                    layout["y0_pct"], layout["y1_pct"], layout["x0_pct"], layout["x1_pct"])
                items_pag, zonas = self.detectar_items(self.agrupar_lineas(palabras_zona))
            else:
                items_pag, zonas = self.detectar_items(lineas_full)
                if aprender and zonas and cuit and self._base is not None:
                    self._aprender_layout(cuit, datos.get("proveedor", ""),
                                          page_w, page_h, zonas,
                                          not layout or not layout.get("necesita_ocr"))

            # IVA por renglón (formato columna-por-línea o agrupado-por-alícuota)
            self._asignar_iva(items_pag, lineas_full, datos.get("_texto", ""))

            for item in items_pag:
                item.update({
                    "proveedor": datos["proveedor"], "cuit_proveedor": cuit,
                    "tipo": datos["tipo"], "punto_venta": datos["punto_venta"],
                    "numero": datos["numero"], "numero_completo": datos["numero_completo"],
                    "fecha": datos["fecha"], "ruta": ruta, "etiqueta": datos["etiqueta"],
                })
                items.append(item)

            debug.append({
                "page_w": page_w, "page_h": page_h,
                "zonas": [{"x0": z[0], "y0": z[1], "x1": z[2], "y1": z[3], "lineas": len(z[4])} for z in zonas],
            })

        if aprender and fuente_qr and cuit and datos.get("proveedor") and self._base is not None:
            self._base.guardar_qr_cache(cuit, datos["proveedor"], datos["_datos_qr"])

        return items, debug, datos

    def _filtrar_zona(self, palabras, page_w, page_h, y0_pct, y1_pct, x0_pct, x1_pct):
        y0 = page_h * y0_pct
        y1 = page_h * y1_pct
        x0 = page_w * x0_pct
        x1 = page_w * x1_pct
        margen_y = page_h * 0.03
        margen_x = page_w * 0.02
        return [
            p for p in palabras
            if (y0 - margen_y) <= p.y0 <= (y1 + margen_y) and (x0 - margen_x) <= p.x0 <= (x1 + margen_x)
        ]

    def _aprender_layout(self, cuit, proveedor, page_w, page_h, zonas, es_pdf_nativo):
        if not zonas:
            return
        zona_principal = max(zonas, key=lambda z: len(z[4]))
        x0, y0, x1, y1, _ = zona_principal
        y0_pct = max(0.0, (y0 / page_h) - 0.02)
        y1_pct = min(1.0, (y1 / page_h) + 0.04)
        x0_pct = max(0.0, (x0 / page_w) - 0.01)
        x1_pct = min(1.0, (x1 / page_w) + 0.01)
        self._base.guardar_layout(
            cuit, proveedor, page_w, page_h,
            y0_pct, y1_pct, x0_pct, x1_pct,
            int(es_pdf_nativo), int(not es_pdf_nativo))
