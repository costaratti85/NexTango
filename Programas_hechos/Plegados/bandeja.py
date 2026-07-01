"""
Desarrollo plano de una bandeja (cajón de 4 lados plegados).

Parámetros de entrada (todos en mm):
    ancho_int   — ancho interior de la bandeja terminada
    largo_int   — largo interior de la bandeja terminada
    alto        — altura de los lados
    espesor     — espesor de chapa

Fórmulas:
    blank_ancho = ancho_int + 2 * alto - 4 * espesor
    blank_largo = largo_int + 2 * alto - 4 * espesor
    despunte    = alto - espesor    (lado del cuadrado cortado en cada punta)
"""

from __future__ import annotations


def calcular_bandeja(
    ancho_int: float,
    largo_int: float,
    alto: float,
    espesor: float,
) -> dict:
    """
    Devuelve un dict con:
      blank_ancho, blank_largo, despunte,
      vertices: list of (x, y) — 12 puntos CCW centrados en origen,
      cara_principal: {"ancho": ancho_int, "largo": largo_int}
    """
    blank_ancho = ancho_int + 2 * alto - 4 * espesor
    blank_largo = largo_int + 2 * alto - 4 * espesor
    despunte = alto - espesor

    BW = blank_ancho
    BL = blank_largo
    D = despunte

    vertices = [
        (-BW / 2,        -BL / 2 + D),
        (-BW / 2 + D,    -BL / 2 + D),
        (-BW / 2 + D,    -BL / 2    ),
        ( BW / 2 - D,    -BL / 2    ),
        ( BW / 2 - D,    -BL / 2 + D),
        ( BW / 2,        -BL / 2 + D),
        ( BW / 2,         BL / 2 - D),
        ( BW / 2 - D,     BL / 2 - D),
        ( BW / 2 - D,     BL / 2    ),
        (-BW / 2 + D,     BL / 2    ),
        (-BW / 2 + D,     BL / 2 - D),
        (-BW / 2,         BL / 2 - D),
    ]

    return {
        "blank_ancho": round(blank_ancho, 3),
        "blank_largo": round(blank_largo, 3),
        "despunte": round(despunte, 3),
        "vertices": vertices,
        "cara_principal": {"ancho": ancho_int, "largo": largo_int},
    }


def calcular_recursos_bandeja(
    ancho_int: float,
    largo_int: float,
    alto: float,
    espesor: float,
    material_row: dict,
) -> dict:
    """
    material_row: fila de la tabla de materiales
                  (requiere densidad_kg_m2, velocidad_corte_mm_s)

    Retorna:
      kg_chapa          — float
      tiempo_laser_s    — float (segundos)
      perforaciones     — int (siempre 0)
      plegados          — int (siempre 4)
    """
    BW = ancho_int + 2 * alto - 4 * espesor
    BL = largo_int + 2 * alto - 4 * espesor
    D = alto - espesor

    area_mm2 = BW * BL - 4 * D * D
    kg_chapa = (area_mm2 / 1_000_000) * float(material_row["densidad_kg_m2"])

    perimetro_mm = 2 * (BW + BL)
    velocidad = float(material_row["velocidad_corte_mm_s"])
    tiempo_laser_s = perimetro_mm / velocidad if velocidad > 0 else 0.0

    return {
        "kg_chapa": round(kg_chapa, 3),
        "tiempo_laser_s": round(tiempo_laser_s, 1),
        "perforaciones": 0,
        "plegados": 4,
    }


def exportar_dxf_bandeja(result: dict, output_path: str) -> None:
    """Genera un DXF con la polilínea de 12 vértices en capa CORTE."""
    import ezdxf

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    verts_2d = [(x, y) for x, y in result["vertices"]]
    msp.add_lwpolyline(verts_2d, close=True, dxfattribs={"layer": "CORTE"})
    doc.saveas(output_path)
