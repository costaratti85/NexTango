"""Matching de líneas de factura contra el catálogo de Items de ERPNext.

Puro (sin frappe): recibe un catálogo ya cargado + una línea OCR y devuelve
candidatos ranqueados. La carga del catálogo desde ERPNext vive en catalog.py.

Criterio portado del standalone (facturas_multiples_a_tango_v6.buscar): cascada
de exactos (barras, código, sinónimo, código-en-descripción) y luego fuzzy por
descripción (SequenceMatcher + solape de tokens). A diferencia del standalone,
que devolvía UN match, acá devolvemos los top-N candidatos con score y razón,
para que la UI (Vega) muestre alternativas y el humano confirme.
"""
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
import unicodedata


# ---------------------------------------------------------------- normalización

def quitar_acentos(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """minúsculas, sin acentos, alfanumérico + espacios colapsados."""
    t = quitar_acentos(texto).lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalizar_codigo(codigo: str) -> str:
    """código sin separadores ni espacios (para match exacto)."""
    return re.sub(r"[^a-z0-9]", "", quitar_acentos(str(codigo or "")).lower())


def tokens(texto: str) -> list:
    return [t for t in normalizar(texto).split(" ") if len(t) >= 2]


# ------------------------------------------------------------------ modelo

@dataclass
class CatalogItem:
    item_code: str
    item_name: str
    barcodes: tuple = ()          # códigos de barra (Item Barcode)
    supplier_codes: tuple = ()    # códigos de proveedor / part no
    _code_n: str = ""
    _name_n: str = ""
    _full_n: str = ""
    _barcodes_n: frozenset = frozenset()
    _supplier_codes_n: frozenset = frozenset()

    def __post_init__(self):
        self._code_n = normalizar_codigo(self.item_code)
        self._name_n = normalizar(self.item_name)
        self._barcodes_n = frozenset(normalizar_codigo(b) for b in self.barcodes if b)
        self._supplier_codes_n = frozenset(
            normalizar_codigo(c) for c in self.supplier_codes if c)
        self._full_n = normalizar(f"{self.item_code} {self.item_name} "
                                  f"{' '.join(self.supplier_codes)}")


@dataclass
class Candidate:
    item_code: str
    item_name: str
    score: int
    reason: str

    def as_dict(self):
        return {"item_code": self.item_code, "item_name": self.item_name,
                "score": self.score, "reason": self.reason}


# umbral por debajo del cual un fuzzy no se ofrece como candidato
FUZZY_MIN = 55
# umbral por debajo del cual NO hay match sugerido (el humano elige a mano)
AUTO_MIN = 82


def build_catalog(rows) -> list:
    """rows: iterable de dicts {item_code, item_name, barcodes?, supplier_codes?}."""
    cat = []
    for r in rows:
        cat.append(CatalogItem(
            item_code=r.get("item_code", ""),
            item_name=r.get("item_name", ""),
            barcodes=tuple(r.get("barcodes") or ()),
            supplier_codes=tuple(r.get("supplier_codes") or ()),
        ))
    return cat


def _fuzzy(a_n: str, b_n: str) -> int:
    if not a_n or not b_n:
        return 0
    ratio = int(SequenceMatcher(None, a_n, b_n).ratio() * 100)
    ta, tb = set(a_n.split()), set(b_n.split())
    tok = int((len(ta & tb) / len(ta)) * 100) if ta else 0
    return max(ratio, tok)


def match_line(line: dict, catalog: list, top_n: int = 5) -> dict:
    """Devuelve {match, confianza, candidatos} para UNA línea OCR.

    line: {codigo_proveedor?, codigo_barras?, descripcion?}
    - match: el mejor candidato (dict) o None si nada supera el piso.
    - confianza: score del mejor (0..100).
    - candidatos: top_n candidatos ordenados por score desc.
    """
    cod = normalizar_codigo(line.get("codigo_proveedor", ""))
    barras = normalizar_codigo(line.get("codigo_barras", ""))
    desc_n = normalizar(line.get("descripcion", ""))

    scored = {}  # item_code -> Candidate (mejor razón/score por item)

    def offer(item, score, reason):
        prev = scored.get(item.item_code)
        if prev is None or score > prev.score:
            scored[item.item_code] = Candidate(item.item_code, item.item_name, score, reason)

    for item in catalog:
        # exactos
        if barras and barras in item._barcodes_n:
            offer(item, 100, "Código de barras exacto")
            continue
        if cod:
            if cod == item._code_n:
                offer(item, 100, "Código Tango exacto"); continue
            if cod in item._supplier_codes_n:
                offer(item, 100, "Código de proveedor exacto"); continue
            if cod and cod in item._full_n.replace(" ", ""):
                offer(item, 94, "Código contenido"); continue
        # fuzzy por descripción — capeado a 99 para que NUNCA le gane a un
        # match exacto (barras/código = 100): un identificador exacto es más
        # certero que la similitud de texto.
        if desc_n:
            s = _fuzzy(desc_n, item._name_n)
            if s >= FUZZY_MIN:
                offer(item, min(99, s), "Similitud descripción")

    candidatos = sorted(scored.values(), key=lambda c: c.score, reverse=True)[:top_n]
    best = candidatos[0] if candidatos else None
    # solo se considera "match sugerido" si supera AUTO_MIN; si no, hay
    # candidatos pero sin sugerencia (el humano elige).
    match = best if (best and best.score >= AUTO_MIN) else None
    return {
        "match": match.as_dict() if match else None,
        "confianza": best.score if best else 0,
        "candidatos": [c.as_dict() for c in candidatos],
    }


def match_lines(lines: list, catalog: list, top_n: int = 5) -> list:
    """Aplica match_line a cada línea, preservando el resto de sus campos."""
    out = []
    for i, line in enumerate(lines):
        m = match_line(line, catalog, top_n=top_n)
        out.append({**line, "idx": line.get("idx", i), **m})
    return out
