"""Endpoints de perfiles plegados (page perfiles-plegados).

URL base: /api/method/sistema_industrial.api.perfiles.

Endpoints:
    guardar_pedido(data_json)
    list_pedidos()
    get_pedido(pedido_id)

Persistencia v1: archivos JSON en Programas_hechos/Plegados/pedidos/ con id
PL-YYYYMMDD-NNNN — mismo formato y store que el server standalone
(panel_sales_local_app), para que los pedidos sean intercambiables entre ambos
entornos. Migrar a DocType cuando Constantino defina el modelo (ver reporte
CYBELEC en coordination/).
"""
import json
import re
from datetime import date
from pathlib import Path

try:
    import frappe
    _whitelist = frappe.whitelist
except ImportError:  # permite unit-testear los helpers puros sin bench
    frappe = None

    def _whitelist(**_kw):
        def deco(fn):
            return fn
        return deco


PEDIDOS_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Plegados" / "pedidos"

_ID_RE = re.compile(r"^PL-(\d{8})-(\d{4})$")

# Campos de cabecera que devuelve list_pedidos (segs y plan son pesados)
_HEADER_FIELDS = (
    "id", "cliente", "ref", "cantidad", "material", "material_corte",
    "espesor_mm", "desarrollo_mm", "n_pliegues", "total", "ts",
)


def _next_pedido_id(base_dir: Path, today: date = None) -> str:
    """PL-YYYYMMDD-NNNN, contador autoincremental por día."""
    today_s = (today or date.today()).strftime("%Y%m%d")
    base_dir.mkdir(parents=True, exist_ok=True)
    last_n = 0
    for p in base_dir.glob(f"PL-{today_s}-*.json"):
        m = _ID_RE.match(p.stem)
        if m and int(m.group(2)) > last_n:
            last_n = int(m.group(2))
    return f"PL-{today_s}-{last_n + 1:04d}"


def _save_pedido(data: dict, base_dir: Path = None) -> dict:
    base_dir = base_dir or PEDIDOS_DIR
    pedido_id = _next_pedido_id(base_dir)
    data = dict(data)
    data["id"] = pedido_id
    path = base_dir / f"{pedido_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "id": pedido_id}


def _list_pedidos(base_dir: Path = None) -> list:
    base_dir = base_dir or PEDIDOS_DIR
    if not base_dir.is_dir():
        return []
    out = []
    for p in sorted(base_dir.glob("PL-*.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        out.append({k: data.get(k) for k in _HEADER_FIELDS})
    return out


def _get_pedido(pedido_id: str, base_dir: Path = None) -> dict:
    base_dir = base_dir or PEDIDOS_DIR
    if not _ID_RE.match(pedido_id or ""):
        return {"ok": False, "error": "id inválido"}
    path = base_dir / f"{pedido_id}.json"
    if not path.is_file():
        return {"ok": False, "error": "not found"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": str(exc)}


@_whitelist(allow_guest=False)
def guardar_pedido(data_json):
    """Guarda un pedido de perfil plegado.

    data_json: JSON string con cliente, ref, cantidad, material, material_corte,
      espesor_mm, densidad_kg_m2, desarrollo_mm, n_pliegues, tonelaje_ton,
      precio_material_unitario, precio_plegado_unitario, total_unitario, total,
      segs, plan, ts.

    r.message: {"ok": true, "id": "PL-20260702-0001"} | {"ok": false, "error": "..."}
    """
    try:
        data = json.loads(data_json) if isinstance(data_json, str) else data_json
        if not isinstance(data, dict):
            raise ValueError("el payload debe ser un objeto")
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return {"ok": False, "error": f"JSON inválido: {exc}"}
    try:
        return _save_pedido(data)
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


@_whitelist(allow_guest=False)
def list_pedidos():
    """Lista de pedidos guardados (solo cabecera), del más reciente al más viejo.

    r.message: {"pedidos": [{id, cliente, ref, cantidad, material, ...}, ...]}
    """
    return {"pedidos": _list_pedidos()}


@_whitelist(allow_guest=False)
def get_pedido(pedido_id):
    """JSON completo de un pedido por ID (incluye segs y plan)."""
    return _get_pedido(pedido_id)
