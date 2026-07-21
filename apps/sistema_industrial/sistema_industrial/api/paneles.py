"""API de paneles decorativos — motor de cálculo y descarga DXF.

Endpoints:
    calcular(batches_json, customer, job_name, observations)
        → recursos por lote (kg, segundos láser, plegados) + warnings

    descargar_dxf(batches_json, customer, job_name)
        → binario .dxf para descarga directa (frappe.response.type = "download")

FUENTE ÚNICA DE PRECIOS (explícita, no deducida):
    Los precios salen de dos lugares, ambos leídos por el motor al calcular `cost`:
      1. `daily_prices.json` — precios por kg de material + plegado (carga manual
         del vendedor en la página de Precios).
      2. Doctype «SI Precios Globales» — precio por segundo de láser / por plegado.
    NO hay PriceCache ni pull de Tango en este camino (ver DECISION_011 / MSG_165).
    El motor lee esas dos fuentes por su cuenta (calculate_cost /
    _precio_segundo_laser); por eso `calcular` no le pasa ninguna ruta de precios.
"""
import json
import shutil
import tempfile
from pathlib import Path

try:
    import frappe
except ImportError:  # pragma: no cover
    frappe = None


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
                "travel_length_mm": 9500.0,   # término crudo para calibración láser
                "pierce_count": 432,
                "peso_kg": 2.24,
                "tiempo_laser_s": 68.6,
                "cantidad_plegados": 0,
                "costo_material": 1234.5,     # $ por panel
                "costo_maquina": 678.9,       # $ por panel (segundos × precio_segundo)
                "costo_total": 1913.4,        # $ por panel
                "costo_total_linea": 1913.4,  # costo_total × quantity
                "prices_missing": false,      # true si faltan precios del día
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
        )

    svc = result.service_result
    lineas = []
    for r in svc.calculated_resources:
        cr = r.get("consumed_resources") or {}
        cost = r.get("cost") or {}
        qty = int(r.get("quantity", 1))
        costo_total_unit = float(cost.get("costo_total", 0))
        lineas.append({
            "patron": r.get("patron", ""),
            "material": r.get("material", ""),
            "espesor_mm": r.get("espesor_mm", 0),
            "quantity": qty,
            "ancho_mm": r.get("occupied_width_mm", 0),
            "alto_mm": r.get("occupied_height_mm", 0),
            "cut_length_mm": r.get("cut_length_mm", 0),
            "travel_length_mm": r.get("travel_length_mm", 0),
            "pierce_count": r.get("pierce_count", 0),
            "peso_kg": float(cr.get("material_kg", 0)) * qty,
            "tiempo_laser_s": float(cr.get("machine_seconds", 0)) * qty,
            "cantidad_plegados": int(r.get("bend_count", 0)) * qty,
            # Precio: unitario (por panel) + total de línea (× cantidad).
            # Sin esto la UI recibía los segundos pero no el precio → Panel
            # Decorativo no cerraba end-to-end.
            "costo_material": float(cost.get("costo_material", 0)),
            "costo_maquina": float(cost.get("costo_maquina", 0)),
            "costo_total": costo_total_unit,
            "costo_total_linea": round(costo_total_unit * qty, 2),
            "prices_missing": bool(cost.get("prices_missing", False)),
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
