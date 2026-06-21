# Materiales y velocidades de corte láser

**Láser de referencia:** Fibra óptica, 1500W  
**Fuentes:** Raymond Laser, GWEIKE, Haotian Lasers, BestSheetMetal, StyleCNC  
**Advertencia:** Valores de cotización (65-70% del máximo publicado). Validar contra cortes de prueba en la máquina real antes de usar en producción (variación típica ±20%).

---

## Sistema de precios

Cinco parámetros globales, actualizados al inicio del día:

| Parámetro | Descripción |
|---|---|
| `precio_segundo_maquina` | $/s de tiempo de láser |
| `precio_kg_doble_decapada` | $/kg de chapa doble decapada |
| `precio_kg_galvanizado` | $/kg de chapa galvanizada |
| `precio_kg_inoxidable_430` | $/kg de inoxidable AISI 430 |
| `precio_kg_inoxidable_304` | $/kg de inoxidable AISI 304 |

**Fórmula de costo por panel:**  
`Costo = kg_material × precio_kg + segundos_maquina × precio_segundo`

Donde:
- `kg_material = area_m2 × densidad_kg_m2`
- `segundos_maquina = (metros_corte × 1000 / velocidad_mm_s) + (perforaciones × tiempo_perforacion_s)`

---

## Chapa doble decapada (acero laminado en frío, CRS / pickled & oiled)

**Densidad:** 7850 kg/m³ | **Gas:** O2

| Calibre | Espesor mm | kg/m² | Vel. corte mm/s | Pierce time s |
|---|---|---|---|---|
| 24 | 0.56 | 4.40  | 280 | 0.10 |
| 22 | 0.7  | 5.50  | 245 | 0.10 |
| 20 | 0.9  | 7.07  | 195 | 0.15 |
| 18 | 1.25 | 9.81  | 140 | 0.20 |
| 16 | 1.6  | 12.56 | 100 | 0.30 |
| 14 | 2.0  | 15.70 | 58  | 0.40 |
| 12 | 2.5  | 19.63 | 38  | 0.60 |

---

## Chapa galvanizada (G90: acero + ~0.275 kg/m² de zinc en ambas caras)

**Densidad base:** 7850 kg/m³ + zinc | **Gas:** O2  
*Velocidades ~25-30% menores que acero desnudo — el zinc altera la dinámica del corte.*

| Calibre | Espesor mm | kg/m² | Vel. corte mm/s | Pierce time s |
|---|---|---|---|---|
| 30 | 0.3  | 2.63  | 350 | 0.10 |
| 25 | 0.5  | 4.20  | 280 | 0.10 |
| 22 | 0.7  | 5.77  | 200 | 0.10 |
| 20 | 0.9  | 7.34  | 155 | 0.15 |
| 18 | 1.25 | 10.09 | 105 | 0.20 |
| 16 | 1.6  | 12.84 | 73  | 0.30 |
| 14 | 2.0  | 15.98 | 45  | 0.40 |

---

## Chapa inoxidable AISI 430 (ferrítico)

**Densidad:** 7700 kg/m³ | **Gas:** N2 (nitrógeno puro)  
*Ligeramente más rápido que 304 — menor contenido de níquel, mejor respuesta al N2.*

| Espesor mm | kg/m² | Vel. corte mm/s | Pierce time s |
|---|---|---|---|
| 0.6  | 4.62  | 290 | 0.10 |
| 0.8  | 6.16  | 250 | 0.10 |
| 1.0  | 7.70  | 200 | 0.15 |
| 1.25 | 9.63  | 150 | 0.20 |
| 1.6  | 12.32 | 105 | 0.30 |
| 2.0  | 15.40 | 70  | 0.50 |
| 2.5  | 19.25 | 43  | 0.80 |

---

## Chapa inoxidable AISI 304 (austenítico)

**Densidad:** 7930 kg/m³ | **Gas:** N2 (nitrógeno puro)  
*Siempre N2 para evitar oxidación del borde.*

| Espesor mm | kg/m² | Vel. corte mm/s | Pierce time s |
|---|---|---|---|
| 0.6  | 4.76  | 260 | 0.10 |
| 0.8  | 6.34  | 225 | 0.10 |
| 1.0  | 7.93  | 180 | 0.15 |
| 1.25 | 9.91  | 135 | 0.20 |
| 1.6  | 12.69 | 95  | 0.30 |
| 2.0  | 15.86 | 63  | 0.50 |
| 2.5  | 19.83 | 39  | 0.80 |

---

## Notas de calibración

- **Pierce time:** valores de referencia. Varían por máquina y estado del cabezal. Calibrar contra la máquina real.
- **Gas:** O2 aumenta velocidad de corte en acero (reacción exotérmica) pero genera borde oxidado. Para piezas decorativas considerar N2 aunque sea más lento.
- **Galvanizado:** el zinc volatiliza al cortar — asegurar ventilación adecuada. Velocidades conservadoras por posible contaminación del lente.
- **430 vs 304:** ambos requieren N2. El 430 (ferrítico) tolera mejor el calor, por eso velocidades ~10% mayores que 304 a igual espesor.
