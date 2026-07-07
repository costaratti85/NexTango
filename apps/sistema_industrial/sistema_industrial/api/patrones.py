"""Endpoints para el catálogo de patrones del panel decorativo.

URL base: /api/method/sistema_industrial.api.patrones.

Endpoints:
    get_all(customer=None)       — patrones Públicos + Exclusivos del cliente (activos)
    get_patron(name, version)    — resolver versionado (contrato con SI Pieza / Lechu)
    upload_pattern(...)          — copia DXF desde File de Frappe a /planos/, crea SI Patron
    delete_pattern(name)         — baja lógica: activo=0 (archivo queda en disco)
    list_admin()                 — todos los patrones incl. inactivos (grilla de admin)
"""
import json
import os
import re
import shutil
from pathlib import Path

import frappe


_THUMBNAIL_BASE = "/assets/sistema_industrial/pattern_thumbnails"


def _safe_name(name):
    return re.sub(r"[^\w]", "_", name)


def _safe_filename(filename):
    """Basename seguro: sin path traversal, sin caracteres peligrosos."""
    name = os.path.basename(filename)
    safe = re.sub(r"[^\w\-.]", "_", name)
    return safe or "patron.dxf"


def _planos_root() -> Path:
    """Raíz configurable en site_config como nextango_planos_path."""
    configured = frappe.conf.get("nextango_planos_path")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[4] / "planos"


def _patron_dest_dir(visibilidad, customer=None) -> Path:
    root = _planos_root()
    if visibilidad == "Exclusivo" and customer:
        return root / customer / "patrones"
    return root / "generico" / "patrones"


def _resolve_frappe_file(file_url: str) -> Path:
    """Resuelve un file_url de Frappe (/private/files/...) al path absoluto en disco."""
    fname = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not fname:
        frappe.throw(f"Archivo de Frappe no encontrado para URL: {file_url}")
    return Path(frappe.get_doc("File", fname).get_full_path())


def _count_splines(dxf_path) -> int:
    """Cuenta entidades SPLINE en el modelspace del DXF. Retorna 0 si falla."""
    try:
        import ezdxf
        doc = ezdxf.readfile(str(dxf_path))
        return sum(1 for e in doc.modelspace() if e.dxftype() == "SPLINE")
    except Exception:
        return 0


def _thumbnail_url(filename):
    """Retorna la URL Frappe si el PNG existe en public/pattern_thumbnails/, o None."""
    thumb_dir = Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"
    p = thumb_dir / filename
    return f"{_THUMBNAIL_BASE}/{filename}" if p.exists() else None


def _render_dxf_thumbnail(file_path: str, out_path, size_px: int = 300):
    """Render DXF directo a PNG — fallback cuando el motor legacy no puede tilear.

    Dibuja LINE/ARC/CIRCLE/SPLINE del modelspace escalados al canvas.
    Retorna out_path en éxito, None en fallo.
    """
    import math as _math
    try:
        import ezdxf as _ezdxf
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
    except ImportError:
        return None
    try:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as _f:
                _doc = _ezdxf.read(_f)
        except Exception:
            with open(file_path, "r", encoding="latin-1") as _f:
                _doc = _ezdxf.read(_f)
        _msp = _doc.modelspace()

        fig, ax = _plt.subplots(figsize=(size_px / 100, size_px / 100), dpi=100)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")
        color = "#1a1a2e"

        def _arc_pts(cx, cy, r, a0_deg, a1_deg):
            a0 = a0_deg % 360
            a1 = a1_deg % 360
            if a1 <= a0:
                a1 += 360
            span = a1 - a0
            n = max(6, int(span / 5))
            return [
                (cx + r * _math.cos(_math.radians(a0 + span * i / n)),
                 cy + r * _math.sin(_math.radians(a0 + span * i / n)))
                for i in range(n + 1)
            ]

        for _e in _msp:
            et = _e.dxftype()
            try:
                if et == "LINE":
                    s, end = _e.dxf.start, _e.dxf.end
                    ax.plot([s.x, end.x], [s.y, end.y], color=color, linewidth=0.5)
                elif et == "ARC":
                    c = _e.dxf.center
                    pts = _arc_pts(c.x, c.y, _e.dxf.radius,
                                   _e.dxf.start_angle, _e.dxf.end_angle)
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
                elif et == "CIRCLE":
                    c = _e.dxf.center
                    pts = _arc_pts(c.x, c.y, _e.dxf.radius, 0, 360)
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
                elif et == "SPLINE":
                    raw = list(_e.flattening(0.5))
                    if len(raw) >= 2:
                        ax.plot([p.x for p in raw], [p.y for p in raw],
                                color=color, linewidth=0.5)
            except Exception:
                pass

        ax.autoscale()
        _plt.tight_layout(pad=0)
        fig.savefig(str(out_path), dpi=100, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        _plt.close(fig)
        return out_path
    except Exception as exc:
        frappe.log_error(title="thumbnail_dxf_directo", message=str(exc))
        try:
            import matplotlib.pyplot as _plt2
            _plt2.close("all")
        except Exception:
            pass
        return None


def _render_panel_thumbnail(file_path: str, step_x: float, step_y: float, out_path, size_px: int = 300):
    """Renderiza thumbnail 300×300mm tileado usando el motor legacy real.

    margin=15mm, cut_partial_figures=True — mismo criterio que un panel de producción.
    Retorna out_path en éxito, None si el motor no produce items (e.g. solo splines)
    o falla (caller debe caer a _render_dxf_thumbnail).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
    except ImportError:
        return None

    try:
        import math as _math
        import sys as _sys
        import os as _os
        from importlib import import_module as _import_module
        from io import StringIO as _StringIO
        from contextlib import redirect_stdout as _redirect_stdout
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir

        legacy_dir = find_legacy_panel_dir()
        legacy_path = str(legacy_dir)
        prev_cwd = Path.cwd()
        inserted = legacy_path not in _sys.path
        if inserted:
            _sys.path.insert(0, legacy_path)
        _os.chdir(legacy_dir)

        try:
            settings_module = _import_module("config.settings")
            layout_module = _import_module("layout.cad_result_layout")
            legacy_main = _import_module("main")

            settings = settings_module.Settings()
            settings.pattern_type = "dxf"
            settings.input_file = str(file_path)
            settings.step_x = step_x
            settings.step_y = step_y
            settings.sheet_sizes = [(300.0, 300.0, 1)]
            settings.margin = 15.0
            settings.cut_partial_figures = True

            stdout_buf = _StringIO()
            with _redirect_stdout(stdout_buf):
                result_items = legacy_main.create_cad_result_items_from_batch(settings)
                arranged_items = layout_module.arrange_cad_result_items(result_items)

            if not result_items:
                return None
        finally:
            _os.chdir(prev_cwd)
            if inserted:
                try:
                    _sys.path.remove(legacy_path)
                except ValueError:
                    pass

        fig, ax = _plt.subplots(figsize=(size_px / 100, size_px / 100), dpi=100)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("white")
        fig.patch.set_facecolor("white")
        color = "#1a1a2e"

        def _draw(geom):
            if hasattr(geom, "points"):
                pts = list(geom.points)
                if len(pts) >= 2:
                    ax.plot([p[0] for p in pts], [p[1] for p in pts],
                            color=color, linewidth=0.5)
            elif hasattr(geom, "entities"):
                for ent in geom.entities:
                    _draw(ent)
            elif hasattr(geom, "cx") and hasattr(geom, "radius"):
                span = geom.end_angle - geom.start_angle
                if span < 0:
                    span += 360
                if abs(span) >= 359.9:
                    n, total = 64, 2 * _math.pi
                else:
                    rad_span = _math.radians(span) % (2 * _math.pi)
                    n = max(8, int(abs(rad_span) / (2 * _math.pi) * 64))
                    total = _math.radians(span)
                a0 = _math.radians(geom.start_angle)
                angles = [a0 + total * i / n for i in range(n + 1)]
                ax.plot(
                    [geom.cx + _math.cos(a) * geom.radius for a in angles],
                    [geom.cy + _math.sin(a) * geom.radius for a in angles],
                    color=color, linewidth=0.5,
                )
            elif hasattr(geom, "x1") and hasattr(geom, "x2"):
                ax.plot([geom.x1, geom.x2], [geom.y1, geom.y2],
                        color=color, linewidth=0.5)

        for item in arranged_items:
            _draw(item)

        ax.autoscale()
        _plt.tight_layout(pad=0)
        fig.savefig(str(out_path), dpi=100, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        _plt.close(fig)
        return out_path

    except Exception as exc:
        frappe.log_error(title="thumbnail_motor_panel", message=str(exc))
        try:
            import matplotlib.pyplot as _plt2
            _plt2.close("all")
        except Exception:
            pass
        return None


def _generate_and_save_thumbnail(nombre: str, dxf_path, step_x=None, step_y=None) -> "str | None":
    """Genera thumbnail tileado con el motor legacy; fallback DXF directo; fallback PIL.

    1. _render_panel_thumbnail — panel 300×300mm tileado, fondo blanco, color #1a1a2e.
    2. _render_dxf_thumbnail   — render DXF directo sin tiling (solo splines/splines mixtos).
    3. Placeholder PIL         — gris con nombre del patrón, para que la UI muestre algo.

    Retorna la URL pública del PNG o None si los tres métodos fallan.
    """
    thumb_dir = Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(nombre)
    out_path = thumb_dir / f"{safe}.png"

    sx = float(step_x) if step_x not in (None, "") else 84.0
    sy = float(step_y) if step_y not in (None, "") else 84.0

    # --- Intento 1: panel tileado con motor legacy ---
    if _render_panel_thumbnail(str(dxf_path), sx, sy, out_path):
        return f"{_THUMBNAIL_BASE}/{safe}.png"

    # --- Intento 2: render DXF directo (fallback sin tiling) ---
    if _render_dxf_thumbnail(str(dxf_path), out_path):
        return f"{_THUMBNAIL_BASE}/{safe}.png"

    # --- Intento 3: placeholder PIL con nombre del patrón ---
    try:
        from PIL import Image, ImageDraw, ImageFont
        SIZE = 216
        img = Image.new("RGB", (SIZE, SIZE), color=(230, 230, 230))
        draw = ImageDraw.Draw(img)
        draw.rectangle([4, 4, SIZE - 5, SIZE - 5], outline=(180, 180, 180), width=2)
        label = nombre[:20]
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 16)
        except Exception:
            font = ImageFont.load_default()
        try:
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(label, font=font)
        draw.text(((SIZE - tw) / 2, (SIZE - th) / 2), label, fill=(80, 80, 80), font=font)
        img.save(str(out_path))
        return f"{_THUMBNAIL_BASE}/{safe}.png"
    except Exception:
        import traceback
        frappe.log_error(
            title=f"thumbnail_placeholder:{nombre}",
            message=traceback.format_exc(),
        )
        return None


@frappe.whitelist(allow_guest=False)
def backfill_thumbnails(force=False, names=None):
    """Genera thumbnails para SI Patron con archivo DXF.

    force: si truthy (pasa "1" desde la API), re-genera aunque el archivo PNG
    ya exista — necesario para sobreescribir placeholders PIL previos.
    names: lista JSON de nombres a procesar; si None/vacío, procesa todos.

    Retorna: {"generados": [...], "ya_existian": [...], "errores": [...]}
    """
    # Frappe pasa parámetros como strings desde HTTP; normalizar.
    if isinstance(force, str):
        force = force.lower() in ("1", "true", "yes")
    if isinstance(names, str):
        import json as _json
        try:
            names = _json.loads(names)
        except Exception:
            names = [n.strip() for n in names.split(",") if n.strip()]

    filters: dict = {"tipo": ["in", ["Archivo", "Vectorizado"]], "activo": 1}
    if names:
        filters["name"] = ["in", names]

    patrones = frappe.db.get_all(
        "SI Patron",
        filters=filters,
        fields=["name", "archivo_dxf", "parametros"],
    )

    generados, ya_existian, errores = [], [], []

    thumb_dir = Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"

    for p in patrones:
        nombre = p["name"]
        dxf_path = (p.get("archivo_dxf") or "").strip()
        if not dxf_path:
            continue

        safe = _safe_name(nombre)
        out_path = thumb_dir / f"{safe}.png"

        if out_path.exists() and not force:
            ya_existian.append(nombre)
            continue

        if not Path(dxf_path).exists():
            errores.append({"name": nombre, "error": f"DXF no encontrado: {dxf_path}"})
            continue

        try:
            params = json.loads(p.get("parametros") or "{}")
        except Exception:
            params = {}
        url = _generate_and_save_thumbnail(
            nombre, dxf_path,
            step_x=params.get("step_x"),
            step_y=params.get("step_y"),
        )
        if url:
            generados.append(nombre)
        else:
            errores.append({"name": nombre, "error": "render falló (ver logs)"})

    return {"generados": generados, "ya_existian": ya_existian, "errores": errores}


@frappe.whitelist(allow_guest=False)
def verify_thumbnails(names=None):
    """Verifica el contenido pixel de los PNGs generados.

    Retorna para cada patrón: background_color (pixel de esquina superior-
    izquierda), has_content (si algún pixel difiere del bg), y si es
    placeholder PIL o render real.

    Requiere Pillow. Si no está instalado retorna error descriptivo.
    """
    try:
        from PIL import Image as _Image
    except ImportError:
        return {"error": "Pillow no está instalado"}

    if isinstance(names, str):
        import json as _json
        try:
            names = _json.loads(names)
        except Exception:
            names = [n.strip() for n in names.split(",") if n.strip()]

    thumb_dir = Path(__file__).resolve().parents[1] / "public" / "pattern_thumbnails"
    resultados = []

    target = names if names else [
        p["name"]
        for p in frappe.db.get_all(
            "SI Patron",
            filters={"tipo": ["in", ["Archivo", "Vectorizado"]], "activo": 1},
            fields=["name"],
        )
    ]

    for nombre in target:
        safe = _safe_name(nombre)
        png_path = thumb_dir / f"{safe}.png"
        if not png_path.exists():
            resultados.append({"name": nombre, "estado": "sin_archivo"})
            continue

        try:
            img = _Image.open(str(png_path)).convert("RGB")
            w, h = img.size
            corner = img.getpixel((0, 0))
            center = img.getpixel((w // 2, h // 2))
            # Cuenta píxeles que difieran del color de esquina (contenido visible)
            pixels = list(img.getdata())
            diff = sum(1 for px in pixels if px != corner)
            # Placeholder PIL: fondo gris claro (220,220,220) aprox.
            is_placeholder = all(abs(c - 220) < 20 for c in corner)
            is_black_bg = all(c < 30 for c in corner)
            resultados.append({
                "name": nombre,
                "estado": "ok",
                "size": f"{w}x{h}",
                "bg_color": corner,
                "center_color": center,
                "pixels_con_contenido": diff,
                "es_placeholder": is_placeholder,
                "fondo_negro": is_black_bg,
            })
        except Exception as exc:
            resultados.append({"name": nombre, "estado": "error", "detalle": str(exc)})

    return {"resultados": resultados}


def _find_pattern_library():
    try:
        from sistema_industrial.presets.legacy_panel_adapter import find_legacy_panel_dir
        p = find_legacy_panel_dir() / "pattern_library.json"
        return p if p.exists() else None
    except Exception:
        return None


def _patron_doc_to_row(doc):
    """Convierte un dict de SI Patron en el formato de fila para get_all()."""
    name = doc.get("name", "")
    tipo = doc.get("tipo", "")
    visibilidad = doc.get("visibilidad", "Público")
    version = int(doc.get("version") or 1)

    try:
        parametros = json.loads(doc.get("parametros") or "{}")
    except (json.JSONDecodeError, TypeError):
        parametros = {}

    step_x = parametros.get("step_x")
    step_y = parametros.get("step_y")

    if tipo in ("Archivo", "Vectorizado"):
        file_path = str(doc.get("archivo_dxf") or "")
        # Frappe Attach stores URLs like /files/... or full paths; check existence via Path
        try:
            file_available = bool(file_path) and Path(file_path).exists()
        except Exception:
            file_available = False
    else:
        # Paramétrico — siempre disponible (el motor lo genera sin DXF externo)
        file_path = ""
        file_available = True

    # Thumbnail: campo Attach del doc tiene precedencia; fallback a public/pattern_thumbnails/
    thumb = doc.get("thumbnail") or _thumbnail_url(f"{_safe_name(name)}.png")

    spline_count = int(doc.get("spline_count") or 0)
    return {
        "name": name,
        "label": name,
        "file_path": file_path,
        "step_x": step_x,
        "step_y": step_y,
        "thumbnail_url": thumb,
        "file_available": file_available,
        "restricted": False,
        "restricted_reason": "",
        "tipo": tipo,
        "visibilidad": visibilidad,
        "version": version,
        "parametros": parametros,
        "has_splines": spline_count > 0,
        "spline_count": spline_count,
    }


_TIPO_ORDER = {"Paramétrico": 0, "Archivo": 1, "Vectorizado": 1}


def _sort_patron_rows(rows):
    """Ordena: Paramétrico primero, luego Archivo/Vectorizado; nombre ascendente dentro de cada grupo."""
    rows.sort(key=lambda r: (_TIPO_ORDER.get(r.get("tipo", "Archivo"), 1), r["name"]))
    return rows


def _get_all_from_frappe(customer=None):
    """Retorna lista de filas desde SI Patron, o None si el doctype está vacío."""
    try:
        total = frappe.db.count("SI Patron", {"activo": 1})
        if not total:
            return None  # trigger fallback a legacy_json

        fields = [
            "name", "tipo", "visibilidad", "cliente",
            "archivo_dxf", "parametros", "version", "thumbnail", "descripcion",
            "activo", "spline_count",
        ]

        public_rows = frappe.get_all(
            "SI Patron",
            filters={"visibilidad": "Público", "activo": 1},
            fields=fields,
        )

        exclusive_rows = []
        if customer:
            exclusive_rows = frappe.get_all(
                "SI Patron",
                filters={"visibilidad": "Exclusivo", "cliente": customer, "activo": 1},
                fields=fields,
            )

        rows = [_patron_doc_to_row(d) for d in public_rows + exclusive_rows]
        return _sort_patron_rows(rows)
    except Exception as exc:
        frappe.log_error(f"patrones.get_all: error leyendo SI Patron: {exc}")
        return None


def _get_all_from_legacy():
    """Fallback: lee pattern_library.json (igual que antes de la migración)."""
    rows = []
    lib_file = _find_pattern_library()
    if lib_file is None:
        frappe.log_error("patrones.get_all: no se encontró pattern_library.json")
        return rows

    try:
        library = json.loads(lib_file.read_text(encoding="utf-8"))
    except Exception as exc:
        frappe.log_error(f"patrones.get_all: error leyendo pattern_library.json: {exc}")
        return rows

    for name, entry in library.items():
        if entry.get("type") != "dxf":
            continue
        safe = _safe_name(name)
        file_path = str(entry.get("file_path", ""))
        try:
            file_available = bool(file_path) and Path(file_path).exists()
        except Exception:
            file_available = False

        rows.append({
            "name": name,
            "label": name,
            "file_path": file_path,
            "step_x": entry.get("step_x"),
            "step_y": entry.get("step_y"),
            "thumbnail_url": _thumbnail_url(f"{safe}.png"),
            "file_available": file_available,
            "restricted": bool(entry.get("restricted", False)),
            "restricted_reason": str(entry.get("restricted_reason", "")),
            "tipo": "Archivo",
            "visibilidad": "Público",
            "version": 1,
            "parametros": {
                "step_x": entry.get("step_x"),
                "step_y": entry.get("step_y"),
            },
        })
    return _sort_patron_rows(rows)


@frappe.whitelist(allow_guest=False)
def get_all(customer=None):
    """Lista de patrones disponibles para la galería del panel decorativo.

    customer (opcional): nombre de Customer ERPNext. Si se pasa, incluye también
        los patrones Exclusivos de ese cliente.

    r.message:
    {
        "rows": [
            {
                "name": "Subte",
                "label": "Subte",
                "file_path": "//190.190.190.9/.../subte.dxf",
                "step_x": 84.0, "step_y": 84.0,
                "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
                "file_available": false,
                "restricted": false, "restricted_reason": "",
                "tipo": "Archivo",          // "Paramétrico" para builtin
                "visibilidad": "Público",   // o "Exclusivo"
                "version": 1,
                "parametros": {"step_x": 84.0, "step_y": 84.0}
            },
            ...
        ],
        "source": "frappe"  // o "legacy_json"
    }

    Notas:
    - Patrones Paramétricos tienen file_available=true siempre (el motor los genera directo).
    - Patrones Archivo: file_available=true solo si el DXF existe en el servidor.
    - Fallback a legacy_json si SI Patron está vacío (pre-migración).
    - Compatibilidad con MSG_047 de Vega: los campos name/file_path/step_x/step_y/
      thumbnail_url/file_available/restricted/restricted_reason se mantienen intactos.
    """
    frappe_rows = _get_all_from_frappe(customer)
    if frappe_rows is not None:
        return {"rows": frappe_rows, "source": "frappe"}

    return {"rows": _get_all_from_legacy(), "source": "legacy_json"}


@frappe.whitelist(allow_guest=False)
def upload_pattern(nombre, step_x, step_y, visibilidad, file_url, customer=None, descripcion=None):
    """Crea o actualiza un SI Patron copiando el DXF desde un File de Frappe a /planos/.

    El File ya fue subido por el browser vía frappe.ui.FileUploader.

    Args:
        nombre:      Nombre del patrón (= SI Patron.name)
        step_x:      Paso horizontal en mm (float o None)
        step_y:      Paso vertical en mm (float o None)
        visibilidad: "Público" o "Exclusivo"
        file_url:    URL del File de Frappe ej. /private/files/subte.dxf
        customer:    Nombre del Customer ERPNext (requerido si visibilidad="Exclusivo")
        descripcion: Descripción libre

    r.message: {ok: true, name, version}
    """
    if visibilidad == "Exclusivo" and not customer:
        frappe.throw("customer es requerido para visibilidad Exclusivo")

    src_path = _resolve_frappe_file(file_url)

    dest_dir = _patron_dest_dir(visibilidad, customer)
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe = _safe_filename(src_path.name)

    if frappe.db.exists("SI Patron", nombre):
        existing = frappe.get_doc("SI Patron", nombre)
        next_v = int(existing.version or 1) + 1
        stem, ext = os.path.splitext(safe)
        safe = f"{stem}_v{next_v}{ext}"

    dest_path = dest_dir / safe
    shutil.copy2(str(src_path), str(dest_path))

    sc = _count_splines(dest_path)

    parametros = json.dumps({
        "step_x": float(step_x) if step_x not in (None, "") else None,
        "step_y": float(step_y) if step_y not in (None, "") else None,
    }, ensure_ascii=False)

    if frappe.db.exists("SI Patron", nombre):
        doc = frappe.get_doc("SI Patron", nombre)
        doc.archivo_dxf = str(dest_path)
        doc.visibilidad = visibilidad
        doc.cliente = customer if visibilidad == "Exclusivo" else ""
        if descripcion:
            doc.descripcion = descripcion
        doc.parametros = parametros
        doc.activo = 1
        doc.spline_count = sc
        doc.save(ignore_permissions=True)
    else:
        payload = {
            "doctype": "SI Patron",
            "name": nombre,
            "tipo": "Archivo",
            "visibilidad": visibilidad,
            "descripcion": descripcion or "",
            "archivo_dxf": str(dest_path),
            "parametros": parametros,
            "activo": 1,
            "spline_count": sc,
        }
        if visibilidad == "Exclusivo" and customer:
            payload["cliente"] = customer
        doc = frappe.get_doc(payload)
        doc.insert(ignore_permissions=True)

    frappe.db.commit()

    _generate_and_save_thumbnail(
        nombre, dest_path,
        step_x=float(step_x) if step_x not in (None, "") else None,
        step_y=float(step_y) if step_y not in (None, "") else None,
    )

    return {
        "ok": True,
        "name": nombre,
        "version": int(doc.version or 1),
        "has_splines": sc > 0,
        "spline_count": sc,
    }


@frappe.whitelist(allow_guest=False)
def delete_pattern(name):
    """Baja lógica: pone activo=0 en el SI Patron. El archivo DXF queda en disco.

    r.message: {ok: true, name: "Subte"}
    Error: frappe.DoesNotExistError si el patrón no existe.
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón '{name}' no encontrado", frappe.DoesNotExistError)
    doc = frappe.get_doc("SI Patron", name)
    doc.activo = 0
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True, "name": name}


@frappe.whitelist(allow_guest=False)
def convert_splines(name):
    """Convierte splines a arcos en el DXF del patrón y guarda como nueva versión.

    Usa el conversor curado tools/dxf_spline_to_arcs.py (TASK_022 + fix puntas).
    El archivo original queda congelado en el historial (constraint de versionado).

    r.message:
    {
        "ok": true, "name": "Subte", "version": 2,
        "splines_convertidas": 12, "arcos_generados": 47, "lineas_generadas": 15
    }
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón '{name}' no encontrado", frappe.DoesNotExistError)

    doc = frappe.get_doc("SI Patron", name)
    src_path = Path(doc.archivo_dxf or "")
    if not src_path.exists():
        frappe.throw(f"Archivo DXF no disponible en disco: {doc.archivo_dxf}")

    next_v = int(doc.version or 1) + 1
    dest_path = src_path.parent / f"{src_path.stem}_v{next_v}{src_path.suffix}"

    from sistema_industrial.presets.panel_sales_local_app import convert_dxf_splines_clean
    stats = convert_dxf_splines_clean(str(src_path), str(dest_path), tolerance=0.1)

    doc.archivo_dxf = str(dest_path)
    doc.spline_count = 0  # convertidas: ya no hay splines
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "ok": True,
        "name": name,
        "version": int(doc.version or 1),
        "splines_convertidas": stats.get("converted_count", 0),
        "arcos_generados": stats.get("arc_count", 0),
        "lineas_generadas": stats.get("line_count", 0),
    }


@frappe.whitelist(allow_guest=False)
def list_admin():
    """Lista TODOS los SI Patron (activos e inactivos) para la página de administración.

    A diferencia de get_all(), no filtra por activo ni por customer.

    r.message:
    {
        "rows": [
            {
                "name", "tipo", "visibilidad", "cliente",
                "thumbnail_url", "file_available", "version", "activo",
                "has_splines", "spline_count"
            },
            ...
        ]
    }
    """
    fields = [
        "name", "tipo", "visibilidad", "cliente",
        "archivo_dxf", "parametros", "version", "thumbnail", "descripcion",
        "activo", "spline_count",
    ]
    docs = frappe.get_all("SI Patron", fields=fields, order_by="name asc")
    rows = []
    for d in docs:
        row = _patron_doc_to_row(d)
        row["cliente"] = d.get("cliente") or ""
        row["activo"] = int(d.get("activo") or 0)
        rows.append(row)
    return {"rows": _sort_patron_rows(rows)}


@frappe.whitelist(allow_guest=False)
def get_patron(name, version=None):
    """Resolver versionado — contrato con SI Pieza / Lechu.

    Dados (name, version), devuelve los parámetros exactos del patrón en ese momento,
    incluso si el patrón fue editado después. Garantía de reproducibilidad permanente.

    Args:
        name:    nombre del SI Patron (e.g. "Subte", "Tresbolillo")
        version: int o None. None → versión vigente. N → versión congelada N.

    r.message:
    {
        "name": "Subte",
        "version": 1,
        "tipo": "Archivo",
        "visibilidad": "Público",
        "parametros": {"step_x": 84.0, "step_y": 84.0},
        "archivo_dxf_url": "",          // URL/path del DXF; vacío para Paramétrico
        "file_available": false,
        "thumbnail_url": "/assets/sistema_industrial/pattern_thumbnails/Subte.png",
        "descripcion": ""
    }

    Error: frappe.DoesNotExistError si el patron o la versión no existen.
    """
    if not frappe.db.exists("SI Patron", name):
        frappe.throw(f"Patrón no encontrado: {name}", frappe.DoesNotExistError)

    doc = frappe.get_doc("SI Patron", name)

    if version is None:
        # Versión vigente — datos del master
        parametros_str = doc.parametros or "{}"
        archivo_dxf = doc.archivo_dxf or ""
        version_num = int(doc.version or 1)
    else:
        version_num = int(version)
        row = next(
            (r for r in doc.versiones if int(r.version_num or 0) == version_num),
            None,
        )
        if row is None:
            frappe.throw(
                f"Versión {version_num} no encontrada para patrón '{name}'",
                frappe.DoesNotExistError,
            )
        parametros_str = row.parametros_frozen or "{}"
        archivo_dxf = row.archivo_dxf_frozen or ""

    try:
        parametros = json.loads(parametros_str)
    except (json.JSONDecodeError, TypeError):
        parametros = {}

    try:
        file_available = bool(archivo_dxf) and Path(archivo_dxf).exists()
    except Exception:
        file_available = False

    thumb = doc.thumbnail or _thumbnail_url(f"{_safe_name(name)}.png")

    return {
        "name": name,
        "version": version_num,
        "tipo": doc.tipo or "",
        "visibilidad": doc.visibilidad or "Público",
        "parametros": parametros,
        "archivo_dxf_url": archivo_dxf,
        "file_available": file_available,
        "thumbnail_url": thumb,
        "descripcion": doc.descripcion or "",
    }
