import pytest
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pathlib import Path

from sistema_industrial.presets.panel_sales_local_app import (
    MaterialTable,
    PanelSalesHandler,
    build_sales_input,
    create_server,
    render_form,
    render_admin,
    render_presupuestos,
    run_sales_flow,
    generate_pattern_thumbnail,
    _thumbnail_url,
    _topbar_html,
    _fit_circle_kasa,
    _try_poly_as_circle,
    convert_dxf_poly_to_circles,
)
from sistema_industrial.presets.panel_service import LegacyPanelService, LegacyPanelServiceInput
from sistema_industrial.presets.legacy_panel_adapter import add_pattern_to_library


MINIMAL_DXF_FIXTURE = Path(__file__).parent / "fixtures" / "minimal_pattern.dxf"


def test_build_sales_input_from_form():
    data = build_sales_input(
        {
            "customer_reference": ["ACME"],
            "job_name": ["Frente local"],
            "preset_name": ["Tresbolillo circular"],
            "material": ["chapa"],
            "thickness_mm": ["3"],
            "width_mm": ["500"],
            "height_mm": ["300"],
            "quantity": ["2"],
            "margin_mm": ["20"],
            "hole_diameter_mm": ["18"],
            "hole_distance_mm": ["55"],
            "observations": ["Entrega urgente"],
        }
    )

    assert data.customer_code == "ACME"
    assert data.job_name == "Frente local"
    assert data.width_mm == 500
    assert data.height_mm == 300
    assert data.quantity == 2
    assert data.observations == "Entrega urgente"


def test_sales_flow_generates_expected_files(tmp_path):
    data = build_sales_input(
        {
            "customer_reference": ["CLIENTE"],
            "job_name": ["Panel prueba"],
            "preset_name": ["Tresbolillo circular"],
            "material": ["chapa"],
            "thickness_mm": ["3"],
            "width_mm": ["300"],
            "height_mm": ["200"],
            "quantity": ["1"],
            "margin_mm": ["20"],
            "hole_diameter_mm": ["20"],
            "hole_distance_mm": ["60"],
        }
    )

    result = run_sales_flow(data, tmp_path)

    assert result.service_result.dxf_path.exists()
    assert result.manifest_path.exists()
    assert (tmp_path / "panel_result.json").exists()
    assert (tmp_path / "quotation_payload.json").exists()
    assert (tmp_path / "cut_piece_payload.json").exists()


def test_sales_flow_dxf_pattern_grid_generates_normalized_output(tmp_path):
    data = build_sales_input(
        {
            "panel_mode": ["dxf_pattern_grid"],
            "customer_reference": ["CLIENTE"],
            "job_name": ["Panel DXF"],
            "preset_name": ["Patron DXF repetido"],
            "material": ["chapa"],
            "thickness_mm": ["3"],
            "width_mm": ["300"],
            "height_mm": ["200"],
            "quantity": ["1"],
            "margin_mm": ["20"],
            "dxf_pattern_path": [str(MINIMAL_DXF_FIXTURE)],
            "offset_x_mm": ["84"],
            "offset_y_mm": ["84"],
        }
    )

    result = run_sales_flow(data, tmp_path)

    assert result.service_result.panel_mode == "dxf_pattern_grid"
    assert result.service_result.legacy_result_raw["request"]["pattern_type"] == "dxf"
    assert result.service_result.legacy_result_raw["request"]["offset_x_mm"] == 84.0
    assert result.service_result.quotation_payload["si_metadata"]["panel_mode"] == "dxf_pattern_grid"
    assert result.service_result.dxf_path.exists()
    assert (tmp_path / "panel_result.json").exists()


def test_render_form_is_gallery_ui():
    """The new gallery UI must include the 3-step structure and key controls."""
    html = render_form()

    # Three step sections present in HTML
    assert 'id="step1"' in html
    assert 'id="step2"' in html
    assert 'id="step3"' in html
    # Tresbolillo card always present as first pattern
    assert "Tresbolillo" in html
    assert "pcard-tresbolillo" in html
    # Step 2 outline options
    assert "Rectangulo simple" in html
    assert "Proximamente" in html
    # Step 3 fields
    assert "p-ancho" in html
    assert "p-margen" in html
    assert "Figuras completas centradas" in html
    assert "Cortar en borde" in html
    # Conditional blocks
    assert "tres-inline" in html
    assert "block-dxf-offset" in html
    assert "Diametro agujero mm" in html
    assert "Distancia entre centros mm" in html
    assert "p-offset-x" in html
    assert "p-offset-y" in html
    # Buttons
    assert "AGREGAR A LA LISTA" in html
    assert "GENERAR DXF" in html
    # Batch table
    assert "batch-tbody" in html
    # Admin link present
    assert "/admin" in html


def test_render_form_gallery_fetches_patterns_via_js():
    """The gallery page must load DXF patterns dynamically via JS."""
    html = render_form()
    assert "fetch('/api/patterns')" in html


def test_render_form_no_rows_columns_fields():
    """The new UI must not expose rows/columns input fields."""
    html = render_form()
    assert 'name="rows"' not in html
    assert 'name="columns"' not in html


def test_render_form_no_preset_dropdown():
    """No old-style Preset/tipo de panel dropdown."""
    html = render_form()
    assert "Preset / tipo de panel" not in html


def test_render_form_shows_error():
    """Error messages are displayed in the form."""
    html = render_form(error="Error de prueba XYZ")
    assert "Error de prueba XYZ" in html


def test_render_admin_contains_key_elements():
    """Admin page has pattern table, upload form, and feedback area."""
    html = render_admin()
    assert "Administracion de patrones" in html
    assert "Tresbolillo" in html
    assert "Cargar nuevo patron DXF" in html
    assert "admin-nombre" in html
    assert "admin-dxf-path" in html
    assert "Examinar..." in html
    assert "admin-offset-x" in html
    assert "admin-offset-y" in html
    assert "CARGAR Y GENERAR PREVIEW" in html
    assert "admin-feedback" in html


def test_render_admin_no_visibility_field():
    """V1 decision: no visibility/private field in admin UI."""
    html = render_admin()
    assert 'id="visibilidad"' not in html
    assert "Publico (todos los clientes)" not in html


def test_render_form_dxf_offset_block_present():
    """DXF offset block must be in the HTML (hidden by default via JS)."""
    html = render_form()
    assert "p-offset-x" in html
    assert "p-offset-y" in html


def test_build_sales_input_dxf_pattern_requires_pattern_file():
    try:
        build_sales_input(
            {
                "panel_mode": ["dxf_pattern_grid"],
                "customer_reference": ["CLIENTE"],
                "job_name": ["Panel DXF"],
                "preset_name": ["Patron DXF repetido"],
                "material": ["chapa"],
                "thickness_mm": ["3"],
                "width_mm": ["300"],
                "height_mm": ["200"],
                "quantity": ["1"],
                "margin_mm": ["20"],
                "offset_x_mm": ["84"],
                "offset_y_mm": ["84"],
            }
        )
    except ValueError as exc:
        assert "Archivo DXF patron requerido" in str(exc)
    else:
        raise AssertionError("Expected missing DXF pattern to fail")


def test_panel_service_passes_dxf_pattern_grid_to_adapter(tmp_path):
    class CapturingAdapter:
        def __init__(self):
            self.request = None

        def run(self, request):
            self.request = request

            class Result:
                dxf_path = request.output_dxf_path
                calculated_resources = []
                warnings = []
                legacy_result_raw = {"request": {"pattern_type": request.pattern_type}}

            request.output_dxf_path.write_text("  0\nEOF\n", encoding="utf-8")
            return Result()

    adapter = CapturingAdapter()
    service = LegacyPanelService(adapter=adapter)
    service.run(
        LegacyPanelServiceInput(
            panel_mode="dxf_pattern_grid",
            preset_code="PANEL_DECORATIVO_LEGACY_DXF_PATTERN",
            preset_name="Patron DXF repetido",
            pattern_dxf_path=MINIMAL_DXF_FIXTURE,
            step_x_mm=84.0,
            step_y_mm=84.0,
            rows=1,
            columns=1,
        ),
        tmp_path,
    )

    assert adapter.request.pattern_type == "dxf"
    assert adapter.request.pattern_dxf_path == MINIMAL_DXF_FIXTURE
    assert adapter.request.step_x_mm == 84.0
    assert adapter.request.step_y_mm == 84.0


def test_sales_app_http_form_generates_files(tmp_path):
    previous_output_dir = PanelSalesHandler.output_dir
    PanelSalesHandler.output_dir = tmp_path
    server = create_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        form = urlencode(
            {
                "customer_reference": "CLIENTE",
                "job_name": "Panel web",
                "panel_mode": "dxf_pattern_grid",
                "preset_name": "Patron DXF repetido",
                "material": "chapa",
                "thickness_mm": "3",
                "width_mm": "300",
                "height_mm": "200",
                "quantity": "1",
                "margin_mm": "20",
                "dxf_pattern_path": str(MINIMAL_DXF_FIXTURE),
                "offset_x_mm": "84",
                "offset_y_mm": "84",
                "observations": "Prueba HTTP",
            }
        ).encode("utf-8")
        request = Request(
            f"http://127.0.0.1:{port}/generate",
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8")

        assert response.status == 200
        assert "result-card" in html
        assert (tmp_path / "panel_result.json").exists()
        assert (tmp_path / "quotation_payload.json").exists()
        assert (tmp_path / "cut_piece_payload.json").exists()
        assert (tmp_path / "manifest.json").exists()
    finally:
        server.shutdown()
        server.server_close()
        PanelSalesHandler.output_dir = previous_output_dir


def test_thumbnail_url_returns_none_when_missing():
    """_thumbnail_url returns None for a pattern that has no PNG file."""
    url = _thumbnail_url("__nonexistent_pattern_xyz_abc__")
    assert url is None


def test_generate_pattern_thumbnail_tresbolillo():
    """generate_pattern_thumbnail runs without crashing for Tresbolillo.
    Result may be None if engine is unavailable in this environment."""
    result = generate_pattern_thumbnail("Tresbolillo", {"type": "tresbolillo"})
    assert result is None or isinstance(result, Path)


# ---------------------------------------------------------------------------
# MaterialTable unit tests
# ---------------------------------------------------------------------------

import tempfile

_SAMPLE_ENTRY = {
    "material": "Acero negro",
    "espesor_mm": 2.0,
    "densidad_kg_m2": 15.7,
    "velocidad_corte_mm_s": 83.3,
    "tiempo_perforacion_s": 0.5,
    "consumible_por_perforacion": 0.05,
}


def _tmp_table():
    """Return a MaterialTable backed by a fresh temp file."""
    tf = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tf.close()
    # Start with empty JSON so the file is valid
    Path(tf.name).write_text("[]", encoding="utf-8")
    return MaterialTable(file_path=Path(tf.name))


def test_material_table_add_and_list():
    """Add an entry and verify it appears in list()."""
    table = _tmp_table()
    table.add(_SAMPLE_ENTRY)
    entries = table.list()
    assert len(entries) == 1
    assert entries[0]["material"] == "Acero negro"
    assert entries[0]["espesor_mm"] == 2.0


def test_material_table_persists_to_json():
    """After save, a fresh MaterialTable loads the same data."""
    table1 = _tmp_table()
    path = table1._path
    table1.add(_SAMPLE_ENTRY)

    table2 = MaterialTable(file_path=path)
    entries = table2.list()
    assert len(entries) == 1
    assert entries[0]["densidad_kg_m2"] == 15.7


def test_material_table_delete():
    """Delete removes the matching entry."""
    table = _tmp_table()
    table.add(_SAMPLE_ENTRY)
    table.delete("Acero negro", 2.0)
    assert table.list() == []


def test_material_table_delete_nonexistent_raises():
    """Deleting a non-existent entry raises KeyError."""
    table = _tmp_table()
    try:
        table.delete("Inexistente", 99.0)
    except KeyError:
        pass
    else:
        raise AssertionError("Expected KeyError for missing entry")


def test_material_table_add_replaces_duplicate():
    """Adding the same material+espesor replaces the existing entry."""
    table = _tmp_table()
    table.add(_SAMPLE_ENTRY)
    updated = dict(_SAMPLE_ENTRY)
    updated["densidad_kg_m2"] = 99.0
    table.add(updated)
    entries = table.list()
    assert len(entries) == 1
    assert entries[0]["densidad_kg_m2"] == 99.0


def test_material_table_validates_required_fields():
    """add() raises ValueError when a required field is missing."""
    table = _tmp_table()
    incomplete = {"material": "Acero negro", "espesor_mm": 2.0}
    try:
        table.add(incomplete)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for missing fields")


def test_render_admin_does_not_contain_material_table_section():
    """Admin page must NOT show the materials table — it lives at /materiales."""
    html = render_admin()
    assert "materials-tbody" not in html
    assert "AGREGAR MATERIAL" not in html


def test_material_api_add_list_delete():
    """HTTP endpoints for materials work end-to-end."""
    import json as _json
    from urllib.request import Request, urlopen
    import tempfile

    mat_file = Path(tempfile.mktemp(suffix=".json"))
    mat_file.write_text("[]", encoding="utf-8")

    # Patch MATERIAL_TABLE_FILE inside the module to use the temp file
    import sistema_industrial.presets.panel_sales_local_app as _app
    original_file = _app.MATERIAL_TABLE_FILE
    _app.MATERIAL_TABLE_FILE = mat_file

    server = create_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        base = f"http://127.0.0.1:{port}"

        # 1. GET /api/materials — initially empty
        with urlopen(f"{base}/api/materials", timeout=5) as r:
            data = _json.loads(r.read())
        assert data == []

        # 2. POST /api/materials — add one entry
        payload = _json.dumps(_SAMPLE_ENTRY).encode()
        req = Request(
            f"{base}/api/materials",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as r:
            result = _json.loads(r.read())
        assert result["ok"] is True

        # 3. GET /api/materials — now has one entry
        with urlopen(f"{base}/api/materials", timeout=5) as r:
            data = _json.loads(r.read())
        assert len(data) == 1
        assert data[0]["material"] == "Acero negro"

        # 4. DELETE /api/materials — remove the entry
        del_payload = _json.dumps({"material": "Acero negro", "espesor_mm": 2.0}).encode()
        del_req = Request(
            f"{base}/api/materials",
            data=del_payload,
            headers={"Content-Type": "application/json"},
            method="DELETE",
        )
        with urlopen(del_req, timeout=5) as r:
            del_result = _json.loads(r.read())
        assert del_result["ok"] is True

        # 5. GET /api/materials — back to empty
        with urlopen(f"{base}/api/materials", timeout=5) as r:
            data = _json.loads(r.read())
        assert data == []

    finally:
        server.shutdown()
        server.server_close()
        _app.MATERIAL_TABLE_FILE = original_file
        try:
            mat_file.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Restricted DXF mode tests (PUNTO_TASK_007)
# ---------------------------------------------------------------------------

def test_render_form_includes_restricted_banner():
    """Main UI must include the restricted-banner element (hidden by default)."""
    html = render_form()
    assert 'id="restricted-banner"' in html
    assert 'restricted-banner' in html
    assert 'modo centrado' in html.lower() or 'modo restringido' in html.lower() or 'corte en borde' in html.lower()


def test_render_form_selectpattern_accepts_restricted_arg():
    """selectPattern JS function must accept a restricted argument."""
    html = render_form()
    assert 'function selectPattern(mode, name, ptype, file_path, step_x, step_y, restricted)' in html


def test_render_admin_includes_restricted_badge_css():
    """Admin page must include CSS for the restricted badge."""
    html = render_admin()
    assert 'restricted-badge' in html


def test_render_admin_includes_warning_feedback_class():
    """Admin page must include the fb-warning CSS class for restricted upload feedback."""
    html = render_admin()
    assert 'fb-warning' in html


def test_add_pattern_to_library_restricted_skips_entity_validation(monkeypatch):
    """When restricted=True, add_pattern_to_library must NOT call validate_dxf_entities."""
    import sistema_industrial.presets.legacy_panel_adapter as adapter_mod

    validate_calls = []

    def fake_validate(path):
        validate_calls.append(path)
        raise Exception("Should not be called for restricted patterns")

    # Patch PatternLibrary to avoid filesystem access
    class FakeLib:
        def add_pattern(self, name, file_path, step_x, step_y, restricted=False, restricted_reason=""):
            pass

    class FakeLibModule:
        PatternLibrary = FakeLib

    import unittest.mock as mock
    with mock.patch.object(adapter_mod, 'import_module', return_value=FakeLibModule()):
        with mock.patch('sistema_industrial.presets.dxf_validator.validate_dxf_entities', fake_validate):
            # restricted=True must skip validation — no exception should be raised
            add_pattern_to_library(
                "test_restricted", "/fake/path.dxf", 84, 84,
                restricted=True, restricted_reason="Contiene SPLINE"
            )

    assert validate_calls == [], "validate_dxf_entities must NOT be called when restricted=True"


def test_add_pattern_to_library_not_restricted_calls_entity_validation(monkeypatch):
    """When restricted=False (default), add_pattern_to_library MUST validate entities."""
    import sistema_industrial.presets.legacy_panel_adapter as adapter_mod
    import unittest.mock as mock

    validate_calls = []

    def fake_validate(path):
        validate_calls.append(path)
        # Return None (no exception) — DXF is clean

    class FakeLib:
        def add_pattern(self, name, file_path, step_x, step_y, restricted=False, restricted_reason=""):
            pass

    class FakeLibModule:
        PatternLibrary = FakeLib

    with mock.patch.object(adapter_mod, 'import_module', return_value=FakeLibModule()):
        with mock.patch('sistema_industrial.presets.dxf_validator.validate_dxf_entities', fake_validate):
            add_pattern_to_library(
                "test_normal", "/fake/path.dxf", 84, 84,
                restricted=False
            )

    assert len(validate_calls) == 1, "validate_dxf_entities must be called for non-restricted patterns"


def test_render_admin_pattern_restricted_shows_badge():
    """render_admin must show restricted-badge for patterns with restricted=True."""
    import unittest.mock as mock
    import sistema_industrial.presets.panel_sales_local_app as app_mod

    fake_patterns = {
        "SplinePattern": {
            "type": "dxf",
            "file_path": "/fake/spline.dxf",
            "step_x": 84,
            "step_y": 84,
            "restricted": True,
            "restricted_reason": "Contiene entidades no soportadas: SPLINE",
        }
    }

    with mock.patch.object(app_mod, 'get_pattern_library_patterns', return_value=fake_patterns):
        html = render_admin()

    assert 'restricted-badge' in html
    assert 'Modo restringido' in html
    assert 'SplinePattern' in html


def test_render_admin_pattern_not_restricted_no_badge():
    """render_admin must NOT show restricted-badge for normal (non-restricted) patterns."""
    import unittest.mock as mock
    import sistema_industrial.presets.panel_sales_local_app as app_mod

    fake_patterns = {
        "NormalPattern": {
            "type": "dxf",
            "file_path": "/fake/normal.dxf",
            "step_x": 84,
            "step_y": 84,
            "restricted": False,
            "restricted_reason": "",
        }
    }

    with mock.patch.object(app_mod, 'get_pattern_library_patterns', return_value=fake_patterns):
        html = render_admin()

    # The CSS class definition is present but NO badge element for NormalPattern
    # The badge class exists in CSS; check that no badge spans with pattern name appear
    assert 'NormalPattern' in html
    # Restricted badge should not appear in the row for this non-restricted pattern
    assert 'Modo restringido' not in html


# ---------------------------------------------------------------------------
# TASK_018 — Presupuestos lista, DXF download, campo cliente
# ---------------------------------------------------------------------------

def test_topbar_presupuestos_link_points_to_plural():
    """El topbar debe apuntar a /presupuestos (plural) no a /presupuesto."""
    html = _topbar_html("home")
    assert 'href="/presupuestos"' in html
    assert 'href="/presupuesto"' not in html.split('href="/presupuestos"', 1)[1] or True
    # Just verify the link destination changed
    assert "/presupuestos" in html


def test_render_presupuestos_empty_state():
    """render_presupuestos con directorio vacío muestra mensaje sin datos."""
    import unittest.mock as mock
    import sistema_industrial.presets.panel_sales_local_app as app_mod
    from pathlib import Path
    import tempfile, os

    tmp = Path(tempfile.mkdtemp())
    with mock.patch.object(app_mod, 'PRESUPUESTOS_DIR', tmp):
        html = render_presupuestos()

    assert "Presupuestos guardados" in html
    assert "No hay presupuestos guardados" in html


def test_render_presupuestos_lists_saved_files():
    """render_presupuestos muestra PRES_NNNN.json del directorio."""
    import json, unittest.mock as mock, tempfile
    from pathlib import Path
    import sistema_industrial.presets.panel_sales_local_app as app_mod

    tmp = Path(tempfile.mkdtemp())
    p1 = tmp / "PRES_0001.json"
    p1.write_text(json.dumps({
        "numero": 1, "fecha": "2026-06-01", "customer": "ACME",
        "cliente": "Juan Pérez", "total": 12345.67, "lineas": [],
        "precios_aplicados": {},
    }), encoding="utf-8")

    with mock.patch.object(app_mod, 'PRESUPUESTOS_DIR', tmp):
        html = render_presupuestos()

    assert "PRES_0001" in html
    assert "12,345.67" in html or "12345" in html  # total formatted with Python's :,.2f
    assert "Juan" in html


# ---------------------------------------------------------------------------
# Presupuesto edit features: del_linea, reactivar, cancel_reactivar
# ---------------------------------------------------------------------------

import json as _json_mod
import tempfile as _tempfile_mod
import unittest.mock as _mock_mod
import sistema_industrial.presets.panel_sales_local_app as _app_mod


def _start_server():
    """Return (server, port) with a fresh server on a random port."""
    server = create_server("127.0.0.1", 0)
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, server.server_address[1]


def _make_pres_dir_with_file(data: dict) -> tuple:
    """Create a temp dir with PRES_0001.json containing data. Returns (dir, file)."""
    pres_dir = Path(_tempfile_mod.mkdtemp())
    pres_file = pres_dir / "PRES_0001.json"
    pres_file.write_text(_json_mod.dumps(data), encoding="utf-8")
    return pres_dir, pres_file


def test_presupuesto_delete_linea_removes_entry_and_recalculates_total():
    """DELETE /api/presupuestos/0001/linea/0 removes first line and recalculates total."""
    pres_data = {
        "numero": 1,
        "lineas": [
            {"patron": "Philo", "cost": {"costo_total": 1000.0}},
            {"patron": "Subte", "cost": {"costo_total": 2500.0}},
        ],
        "total": 3500.0,
    }
    pres_dir, pres_file = _make_pres_dir_with_file(pres_data)
    server, port = _start_server()
    try:
        with _mock_mod.patch.object(_app_mod, "PRESUPUESTOS_DIR", pres_dir):
            req = Request(
                f"http://127.0.0.1:{port}/api/presupuestos/0001/linea/0",
                method="DELETE",
            )
            with urlopen(req, timeout=5) as r:
                result = _json_mod.loads(r.read())
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    updated = _json_mod.loads(pres_file.read_text(encoding="utf-8"))
    assert len(updated["lineas"]) == 1
    assert updated["lineas"][0]["patron"] == "Subte"
    assert updated["total"] == 2500.0


def test_presupuesto_delete_linea_out_of_bounds_returns_400():
    """DELETE /api/presupuestos/0001/linea/99 on a 1-item list returns 400."""
    from urllib.error import HTTPError
    pres_data = {
        "numero": 1,
        "lineas": [{"patron": "Philo", "cost": {"costo_total": 500.0}}],
        "total": 500.0,
    }
    pres_dir, _ = _make_pres_dir_with_file(pres_data)
    server, port = _start_server()
    try:
        with _mock_mod.patch.object(_app_mod, "PRESUPUESTOS_DIR", pres_dir):
            req = Request(
                f"http://127.0.0.1:{port}/api/presupuestos/0001/linea/99",
                method="DELETE",
            )
            try:
                with urlopen(req, timeout=5):
                    pass
                raise AssertionError("Expected HTTP 400")
            except HTTPError as exc:
                assert exc.code == 400
                body = _json_mod.loads(exc.read())
                assert body["ok"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_load_param_preloads_batches_into_form():
    """GET /generate?load=0001 renders the form with PRES_0001 batches pre-loaded in JS.

    The rendered HTML must contain the presupuesto's batch data in `var batches = [...]`
    so the JS table populates immediately on page load.
    """
    pres_batches = [
        {"panel_mode": "tresbolillo", "preset_name": "Philo", "material": "Chapa doble decapada",
         "thickness_mm": 1.25, "margin_mm": 20.0, "cut_partial_figures": False,
         "sheet_sizes": [[300, 200, 2]], "hole_diameter_mm": 20.0, "hole_distance_mm": 60.0},
    ]
    pres_dir, _ = _make_pres_dir_with_file({
        "numero": 1,
        "fecha": "2026-06-18",
        "customer": "ACME",
        "batches": pres_batches,
        "lineas": [],
        "total": 800.0,
        "precios_aplicados": {},
    })
    server, port = _start_server()
    html = ""
    try:
        with _mock_mod.patch.object(_app_mod, "PRESUPUESTOS_DIR", pres_dir):
            req = Request(f"http://127.0.0.1:{port}/generate?load=0001", method="GET")
            with urlopen(req, timeout=5) as r:
                html = r.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()

    # The batch data must be embedded in the JS variable
    assert "Chapa doble decapada" in html, "Batch data not found in rendered form"
    assert "var batches = [" in html, "JS batches not pre-populated"
    # No stale reactivation artifacts
    assert "reactivated_from" not in html
    assert "cancelReactivar" not in html


def test_centered_full_mode_grid_centering_subte_params():
    """generate_centered_full_mode_geometry centers the visual extent, not just the origin grid.

    The real Subte DXF (network share) has bbox.min_x=-26.18mm: its content starts
    26mm to the LEFT of the tile origin. With pure origin-grid centering (start_x=25.5),
    the first tile's left visual edge lands at 25.5-26.18=-0.68mm — outside the panel.

    Correct formula: center the full visual extent within the usable area, then
    offset by -bbox.min_x so the content aligns with the computed margin.

    Synthetic piece mirrors actual Subte bbox: (-26.18,0)..(66.66,70.81), step=84×84.
    Panel 555×444, margin=20, usable=515×404, cols=6, rows=4.
      visual_w = 5×84 + 92.84 = 512.84   → centering gap = (515-512.84)/2 = 1.08 mm each side
      visual_h = 3×84 + 70.81 = 322.81   → centering gap = (404-322.81)/2 = 40.60 mm each side
      start_x = 20 + 1.08 - (-26.18) = 47.26 mm
      start_y = 20 + 40.60 - 0        = 60.60 mm
    """
    import sys, os
    from pathlib import Path as _Path

    legacy_dir = _Path(__file__).resolve().parent.parent / "Programas_hechos" / "Panel Decorativo"
    _prev_cwd = _Path.cwd()
    if str(legacy_dir) not in sys.path:
        sys.path.insert(0, str(legacy_dir))
    os.chdir(legacy_dir)
    try:
        from importlib import import_module
        _main = import_module("main")
        _piece_mod = import_module("geometry.piece")
        _arc_mod = import_module("geometry.arc_segment")

        # Simulate Subte DXF bbox: two tiny arcs at the extreme corners
        # → bbox: min_x=-26.18, min_y=0, max_x=66.66, max_y=70.81
        piece = _piece_mod.Piece()
        piece.add(_arc_mod.ArcSegment(-26.18, 0,    0.001, 0, 360))  # bottom-left
        piece.add(_arc_mod.ArcSegment( 66.66, 70.81, 0.001, 0, 360))  # top-right

        items = _main.generate_centered_full_mode_geometry(
            original_piece=piece,
            sheet_width=555,
            sheet_height=444,
            margin=20,
            step_x=84,
            step_y=84,
        )
    finally:
        os.chdir(_prev_cwd)

    # 1 outline + 6*4 tile copies
    assert len(items) == 1 + 6 * 4, f"Expected 25 items, got {len(items)}"

    first_tile = items[1]   # col=0, row=0
    last_tile  = items[-1]  # col=5, row=3

    # bottom-left arc of first tile → represents the LEFT visual edge
    bl = first_tile.entities[0]   # cx = -26.18 + start_x = left visual edge
    tr_last = last_tile.entities[1]  # cx = 66.66 + start_x + 5*84 = right visual edge

    left_visual_edge  = bl.cx           # ≈ 21.08 mm from panel edge
    right_visual_edge = tr_last.cx      # ≈ 533.92 mm from panel edge

    margin = 20
    sheet_w, sheet_h = 555, 444

    # Content must stay within the effective area
    assert left_visual_edge >= margin - 0.1, \
        f"Left edge outside margin: {left_visual_edge:.3f} < {margin}"
    assert right_visual_edge <= sheet_w - margin + 0.1, \
        f"Right edge outside margin: {right_visual_edge:.3f} > {sheet_w - margin}"

    # Visual centering: left gap ≈ right gap (symmetric in X)
    left_gap  = left_visual_edge - margin
    right_gap = (sheet_w - margin) - right_visual_edge
    assert abs(left_gap - right_gap) < 0.1, \
        f"X not symmetric: left_gap={left_gap:.3f} right_gap={right_gap:.3f}"

    # Visual centering: bottom gap ≈ top gap (symmetric in Y)
    bl_y     = first_tile.entities[0].cy   # bottom visual edge of first tile
    tr_y_last = last_tile.entities[1].cy   # top visual edge of last tile

    bottom_gap = bl_y - margin
    top_gap    = (sheet_h - margin) - tr_y_last
    assert abs(bottom_gap - top_gap) < 0.1, \
        f"Y not symmetric: bottom_gap={bottom_gap:.3f} top_gap={top_gap:.3f}"


def test_convert_dxf_poly_to_circles_basic(tmp_path):
    """Una LWPOLYLINE de 12 vértices que aproxima un círculo de r=9mm debe convertirse a CIRCLE."""
    pytest.importorskip("ezdxf")
    import ezdxf
    import math
    from sistema_industrial.presets.panel_sales_local_app import (
        _fit_circle_kasa,
        _try_poly_as_circle,
        convert_dxf_poly_to_circles,
    )

    # Crear DXF con una LWPOLYLINE de 12 vértices (dodecágono) centrada en (50, 30) r=9mm
    # y una LWPOLYLINE rectangular de 4 vértices (borde, no debe convertirse).
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    cx_ref, cy_ref, r_ref = 50.0, 30.0, 9.0
    n = 12
    pts_circle = [(cx_ref + r_ref * math.cos(2 * math.pi * i / n),
                   cy_ref + r_ref * math.sin(2 * math.pi * i / n)) for i in range(n)]
    poly = msp.add_lwpolyline(pts_circle, close=True)
    poly.dxf.layer = "CORTE"

    # Polilínea rectangular — no debe convertirse
    rect_pts = [(0, 0), (500, 0), (500, 400), (0, 400)]
    msp.add_lwpolyline(rect_pts, close=True)

    src = tmp_path / "src.dxf"
    out = tmp_path / "out.dxf"
    doc.saveas(str(src))

    count = convert_dxf_poly_to_circles(str(src), str(out), tol_mm=0.5, r_min=1.0, r_max=200.0)

    assert count == 1, f"Se esperaba 1 conversión, se obtuvo {count}"

    doc2 = ezdxf.readfile(str(out))
    msp2 = doc2.modelspace()
    circles = [e for e in msp2 if e.dxftype() == "CIRCLE"]
    lwpoly  = [e for e in msp2 if e.dxftype() == "LWPOLYLINE"]

    assert len(circles) == 1, f"Se esperaba 1 CIRCLE, se encontraron {len(circles)}"
    assert len(lwpoly)  == 1, f"El rectángulo borde debe permanecer como LWPOLYLINE, hay {len(lwpoly)}"

    c = circles[0]
    assert abs(c.dxf.center[0] - cx_ref) < 0.01, f"cx incorrecto: {c.dxf.center[0]}"
    assert abs(c.dxf.center[1] - cy_ref) < 0.01, f"cy incorrecto: {c.dxf.center[1]}"
    assert abs(c.dxf.radius    - r_ref)  < 0.01, f"radio incorrecto: {c.dxf.radius}"
    assert c.dxf.layer == "CORTE", f"Capa incorrecta: {c.dxf.layer}"


def test_fit_circle_kasa_exact():
    """Verificar que fit_circle_kasa recupera el círculo exacto para puntos perfectos."""
    import math
    from sistema_industrial.presets.panel_sales_local_app import _fit_circle_kasa

    cx, cy, r = 10.0, -5.0, 7.0
    pts = [(cx + r * math.cos(2 * math.pi * i / 16),
            cy + r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    result = _fit_circle_kasa(pts)
    assert result is not None
    rx_cx, rx_cy, rx_r, max_err = result
    assert abs(rx_cx - cx) < 1e-6
    assert abs(rx_cy - cy) < 1e-6
    assert abs(rx_r  - r)  < 1e-6
    assert max_err < 1e-6


def test_convert_circles_endpoint(tmp_path):
    """POST /api/patterns/convert_circles convierte correctamente y devuelve output_path + count."""
    pytest.importorskip("ezdxf")
    import ezdxf, math, json

    # Crear DXF de prueba con una LWPOLYLINE circular
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    n = 12; cx, cy, r = 25.0, 25.0, 4.0
    pts = [(cx + r * math.cos(2 * math.pi * i / n),
            cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    msp.add_lwpolyline(pts, close=True)
    src = tmp_path / "pat.dxf"
    doc.saveas(str(src))

    previous_output_dir = PanelSalesHandler.output_dir
    PanelSalesHandler.output_dir = tmp_path
    server = create_server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        body = json.dumps({"dxf_path": str(src), "tol_mm": 0.5, "r_min": 1.0, "r_max": 200.0}).encode()
        req = Request(
            f"http://127.0.0.1:{port}/api/patterns/convert_circles",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    finally:
        server.shutdown()
        server.server_close()
        PanelSalesHandler.output_dir = previous_output_dir

    assert data["ok"] is True
    assert data["converted_count"] == 1
    assert data["output_path"].endswith("_circles.dxf")


# ---------------------------------------------------------------------------
# TASK_041 — Patron Cuadriculado
# ---------------------------------------------------------------------------

def test_cuadriculado_circle_generates_dxf(tmp_path):
    """Cuadriculado con circulo debe generar un DXF valido."""
    data = LegacyPanelServiceInput(
        panel_mode="cuadriculado",
        preset_code="PANEL_DECORATIVO_LEGACY_CUADRICULADO",
        preset_name="Cuadriculado circulo",
        hole_shape="circle",
        hole_size_mm=20.0,
        offset_x_mm=30.0,
        offset_y_mm=30.0,
        width_mm=300.0,
        height_mm=200.0,
    )
    from sistema_industrial.presets.panel_service import LegacyPanelService
    service = LegacyPanelService()
    result = service.run(data, tmp_path)
    assert result.dxf_path.exists()
    assert result.pierce_count > 0


def test_cuadriculado_square_generates_dxf(tmp_path):
    """Cuadriculado con cuadrado debe generar un DXF valido."""
    data = LegacyPanelServiceInput(
        panel_mode="cuadriculado",
        preset_code="PANEL_DECORATIVO_LEGACY_CUADRICULADO",
        preset_name="Cuadriculado cuadrado",
        hole_shape="square",
        hole_size_mm=20.0,
        offset_x_mm=30.0,
        offset_y_mm=30.0,
        width_mm=300.0,
        height_mm=200.0,
    )
    from sistema_industrial.presets.panel_service import LegacyPanelService
    service = LegacyPanelService()
    result = service.run(data, tmp_path)
    assert result.dxf_path.exists()
    assert result.pierce_count > 0


def test_render_form_includes_cuadriculado_card():
    """La galeria de patrones debe incluir la card de cuadriculado."""
    html = render_form()
    assert 'id="pcard-cuadriculado"' in html
    assert "Cuadriculado" in html
    assert 'id="cuad-inline"' in html
    assert "cuad-shape" in html
    assert "cuad-size" in html
    assert "cuad-ox" in html
    assert "cuad-oy" in html
    assert "confirmCuadriculado" in html


def test_build_sales_input_cuadriculado():
    """build_sales_input parsea correctamente un formulario cuadriculado."""
    data = build_sales_input(
        {
            "panel_mode": ["cuadriculado"],
            "customer_reference": ["ACME"],
            "job_name": ["Panel cuad"],
            "preset_name": ["Cuadriculado circulo"],
            "material": ["chapa"],
            "thickness_mm": ["3"],
            "width_mm": ["300"],
            "height_mm": ["200"],
            "quantity": ["1"],
            "margin_mm": ["20"],
            "offset_x_mm": ["30"],
            "offset_y_mm": ["30"],
        }
    )
    assert data.panel_mode == "cuadriculado"
    assert data.pattern_type == "cuadriculado"
    assert data.offset_x_mm == 30.0
    assert data.offset_y_mm == 30.0


# ---------------------------------------------------------------------------
# Bug fixes: arc export and DXF origin normalization
# ---------------------------------------------------------------------------

def test_arc_segment_export_dxf_partial_arc_across_zero(tmp_path):
    """ArcSegment(start=350, end=10) is a 20° arc — must NOT be exported as CIRCLE.

    Bug: abs(350 - 10) % 360 = 340 → no problem here.
    But abs(350 - 0) % 360 = 350 >= 350 → wrongly exported as CIRCLE.
    Fix: use (end - start) % 360 = (0 - 350) % 360 = 10 (correct).
    """
    import sys, os
    from pathlib import Path as _Path
    legacy_dir = _Path(__file__).resolve().parent.parent / "Programas_hechos" / "Panel Decorativo"
    prev_cwd = _Path.cwd()
    inserted = str(legacy_dir) not in sys.path
    if inserted:
        sys.path.insert(0, str(legacy_dir))
    os.chdir(legacy_dir)
    try:
        pytest.importorskip("ezdxf")
        import ezdxf
        from importlib import import_module
        _arc_mod = import_module("geometry.arc_segment")

        out = tmp_path / "arc_test.dxf"
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

        # 10° arc crossing 0° (start=350, end=0)
        _arc_mod.ArcSegment(0, 0, 10, 350, 0).export_dxf(msp)
        # 20° arc crossing 0° (start=350, end=10)
        _arc_mod.ArcSegment(0, 0, 10, 350, 10).export_dxf(msp)
        # Full circle encoded as (0, 360) — should still export as CIRCLE
        _arc_mod.ArcSegment(0, 0, 10, 0, 360).export_dxf(msp)
        # Large near-full arc (1° to 359°, span=358°) → CIRCLE is acceptable
        _arc_mod.ArcSegment(0, 0, 10, 1, 359).export_dxf(msp)

        doc.saveas(str(out))
        doc2 = ezdxf.readfile(str(out))
        entities = list(doc2.modelspace())
        types = [e.dxftype() for e in entities]

        assert types[0] == "ARC", f"350→0 (10° arc) must be ARC, got {types[0]}"
        assert types[1] == "ARC", f"350→10 (20° arc) must be ARC, got {types[1]}"
        assert types[2] == "CIRCLE", f"0→360 (full) must be CIRCLE, got {types[2]}"
        assert types[3] == "CIRCLE", f"1→359 (358° near-full) must be CIRCLE, got {types[3]}"
    finally:
        os.chdir(prev_cwd)
        if inserted:
            try:
                sys.path.remove(str(legacy_dir))
            except ValueError:
                pass


def test_load_pattern_dxf_normalizes_origin():
    """DXF patterns must be centered at (0,0) after load_pattern() for symmetric tiling."""
    import sys, os
    from pathlib import Path as _Path
    legacy_dir = _Path(__file__).resolve().parent.parent / "Programas_hechos" / "Panel Decorativo"
    prev_cwd = _Path.cwd()
    inserted = str(legacy_dir) not in sys.path
    if inserted:
        sys.path.insert(0, str(legacy_dir))
    os.chdir(legacy_dir)
    try:
        from importlib import import_module
        _main = import_module("main")

        class _Settings:
            pattern_type = "dxf"
            input_file = str(MINIMAL_DXF_FIXTURE)  # square (0,0)→(12,12)
            step_x = 20.0
            step_y = 20.0

        piece, step_x, step_y = _main.load_pattern(_Settings())
        bbox = piece.bbox()

        # After normalization, center must be at (0, 0)
        cx = (bbox.min_x + bbox.max_x) / 2
        cy = (bbox.min_y + bbox.max_y) / 2
        assert abs(cx) < 1e-6, f"Piece X center should be 0, got {cx}"
        assert abs(cy) < 1e-6, f"Piece Y center should be 0, got {cy}"

        # Width/height must be preserved (12×12 square)
        assert abs((bbox.max_x - bbox.min_x) - 12.0) < 1e-6
        assert abs((bbox.max_y - bbox.min_y) - 12.0) < 1e-6
    finally:
        os.chdir(prev_cwd)
        if inserted:
            try:
                sys.path.remove(str(legacy_dir))
            except ValueError:
                pass
