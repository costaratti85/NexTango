"""SEAM de extracción OCR — contrato entre la orquestación (Atlas) y el motor OCR (agente OCR).

⚠️ EL CUERPO DE `extract_invoice` LO IMPLEMENTA EL AGENTE OCR.
Acá vive SOLO el contrato (firma + forma de retorno) para que:
  - la orquestación de `api/ocr_proveedores.py` tenga a quién llamar, y
  - OCR sepa exactamente qué recibir y qué devolver, sin ambigüedad.

La orquestación importa `extract_invoice` y maneja `NotImplementedError` con
gracia (devuelve estado "ocr_pendiente"), así la página se puede probar de punta
a punta aunque el motor todavía no esté conectado.
"""


def extract_invoice(file_path: str, options: dict | None = None) -> dict:
    """Extrae proveedor + líneas de una factura (PDF/imagen).

    Args:
        file_path: ruta absoluta al archivo en disco (PDF o imagen).
        options:   dict opcional (ej. {"cuit_hint": "..."} o flags de motor).

    DEBE devolver un dict con esta forma (contrato con Atlas/Vega):
    {
        "proveedor": {
            "cuit": "30712517383",          # 11 dígitos, str (o "" si no se detectó)
            "nombre": "ORANGE BLUE ...",     # razón social detectada
        },
        "lineas": [
            {
                "codigo_proveedor": "AB-123",  # código del ítem en la factura ("" si no hay)
                "codigo_barras": "7790...",    # EAN/UPC ("" si no hay)
                "descripcion": "Broca HSS 6mm",
                "cantidad": 10.0,              # float
                "precio_unitario": 1234.5,     # float
                "raw_text": "..."              # texto crudo de la fila (debug, opcional)
            },
            ...
        ],
        "meta": {
            "es_pdf_nativo": true,             # el PDF traía texto
            "necesita_ocr": false,             # hubo que rasterizar+OCR
            "page_ref": {"w": 1191.0, "h": 1684.0},   # opcional
            "warnings": []                     # avisos de extracción, opcional
        }
    }

    NO hace matching contra ERPNext (eso es de la orquestación) ni escribe nada.
    Es una función pura de archivo -> estructura.
    """
    raise NotImplementedError(
        "ocr_suppliers.extraction.extract_invoice: pendiente de implementar por "
        "el agente OCR. Contrato definido en este archivo."
    )
