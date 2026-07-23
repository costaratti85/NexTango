"""Sugerencia inteligente de código de artículo (Fase 2 OCR).

Dos cosas:
  - `suggest_next_item_code`: infiere familia+subcategoría del candidato top del
    matcher y calcula el próximo código libre con el paso correcto, según el
    esquema CC-SS-SS-SS-NNN (familia/subcat/secuencial). Cuerpo implementado por
    FORGE y verificado contra los 2189 códigos reales (ver
    `coordination/reports/FORGE_ANATOMIA_CODIGOS_ARTICULOS.md`).
  - `aplicar_sugerencias`: wiring PURO (de Atlas) que, por cada línea SIN match,
    pide un `codigo_sugerido` al suggester y lo agrega a la línea. La orquestación
    lo llama al armar el resultado.

El código sugerido es SOLO una pre-carga del campo editable (Regla 8): el humano
confirma/edita, y el Item se crea con el código que quede en el campo, no
necesariamente el sugerido.

NO reconstruye el árbol de Item Groups (decisión de Constantino): solo lee los
`item_code` existentes para calcular el próximo libre.
"""
from __future__ import annotations

import re

try:
    import frappe
except ImportError:  # pragma: no cover
    frappe = None

# Familias con numeración "plana" (paso 1). El resto usa paso 5.
_FLAT_FAMILIES = {"52", "54", "99"}
_DEFAULT_STEP = 5
_CODE_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})$")
_MAX_SEQ = 999  # el último bloque es de 3 dígitos


# ------------------------------------------------------------ INTERFAZ (Atlas)

def suggest_next_item_code(linea: dict, candidatos: list) -> str | None:
    """Sugiere el próximo item_code libre para una línea SIN match.

    Args:
        linea: la línea del OCR (descripcion, codigo_proveedor, ...). Reservado
            para señales futuras; hoy la inferencia se basa en `candidatos`.
        candidatos: top candidatos del matcher [{item_code, item_name, score, reason}].
            El candidato [0] (mejor score) sirve para inferir familia+subcategoría.

    Returns:
        item_code sugerido (str) siguiendo la convención CC-SS-SS-SS-NNN, o None
        si no se puede inferir (la UI deja el campo vacío para carga manual).
    """
    return _suggest_details(linea, candidatos).get("codigo_sugerido")


def aplicar_sugerencias(lineas: list, suggester) -> list:
    """PURO (de Atlas): por cada línea SIN match, setea `codigo_sugerido`.

    Graceful: cualquier fallo del suggester deja `codigo_sugerido=None` sin romper
    el flujo. Las líneas CON match no llevan sugerencia (ya tienen ítem propuesto).
    """
    for l in lineas:
        if l.get("match"):
            l.setdefault("codigo_sugerido", None)
            continue
        try:
            l["codigo_sugerido"] = suggester(l, l.get("candidatos", [])) or None
        except Exception:
            l["codigo_sugerido"] = None
    return lineas


# ------------------------------------------------------------ LÓGICA (Forge)

def _candidate_code(c) -> str | None:
    """Extrae el item_code de un candidato (dict del matcher, o string)."""
    if isinstance(c, str):
        return c
    if isinstance(c, dict):
        return c.get("item_code") or c.get("code")
    return None


def _infer_group(candidatos) -> dict:
    """Infiere familia + group_key (CC-SS-SS-SS) desde los candidatos rankeados.

    Si los candidatos no dan una familia clara, deja la subcategoría en 00
    (genérico) y marca `needs_subcat`. No inventa.
    """
    parsed = []
    for c in candidatos or []:
        code = _candidate_code(c)
        m = _CODE_RE.match(code or "")
        if m:
            parsed.append((code, m))

    if not parsed:
        return {"familia": None, "group_key": None, "confianza": "baja",
                "fuente": "sin_candidatos", "ref": None, "needs_subcat": False}

    top_code, top_m = parsed[0]
    top_group = "-".join(top_m.groups()[:4])
    top_fam = top_m.group(1)
    groups = ["-".join(m.groups()[:4]) for _, m in parsed]
    fams = [m.group(1) for _, m in parsed]

    if len(parsed) == 1 or groups.count(top_group) >= 2:
        return {
            "familia": top_fam, "group_key": top_group,
            "confianza": "alta" if groups.count(top_group) >= 2 else "media",
            "fuente": "consenso_candidatos" if groups.count(top_group) >= 2 else "candidato_top",
            "ref": top_code, "needs_subcat": False,
        }

    if fams.count(top_fam) >= max(2, len(parsed) // 2):
        return {"familia": top_fam, "group_key": f"{top_fam}-00-00-00",
                "confianza": "media", "fuente": "consenso_familia",
                "ref": top_code, "needs_subcat": True}

    return {"familia": top_fam, "group_key": f"{top_fam}-00-00-00",
            "confianza": "baja", "fuente": "candidatos_dispersos",
            "ref": top_code, "needs_subcat": True}


def _step_for_family(familia: str) -> int:
    return 1 if familia in _FLAT_FAMILIES else _DEFAULT_STEP


def _existing_seqs(group_key: str) -> set:
    """Números secuenciales ya usados en un grupo CC-SS-SS-SS (una query)."""
    if frappe is None:
        return set()
    prefix = group_key + "-"
    rows = frappe.get_all(
        "Item",
        filters={"item_code": ["like", prefix + "%"]},
        fields=["item_code"],
        limit_page_length=0,
    )
    seqs = set()
    for r in rows:
        code = r["item_code"]
        m = _CODE_RE.match(code or "")
        if m and code.startswith(prefix):
            seqs.add(int(m.group(5)))
    return seqs


def _next_free(group_key: str, step: int) -> tuple:
    """Próximo código libre en el grupo. Devuelve (codigo|None, grupo_vacio)."""
    seqs = _existing_seqs(group_key)
    vacio = not seqs
    n = step if vacio else max(seqs) + step
    while n in seqs:  # saltar colisiones (raro, porque n > max)
        n += step
    if n > _MAX_SEQ:
        return None, vacio
    return f"{group_key}-{n:03d}", vacio


def _suggest_details(linea, candidatos) -> dict:
    """Lógica completa: devuelve el código + metadata (confianza, needs_review, nota).

    `suggest_next_item_code` (interfaz de Atlas) devuelve solo el `codigo_sugerido`.
    Este helper preserva la metadata por si la UI la quiere más adelante; se expone
    en el endpoint de debug `suggest_code_details_api`.
    """
    info = _infer_group(candidatos)
    fam, gk = info["familia"], info["group_key"]

    if not fam or not gk:
        return {"codigo_sugerido": None, "familia": None, "grupo": None, "paso": None,
                "confianza": "baja", "fuente": info["fuente"], "candidato_ref": None,
                "editable": True, "needs_review": True,
                "nota": "Sin candidatos claros: el humano elige familia y código."}

    step = _step_for_family(fam)
    code, vacio = _next_free(gk, step)

    if code is None:
        nota = f"Grupo {gk} lleno (secuencial > {_MAX_SEQ}): el humano define el código."
        needs_review = True
    elif info["needs_subcat"]:
        nota = (f"Familia {fam} inferida de los candidatos, pero la subcategoría no es "
                f"clara: se usó el bucket genérico {gk}. Ajustá la subcategoría si corresponde.")
        needs_review = True
    elif vacio:
        nota = f"Primer artículo del grupo {gk} (estaba vacío). Sugerido con paso {step}."
        needs_review = info["confianza"] != "alta"
    else:
        nota = (f"Según artículos similares (ref {info['ref']}): próximo libre en {gk} "
                f"con paso {step}.")
        needs_review = info["confianza"] == "baja"

    return {"codigo_sugerido": code, "familia": fam, "grupo": gk, "paso": step,
            "confianza": info["confianza"], "fuente": info["fuente"],
            "candidato_ref": info["ref"], "editable": True,
            "needs_review": needs_review, "nota": nota}


if frappe is not None:
    @frappe.whitelist()
    def suggest_code_details_api(candidatos=None, linea=None) -> dict:
        """Debug: devuelve el código sugerido + metadata (confianza, needs_review, nota)."""
        if isinstance(candidatos, str) and candidatos.strip():
            candidatos = frappe.parse_json(candidatos)
        if isinstance(linea, str) and linea.strip():
            linea = frappe.parse_json(linea)
        return _suggest_details(linea, candidatos)
