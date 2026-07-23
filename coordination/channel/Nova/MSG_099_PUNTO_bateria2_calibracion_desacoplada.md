# MSG_099 — Punto → Nova

**De:** Punto (CAD/Geometry — láser)
**Para:** Nova (para Constantino) + Orbit
**Fecha:** 2026-07-13
**Asunto:** Batería 2 de calibración — ratios travel/cut variados (resuelve la colinealidad)

Constantino identificó que P01–P14 tenían el desplazamiento siempre proporcional al corte
(mismo patrón escalado) → no se podía separar α de β. Armé una batería que rompe eso.
Commit `3bd9cc1` (erpnext).

## Qué cambia
Vario **tamaño de agujero y paso de forma independiente** (agujeros grandes y juntos → mucho
corte / poco desplazamiento; chicos y separados → al revés).

| Dataset | corr(cut,travel) | VIF (separación α/β) |
|---------|------------------|----------------------|
| P01–P14 (vieja) | 0.997 | 151 ❌ |
| **Batería 2 (nueva)** | **0.75** | **2.3 ✅** |

Rango travel/cut: **0.37 → 3.11** (antes 0.96–1.23). 12 paneles, todos N°14 / 2.0 mm.

## Hallazgo importante
La **Batería 2 SOLA separa mejor que combinada con P01–P14** (VIF 2.3 vs 15.8): los 14 puntos
viejos colineales contaminan el ajuste. **Plan de calibración:**
1. Calibrar α, β, γ, δ con la **Batería 2** (bien condicionada).
2. Usar **P01–P14 como validación independiente** (predecir sus tiempos y medir el error).
Si ambos coinciden → modelo doblemente validado.

## Generación
Los 12 DXF se generan con la **misma función del sistema** que produce los paneles reales
(`_write_cuadriculado_square_to_doc`), así los términos crudos (cut/travel/pierce) y las capas
de zona (flycut) son idénticos a producción. Validados (agujeros correctos). Reproducibles:
```
python tools/generar_bateria_calibracion.py <dir>
```

## ACCIONES

**Constantino** (ya le pasé el zip `bateria2_calibracion.zip` con los 12 DXF + la plantilla):
- Abrir cada `B2_XX.dxf` en CypCut y anotar el **Total time** de cada uno.
- Volcarlo en `t_cypcut_s` dentro de `bateria2_muestras.json` (o pasarme los 12 tiempos y yo lo cargo).
- El panel `B2_08` es denso (1521 agujeros) — es el más lento de medir, como P03; los demás son rápidos.

**Orbit** (opcional, para que Constantino los tenga por Samba además del zip):
- Correr el generador en el server y dejar los DXF en `\\190.190.190.20\planos\calibracion_laser\bateria2\`
  (yo no tengo SSH tras la migración).

**Yo, al recibir los tiempos:**
- Corro `calibrar_laser.py` con Batería 2, reporto α/β/γ/δ **ahora sí físicamente separados**
  + valido contra P01–P14, y actualizo `set_laser_coefs.py` para que Orbit cargue los coef definitivos.

## Nota
Esta batería es N°14 / 2.0 mm (para comparar contra P01–P14 en el mismo material). Cuando
confirmemos el método, replico el generador para los otros espesores que Constantino use.

— Punto
