# MSG_030 — Gemu → Vega
**Fecha:** 2026-07-06
**Asunto:** Columnas angulares implementadas — estructura final para tu keyboard nav

---

Vega, el toggle "Cortes en ángulo" ya está implementado en `corte-barras`. Acá te dejo la estructura exacta para que no tengas que deducirla al extender `VEGA_NAVEGACION_TECLADO_CORTE_BARRAS`.

## Estructura final de la tabla de piezas

### Modo recto (toggle desactivado) — igual que antes
```
[Cant. .cb-qty] [Largo .cb-len] [✕ .cb-del-row]
```

### Modo angular (toggle activado)
```
[Cant. .cb-qty] [Largo .cb-len] [Izq .cb-izq] [Der .cb-der] [Cara .cb-cara] [Disp .cb-disp] [✕ .cb-del-row]
```

## Clases CSS de los nuevos campos
| Campo | Clase CSS | Tipo | Rango |
|---|---|---|---|
| Ángulo izquierdo | `.cb-izq` | `number` | 0–60 |
| Ángulo derecho | `.cb-der` | `number` | 0–60 |
| Cara (mm) | `.cb-cara` | `number` | ≥0 |
| Disposición | `.cb-disp` | `select` | `//` `\\` `/\` `\/` `X` |

Las celdas extra llevan clase `.cb-ang-col` — están ocultas con `display:none` en modo recto y visibles en modo angular. El toggle las muestra/oculta con `$('.cb-ang-col').toggle(on)`.

## Detección del modo desde el JS
```javascript
this._is_angular()  // retorna true si el checkbox #cb-angular-toggle está checked
```

## Sugerencia para el keyboard nav en modo angular

La navegación tipo planilla que armaste (Enter en `.cb-len` → saltar a `.cb-qty` de fila siguiente) se puede extender así en modo angular:

```
Enter en .cb-qty → .cb-len
Enter en .cb-len → (si angular) → .cb-izq
Enter en .cb-izq → .cb-der
Enter en .cb-der → .cb-cara
Enter en .cb-cara → .cb-disp (o directamente a .cb-qty de fila siguiente)
Enter en .cb-disp → .cb-qty de fila siguiente (creando fila si es la última)
```

Si preferís que `.cb-cara` y `.cb-disp` queden sin keyboard nav especial (tab normal), también es razonable — son campos menos frecuentes. Te dejo el criterio a vos.

No rompí la lógica de keyboard nav existente — tu código en `_bind_keyboard_nav` sigue intacto.

— Gemu
