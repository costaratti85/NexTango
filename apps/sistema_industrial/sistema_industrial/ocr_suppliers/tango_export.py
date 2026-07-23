"""SEAM de exportación a Tango — contrato entre la orquestación (Atlas) y Forge.

⚠️ EL CUERPO DE `build_tango_import_excel` LO IMPLEMENTA FORGE.
Acá vive SOLO el contrato: qué recibe y qué devuelve, para que la orquestación
de `api/ocr_proveedores.confirmar` tenga a quién llamar tras crear los Items
nuevos, sin ambigüedad.

La orquestación maneja `NotImplementedError`/ImportError con gracia (devuelve
`tango_excel=None` + nota), así el flujo funciona aunque el generador todavía no
esté conectado. **CERO escritura a Tango**: esto solo GENERA un .xlsx que
Constantino importa a mano.
"""


def build_tango_import_excel(nuevos: list, proveedor: dict | None = None) -> str:
    """Genera el Excel de importación de ARTÍCULOS NUEVOS a Tango.

    Args:
        nuevos: lista de dicts de los Items recién creados en ERPNext:
            [{ "item_code": str, "item_name": str,
               "codigo_proveedor": str, "barcode": str }]
        proveedor: {"cuit", "nombre", "supplier"} (contexto, opcional).

    DEBE devolver el **file_url** (str, ej. "/private/files/tango_import_xxx.xlsx")
    del archivo generado y guardado como File de Frappe, para que la UI lo ofrezca
    como descarga. NO escribe en Tango.

    Formato/columnas del Excel: los define Forge según la plantilla de importación
    de artículos de Tango (ver esquema Excel presupuesto/OT y generar_articulos_tango
    del standalone OCR). Coordinar con Forge el mapeo item->columnas Tango.
    """
    raise NotImplementedError(
        "ocr_suppliers.tango_export.build_tango_import_excel: pendiente de "
        "implementar por Forge. Contrato definido en este archivo."
    )
