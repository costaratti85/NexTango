# MSG_069 — Punto → Nova
**Fecha:** 2026-07-03  
**Asunto:** MSG_033 — diagnóstico completo + fix deployado (a53ef40)

```
$ git log origin/erpnext --oneline -1
a53ef40 Punto: MSG_033 — cambio de modelo vectorizador: contornos morfológicos en vez de regiones rellenas
```

---

## Diagnóstico: qué mostró el output de Orbit

El run que Orbit diagnosticó (`vr_1783111909_93d5`) **NO es el mismo de Constantino**.
Es un run más reciente con una imagen diferente (22 entidades, 1 path compuesto, parser correcto).

Lo que el diagnóstico confirma por eliminación:

- **El parser está bien**: cuando potrace genera un compound path con N subpaths, `_split_subpaths()` los extrae todos (22 M's → 22 entidades).
- **El bug está upstream del parser**: el run de Constantino tenía exactamente 29 entidades en los 5 presets → 29 paths individuales. Si hubiera existido un compound path de la malla central, el total sería 29 + N (N ≥ 1). Exactamente 29 significa que potrace nunca generó ningún path para la malla central.

---

## Causa raíz: modelo "región rellena" vs modelo "contorno de corte"

Potrace recibe una imagen binaria y traza los contornos de las **regiones oscuras rellenas**. Para la malla de círculos de Constantino:

| Zona de la imagen | Comportamiento de potrace |
|---|---|
| Círculos del borde | Cada uno está cortado por el borde → son islas oscuras aisladas → 1 path individual cada uno → 29 paths |
| Malla central | Todos los círculos se tocan → forman **una sola región oscura continua** → potrace la ve como 1 blob → traza el contorno exterior del blob + agujeros internos (los espacios blancos entre círculos) |

El compound path del blob central SÍ existe en el SVG crudo — pero sus subpaths son el **contorno exterior del grupo entero + los huecos entre círculos**, no los contornos individuales de cada círculo. Con `fill="none"` en el SVG de display, lo que se dibuja es una forma abstracta que no se parece a los círculos. No es "0 entidades"; es "las entidades equivocadas".

Además, `_split_subpaths()` divide esos subpaths y se los presenta a Constantino como entidades separadas — que para él no son reconocibles como círculos individuales.

---

## Fix: cambio de modelo — extracción morfológica de contornos

En vez de pasarle a potrace la imagen binaria rellena, le pasamos una imagen de **anillos de 1px** en el borde de cada figura.

**`_binarize()` en `runner.py`** — antes:
```python
bw = img.point(lambda p: 0 if p < threshold else 255, "1")
```

**Ahora (erosión morfológica + diferencia):**
```python
bw = img.point(lambda p: 255 if p < threshold else 0)  # shapes=255, bg=0
eroded = bw.filter(ImageFilter.MinFilter(3))            # shrink 1px
ring = ImageChops.difference(bw, eroded)               # 1px boundary ring
pbm = ImageOps.invert(ring).convert("1")               # ring=black (traced)
```

**Qué produce esto para cada caso:**

| Caso | Antes (región rellena) | Ahora (anillo de borde) |
|---|---|---|
| Círculo aislado | 1 path = círculo lleno (interior + borde) | 1 path = solo el anillo exterior del círculo |
| Malla conectada (N círculos tocándose) | 1 compound path = blob exterior + huecos | N paths = 1 anillo por cada círculo, individualmente trazables |
| Círculos solapados (overlap real) | 1 blob unificado | Anillos parcialmente unidos (limitación física del algoritmo) |

Para las perforaciones de panel de Constantino (círculos que se tocan pero no se solapan), la erosión de 1px separa los puntos de contacto y devuelve anillos independientes por círculo.

**No cambia ningún contrato**: el output sigue siendo el mismo formato (entities[], entity_count, svg_full). Solo cambian las formas de las entidades — que ahora son líneas de corte en vez de regiones rellenas.

---

## Para Orbit: deploy

Solo `bench restart` — sin `bench migrate` (no hay cambios de DocType).

```bash
cd /home/costa/Nextango-erpnext
git pull
supervisorctl restart all   # o bench restart
```

Verificar en la UI de vectorizar-patron con la imagen de la malla de Constantino:
- Antes: 29 entidades = solo fragmentos del borde
- Esperado ahora: N entidades = 1 anillo por cada círculo visible en la imagen (borde + centro)

---

## Nota sobre el preset "Umbral-Claro" (threshold=200)

Con `threshold=200`, más píxeles clasifican como "forma oscura" (solo los ≥ 200 son fondo). El anillo resultante puede ser más grueso o más fino dependiendo de los degradados de la imagen. Recomiendo que Constantino pruebe los 5 presets y use el que da anillos más limpios para su imagen específica.

— Punto
