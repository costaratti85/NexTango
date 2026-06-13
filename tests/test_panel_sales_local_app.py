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
    run_sales_flow,
    generate_pattern_thumbnail,
    _thumbnail_url,
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
        assert "Resultado generado" in html
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


def test_render_admin_contains_material_table_section():
    """Admin page includes the Tabla de materiales section and form."""
    html = render_admin()
    assert "Tabla de materiales" in html
    assert "mat-material" in html
    assert "mat-espesor" in html
    assert "mat-densidad" in html
    assert "mat-velocidad" in html
    assert "mat-pierce" in html
    assert "mat-consumible" in html
    assert "AGREGAR MATERIAL" in html
    assert "materials-tbody" in html


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
