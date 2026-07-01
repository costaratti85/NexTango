"""
dat_decoder.py — Lector del formato de archivos .DAT de Cybelec PC1200 / DNC
============================================================================

Formato reverse-engineereado del CD ADIRA (carpeta Tools/cycad/DATA y los
.DAT del instalador PC1200). Usado por LSTMAT (matrices), LSTPOIN (punzones),
LSTCPLE (pares de útiles), LSTMAC (máquina), Pi*.dat (piezas), DIRPIE (índice).

Estructura:
  - Cabecera: 0x01, <nº de campos>, y una tabla de descriptores de campo
    (tripletas id16 + flag de tipo).
  - Registros: secuencia de campos. Cada campo es:
        * STRING  : 1 byte de longitud N (1..40) + N bytes ASCII.
        * NÚMERO  : float de 4 bytes en MICROSOFT BINARY FORMAT (MBF single),
                    almacenado [exp][mant_lo][mant_mid][mant_hi]:
                        valor = (-1)^sign * (1 + frac) * 2^(exp - 128)
                        sign  = bit7 de mant_hi
                        frac  = ((mant_hi & 0x7f)<<16 | mant_mid<<8 | mant_lo) / 2^23

Este lector usa un parse heurístico secuencial (string vs float) suficiente
para volcar el contenido legible de las tablas. Para un parse exacto campo a
campo haría falta el diccionario de IDs interno del PC1200.
"""
from __future__ import annotations
import sys


def mbf_single(b4: bytes) -> float:
    """Decodifica un float MBF de 4 bytes (orden exponente-primero)."""
    e, m0, m1, m2 = b4[0], b4[1], b4[2], b4[3]
    if e == 0:
        return 0.0
    sign = -1.0 if (m2 & 0x80) else 1.0
    frac = (((m2 & 0x7f) << 16) | (m1 << 8) | m0) / float(1 << 23)
    return sign * (1.0 + frac) * (2.0 ** (e - 128))


def tokenize(data: bytes):
    """Devuelve una lista de tokens ('S', str) | ('F', float) recorriendo el
    archivo de forma secuencial con heurística."""
    toks = []
    i, n = 0, len(data)
    while i < n:
        b = data[i]
        # ¿string de longitud b?
        if 1 <= b <= 40 and i + 1 + b <= n and all(32 <= c < 127 for c in data[i + 1:i + 1 + b]):
            s = data[i + 1:i + 1 + b].decode('latin1')
            if sum(c.isalnum() or c in '-_./: ' for c in s) >= b * 0.8 and any(c.isalnum() for c in s):
                toks.append(('S', s))
                i += 1 + b
                continue
        # ¿float MBF?
        if 0x80 <= b <= 0x9b and i + 4 <= n:
            v = mbf_single(data[i:i + 4])
            if abs(v) < 1e5:
                toks.append(('F', round(v, 3)))
                i += 4
                continue
        i += 1
    return toks


def dump(path: str):
    data = open(path, 'rb').read()
    toks = tokenize(data)
    out = [f"# {path}  ({len(data)} bytes, {len(toks)} tokens)"]
    nums = []
    for t, v in toks:
        if t == 'S':
            if nums:
                out.append("      " + str(nums))
                nums = []
            out.append(f"  STR: {v!r}")
        else:
            nums.append(v)
    if nums:
        out.append("      " + str(nums))
    return "\n".join(out)


if __name__ == "__main__":
    paths = sys.argv[1:] or ["LSTMAT.DAT", "LSTPOIN.DAT", "PI20000.DAT", "DIRPIE.DAT"]
    for p in paths:
        try:
            print(dump(p))
            print()
        except FileNotFoundError:
            print(f"(no encontrado: {p})")
