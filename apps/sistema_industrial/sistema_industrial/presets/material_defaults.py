"""
Tabla de materiales predeterminada para paneles decorativos.
Fuente: docs/MATERIALES_Y_VELOCIDADES.md
Laser referencia: fibra 1500W. Velocidades conservadoras (cotización, no producción).

Pesos (densidad_kg_m2):
  Chapa doble decapada: tabla tabulada de hierrosratti.com.ar (norma argentina)
  Chapa galvanizada: tabla egresadoselectronicaunc.blogspot.com (ASTM A653 / IRAM 621)
    N°25 no aparece en tabla estándar argentina — calculado: 7.85 × 0.5 + 0.275 zinc
  Inoxidable 430 y 304: calculado desde densidad × espesor nominal
    (430: 7700 kg/m³, 304: 7930 kg/m³ — no existen tablas tabuladas públicas para AR)
"""

MATERIAL_DEFAULTS = [
    # --- Chapa doble decapada — pesos de tabla hierrosratti.com.ar ---
    {"material": "Chapa doble decapada", "calibre": "24", "espesor_mm": 0.56, "densidad_kg_m2":  4.48, "velocidad_corte_mm_s": 280.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Chapa doble decapada", "calibre": "22", "espesor_mm": 0.7,  "densidad_kg_m2":  5.68, "velocidad_corte_mm_s": 245.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Chapa doble decapada", "calibre": "20", "espesor_mm": 0.9,  "densidad_kg_m2":  7.04, "velocidad_corte_mm_s": 195.0, "tiempo_perforacion_s": 0.15, "consumible_por_perforacion": 0.0},
    {"material": "Chapa doble decapada", "calibre": "18", "espesor_mm": 1.25, "densidad_kg_m2": 10.16, "velocidad_corte_mm_s": 140.0, "tiempo_perforacion_s": 0.20, "consumible_por_perforacion": 0.0},
    {"material": "Chapa doble decapada", "calibre": "16", "espesor_mm": 1.6,  "densidad_kg_m2": 12.76, "velocidad_corte_mm_s": 100.0, "tiempo_perforacion_s": 0.30, "consumible_por_perforacion": 0.0},
    {"material": "Chapa doble decapada", "calibre": "14", "espesor_mm": 2.0,  "densidad_kg_m2": 16.03, "velocidad_corte_mm_s":  58.0, "tiempo_perforacion_s": 0.40, "consumible_por_perforacion": 0.0},
    {"material": "Chapa doble decapada", "calibre": "12", "espesor_mm": 2.5,  "densidad_kg_m2": 20.23, "velocidad_corte_mm_s":  38.0, "tiempo_perforacion_s": 0.60, "consumible_por_perforacion": 0.0},

    # --- Chapa galvanizada — pesos de tabla ASTM A653 / IRAM 621 ---
    # N°25 no está en tabla estándar AR — peso calculado (7.85×0.5 + 0.275 zinc)
    {"material": "Chapa galvanizada", "calibre": "30", "espesor_mm": 0.3,  "densidad_kg_m2":  2.60, "velocidad_corte_mm_s": 350.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Chapa galvanizada", "calibre": "25", "espesor_mm": 0.5,  "densidad_kg_m2":  4.20, "velocidad_corte_mm_s": 280.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Chapa galvanizada", "calibre": "22", "espesor_mm": 0.7,  "densidad_kg_m2":  6.00, "velocidad_corte_mm_s": 200.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Chapa galvanizada", "calibre": "20", "espesor_mm": 0.9,  "densidad_kg_m2":  7.50, "velocidad_corte_mm_s": 155.0, "tiempo_perforacion_s": 0.15, "consumible_por_perforacion": 0.0},
    {"material": "Chapa galvanizada", "calibre": "18", "espesor_mm": 1.25, "densidad_kg_m2": 10.20, "velocidad_corte_mm_s": 105.0, "tiempo_perforacion_s": 0.20, "consumible_por_perforacion": 0.0},
    {"material": "Chapa galvanizada", "calibre": "16", "espesor_mm": 1.6,  "densidad_kg_m2": 13.00, "velocidad_corte_mm_s":  73.0, "tiempo_perforacion_s": 0.30, "consumible_por_perforacion": 0.0},
    {"material": "Chapa galvanizada", "calibre": "14", "espesor_mm": 2.0,  "densidad_kg_m2": 16.00, "velocidad_corte_mm_s":  45.0, "tiempo_perforacion_s": 0.40, "consumible_por_perforacion": 0.0},

    # --- Inoxidable AISI 430 (ferrítico, 7700 kg/m³) — calculado desde densidad ---
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 0.6,  "densidad_kg_m2":  4.62, "velocidad_corte_mm_s": 290.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 0.8,  "densidad_kg_m2":  6.16, "velocidad_corte_mm_s": 250.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 1.0,  "densidad_kg_m2":  7.70, "velocidad_corte_mm_s": 200.0, "tiempo_perforacion_s": 0.15, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 1.25, "densidad_kg_m2":  9.63, "velocidad_corte_mm_s": 150.0, "tiempo_perforacion_s": 0.20, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 1.6,  "densidad_kg_m2": 12.32, "velocidad_corte_mm_s": 105.0, "tiempo_perforacion_s": 0.30, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 2.0,  "densidad_kg_m2": 15.40, "velocidad_corte_mm_s":  70.0, "tiempo_perforacion_s": 0.50, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 430", "calibre": "-", "espesor_mm": 2.5,  "densidad_kg_m2": 19.25, "velocidad_corte_mm_s":  43.0, "tiempo_perforacion_s": 0.80, "consumible_por_perforacion": 0.0},

    # --- Inoxidable AISI 304 (austenítico, 7930 kg/m³) — calculado desde densidad ---
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 0.6,  "densidad_kg_m2":  4.76, "velocidad_corte_mm_s": 260.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 0.8,  "densidad_kg_m2":  6.34, "velocidad_corte_mm_s": 225.0, "tiempo_perforacion_s": 0.10, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 1.0,  "densidad_kg_m2":  7.93, "velocidad_corte_mm_s": 180.0, "tiempo_perforacion_s": 0.15, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 1.25, "densidad_kg_m2":  9.91, "velocidad_corte_mm_s": 135.0, "tiempo_perforacion_s": 0.20, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 1.6,  "densidad_kg_m2": 12.69, "velocidad_corte_mm_s":  95.0, "tiempo_perforacion_s": 0.30, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 2.0,  "densidad_kg_m2": 15.86, "velocidad_corte_mm_s":  63.0, "tiempo_perforacion_s": 0.50, "consumible_por_perforacion": 0.0},
    {"material": "Inoxidable 304", "calibre": "-", "espesor_mm": 2.5,  "densidad_kg_m2": 19.83, "velocidad_corte_mm_s":  39.0, "tiempo_perforacion_s": 0.80, "consumible_por_perforacion": 0.0},
]
