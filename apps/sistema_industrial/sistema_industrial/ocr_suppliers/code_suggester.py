"""Sugerencia inteligente de código de artículo (Fase 2 OCR).

Dos cosas:
  - `suggest_next_item_code`: SEAM cuyo cuerpo implementa FORGE (infiere
    familia+subcategoría del candidato top del matcher y calcula el próximo
    código libre con el paso correcto). Ver esquema de códigos
    CC-SS-SS-SS-NNN (familia/subcat/secuencial).
  - `aplicar_sugerencias`: wiring PURO (mío) que, por cada línea SIN match,
    pide un `codigo_sugerido` al suggester y lo agrega a la línea. Es la
    orquestación la que lo llama al armar el resultado.

El código sugerido es SOLO una pre-carga del campo editable (Regla 8): el humano
confirma/edita, y el Item se crea con el código que quede en el campo, no
necesariamente el sugerido.
"""


def suggest_next_item_code(linea: dict, candidatos: list) -> str | None:
    """Sugiere el próximo item_code libre para una línea SIN match.

    ⚠️ EL CUERPO LO IMPLEMENTA FORGE.

    Args:
        linea: la línea del OCR (descripcion, codigo_proveedor, ...).
        candidatos: top candidatos del matcher [{item_code, item_name, score, reason}].
            El candidato [0] (mejor score) sirve para inferir familia+subcategoría.

    Returns:
        item_code sugerido (str) siguiendo la convención CC-SS-SS-SS-NNN, o None
        si no se puede inferir (la UI deja el campo vacío para carga manual).
    """
    raise NotImplementedError(
        "ocr_suppliers.code_suggester.suggest_next_item_code: pendiente de "
        "implementar por Forge. Contrato definido en este archivo."
    )


def aplicar_sugerencias(lineas: list, suggester) -> list:
    """PURO: por cada línea SIN match, setea `codigo_sugerido` (suggester o None).

    Graceful: cualquier fallo del suggester (incl. NotImplementedError mientras
    Forge no lo conecta) deja `codigo_sugerido=None` sin romper el flujo. Las
    líneas CON match no llevan sugerencia (ya tienen ítem propuesto).
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
