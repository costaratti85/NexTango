#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONVERSOR DXF: POLÍGONOS CIRCULARES A CÍRCULOS REALES
------------------------------------------------------
Detecta LWPOLYLINE cerradas que aproximan un círculo (p.ej. dodecágonos de
12 vértices generados por vectorizadores de imagen) y las reemplaza por
entidades CIRCLE usando ajuste por mínimos cuadrados (método Kasa).

Uso: ejecutar directamente con Python. Requiere ezdxf.
"""

import math
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar

try:
    import ezdxf
except ImportError:
    print("Error: la libreria 'ezdxf' no esta instalada.")
    print("  Instalar con: pip install ezdxf")
    sys.exit(1)


# ============================================================================
#                         ALGORITMO CENTRAL
# ============================================================================

def fit_circle_kasa(pts):
    """Ajuste de círculo por mínimos cuadrados (método Kasa).

    Devuelve (cx, cy, r, max_error) o None si la matriz es singular.
    """
    n = len(pts)
    sx = sy = sxx = syy = sxy = sx3 = sy3 = sxxy = sxyy = 0.0
    for x, y in pts:
        sx += x; sy += y
        sxx += x * x; syy += y * y; sxy += x * y
        sx3 += x ** 3; sy3 += y ** 3
        sxxy += x * x * y; sxyy += x * y * y
    A = 2.0 * (sx * sx - n * sxx)
    B = 2.0 * (sx * sy - n * sxy)
    C = 2.0 * (sy * sy - n * syy)
    D = sx * sxx - n * sx3 + sx * syy - n * sxyy
    E = sy * sxx - n * sxxy + sy * syy - n * sy3
    det = A * C - B * B
    if abs(det) < 1e-10:
        return None
    cx = (D * C - B * E) / det
    cy = (A * E - B * D) / det
    r = math.sqrt(sum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / n)
    max_err = max(abs(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - r) for x, y in pts)
    return cx, cy, r, max_err


def try_convert_to_circle(entity, tol_mm, r_min, r_max):
    """Intenta convertir una LWPOLYLINE a círculo.

    Devuelve (cx, cy, r) si la polilínea ajusta dentro de la tolerancia
    y el radio está en rango; de lo contrario devuelve None.
    """
    try:
        if not entity.closed:
            return None
        pts = [(v[0], v[1]) for v in entity.vertices()]
    except Exception:
        return None

    if len(pts) < 6:
        return None

    res = fit_circle_kasa(pts)
    if res is None:
        return None
    cx, cy, r, max_err = res

    if max_err > tol_mm:
        return None
    if r < r_min or r > r_max:
        return None

    # Verificar aspecto cercano a 1:1 (no rectángulo con esquinas redondeadas)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    if min(w, h) < 0.5 * max(w, h):
        return None

    return cx, cy, r


def convert_dxf_poly_to_circles(input_path, output_path, tol_mm=0.5,
                                  r_min=1.0, r_max=200.0,
                                  status_cb=None, progress_cb=None):
    """Carga un DXF, convierte LWPOLYLINE circulares a CIRCLE y guarda.

    Devuelve el conteo de polilíneas convertidas, o -1 si hubo error.
    """
    input_path = os.path.normpath(input_path)
    output_path = os.path.normpath(output_path)

    if not os.path.exists(input_path):
        if status_cb:
            status_cb("Error: el archivo no existe")
        return -1

    if status_cb:
        status_cb("Leyendo archivo DXF...")

    try:
        try:
            with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
                doc = ezdxf.read(f)
        except Exception:
            with open(input_path, "r", encoding="latin-1") as f:
                doc = ezdxf.read(f)
    except Exception as exc:
        if status_cb:
            status_cb(f"Error al leer DXF: {exc}")
        return -1

    msp = doc.modelspace()

    candidates = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    total = len(candidates)

    if status_cb:
        status_cb(f"LWPOLYLINE encontradas: {total}")

    converted = 0
    to_delete = []

    for i, entity in enumerate(candidates):
        if progress_cb:
            progress_cb(i + 1, total)

        result = try_convert_to_circle(entity, tol_mm, r_min, r_max)
        if result is None:
            continue

        cx, cy, r = result
        layer = entity.dxf.layer if entity.dxf.hasattr("layer") else "0"
        circle = msp.add_circle(center=(cx, cy, 0), radius=r)
        circle.dxf.layer = layer
        to_delete.append(entity)
        converted += 1

    for entity in to_delete:
        msp.delete_entity(entity)

    if status_cb:
        status_cb(f"Guardando archivo...")

    try:
        doc.saveas(output_path)
    except Exception as exc:
        if status_cb:
            status_cb(f"Error al guardar: {exc}")
        return -1

    if status_cb:
        status_cb(
            f"Completado: {converted} poligono(s) convertido(s) a circulo(s). "
            f"({total - converted} LWPOLYLINE sin cambios)"
        )

    return converted


# ============================================================================
#                         INTERFAZ GRÁFICA
# ============================================================================

class DXFPolyToCirclesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor DXF: Polígonos circulares → Círculos")
        self.root.geometry("800x580")

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.tol_mm = tk.DoubleVar(value=0.5)
        self.r_min = tk.DoubleVar(value=1.0)
        self.r_max = tk.DoubleVar(value=200.0)
        self.is_running = False

        self._build_ui()

    def _build_ui(self):
        tk.Label(
            self.root,
            text="CONVERSOR DXF — POLÍGONOS CIRCULARES A CÍRCULOS",
            font=("Arial", 14, "bold"),
            fg="#2c3e50",
        ).pack(pady=10)

        tk.Label(
            self.root,
            text="Detecta polilíneas cerradas que aproximan círculos y las reemplaza por entidades CIRCLE",
            font=("Arial", 9),
            fg="#666",
        ).pack()

        # Entrada
        f1 = tk.LabelFrame(self.root, text="1. Archivo de entrada", padx=10, pady=8)
        f1.pack(pady=8, padx=20, fill="x")
        tk.Entry(f1, textvariable=self.input_path, state="readonly", width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="Examinar", command=self._browse_input,
                  bg="#3498db", fg="white").pack(side=tk.RIGHT, padx=5)

        # Parámetros
        f2 = tk.LabelFrame(self.root, text="2. Parámetros", padx=10, pady=8)
        f2.pack(pady=4, padx=20, fill="x")

        row = tk.Frame(f2)
        row.pack(fill="x")

        tk.Label(row, text="Tolerancia (mm):").pack(side=tk.LEFT, padx=5)
        tk.Spinbox(row, from_=0.01, to=5.0, increment=0.05,
                   textvariable=self.tol_mm, width=8).pack(side=tk.LEFT, padx=4)
        tk.Label(row, text="Radio mín (mm):").pack(side=tk.LEFT, padx=(20, 5))
        tk.Spinbox(row, from_=0.1, to=50.0, increment=0.5,
                   textvariable=self.r_min, width=8).pack(side=tk.LEFT, padx=4)
        tk.Label(row, text="Radio máx (mm):").pack(side=tk.LEFT, padx=(20, 5))
        tk.Spinbox(row, from_=1.0, to=5000.0, increment=10.0,
                   textvariable=self.r_max, width=10).pack(side=tk.LEFT, padx=4)

        tk.Label(f2, text="Tolerancia: error máximo permitido en el ajuste. "
                           "Radio mín/máx: filtro para excluir el contorno del archivo.",
                 font=("Arial", 8), fg="#888").pack(anchor="w", padx=5, pady=(4, 0))

        # Salida
        f3 = tk.LabelFrame(self.root, text="3. Archivo de salida", padx=10, pady=8)
        f3.pack(pady=4, padx=20, fill="x")
        tk.Entry(f3, textvariable=self.output_path, state="readonly", width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(f3, text="Guardar como...", command=self._browse_output,
                  bg="#2ecc71", fg="white").pack(side=tk.RIGHT, padx=5)

        # Progreso
        f4 = tk.LabelFrame(self.root, text="4. Progreso", padx=10, pady=8)
        f4.pack(pady=4, padx=20, fill="both", expand=True)

        self.progress = Progressbar(f4, orient="horizontal", length=750, mode="determinate")
        self.progress.pack(pady=4, fill="x")

        self.log = tk.Text(f4, height=8, font=("Consolas", 9), state="disabled")
        scroll = tk.Scrollbar(f4, command=self.log.yview)
        self.log.config(yscrollcommand=scroll.set)
        self.log.pack(side=tk.LEFT, fill="both", expand=True, pady=4)
        scroll.pack(side=tk.RIGHT, fill="y", pady=4)

        # Botón
        self.btn = tk.Button(
            self.root,
            text="CONVERTIR",
            command=self._start,
            bg="#e67e22",
            fg="white",
            font=("Arial", 13, "bold"),
            padx=40,
            pady=12,
        )
        self.btn.pack(pady=10)

        self.status_lbl = tk.Label(self.root, text="Listo", font=("Arial", 9), fg="#27ae60")
        self.status_lbl.pack()

    def _browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("DXF", "*.dxf"), ("Todos", "*.*")])
        if path:
            self.input_path.set(path)
            base, _ = os.path.splitext(path)
            self.output_path.set(base + "_circulos.dxf")
            self._log(f"Archivo: {os.path.basename(path)}")

    def _browse_output(self):
        if not self.input_path.get():
            messagebox.showwarning("Atención", "Primero seleccioná un archivo de entrada")
            return
        path = filedialog.asksaveasfilename(defaultextension=".dxf",
                                             filetypes=[("DXF", "*.dxf")])
        if path:
            self.output_path.set(path)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")
        self.root.update()

    def _start(self):
        if self.is_running:
            return
        if not self.input_path.get():
            messagebox.showerror("Error", "Seleccioná un archivo de entrada")
            return
        if not self.output_path.get():
            messagebox.showerror("Error", "Especificá un archivo de salida")
            return

        self.is_running = True
        self.btn.config(state="disabled", text="Procesando...")
        self.progress["value"] = 0
        self.log.config(state="normal")
        self.log.delete(1.0, tk.END)
        self.log.config(state="disabled")

        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        t0 = time.time()
        try:
            count = convert_dxf_poly_to_circles(
                self.input_path.get(),
                self.output_path.get(),
                tol_mm=self.tol_mm.get(),
                r_min=self.r_min.get(),
                r_max=self.r_max.get(),
                status_cb=lambda m: self.root.after(0, self._log, m),
                progress_cb=lambda c, t: self.root.after(
                    0, lambda: self.progress.__setitem__("value", int(c / t * 100) if t else 0)
                ),
            )
            elapsed = time.time() - t0
            self.root.after(0, self._done, count, elapsed)
        except Exception as exc:
            import traceback
            msg = str(exc) + "\n" + traceback.format_exc()
            self.root.after(0, self._error, msg)

    def _done(self, count, elapsed):
        self.is_running = False
        self.btn.config(state="normal", text="CONVERTIR")
        self.progress["value"] = 100
        if count < 0:
            self.status_lbl.config(text="Error en conversión", fg="#e74c3c")
        elif count == 0:
            messagebox.showinfo("Completado", "No se encontraron polígonos circulares para convertir.")
            self.status_lbl.config(text="Sin conversiones", fg="#f39c12")
        else:
            messagebox.showinfo(
                "Completado",
                f"{count} polígono(s) convertido(s) a círculo(s) en {elapsed:.1f}s\n\n"
                f"Archivo guardado: {os.path.basename(self.output_path.get())}",
            )
            self.status_lbl.config(text=f"{count} círculo(s) en {elapsed:.1f}s", fg="#27ae60")

    def _error(self, msg):
        self.is_running = False
        self.btn.config(state="normal", text="CONVERTIR")
        self.status_lbl.config(text="Error", fg="#e74c3c")
        self._log(f"ERROR: {msg}")
        messagebox.showerror("Error", f"Error en la conversión:\n\n{msg[:500]}")


def main():
    root = tk.Tk()
    DXFPolyToCirclesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
