"""Tests de update_pattern y list_dxf_files (api/patrones.py) con frappe fake.

El save() del doc fake ejecuta el _handle_versioning REAL de SIPatron, así se
verifica la semántica de versionado congelado (contrato con Lechu/MES):
cambio en parametros/archivo_dxf => nueva fila append-only + bump de version.
"""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "sistema_industrial" / "sistema_industrial"


# ---------------------------------------------------------------- frappe fake

class DoesNotExistError(Exception):
    pass


class ValidationError(Exception):
    pass


def _make_fake_frappe():
    fake = types.ModuleType("frappe")
    fake.DoesNotExistError = DoesNotExistError
    fake.ValidationError = ValidationError
    fake.whitelist = lambda **kw: (lambda f: f)

    def throw(msg, exc=None):
        raise (exc or ValidationError)(msg)

    fake.throw = throw
    fake.log_error = lambda *a, **k: None
    fake.utils = SimpleNamespace(now=lambda: "2026-07-14 12:00:00")

    fake._conf = {}
    fake.conf = SimpleNamespace(get=lambda k, d=None: fake._conf.get(k, d))

    fake._docs = {}       # name -> FakePatron
    fake._files = {}      # file_url -> path en disco

    def db_exists(doctype, name):
        if doctype == "SI Patron":
            return name in fake._docs
        return False

    def db_get_value(doctype, filters, fieldname):
        if doctype == "File":
            url = filters.get("file_url") if isinstance(filters, dict) else filters
            return url if url in fake._files else None
        return None

    fake.db = SimpleNamespace(
        exists=db_exists,
        get_value=db_get_value,
        count=lambda *a, **k: len(fake._docs),
        commit=lambda: None,
    )

    def get_doc(doctype, name=None):
        if doctype == "SI Patron":
            if name not in fake._docs:
                raise DoesNotExistError(name)
            return fake._docs[name]
        if doctype == "File":
            path = fake._files[name]
            return SimpleNamespace(get_full_path=lambda: str(path))
        raise AssertionError(f"get_doc inesperado: {doctype}")

    fake.get_doc = get_doc

    def get_all(doctype, fields=None, **kw):
        assert doctype == "SI Patron"
        return [
            {"name": d.name, "archivo_dxf": d.archivo_dxf}
            for d in fake._docs.values()
        ]

    fake.get_all = get_all

    # submódulos para `from frappe.model.document import Document`
    model = types.ModuleType("frappe.model")
    document = types.ModuleType("frappe.model.document")
    document.Document = object
    model.document = document
    fake.model = model
    return fake, model, document


FAKE_FRAPPE, _MODEL, _DOCUMENT = _make_fake_frappe()
sys.modules["frappe"] = FAKE_FRAPPE
sys.modules["frappe.model"] = _MODEL
sys.modules["frappe.model.document"] = _DOCUMENT


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


si_patron_mod = _load(
    "si_patron_ctrl",
    APP / "sistema_industrial" / "doctype" / "si_patron" / "si_patron.py",
)
patrones = _load("si_api_patrones", APP / "api" / "patrones.py")


# ------------------------------------------------------------------- FakeDoc

class FakePatron:
    """Doc fake cuyo save() corre el _handle_versioning REAL de SIPatron."""

    def __init__(self, **kw):
        self.name = kw.get("name", "")
        self.tipo = kw.get("tipo", "Archivo")
        self.visibilidad = kw.get("visibilidad", "Público")
        self.cliente = kw.get("cliente", "")
        self.descripcion = kw.get("descripcion", "")
        self.archivo_dxf = kw.get("archivo_dxf", "")
        self.parametros = kw.get("parametros", "")
        self.activo = kw.get("activo", 1)
        self.spline_count = kw.get("spline_count", 0)
        self.version = kw.get("version", 1)
        self.versiones = []

    def append(self, field, row):
        getattr(self, field).append(SimpleNamespace(**row))

    def save(self, ignore_permissions=False):
        si_patron_mod.SIPatron._handle_versioning(self)
        FAKE_FRAPPE._docs[self.name] = self


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Raíz de planos en tmp + un patrón 'Aconcagua' guardado (v1 congelada)."""
    FAKE_FRAPPE._docs.clear()
    FAKE_FRAPPE._files.clear()
    FAKE_FRAPPE._conf.clear()

    planos = tmp_path / "planos"
    (planos / "generico" / "patrones").mkdir(parents=True)
    FAKE_FRAPPE._conf["nextango_planos_path"] = str(planos)

    # el archivo "congelado" en la base NO existe en disco (caso Aconcagua real)
    doc = FakePatron(
        name="Aconcagua",
        archivo_dxf=str(planos / "generico" / "patrones" / "Aconcagua.dxf"),
        parametros=json.dumps({"step_x": 84.0, "step_y": 84.0}),
    )
    doc.save()
    assert doc.version == 1 and len(doc.versiones) == 1

    # el archivo REAL con otro nombre
    real = planos / "generico" / "patrones" / "Aconcagua_OFF_XY_85.dxf"
    real.write_text("0\nSECTION\n0\nENDSEC\n0\nEOF\n", encoding="utf-8")

    # thumbnails: no intentar renderizar en tests
    monkeypatch.setattr(patrones, "generate_thumbnail",
                        lambda name: {"ok": False, "url": None})
    monkeypatch.setattr(patrones, "_count_splines", lambda p: 0)

    return SimpleNamespace(planos=planos, doc=doc, real=real)


# ---------------------------------------------------------------- update_pattern

def test_patron_inexistente(env):
    with pytest.raises(DoesNotExistError):
        patrones.update_pattern(name="NoExiste")


def test_editar_descripcion_no_crea_version(env):
    r = patrones.update_pattern(name="Aconcagua", descripcion="patrón andino")
    assert r["ok"] is True
    assert r["descripcion"] == "patrón andino"
    assert r["version"] == 1
    assert r["previous_version"] == 1
    assert r["version_created"] is False
    assert len(env.doc.versiones) == 1


def test_reapuntar_dxf_crea_version_y_congela_la_vieja(env):
    old_path = env.doc.archivo_dxf
    r = patrones.update_pattern(name="Aconcagua", dxf_path=str(env.real))

    assert r["version"] == 2 and r["previous_version"] == 1
    assert r["version_created"] is True
    assert r["archivo_dxf"] == str(env.real)
    assert r["file_available"] is True

    # inmutabilidad: la v1 congelada sigue apuntando a la ruta vieja
    assert len(env.doc.versiones) == 2
    v1 = next(v for v in env.doc.versiones if v.version_num == 1)
    assert v1.archivo_dxf_frozen == old_path
    v2 = next(v for v in env.doc.versiones if v.version_num == 2)
    assert v2.archivo_dxf_frozen == str(env.real)


def test_reapuntar_acepta_relpath(env):
    r = patrones.update_pattern(
        name="Aconcagua",
        dxf_path="generico/patrones/Aconcagua_OFF_XY_85.dxf",
    )
    assert r["archivo_dxf"] == str(env.real)
    assert r["file_available"] is True


def test_reapuntar_fuera_de_planos_rechazado(env, tmp_path):
    fuera = tmp_path / "fuera.dxf"
    fuera.write_text("x", encoding="utf-8")
    with pytest.raises(ValidationError, match="dentro de la carpeta de planos"):
        patrones.update_pattern(name="Aconcagua", dxf_path=str(fuera))


def test_reapuntar_traversal_rechazado(env):
    with pytest.raises(ValidationError, match="dentro de la carpeta de planos"):
        patrones.update_pattern(name="Aconcagua",
                                dxf_path="generico/../../../etc/passwd.dxf")


def test_reapuntar_inexistente_rechazado(env):
    with pytest.raises(ValidationError, match="no encontrado"):
        patrones.update_pattern(name="Aconcagua",
                                dxf_path="generico/patrones/nada.dxf")


def test_reapuntar_no_dxf_rechazado(env):
    txt = env.planos / "generico" / "notas.txt"
    txt.write_text("x", encoding="utf-8")
    with pytest.raises(ValidationError, match=r"\.dxf"):
        patrones.update_pattern(name="Aconcagua", dxf_path=str(txt))


def test_file_url_y_dxf_path_excluyentes(env):
    with pytest.raises(ValidationError, match="mutuamente excluyentes"):
        patrones.update_pattern(name="Aconcagua",
                                file_url="/private/files/x.dxf",
                                dxf_path=str(env.real))


def test_file_url_copia_con_sufijo_de_version(env, tmp_path):
    src = tmp_path / "upload" / "philo.dxf"
    src.parent.mkdir()
    src.write_text("0\nEOF\n", encoding="utf-8")
    FAKE_FRAPPE._files["/private/files/philo.dxf"] = src

    r = patrones.update_pattern(name="Aconcagua",
                                file_url="/private/files/philo.dxf")
    assert r["version"] == 2 and r["version_created"] is True
    dest = Path(r["archivo_dxf"])
    assert dest.name == "philo_v2.dxf"
    assert dest.parent == env.planos / "generico" / "patrones"
    assert dest.is_file()
    assert r["file_available"] is True


def test_parametrico_no_acepta_dxf(env):
    doc = FakePatron(name="Tresbolillo", tipo="Paramétrico",
                     parametros=json.dumps({"forma": "tresbolillo"}))
    doc.save()
    with pytest.raises(ValidationError, match="Paramétrico"):
        patrones.update_pattern(name="Tresbolillo", dxf_path=str(env.real))


def test_step_x_crea_version_y_mergea(env):
    r = patrones.update_pattern(name="Aconcagua", step_x=85.0)
    assert r["version"] == 2 and r["version_created"] is True
    assert r["parametros"] == {"step_x": 85.0, "step_y": 84.0}


def test_step_vacio_limpia_valor(env):
    r = patrones.update_pattern(name="Aconcagua", step_y="")
    assert r["parametros"]["step_y"] is None
    assert r["parametros"]["step_x"] == 84.0


def test_parametros_json_merge_preserva_claves(env):
    env.doc.parametros = json.dumps({"step_x": 84.0, "step_y": 84.0, "forma": "libre"})
    env.doc.save()
    r = patrones.update_pattern(name="Aconcagua",
                                parametros=json.dumps({"hole_size": 10.0}),
                                step_x=90.0)
    assert r["parametros"]["forma"] == "libre"
    assert r["parametros"]["hole_size"] == 10.0
    assert r["parametros"]["step_x"] == 90.0     # explícito pisa al merge


def test_parametros_invalido_rechazado(env):
    with pytest.raises(ValidationError, match="JSON"):
        patrones.update_pattern(name="Aconcagua", parametros="{no json}")


def test_exclusivo_sin_customer_rechazado(env):
    with pytest.raises(ValidationError, match="customer"):
        patrones.update_pattern(name="Aconcagua", visibilidad="Exclusivo")


def test_exclusivo_con_customer_ok_y_publico_limpia(env):
    r = patrones.update_pattern(name="Aconcagua", visibilidad="Exclusivo",
                                customer="ACME SA")
    assert r["visibilidad"] == "Exclusivo" and r["cliente"] == "ACME SA"
    r = patrones.update_pattern(name="Aconcagua", visibilidad="Público")
    assert r["visibilidad"] == "Público" and r["cliente"] == ""


def test_activo_toggle_no_crea_version(env):
    r = patrones.update_pattern(name="Aconcagua", activo=0)
    assert r["activo"] == 0 and r["version_created"] is False
    r = patrones.update_pattern(name="Aconcagua", activo="1")
    assert r["activo"] == 1 and r["version_created"] is False


def test_update_sin_cambios_es_noop_versionado(env):
    r = patrones.update_pattern(name="Aconcagua")
    assert r["ok"] is True and r["version_created"] is False
    assert len(env.doc.versiones) == 1


def test_offset_alias_de_step(env):
    r = patrones.update_pattern(name="Aconcagua", offset_x=85.0, offset_y=85.0)
    assert r["version_created"] is True
    # se guarda canónico como step_x/step_y
    assert r["parametros"] == {"step_x": 85.0, "step_y": 85.0}
    # espejo en la response para la UI
    assert r["offset_x"] == 85.0 and r["offset_y"] == 85.0


def test_offset_vacio_limpia_valor(env):
    r = patrones.update_pattern(name="Aconcagua", offset_x="")
    assert r["parametros"]["step_x"] is None
    assert r["offset_x"] is None


def test_offset_y_step_juntos_rechazado(env):
    with pytest.raises(ValidationError, match="misma propiedad"):
        patrones.update_pattern(name="Aconcagua", step_x=85.0, offset_x=85.0)
    with pytest.raises(ValidationError, match="misma propiedad"):
        patrones.update_pattern(name="Aconcagua", step_y=85.0, offset_y=85.0)


def test_dxf_nuevo_mas_offsets_en_un_solo_update(env):
    """El flujo pedido por Constantino: archivo + offset X + offset Y juntos."""
    r = patrones.update_pattern(name="Aconcagua", dxf_path=str(env.real),
                                offset_x=85.0, offset_y=85.0)
    assert r["version"] == 2 and r["version_created"] is True
    assert r["archivo_dxf"] == str(env.real) and r["file_available"] is True
    assert r["offset_x"] == 85.0 and r["offset_y"] == 85.0

    # una sola versión nueva congela archivo + offsets juntos
    assert len(env.doc.versiones) == 2
    v2 = next(v for v in env.doc.versiones if v.version_num == 2)
    assert v2.archivo_dxf_frozen == str(env.real)
    assert json.loads(v2.parametros_frozen) == {"step_x": 85.0, "step_y": 85.0}


# ---------------------------------------------------------------- list_dxf_files

def test_list_dxf_files_marca_used_by_y_huerfanos(env):
    r = patrones.list_dxf_files()
    assert r["root"] == str(env.planos)
    by_rel = {f["relpath"]: f for f in r["files"]}
    # el archivo real está huérfano (la base apunta a Aconcagua.dxf inexistente)
    assert by_rel["generico/patrones/Aconcagua_OFF_XY_85.dxf"]["used_by"] == []

    # tras reapuntar, figura como usado
    patrones.update_pattern(name="Aconcagua", dxf_path=str(env.real))
    r = patrones.list_dxf_files()
    by_rel = {f["relpath"]: f for f in r["files"]}
    assert by_rel["generico/patrones/Aconcagua_OFF_XY_85.dxf"]["used_by"] == ["Aconcagua"]


def test_list_dxf_files_ignora_no_dxf(env):
    (env.planos / "generico" / "leeme.txt").write_text("x", encoding="utf-8")
    r = patrones.list_dxf_files()
    assert all(f["relpath"].lower().endswith(".dxf") for f in r["files"])
    assert all("size_kb" in f and "modified" in f for f in r["files"])
