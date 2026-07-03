"""API de paneles decorativos — motor de cálculo y descarga DXF.

Endpoints:
    calcular(batches_json, customer, job_name, observations)
        → recursos por lote (kg, segundos láser, plegados) + warnings

    descargar_dxf(batches_json, customer, job_name)
        → binario .dxf para descarga directa (frappe.response.type = "download")
"""
import json
import shutil
import tempfile
from pathlib import Path

try:
    import frappe
except ImportError:  # pragma: no cover
    frappe = None


def _get_price_file() -> Path:
    """Devuelve la ruta al daily_prices.json legacy (opcional — precios vienen del doctype)."""
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        return find_legacy_panel_dir() / "daily_prices.json"
    except Exception:
        return Path("/nonexistent/daily_prices.json")


@frappe.whitelist(allow_guest=False)
def calcular(batches_json, customer="", job_name="", observations=""):
    """Calcula recursos por lote (sin generar DXF).

    Parámetros (todos string desde JS/frappe.call):
        batches_json: JSON string — lista de batch dicts
        customer:     nombre/código del cliente
        job_name:     nombre del trabajo
        observations: observaciones libres

    Respuesta (r.message):
    {
        "lineas": [
            {
                "patron": "tresbolillo",
                "material": "Chapa doble decapada",
                "espesor_mm": 0.56,
                "quantity": 1,
                "ancho_mm": 500.0,
                "alto_mm": 1000.0,
                "cut_length_mm": 12345.0,
                "pierce_count": 432,
                "peso_kg": 2.24,
                "tiempo_laser_s": 68.6,
                "cantidad_plegados": 0,
                "consumed_resources": {...},
                "consumed_resources_warning": false
            }, ...
        ],
        "warnings": [...],
        "order_id": "VENTA-CLIENTE-TRABAJO"
    }
    """
    if isinstance(batches_json, str):
        batches = json.loads(batches_json)
    else:
        batches = batches_json

    if not batches:
        frappe.throw("Lista de lotes vacía.")

    from sistema_industrial.presets.panel_sales_local_app import _run_all_batches

    with tempfile.TemporaryDirectory() as tmp:
        result = _run_all_batches(
            batches=batches,
            customer=customer or "FRAPPE-CALCULAR",
            job_name=job_name or "panel",
            observations=observations or "",
            output_dir=Path(tmp) / "output",
            price_file=_get_price_file(),
        )

    svc = result.service_result
    lineas = []
    for r in svc.calculated_resources:
        cr = r.get("consumed_resources") or {}
        lineas.append({
            "patron": r.get("patron", ""),
            "material": r.get("material", ""),
            "espesor_mm": r.get("espesor_mm", 0),
            "quantity": r.get("quantity", 1),
            "ancho_mm": r.get("occupied_width_mm", 0),
            "alto_mm": r.get("occupied_height_mm", 0),
            "cut_length_mm": r.get("cut_length_mm", 0),
            "pierce_count": r.get("pierce_count", 0),
            "peso_kg": float(cr.get("material_kg", 0)) * int(r.get("quantity", 1)),
            "tiempo_laser_s": float(cr.get("machine_seconds", 0)) * int(r.get("quantity", 1)),
            "cantidad_plegados": int(r.get("bend_count", 0)) * int(r.get("quantity", 1)),
            "consumed_resources": cr,
            "consumed_resources_warning": r.get("consumed_resources_warning", False),
        })

    return {
        "lineas": lineas,
        "warnings": svc.warnings,
        "order_id": getattr(svc, "order_id", ""),
    }


@frappe.whitelist(allow_guest=False)
def descargar_dxf(batches_json, customer="", job_name=""):
    """Genera y descarga el DXF en-demand (sin persistencia).

    El frontend llama esta URL directamente (NO via frappe.call):
        /api/method/sistema_industrial.api.paneles.descargar_dxf?batches_json=...

    Frappe sirve el binario con Content-Disposition: attachment.
    """
    if isinstance(batches_json, str):
        batches = json.loads(batches_json)
    else:
        batches = batches_json

    if not batches:
        frappe.throw("Lista de lotes vacía.")

    # --- TRACE TEMPORAL (bug DXF stale, VEGA_BUG_DXF_RACE) ---
    # Loguea qué recibió el endpoint vs qué generó, con PID+timestamp, para
    # trazar el origen de los bytes. QUITAR cuando el bug esté cerrado.
    import os as _os
    import time as _time
    import hashlib as _hl
    _t0 = _time.time()
    _in_sizes = [sz for b in batches for sz in b.get("sheet_sizes", [])]
    _in_widths = [str(s[0]) for s in _in_sizes]

    from sistema_industrial.presets.panel_sales_local_app import _run_all_batches

    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "output"
        # Paso 2: empezar de cero — borrar cualquier DXF anterior antes de generar.
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Paso 3: generar el DXF nuevo.
        result = _run_all_batches(
            batches=batches,
            customer=customer or "FRAPPE",
            job_name=job_name or "panel",
            observations="",
            output_dir=output_dir,
            price_file=_get_price_file(),
        )
        dxf_path = result.service_result.dxf_path
        if not Path(dxf_path).exists():
            frappe.throw("El motor no generó un archivo DXF.")
        content = Path(dxf_path).read_bytes()

    # --- TRACE: pid, worker, batches IN, bytes/hash del DXF OUT, duración ---
    try:
        _md5 = _hl.md5(content).hexdigest()[:8]
        _txt = content.decode("latin-1", "ignore")
        _present = sorted(
            w for w in set(_in_widths)
            if ("\n" + w + "\n") in _txt or ("\n" + str(int(float(w))) + ".0\n") in _txt
        )
        _line = (
            f"{_time.strftime('%H:%M:%S')} pid={_os.getpid()} t={_t0:.3f} "
            f"dur={_time.time()-_t0:.2f}s n_batches={len(batches)} "
            f"anchos_in={_in_widths} bytes={len(content)} md5={_md5} "
            f"anchos_en_dxf={_present} customer={customer!r} job={job_name!r}\n"
        )
        with open("/home/costa/dxf_trace.log", "a", encoding="utf-8") as _f:
            _f.write(_line)
    except Exception as _e:
        try:
            with open("/home/costa/dxf_trace.log", "a", encoding="utf-8") as _f:
                _f.write(f"TRACE_ERROR: {_e}\n")
        except Exception:
            pass

    nombre_trabajo = (job_name or "panel").replace(" ", "_")[:40]
    frappe.response.filename = f"{nombre_trabajo}.dxf"
    frappe.response.filecontent = content
    frappe.response.type = "download"
