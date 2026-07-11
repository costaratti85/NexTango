import os
import requests
import json

# El token vive en la variable de entorno APP_INSTANCE_ID (nunca hardcodeado).
TOKEN = os.environ.get("APP_INSTANCE_ID", "")
COMPANY = os.environ.get("TANGO_COMPANY", "25")

URL = "http://server-t:17000/Api/Create/360"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "ApiAuthorization": TOKEN,
    "Company": COMPANY,
}

articulo = {
    "COD_STA11_DEFECTO": "",
    "COD_STA11": "PRUEBA007",
    "COD_ARTICU": "PRUEBA007",
    "DESCRIPCIO": "ARTICULO OCR 7",
    "SINONIMO": "OCR7",
    "COD_BARRA": "7799999999997",
    "PROMO_MENU": "N",
    "USA_ESC": "N",
    "STOCK": True,
    "USA_PARTID": False,
    "USA_SERIE": False,
    "COD_BARRA_NOTMAPPED": False,
}

print("Enviando artículo a Tango:")
print(json.dumps(articulo, indent=4, ensure_ascii=False))

try:
    respuesta = requests.post(
        URL,
        headers=headers,
        json=articulo,
        timeout=30
    )

    print("\nSTATUS:", respuesta.status_code)
    print("CONTENT-TYPE:", respuesta.headers.get("Content-Type"))
    print("\nRESPUESTA:")

    if respuesta.text.strip():
        print(respuesta.text)
    else:
        print("(Respuesta vacía)")

except requests.exceptions.RequestException as e:
    print("\nERROR DE CONEXIÓN:")
    print(e)