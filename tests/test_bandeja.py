"""Tests para el motor de geometría de bandeja (TASK_043)."""

import sys
from pathlib import Path

# Asegurar que el directorio Plegados esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Programas_hechos" / "Plegados"))

from bandeja import calcular_bandeja, calcular_recursos_bandeja


def test_calcular_bandeja_dimensiones():
    """Bandeja 300×200×50mm, espesor 1.25mm."""
    result = calcular_bandeja(300, 200, 50, 1.25)

    # blank_ancho = 300 + 2*50 - 4*1.25 = 395
    assert result["blank_ancho"] == 395.0
    # blank_largo = 200 + 2*50 - 4*1.25 = 295
    assert result["blank_largo"] == 295.0
    # despunte = 50 - 1.25 = 48.75
    assert result["despunte"] == 48.75

    # 12 vértices
    assert len(result["vertices"]) == 12

    # cara_principal preserva las dimensiones interiores
    assert result["cara_principal"] == {"ancho": 300, "largo": 200}


def test_calcular_bandeja_vertices_simetria():
    """Los vértices deben ser simétricos respecto al origen."""
    result = calcular_bandeja(300, 200, 50, 1.25)
    verts = result["vertices"]

    BW = result["blank_ancho"]
    BL = result["blank_largo"]
    D = result["despunte"]

    # Vértice 1: (-BW/2, -BL/2 + D)
    assert abs(verts[0][0] - (-BW / 2)) < 1e-9
    assert abs(verts[0][1] - (-BL / 2 + D)) < 1e-9

    # Vértice 6: (BW/2, -BL/2 + D)
    assert abs(verts[5][0] - (BW / 2)) < 1e-9
    assert abs(verts[5][1] - (-BL / 2 + D)) < 1e-9

    # Vértice 9: (BW/2 - D, BL/2)
    assert abs(verts[8][0] - (BW / 2 - D)) < 1e-9
    assert abs(verts[8][1] - (BL / 2)) < 1e-9


def test_calcular_recursos_bandeja_kg():
    """Kg de chapa con material conocido."""
    # Bandeja 300×200×50, espesor 1.25
    # BW=395, BL=295, D=48.75
    # area = 395*295 - 4*48.75^2 = 116525 - 9506.25 = 107018.75 mm²
    # Con densidad 15.0 kg/m²:
    # kg = (107018.75 / 1_000_000) * 15.0 = 1.605 kg

    material_row = {
        "densidad_kg_m2": 15.0,
        "velocidad_corte_mm_s": 100.0,
    }
    result = calcular_recursos_bandeja(300, 200, 50, 1.25, material_row)

    assert abs(result["kg_chapa"] - 1.605) < 0.01
    assert result["perforaciones"] == 0
    assert result["plegados"] == 4


def test_calcular_recursos_bandeja_tiempo_laser():
    """Tiempo de laser = perimetro / velocidad."""
    # BW=395, BL=295 → perimetro = 2*(395+295) = 1380 mm
    # velocidad = 100 mm/s → tiempo = 13.8 s

    material_row = {
        "densidad_kg_m2": 15.0,
        "velocidad_corte_mm_s": 100.0,
    }
    result = calcular_recursos_bandeja(300, 200, 50, 1.25, material_row)

    assert abs(result["tiempo_laser_s"] - 13.8) < 0.1


def test_calcular_bandeja_cuadrada():
    """Bandeja cuadrada: ancho_int == largo_int."""
    result = calcular_bandeja(200, 200, 40, 1.0)

    # blank_ancho = blank_largo = 200 + 80 - 4 = 276
    assert result["blank_ancho"] == 276.0
    assert result["blank_largo"] == 276.0
    assert result["despunte"] == 39.0


def test_exportar_dxf_bandeja(tmp_path):
    """exportar_dxf_bandeja genera un archivo DXF válido con 12 vértices."""
    import ezdxf
    from bandeja import exportar_dxf_bandeja

    result = calcular_bandeja(300, 200, 50, 1.25)
    out = tmp_path / "bandeja_test.dxf"
    exportar_dxf_bandeja(result, str(out))

    assert out.exists()
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    assert len(polylines) == 1
    assert polylines[0].dxf.layer == "CORTE"
    # 12 vértices
    assert len(list(polylines[0])) == 12
