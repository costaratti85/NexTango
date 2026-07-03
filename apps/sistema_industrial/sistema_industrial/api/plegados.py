"""Endpoints de plegados para la page plegados-complejos.

URL base: /api/method/sistema_industrial.api.plegados.

Endpoints:
    calcular(material_corte, ancho_int, largo_int, alto, espesor)
    guardar_pedido(data_json)
    list_pedidos(filters_json?)
    get_pedido(name)
    descargar_dxf(material_corte, ancho_int, largo_int, alto, espesor, job_name?) — URL directa
"""
import json
import sys
import tempfile
from pathlib import Path

import frappe

_PLEGADOS_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Plegados"


def _load_bandeja():
    plegados_path = str(_PLEGADOS_DIR)
    inserted = plegados_path not in sys.path
    if inserted:
        sys.path.insert(0, plegados_path)
    try:
        from bandeja import calcular_bandeja, calcular_recursos_bandeja, exportar_dxf_bandeja  # type: ignore
        return calcular_bandeja, calcular_recursos_bandeja, exportar_dxf_bandeja
    finally:
        if inserted and plegados_path in sys.path:
            sys.path.remove(plegados_path)


def _get_material_row(material_corte_name: str) -> dict:
    """Retorna dict compatible con calcular_recursos_bandeja."""
    mat = frappe.get_doc("SI Material Corte", material_corte_name)
    return {
        "densidad_kg_m2": float(mat.densidad_kg_m2 or 0),
        "velocidad_corte_mm_s": float(mat.velocidad_corte_mm_s or 0),
        "material": str(mat.material or ""),
        "calibre": str(mat.calibre or "-"),
        "familia": str(mat.familia or ""),
        "espesor_mm": float(mat.espesor_mm or 0),
    }


@frappe.whitelist(allow_guest=False)
def calcular(material_corte, ancho_int, largo_int, alto, espesor):
    """Calcula geometría y recursos de una bandeja plegada.

    r.message (ok):
    {
        "ok": true,
        "blank_ancho": 620.0,
        "blank_largo": 820.0,
        "despunte": 10.0,
        "kg_chapa": 1.234,
        "tiempo_laser_s": 45.6,
        "perforaciones": 0,
        "plegados": 4
    }

    r.message (error):
    {
        "ok": false,
        "error": "descripción del error"
    }
    """
    try:
        ancho_int = float(ancho_int)
        largo_int = float(largo_int)
        alto = float(alto)
        espesor = float(espesor)
    except (TypeError, ValueError) as exc:
        return {"ok": False, "error": f"Parámetros inválidos: {exc}"}

    if alto <= espesor:
        return {"ok": False, "error": "El alto debe ser mayor al espesor"}

    try:
        material_row = _get_material_row(material_corte)
    except Exception as exc:
        return {"ok": False, "error": f"Material no encontrado: {exc}"}

    try:
        calcular_bandeja, calcular_recursos_bandeja, _ = _load_bandeja()
        geom = calcular_bandeja(ancho_int, largo_int, alto, espesor)
        rec = calcular_recursos_bandeja(ancho_int, largo_int, alto, espesor, material_row)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "blank_ancho": geom["blank_ancho"],
        "blank_largo": geom["blank_largo"],
        "despunte": geom["despunte"],
        "kg_chapa": rec["kg_chapa"],
        "tiempo_laser_s": rec["tiempo_laser_s"],
        "perforaciones": 0,
        "plegados": rec["plegados"],
    }


@frappe.whitelist(allow_guest=False)
def guardar_pedido(data_json):
    """Crea o actualiza un SI Pedido Plegado.

    data_json: JSON string con campos del pedido.
      Campos obligatorios: customer, material_corte, ancho_int, largo_int, alto, espesor
      Campos calculados (opcionales — before_save los recalcula): blank_ancho, blank_largo,
        despunte, peso_kg, tiempo_laser_s, cantidad_pliegues
      Otros opcionales: job_name, factor_kg, factor_laser, factor_plegar_kg, factor_pliegue,
        observaciones, name (para update)

    r.message:
    {
        "ok": true,
        "name": "BAN-2026-00001",
        "costo_total": 5678.90
    }
    """
    try:
        data = json.loads(data_json) if isinstance(data_json, str) else data_json
    except (json.JSONDecodeError, TypeError) as exc:
        return {"ok": False, "error": f"JSON inválido: {exc}"}

    doc_name = data.get("name")
    try:
        if doc_name and frappe.db.exists("SI Pedido Plegado", doc_name):
            doc = frappe.get_doc("SI Pedido Plegado", doc_name)
            for k, v in data.items():
                if k not in ("name", "doctype"):
                    setattr(doc, k, v)
            doc.save()
        else:
            payload = {"doctype": "SI Pedido Plegado"}
            payload.update({k: v for k, v in data.items() if k not in ("name", "doctype")})
            doc = frappe.get_doc(payload)
            doc.insert()
        frappe.db.commit()
        return {"ok": True, "name": doc.name, "costo_total": float(doc.costo_total or 0)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@frappe.whitelist(allow_guest=False)
def list_pedidos(filters_json=None):
    """Lista de SI Pedido Plegado con campos de resumen.

    filters_json: JSON string con filtros Frappe opcionales (e.g. '{"customer": "XYZ"}')

    r.message:
    {
        "pedidos": [
            {
                "name": "BAN-2026-00001",
                "customer": "...",
                "job_name": "...",
                "fecha": "2026-07-01",
                "material_corte": "...",
                "ancho_int": 300.0,
                "largo_int": 500.0,
                "alto": 30.0,
                "espesor": 0.56,
                "peso_kg": 1.234,
                "costo_total": 5678.90,
                "status": "Borrador"
            }
        ]
    }
    """
    filters = {}
    if filters_json:
        try:
            filters = json.loads(filters_json) if isinstance(filters_json, str) else filters_json
        except (json.JSONDecodeError, TypeError):
            pass

    pedidos = frappe.get_all(
        "SI Pedido Plegado",
        fields=[
            "name", "customer", "job_name", "fecha", "material_corte",
            "ancho_int", "largo_int", "alto", "espesor",
            "peso_kg", "costo_total", "status",
        ],
        filters=filters,
        order_by="fecha desc, creation desc",
        limit=200,
    )
    return {"pedidos": pedidos}


@frappe.whitelist(allow_guest=False)
def get_pedido(name):
    """Retorna el doc completo de un SI Pedido Plegado como dict.

    r.message: dict con todos los campos del documento.
    """
    if not frappe.db.exists("SI Pedido Plegado", name):
        frappe.throw(f"Pedido no encontrado: {name}", frappe.DoesNotExistError)
    doc = frappe.get_doc("SI Pedido Plegado", name)
    return doc.as_dict()


@frappe.whitelist(allow_guest=False)
def descargar_dxf(material_corte, ancho_int, largo_int, alto, espesor, job_name="bandeja"):
    """Genera y descarga el DXF de la bandeja.

    Usar URL directa (NO frappe.call):

        const url = '/api/method/sistema_industrial.api.plegados.descargar_dxf'
            + '?material_corte=' + encodeURIComponent(materialCorte)
            + '&ancho_int=' + ancho + '&largo_int=' + largo
            + '&alto=' + alto + '&espesor=' + espesor
            + '&job_name=' + encodeURIComponent(jobName);
        window.open(url, '_blank');
    """
    try:
        ancho_int = float(ancho_int)
        largo_int = float(largo_int)
        alto = float(alto)
        espesor = float(espesor)
    except (TypeError, ValueError) as exc:
        frappe.throw(f"Parámetros inválidos: {exc}")

    try:
        material_row = _get_material_row(material_corte)
    except Exception as exc:
        frappe.throw(f"Material no encontrado: {exc}")

    try:
        calcular_bandeja, _, exportar_dxf_bandeja = _load_bandeja()
        geom = calcular_bandeja(ancho_int, largo_int, alto, espesor)
    except Exception as exc:
        frappe.throw(str(exc))

    with tempfile.TemporaryDirectory() as tmpdir:
        dxf_path = Path(tmpdir) / "bandeja.dxf"
        # Paso 2: empezar de cero — borrar cualquier DXF anterior antes de generar.
        if dxf_path.exists():
            dxf_path.unlink()

        # Paso 3: generar el DXF nuevo.
        exportar_dxf_bandeja(
            geom,
            str(dxf_path),
            material=material_row.get("material", ""),
            calibre=material_row.get("calibre", "-"),
            familia=material_row.get("familia", ""),
            espesor_mm=material_row.get("espesor_mm", 0.0),
        )
        dxf_bytes = dxf_path.read_bytes()

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(job_name))
    frappe.response.filename = f"{safe_name}.dxf"
    frappe.response.filecontent = dxf_bytes
    frappe.response.type = "download"
