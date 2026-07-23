"""Sugerencia inteligente del próximo `item_code` para artículos nuevos del OCR.

Basado en la anatomía de los códigos (ver `coordination/reports/FORGE_ANATOMIA_CODIGOS_ARTICULOS.md`):
`CC-SS-SS-SS-NNN` = familia · subcategorías · secuencial. El secuencial usa
**paso 5** en las familias de taller y **paso 1** en las planas (52, 54, 99).

Estrategia (Regla 8: el sistema SUGIERE, el humano confirma/edita):
1. INFERIR familia+subcategoría desde los **candidatos** que ya rankeó el matcher
   para esa línea (los artículos parecidos). El grupo del candidato top es la mejor
   señal. Si los candidatos no coinciden en familia, se baja la confianza y se deja
   la subcategoría en `00` (genérico) para que el humano la ajuste — **no se inventa**.
2. Buscar el MÁXIMO secuencial usado en ese grupo y sumar el paso (con ceros).
3. Manejar grupo vacío (primer artículo de la subcategoría) y colisiones (si el
   próximo ya existe, saltar al siguiente libre).

NO reconstruye el árbol de Item Groups (decisión de Constantino): solo lee los
`item_code` existentes para calcular el próximo libre.
"""
from __future__ import annotations

import re

import frappe

# Familias con numeración "plana" (paso 1). El resto usa paso 5.
_FLAT_FAMILIES = {"52", "54", "99"}
_DEFAULT_STEP = 5

_CODE_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})$")
_MAX_SEQ = 999  # el último bloque es de 3 dígitos


def _step_for_family(familia: str) -> int:
    return 1 if familia in _FLAT_FAMILIES else _DEFAULT_STEP


def _candidate_code(c) -> str | None:
    """Extrae el item_code de un candidato (dict del matcher/catálogo, o string)."""
    if isinstance(c, str):
        return c
    if isinstance(c, dict):
        return c.get("item_code") or c.get("code")
    return None


def _infer_group(candidatos) -> dict:
    """Infiere familia + group_key (CC-SS-SS-SS) desde los candidatos rankeados.

    Devuelve confianza y fuente. Si los candidatos no dan una familia clara, deja
    la subcategoría en 00 (genérico) y marca `needs_subcat`.
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

    # Consenso de grupo entre los candidatos (el top + al menos otro que coincida)
    if len(parsed) == 1 or groups.count(top_group) >= 2:
        return {
            "familia": top_fam, "group_key": top_group,
            "confianza": "alta" if groups.count(top_group) >= 2 else "media",
            "fuente": "consenso_candidatos" if groups.count(top_group) >= 2 else "candidato_top",
            "ref": top_code, "needs_subcat": False,
        }

    # Familia clara aunque la subcategoría no: usar el bucket genérico CC-00-00-00
    if fams.count(top_fam) >= max(2, len(parsed) // 2):
        return {"familia": top_fam, "group_key": f"{top_fam}-00-00-00",
                "confianza": "media", "fuente": "consenso_familia",
                "ref": top_code, "needs_subcat": True}

    # Candidatos dispersos: familia del top, subcategoría a definir
    return {"familia": top_fam, "group_key": f"{top_fam}-00-00-00",
            "confianza": "baja", "fuente": "candidatos_dispersos",
            "ref": top_code, "needs_subcat": True}


def _existing_seqs(group_key: str) -> set[int]:
    """Números secuenciales ya usados en un grupo CC-SS-SS-SS (una query)."""
    prefix = group_key + "-"
    rows = frappe.get_all(
        "Item",
        filters={"item_code": ["like", prefix + "%"]},
        fields=["item_code"],
        limit_page_length=0,
    )
    seqs: set[int] = set()
    for r in rows:
        code = r["item_code"]
        m = _CODE_RE.match(code or "")
        if m and code.startswith(prefix):
            seqs.add(int(m.group(5)))
    return seqs


def _next_free(group_key: str, step: int) -> tuple[str | None, bool]:
    """Próximo código libre en el grupo. Devuelve (codigo|None, grupo_vacio)."""
    seqs = _existing_seqs(group_key)
    vacio = not seqs
    n = step if vacio else max(seqs) + step
    # saltar colisiones (raro, porque n > max; por si acaso)
    while n in seqs:
        n += step
    if n > _MAX_SEQ:
        return None, vacio
    return f"{group_key}-{n:03d}", vacio


def suggest_next_item_code(linea_ocr=None, candidatos=None) -> dict:
    """Sugiere el próximo item_code para una línea de factura sin match.

    Args:
        linea_ocr: la línea OCR (dict). Reservado para señales futuras
            (descripción / código de proveedor); hoy la inferencia se basa en
            `candidatos`, que es la mejor señal.
        candidatos: lista rankeada de artículos parecidos (dicts con `item_code`,
            o strings). El top define familia+subcategoría.

    Returns:
        {
            "codigo_sugerido": str | None,   # None si no hay familia clara o grupo lleno
            "familia": str | None,
            "grupo": str | None,             # CC-SS-SS-SS resuelto
            "paso": int | None,
            "confianza": "alta"|"media"|"baja",
            "fuente": str,
            "candidato_ref": str | None,     # item_code del candidato usado
            "editable": True,                # SIEMPRE — Regla 8
            "needs_review": bool,            # True si el humano debería ajustar
            "nota": str,
        }
    """
    info = _infer_group(candidatos)
    fam, gk = info["familia"], info["group_key"]

    if not fam or not gk:
        return {
            "codigo_sugerido": None, "familia": None, "grupo": None, "paso": None,
            "confianza": "baja", "fuente": info["fuente"], "candidato_ref": None,
            "editable": True, "needs_review": True,
            "nota": "Sin candidatos claros: el humano elige familia y código.",
        }

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

    return {
        "codigo_sugerido": code, "familia": fam, "grupo": gk, "paso": step,
        "confianza": info["confianza"], "fuente": info["fuente"],
        "candidato_ref": info["ref"], "editable": True,
        "needs_review": needs_review, "nota": nota,
    }


@frappe.whitelist()
def suggest_next_item_code_api(candidatos=None, linea_ocr=None) -> dict:
    """Wrapper whitelisted (debug / disparo desde UI). `candidatos` puede venir JSON."""
    if isinstance(candidatos, str) and candidatos.strip():
        candidatos = frappe.parse_json(candidatos)
    if isinstance(linea_ocr, str) and linea_ocr.strip():
        linea_ocr = frappe.parse_json(linea_ocr)
    return suggest_next_item_code(linea_ocr=linea_ocr, candidatos=candidatos)
