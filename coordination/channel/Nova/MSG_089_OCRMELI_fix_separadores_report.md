**De:** OCR-MELI (sesión satélite)
**Para:** Nova (→ Dispatch / Constantino)
**Fecha:** 2026-07-20
**Asunto:** Fix separadores miles/decimales OCR Mercado Pago — hecho y verificado en copia local; falta credencial para aplicar en `.9`

---

## Qué encontré

El bug estaba **solo en el formateo de salida**, no en el parseo.

- **Parseo del número escaneado** (`_ocr_monto_a_float`, línea ~590): ya usaba regla **fija** correcta (`.`=miles, `,`=decimal, formato MP). **No se tocó.**
- **Formateo de salida** (`formatear_importe`, línea ~629): **dependía del locale del sistema operativo**. Detectaba los separadores con `_detect_separators()` (locale del SO) vía `SEP_MILES`/`SEP_DECIMAL`. En una máquina cuyo locale **no** es es-AR (US o POSIX/C), invertía a formato US.

**Por qué acá "parecía andar":** esta Mint tiene `LANG=es_AR.UTF-8`, así que localmente el código viejo ya salía bien. El `.pyw` corre en la máquina `vendo`/`.9`, cuyo locale evidentemente devuelve separadores US → de ahí el número mal.

### Evidencia (código VIEJO bajo locale no-AR)
```
'12.500'        -> '$ 12,500.00'      (mal, US)
'1.234.567,89'  -> '$ 1,234,567.89'   (mal, US)
'234,5'         -> '$ 234.50'         (mal, US)
```

## El fix exacto

Archivo: `ocr_transferencias.pyw` (copia local `~/Claude/Cloud Code OCR Mercadopago/`). Backup: `ocr_transferencias.pyw.bak_20260720`.

**Cambio 1** — dejar de depender del locale del SO (línea ~567):
```python
# antes:
SEP_MILES, SEP_DECIMAL = _detect_separators()
# ahora (fijo es-AR):
SEP_MILES, SEP_DECIMAL = ".", ","
```

**Cambio 2** — `formatear_importe()` reescrito a formato es-AR fijo + redondeo en centavos enteros (arregla además un bug latente: `round((valor-entero)*100)` podía dar `100` y escribir `,100`):
```python
def formatear_importe(valor: float) -> str:
    try:
        centavos = int(round(abs(float(valor)) * 100))
    except (TypeError, ValueError):
        return "$ 0,00"
    entero, dec = divmod(centavos, 100)
    signo = "-" if valor < 0 else ""
    miles = f"{entero:,}".replace(",", ".")
    return f"$ {signo}{miles},{dec:02d}"
```

Esto cubre las dos exigencias: **`.`=miles / `,`=decimales fijo** y **siempre 2 decimales** (aunque sean cero). `_detect_separators()` queda definida pero sin uso (no la borré para no tocar de más).

## Casos de prueba (verificados en las funciones reales, es-AR **y** C/POSIX → idéntico)

| Entrada (raw MP) | Antes (locale no-AR) | Ahora |
|---|---|---|
| `12.500` | `$ 12,500.00` ❌ | `$ 12.500,00` ✅ |
| `15000` | `$ 15,000.00` ❌ | `$ 15.000,00` ✅ |
| `234,5` | `$ 234.50` ❌ | `$ 234,50` ✅ |
| `1.234.567,89` | `$ 1,234,567.89` ❌ | `$ 1.234.567,89` ✅ |
| `1.000.000` | `$ 1,000,000.00` ❌ | `$ 1.000.000,00` ✅ |

Bordes: `0 → $ 0,00`, `5 → $ 5,00`, `999.999 → $ 1.000,00` (redondeo OK), `1234.005 → $ 1.234,01`. Sintaxis del archivo completo: OK (`ast.parse`).

## Acceso a `.9` — BLOQUEADO por credenciales

- `smbclient -L //190.190.190.9` con login anónimo **lista** los shares (`Contaduria, Administracion, Ventas, Compartido, IPC$`).
- Pero conectar al tree `//190.190.190.9/Ventas` (y `Compartido`) con anónimo → **`NT_STATUS_ACCESS_DENIED`**.

**No adiviné credenciales.** Para tocar directamente el archivo de `.9` necesito, exactamente:
- **usuario y contraseña** de una cuenta con acceso al share `Ventas` del equipo `190.190.190.9` (y, si aplica, el **dominio/workgroup**).

Con eso puedo montar/copiar así (ejemplo, sin las claves):
```
smbclient "//190.190.190.9/Ventas" -U 'USUARIO%CLAVE' \
  -c 'cd "OCR Mercadopago"; get ocr_transferencias.pyw'   # traer y diffear
# ...y tras confirmar, put del archivo corregido.
```
Antes de sobrescribir en `.9` voy a **diffear** el archivo remoto contra mi copia local (pueden no ser idénticos) y a hacer **backup del remoto**, para no pisar cambios que sólo estén en `.9`.

## Estado

- ✅ Fix hecho y verificado en copia local (`~/Claude/Cloud Code OCR Mercadopago/ocr_transferencias.pyw`).
- ⏳ Falta: **credenciales del share `Ventas` de `.9`** para aplicarlo en el archivo de producción.
- Nota aparte: `Version 1 lista/ocr_transferencias.pyw` es **distinto** al principal (más viejo/chico). Confirmar si también hay que corregirlo o si quedó obsoleto.

— OCR-MELI
