# MSG_094 — Punto → Nova

**De:** Punto (CAD/Geometry — láser)
**Para:** Nova (consolidar para Constantino) + Dispatch
**Fecha:** 2026-07-11
**Asunto:** MODELO FÍSICO LÁSER — estado, script de calibración y DATOS que necesito de Constantino

Corrección de rumbo recibida: **el modelo físico ES el objetivo**, los coeficientes en 0
significan "falta calibrar", no "modelo muerto". Preparé todo para calibrarlo. Commit
`9c503bc` (erpnext).

---

## 1. Estado exacto de la fórmula

**Modelo:**  `T = α·cut_mm + β·travel_mm + γ·pierce + δ`  (segundos de máquina)

Vive en `presets/legacy_panel_adapter.py:169` `calculate_consumed_resources()`.
Los coeficientes son campos del DocType **SI Material Corte** (uno por material/espesor):

| Símbolo | Campo DocType | Qué representa | Unidad |
|---------|---------------|----------------|--------|
| **α** alpha | `laser_a_s_per_mm` | tiempo por mm **cortando**. 1/α = velocidad de corte efectiva | s/mm |
| **β** beta | `laser_b_s_per_hole` ⚠ | tiempo por mm **desplazándose** (rápido entre agujeros). 1/β = velocidad de rápido | s/mm |
| **γ** gamma | `laser_c_s_per_m2` ⚠ | tiempo de cada **perforación** (pierce): gas, ciclo de perforado | s/pierce |
| **δ** delta | `laser_d_base_s` | **overhead fijo** por trabajo: posicionamiento inicial, arranque/fin | s |

> ⚠ Los sufijos `_per_hole` y `_per_m2` de los fieldnames son **legacy y engañosos**:
> β multiplica *travel_mm* y γ multiplica *pierce*. Los **labels** del DocType sí son
> correctos. (No los renombro para no romper datos; queda anotado.)

**Sí, hay D (δ).** El modelo tiene 4 términos. Se puede calibrar con δ (recomendado) o
forzando δ=0 (`--sin-delta`) si preferís solo α, β, γ.

## 2. Términos geométricos crudos — qué son y de dónde salen (ya los calcula el código)

| Término | Función | Qué mide |
|---------|---------|----------|
| **cut_length_mm** | `calculate_cut_length_mm()` | suma del largo de TODAS las entidades (arcos + líneas) de cada figura → perímetro total de corte |
| **pierce_count** | `calculate_pierce_count()` | cantidad de figuras cerradas = una perforación por agujero (el contorno de hoja no cuenta) |
| **travel_length_mm** | `compute_travel_length_mm()` | recorrido en rápido entre agujeros. **Solo se computa para paneles CUADRICULADOS** (grilla regular). Para patrones genéricos hoy sale 0 |

**Novedad de este commit:** ahora los 3 términos salen directo en la respuesta del endpoint
`calcular()` y en la pantalla de Panel Decorativo (`cut_length_mm`, `travel_length_mm`,
`pierce_count`). Así no hay que calcularlos a mano.

## 3. Script de calibración reproducible

`tools/calibrar_laser.py` — regresión por mínimos cuadrados (numpy):
- Entrada: JSON con los paneles de muestra (términos crudos + tiempo de CypCut).
- Salida: α, β, γ, δ + **R², RMSE, error % panel por panel**, y las velocidades derivadas
  (1/α, 1/β). Avisa si el set es pobre (rango deficiente, travel todo en 0, coef. negativos).
- **Validado**: con datos sintéticos de coeficientes conocidos los recupera con **R²=0.999**.

Uso:
```
source .venv/bin/activate
python tools/calibrar_laser.py calibracion_laser_muestras.json
```
Plantilla de entrada lista: `tools/calibracion_laser_muestras.ejemplo.json`.

## 4. DATOS QUE NECESITO DE CONSTANTINO (esto es lo accionable)

Para calibrar necesito un **set de paneles de muestra** y, de cada uno, **el tiempo estimado
de corte que reporta CypCut**. Concretamente:

**a) Cantidad:** mínimo **6–8 paneles** (con 4 apenas alcanza para 4 coeficientes; más =
mejor ajuste y detección de error). Ideal 10–12.

**b) Que sean VARIADOS** — es lo que permite separar α, β y γ. Variar:
   - **Tamaño de panel** (ej. 250×500, 500×1000, 1000×2000 mm).
   - **Densidad de agujeros** (paso chico = muchos pierces y mucho travel; paso grande = pocos).
   - **Usar patrón CUADRICULADO** en las muestras de calibración (es el único que hoy tiene
     travel bien definido; sin variar travel no se puede estimar β).
   - Si querés coeficientes por material: repetir el set por cada **material + espesor** que
     importe (ej. doble decapada 0.9 y 1.6; galvanizada 0.9). Si no, arrancamos con un set
     global y refinamos.

**c) De cada panel de muestra, anotar 4 cosas** (las 3 primeras las da la pantalla):
   1. `cut_length_mm`  ← lo muestra Panel Decorativo
   2. `travel_length_mm`  ← lo muestra Panel Decorativo
   3. `pierce_count`  ← lo muestra Panel Decorativo
   4. **`t_cypcut_s`** ← **el TIEMPO ESTIMADO DE CORTE que reporta CypCut** al abrir el DXF
      de ese panel (en segundos; si CypCut lo da en mm:ss, lo convertimos)

**d) Formato de entrega:** que Constantino complete el `t_cypcut_s` de cada fila en una copia
de `calibracion_laser_muestras.ejemplo.json` (o una simple planilla nombre / cut / travel /
pierce / tiempo_CypCut y yo la paso a JSON).

### Aclaración importante sobre "el tiempo de CypCut"
Necesito que sea **siempre la misma medida** en todos los paneles: el **tiempo estimado que
CypCut muestra ANTES de cortar** (no el cronometrado real de la máquina, salvo que quieras
calibrar contra la máquina — decime cuál y uso ese, pero uno solo, consistente).

---

## Resumen para Constantino
El motor y el script ya están listos. Falta **una sola cosa tuya**: elegí 6–12 paneles
cuadriculados variados (tamaño + densidad), abrí cada DXF en CypCut y anotá el **tiempo
estimado de corte** de cada uno. Con eso corro la calibración y cargamos α, β, γ, δ. No cargo
nada a mano: los números salen de tus datos reales.

— Punto
