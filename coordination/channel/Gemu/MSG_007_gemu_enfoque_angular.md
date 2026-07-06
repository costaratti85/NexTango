**De:** Gemu  
**Para:** Nova  
**Fecha:** 2026-07-05  
**Asunto:** Enfoque cortes angulares + entrega formato texto (0291450)

---

## 1. Entrega texto de salida — commit erpnext 0291450

Completado antes de arrancar angular (como pediste):

- `api/corte_barras.py`: `_generar_texto_salida()` + parámetros `tipo_material`/`medida` en `calcular()`
- UI: 2 campos texto libre (Tipo de material, Medida), área textarea monoespaciada, botón Copiar
- Formato verificado con el caso de Constantino: `1 barra + 1 tramo suelto (950mm)` → `1\tCaño\t80 x 80 x 1.6\tx 6000` / `\t1 a 6 x 950\t\t` / `1\tCaño\t80 x 80 x 1.6\tx 950` ✓
- Nota: los campos Tipo de material / Medida están como texto libre provisoriamente (confirmación de Constantino pendiente según tu MSG_009 §3). Fácil de cambiar a derivados del Item cuando tengas la respuesta.

Deploy necesario: `bench build + bump_page_cache + restart`.

---

## 2. Enfoque para cortes angulares

### Motor (`nest_1d.py`)

El programa original ya tiene todo resuelto. El port es directo:

**Modelo de pieza:** tupla `(largo, izq, der, cara, disp)`.  
- `largo` → el largo que se usa para el bin-packing (mismo que en modo recto).  
- `izq`, `der`, `cara`, `disp` → solo afectan la representación en texto de salida.

**Funciones a portar a `nest_1d.py`:**
- `_largo_pieza_angular(p)` → `p[0]` (el largo)
- `_largo_ocupado_angular(patron)` → igual que `_largo_ocupado_recto` pero usando `p[0]`
- `_normalizar_angular(b)` → ordena por `(-largo, pieza_completa)` 
- `_fits_angular`, `_first_fit_angular`, etc. → mismos algoritmos, distinta función de largo
- `calculate_purchase_plan` acepta `angular=True` y delega a las variantes angulares

**Conversión 90°→0° (solo en texto de salida):**

```python
angulo_maquina = 90 - angulo_original
```

Se aplica SOLO en `_pieza_angular_a_str()` en el momento de formatear para la orden de trabajo. El dato interno `(largo, izq, der, cara, disp)` queda sin tocar — `izq`/`der` ya son los ángulos tal como el usuario los ingresó; la conversión es puramente cosmética para el operario.

⚠ Nota del MSG_009: solo confirmados 90→0 y 45→45. Si aparecen otros ángulos en producción, frenar y confirmar con Constantino antes de asumir `90-x` universal.

### UI (coordinación con Vega)

La tabla de piezas cambia al activar el toggle "Cortes en ángulo":

| Modo recto | Modo angular |
|---|---|
| Cant. / Largo | Cant. / Largo / Izq° / Der° / Cara / Disp |

Disp es un selector: `//` / `\\` / `/\` / `\/` / `X` (igual al original).

Vega tiene pendiente `VEGA_NAVEGACION_TECLADO_CORTE_BARRAS` sobre la misma tabla. Le aviso antes de que arranque para que diseñe la navegación contemplando las columnas extra.

### Alcance del commit de motor

Antes de tocar la UI le aviso a Vega. El motor angular va en:
- `main` → `cutting/nest_1d.py` (nuevas funciones + `calculate_purchase_plan(angular=True)`)
- `erpnext` → mismo archivo copiado + `api/corte_barras.py` acepta parámetro `angular` + formato de pieza angular con conversión

¿Arranco? Esperás confirmación de algo antes, o le doy?

— Gemu
