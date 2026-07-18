"""Tests del parser de toolpath (Etapa 1 del simulador de movimiento) — descomposición de
DXF real en tramos (línea/arco) con ángulos de vértice reales, para Junction Deviation.

Principio: verificar la geometría/álgebra con casos sintéticos donde el resultado se conoce
de antemano, y confirmar el comportamiento contra los DXF reales (grillas + figura orgánica).
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from simulador_toolpath import (
    extraer_entidades,
    agrupar_en_figuras,
    encadenar_figura,
    entidad_a_tramo,
    angulo_de_giro_grados,
    parsear_figuras,
    _bulge_a_arco,
)

_BATERIA2_DIR = Path(__file__).resolve().parents[1] / "tools" / "calibracion_bateria2"


def _dxf_sintetico(tmp_path, nombre, build_fn):
    import ezdxf
    doc = ezdxf.new()
    msp = doc.modelspace()
    build_fn(msp)
    path = tmp_path / nombre
    doc.saveas(str(path))
    return path


# ---- ángulo de giro: cuadrado (90°) y triángulo (120°, EXTERIOR no interior) ----

def test_cuadrado_da_4_tramos_90_grados(tmp_path):
    path = _dxf_sintetico(tmp_path, "cuadrado.dxf",
                          lambda msp: msp.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True))
    figs = parsear_figuras(path)
    assert len(figs) == 1
    f = figs[0]
    assert len(f["tramos"]) == 4
    assert f["cerrada"] is True
    for l in [t.longitud_mm for t in f["tramos"]]:
        assert l == pytest.approx(10.0)
    for a in f["angulos_vertice_grados"]:
        assert a == pytest.approx(90.0)


def test_triangulo_equilatero_da_angulo_exterior_120():
    """El ángulo de GIRO es el exterior (360/n para un polígono regular), no el
    interior (60° en un triángulo equilátero) — verificación explícita para no
    confundir los dos conceptos."""
    import ezdxf
    h = 10 * math.sqrt(3) / 2
    doc = ezdxf.new(); msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (10, 0), (5, h)], close=True)
    path = Path("/tmp") / "triangulo_test_pytest.dxf"
    doc.saveas(str(path))
    figs = parsear_figuras(path)
    f = figs[0]
    assert len(f["tramos"]) == 3
    for a in f["angulos_vertice_grados"]:
        assert a == pytest.approx(120.0)
    path.unlink()


def test_poligono_regular_n_lados_angulo_exterior_360_sobre_n():
    """Generaliza: para un polígono regular de n lados, el ángulo de giro en
    cada vértice es 360/n, verificado para varios n."""
    import ezdxf
    for n in [5, 6, 8, 12]:
        pts = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
        doc = ezdxf.new(); msp = doc.modelspace()
        msp.add_lwpolyline(pts, close=True)
        path = Path("/tmp") / f"poligono_{n}_pytest.dxf"
        doc.saveas(str(path))
        figs = parsear_figuras(path)
        for a in figs[0]["angulos_vertice_grados"]:
            assert a == pytest.approx(360.0 / n, abs=1e-6)
        path.unlink()


# ---- arcos: longitud, radio, tangentes ----

def test_arco_90_grados_longitud_y_tangentes():
    import ezdxf
    doc = ezdxf.new(); msp = doc.modelspace()
    msp.add_arc(center=(0, 0), radius=5, start_angle=0, end_angle=90)
    path = Path("/tmp") / "arco_pytest.dxf"
    doc.saveas(str(path))
    ents = extraer_entidades(path)
    t = entidad_a_tramo(ents[0])
    assert t.tipo == "arco"
    assert t.longitud_mm == pytest.approx(5 * math.pi / 2)
    assert t.p_inicio == pytest.approx((5.0, 0.0))
    assert t.p_fin[0] == pytest.approx(0.0, abs=1e-9)
    assert t.p_fin[1] == pytest.approx(5.0)
    # tangente CCW en (5,0) apunta hacia +y; en (0,5) apunta hacia -x
    assert t.dir_entrada == pytest.approx((0.0, 1.0), abs=1e-9)
    assert t.dir_salida == pytest.approx((-1.0, 0.0), abs=1e-9)
    path.unlink()


def test_circulo_completo_es_una_figura_de_1_tramo():
    import ezdxf
    doc = ezdxf.new(); msp = doc.modelspace()
    msp.add_circle(center=(0, 0), radius=3)
    path = Path("/tmp") / "circulo_pytest.dxf"
    doc.saveas(str(path))
    ents = extraer_entidades(path)
    assert len(ents) == 1
    t = entidad_a_tramo(ents[0])
    assert t.longitud_mm == pytest.approx(2 * math.pi * 3)
    path.unlink()


def test_bulge_a_arco_semicirculo():
    """bulge=1.0 en un segmento de polyline = arco de 180° (semicírculo)."""
    p0, p1 = (-5.0, 0.0), (5.0, 0.0)
    arco = _bulge_a_arco(p0, p1, 1.0)
    assert arco["tipo"] == "arco"
    assert arco["radio_mm"] == pytest.approx(5.0)
    barrido = abs(arco["angulo_fin_rad"] - arco["angulo_inicio_rad"])
    assert barrido == pytest.approx(math.pi)


def test_bulge_cero_da_linea():
    arco = _bulge_a_arco((0.0, 0.0), (10.0, 0.0), 0.0)
    assert arco["tipo"] == "linea"


def test_lwpolyline_con_bulge_da_arco_correcto():
    import ezdxf
    doc = ezdxf.new(); msp = doc.modelspace()
    # medio círculo: 2 puntos, bulge=1.0 en el primero -> arco de 180°, radio 5
    msp.add_lwpolyline([(-5.0, 0.0, 0.0, 0.0, 1.0), (5.0, 0.0, 0.0, 0.0, 0.0)], format="xyseb")
    path = Path("/tmp") / "bulge_polyline_pytest.dxf"
    doc.saveas(str(path))
    figs = parsear_figuras(path)
    t = figs[0]["tramos"][0]
    assert t.tipo == "arco"
    assert t.radio_mm == pytest.approx(5.0)
    assert t.longitud_mm == pytest.approx(5 * math.pi)
    path.unlink()


# ---- tangencia línea-arco (ángulo de giro ≈ 0°) ----

def test_linea_arco_tangente_da_angulo_cero():
    import ezdxf
    doc = ezdxf.new(); msp = doc.modelspace()
    msp.add_line((0, 0), (5, 0))
    # arco centrado en (5,5) r=5, de 270 a 360 grados: en 270° está en (5,0),
    # tangente CCW ahí = (1,0) — coincide con la dirección de la línea (tangencia perfecta)
    msp.add_arc(center=(5, 5), radius=5, start_angle=270, end_angle=360)
    path = Path("/tmp") / "linea_arco_tangente_pytest.dxf"
    doc.saveas(str(path))
    figs = parsear_figuras(path)
    f = figs[0]
    assert [t.tipo for t in f["tramos"]] == ["linea", "arco"]
    assert f["cerrada"] is False
    assert f["angulos_vertice_grados"][0] == pytest.approx(0.0, abs=1e-6)
    path.unlink()


def test_angulo_de_giro_reversa_180():
    import ezdxf
    doc = ezdxf.new(); msp = doc.modelspace()
    msp.add_line((0, 0), (10, 0))
    msp.add_line((10, 0), (0, 0))  # vuelve exactamente sobre sus pasos
    path = Path("/tmp") / "reversa_pytest.dxf"
    doc.saveas(str(path))
    figs = parsear_figuras(path)
    f = figs[0]
    assert f["angulos_vertice_grados"][0] == pytest.approx(180.0, abs=1e-6)
    path.unlink()


# ---- agrupamiento en figuras (componentes conexas) ----

def test_dos_figuras_separadas_no_se_mezclan():
    import ezdxf
    doc = ezdxf.new(); msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)      # cuadrado 1
    msp.add_lwpolyline([(100, 100), (110, 100), (110, 110)], close=True)      # triángulo, lejos
    path = Path("/tmp") / "dos_figuras_pytest.dxf"
    doc.saveas(str(path))
    figs = parsear_figuras(path)
    assert len(figs) == 2
    tamaños = sorted(len(f["tramos"]) for f in figs)
    assert tamaños == [3, 4]
    path.unlink()


def test_encadenamiento_voltea_entidades_en_orden_mixto():
    """Si las entidades no vienen en orden de recorrido en el DXF (algunas
    'al revés'), el encadenador las debe voltear para formar la cadena continua."""
    entidades = [
        {"tipo": "linea", "p_inicio": (10.0, 0.0), "p_fin": (0.0, 0.0)},   # al revés
        {"tipo": "linea", "p_inicio": (0.0, 0.0), "p_fin": (0.0, 10.0)},
        {"tipo": "linea", "p_inicio": (10.0, 10.0), "p_fin": (0.0, 10.0)},  # al revés
        {"tipo": "linea", "p_inicio": (10.0, 0.0), "p_fin": (10.0, 10.0)},
    ]
    cadena, cerrada = encadenar_figura(entidades)
    assert len(cadena) == 4
    # verificar continuidad real: cada p_fin coincide con el p_inicio del siguiente
    for a, b in zip(cadena, cadena[1:]):
        assert a["p_fin"] == pytest.approx(b["p_inicio"])
    assert cerrada is True


# ---- contra los DXF REALES ----

def test_bateria2_agujero_cuadrado_da_4_tramos_90_grados():
    figs = parsear_figuras(_BATERIA2_DIR / "B2_01_L60_p70_500x500.dxf")
    # 36 agujeros + 1 contorno = 37 figuras
    assert len(figs) == 37
    agujeros = [f for f in figs if len(f["tramos"]) == 4]
    assert len(agujeros) >= 36
    for f in agujeros[:5]:
        assert f["cerrada"] is True
        for a in f["angulos_vertice_grados"]:
            assert a == pytest.approx(90.0)


def test_corazon_real_da_figuras_cerradas_con_angulos_variados():
    """Validación clave del riesgo de identificabilidad marcado en el brainstorm:
    a diferencia de Batería 2 (todo a 90°/120°), una figura orgánica real debe dar
    un RANGO amplio de ángulos — la variedad que Junction Deviation necesita para
    calibrarse de verdad."""
    import ezdxf
    src = Path("/tmp/claude-1000/-home-costa-SistemaIndustrial-Nextango/2e2c95aa-f8d6-4494-9353-9cd81ac27270/scratchpad/Corazon.dxf")
    if not src.exists():
        pytest.skip("Corazon.dxf no disponible en este entorno (se bajó ad-hoc del server)")
    # convierto splines a líneas (flattening) igual que en la investigación manual
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    splines = [e for e in msp if e.dxftype() == "SPLINE"]
    lines = [e for e in msp if e.dxftype() == "LINE"]
    nuevo = ezdxf.new(); nmsp = nuevo.modelspace()
    for e in lines:
        nmsp.add_line(e.dxf.start, e.dxf.end)
    for s in splines:
        pts = list(s.flattening(0.05))
        for p0, p1 in zip(pts, pts[1:]):
            nmsp.add_line((p0.x, p0.y), (p1.x, p1.y))
    path = Path("/tmp") / "corazon_convertido_pytest.dxf"
    nuevo.saveas(str(path))

    figs = parsear_figuras(path)
    assert len(figs) >= 1
    todos_angulos = [a for f in figs for a in f["angulos_vertice_grados"]]
    assert len(todos_angulos) > 0
    assert min(todos_angulos) < 10.0    # hay ángulos casi rectos (suaves)
    assert max(todos_angulos) > 80.0    # hay ángulos bastante cerrados
    for f in figs:
        assert f["cerrada"] is True     # un corazón es un contorno cerrado
    path.unlink()
