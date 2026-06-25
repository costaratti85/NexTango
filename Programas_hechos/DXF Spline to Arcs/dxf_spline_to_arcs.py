#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CONVERSOR DXF: SPLINES A ARCOS - CON CAPA ROJA
------------------------------------------------
Convierte splines en arcos y líneas, y los coloca en una capa nueva (ROJO)
sin eliminar las splines originales.
"""

import bisect
import os
import sys
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.ttk import Progressbar
import threading
import time

try:
    import ezdxf
    from ezdxf.colors import RGB
except ImportError:
    print("❌ Error: La librería 'ezdxf' no está instalada.")
    print("   Instálala con: pip install ezdxf")
    sys.exit(1)


# ============================================================================
#                         FUNCIONES DE CONVERSIÓN
# ============================================================================

def normalize_path(path):
    if not path:
        return path
    path = path.strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    if path.startswith("'") and path.endswith("'"):
        path = path[1:-1]
    path = path.replace('\\\\\\\\', '//')
    path = path.replace('\\\\', '//')
    path = path.replace('\\', '/')
    path = os.path.normpath(path)
    return path


def fit_arc_to_points(points, tolerance):
    if len(points) < 3:
        return None
    
    p1 = points[0]
    p2 = points[len(points)//2]
    p3 = points[-1]
    
    try:
        v1x = p2.x - p1.x
        v1y = p2.y - p1.y
        v2x = p3.x - p1.x
        v2y = p3.y - p1.y
        
        cross = v1x * v2y - v1y * v2x
        if abs(cross) < 1e-10:
            return None
        
        d1 = (p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2) / 2
        d2 = (p3.x**2 + p3.y**2 - p1.x**2 - p1.y**2) / 2
        
        det = (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
        if abs(det) < 1e-10:
            return None
        
        cx = (d1 * (p3.y - p1.y) - d2 * (p2.y - p1.y)) / det
        cy = ((p2.x - p1.x) * d2 - (p3.x - p1.x) * d1) / det
        
        center = (cx, cy)
        radius = math.sqrt((p1.x - cx)**2 + (p1.y - cy)**2)
        
        if radius < 0.001 or radius > 10000:
            return None
        
        for pt in points:
            dist = math.sqrt((pt.x - cx)**2 + (pt.y - cy)**2)
            if abs(dist - radius) > tolerance:
                return None
        
        angle_start = math.atan2(p1.y - cy, p1.x - cx)
        angle_mid = math.atan2(p2.y - cy, p2.x - cx)
        angle_end = math.atan2(p3.y - cy, p3.x - cx)
        
        if angle_end < angle_start:
            angle_end += 2 * math.pi
        if angle_mid < angle_start:
            angle_mid += 2 * math.pi
        if angle_mid > angle_end:
            angle_start, angle_end = angle_end, angle_start
            angle_start -= 2 * math.pi
        
        return (cx, cy, radius, math.degrees(angle_start), math.degrees(angle_end), len(points))
    except:
        return None


def _find_corner_indices(points, corner_threshold_deg=20.0):
    """Return set of indices where consecutive chord directions change by more
    than corner_threshold_deg — these are tangent discontinuities (corners,
    cusps) where the arc-fitting window must not cross."""
    corners = set()
    for i in range(1, len(points) - 1):
        dx1 = points[i].x - points[i - 1].x
        dy1 = points[i].y - points[i - 1].y
        dx2 = points[i + 1].x - points[i].x
        dy2 = points[i + 1].y - points[i].y
        len1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
        len2 = math.sqrt(dx2 * dx2 + dy2 * dy2)
        if len1 < 1e-9 or len2 < 1e-9:
            continue
        cos_a = (dx1 * dx2 + dy1 * dy2) / (len1 * len2)
        cos_a = max(-1.0, min(1.0, cos_a))
        if math.degrees(math.acos(cos_a)) > corner_threshold_deg:
            corners.add(i)
    return corners


def discretize_and_convert_spline(spline_entity, modelspace, layer_name):
    arcs = []
    lines = []
    
    try:
        points = []
        tolerance = 0.1  # Tolerancia fija para discretización
        
        if hasattr(spline_entity, 'flattening'):
            try:
                points = list(spline_entity.flattening(tolerance))
            except:
                pass
        if not points:
            try:
                points = list(spline_entity.vertices())
            except:
                pass
        if not points:
            try:
                pts = list(spline_entity.control_points())
                if len(pts) >= 2:
                    points = []
                    for i in range(len(pts) - 1):
                        points.append(pts[i])
                    points.append(pts[-1])
            except:
                pass
        
        if not points or len(points) < 3:
            return [], []
        
        max_points = 500
        if len(points) > max_points:
            step = max(1, len(points) // max_points)
            points = points[::step]

        # Pre-detect tangent discontinuities so the fitting window never
        # crosses a corner and produces a spurious arc spanning two curves.
        corners = _find_corner_indices(points)
        sorted_corners = sorted(corners)

        i = 0
        while i < len(points) - 2:
            # First corner index strictly after i — cap the fitting window there
            # so no segment ever spans a tangent discontinuity.
            idx = bisect.bisect_right(sorted_corners, i)
            corner_limit = sorted_corners[idx] if idx < len(sorted_corners) else len(points)

            best_end = i + 2
            best_result = None

            for end in range(i + 2, min(i + 50, corner_limit, len(points))):
                segment = points[i:end+1]
                result = fit_arc_to_points(segment, tolerance)
                if result:
                    best_result = result
                    best_end = end
                else:
                    if end == i + 2:
                        break

            if best_result:
                cx, cy, radius, start_angle, end_angle, num_points = best_result
                span = abs(end_angle - start_angle) % 360
                if radius > 500 or span < 1.0:
                    # Nearly-straight arc — emit LINE from start to end point
                    p1 = points[i]
                    p2 = points[best_end]
                    try:
                        line = modelspace.add_line(p1, p2)
                        line.dxf.layer = layer_name
                        lines.append(line)
                    except:
                        pass
                else:
                    try:
                        new_arc = modelspace.add_arc(
                            center=(cx, cy, 0),
                            radius=radius,
                            start_angle=start_angle,
                            end_angle=end_angle
                        )
                        new_arc.dxf.layer = layer_name
                        arcs.append(new_arc)
                    except:
                        pass
                i = best_end
            else:
                p1 = points[i]
                p2 = points[i + 1]
                try:
                    line = modelspace.add_line(p1, p2)
                    line.dxf.layer = layer_name
                    lines.append(line)
                except:
                    pass
                i += 1
        
        while i < len(points) - 1:
            p1 = points[i]
            p2 = points[i + 1]
            try:
                line = modelspace.add_line(p1, p2)
                line.dxf.layer = layer_name
                lines.append(line)
            except:
                pass
            i += 1
    except Exception as e:
        print(f"   ❌ Error en discretización: {e}")
    
    return arcs, lines


def process_lwpolyline(polyline, modelspace, layer_name):
    arcs = []
    lines = []
    
    try:
        vertices = list(polyline.vertices())
        if len(vertices) < 2:
            return [], []
        
        is_closed = polyline.closed
        
        for i in range(len(vertices)):
            current = vertices[i]
            next_idx = (i + 1) % len(vertices) if is_closed else i + 1
            
            if next_idx >= len(vertices):
                break
            
            next_vertex = vertices[next_idx]
            
            p1 = current[0] if isinstance(current, tuple) else current
            p2 = next_vertex[0] if isinstance(next_vertex, tuple) else next_vertex
            
            if len(current) > 4:
                bulge = current[4]
            else:
                bulge = 0
            
            if bulge == 0:
                line = modelspace.add_line(p1, p2)
                line.dxf.layer = layer_name
                lines.append(line)
            else:
                try:
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    chord_length = math.sqrt(dx*dx + dy*dy)
                    
                    if chord_length < 0.001:
                        continue
                    
                    radius = abs(chord_length / (2 * math.sin(2 * math.atan(bulge))))
                    perp_x = -dy / chord_length
                    perp_y = dx / chord_length
                    sagitta = radius * math.cos(2 * math.atan(bulge))
                    
                    center_x = (p1.x + p2.x) / 2 + perp_x * sagitta
                    center_y = (p1.y + p2.y) / 2 + perp_y * sagitta
                    
                    angle1 = math.atan2(p1.y - center_y, p1.x - center_x)
                    angle2 = math.atan2(p2.y - center_y, p2.x - center_x)
                    
                    start_angle = math.degrees(angle1)
                    end_angle = math.degrees(angle2)
                    
                    if bulge < 0:
                        start_angle, end_angle = end_angle, start_angle
                    
                    new_arc = modelspace.add_arc(
                        center=(center_x, center_y, 0),
                        radius=abs(radius),
                        start_angle=start_angle,
                        end_angle=end_angle
                    )
                    new_arc.dxf.layer = layer_name
                    arcs.append(new_arc)
                except:
                    line = modelspace.add_line(p1, p2)
                    line.dxf.layer = layer_name
                    lines.append(line)
    except Exception as e:
        print(f"   ❌ Error procesando LWPOLYLINE: {e}")
    
    return arcs, lines


def convert_dxf_with_progress(input_file, output_file, tolerance=0.1, status_callback=None, progress_callback=None):
    input_file = normalize_path(input_file)
    output_file = normalize_path(output_file)
    
    if not os.path.exists(input_file):
        if status_callback:
            status_callback(f"❌ Error: El archivo no existe")
        return -1
    
    if status_callback:
        status_callback("📖 Leyendo archivo DXF...")
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            doc = ezdxf.read(f)
    except:
        with open(input_file, 'r', encoding='latin-1') as f:
            doc = ezdxf.read(f)
    
    modelspace = doc.modelspace()
    
    # Crear una nueva capa en ROJO (color 1 = rojo en AutoCAD)
    try:
        # Verificar si la capa ya existe
        if 'ARCOS_CONVERTIDOS' not in doc.layers:
            new_layer = doc.layers.new('ARCOS_CONVERTIDOS')
            new_layer.color = 1  # Rojo
            if status_callback:
                status_callback("🆕 Capa 'ARCOS_CONVERTIDOS' creada (color ROJO)")
        else:
            # Asegurar que la capa existente sea roja
            doc.layers.get('ARCOS_CONVERTIDOS').color = 1
            if status_callback:
                status_callback("🔄 Capa 'ARCOS_CONVERTIDOS' ya existía, configurada a ROJO")
    except Exception as e:
        if status_callback:
            status_callback(f"⚠️ Error al crear capa: {e}")
    
    # Contar splines y polilíneas con curvas
    spline_count = 0
    polyline_count = 0
    all_splines = []
    all_polylines = []
    
    for entity in modelspace:
        try:
            et = entity.dxftype()
            if et == 'SPLINE':
                spline_count += 1
                all_splines.append(entity)
            elif et == 'LWPOLYLINE':
                has_arc = False
                try:
                    for v in entity.vertices():
                        if len(v) > 4 and v[4] != 0:
                            has_arc = True
                            break
                except:
                    pass
                if has_arc:
                    polyline_count += 1
                    all_polylines.append(entity)
        except:
            pass
    
    if status_callback:
        status_callback(f"📊 Splines: {spline_count}, Polilíneas con curvas: {polyline_count}")
    
    converted_count = 0
    total_arcs = 0
    total_lines = 0
    
    total_to_process = spline_count + polyline_count
    processed = 0
    
    # Capa destino
    target_layer = 'ARCOS_CONVERTIDOS'
    
    # Convertir splines
    for entity in all_splines:
        processed += 1
        if progress_callback:
            progress_callback(processed, total_to_process)
        if status_callback:
            status_callback(f"🔄 SPLINE {processed}/{total_to_process}...")
        
        arcs, lines = discretize_and_convert_spline(entity, modelspace, target_layer)
        if arcs or lines:
            converted_count += 1
            total_arcs += len(arcs)
            total_lines += len(lines)
            if status_callback:
                status_callback(f"   ✅ {len(arcs)} arcos, {len(lines)} líneas")
        else:
            if status_callback:
                status_callback(f"   ⚠️ No se pudo convertir")
    
    # Convertir polilíneas con curvas
    for entity in all_polylines:
        processed += 1
        if progress_callback:
            progress_callback(processed, total_to_process)
        if status_callback:
            status_callback(f"🔄 LWPOLYLINE {processed}/{total_to_process}...")
        
        arcs, lines = process_lwpolyline(entity, modelspace, target_layer)
        if arcs or lines:
            converted_count += 1
            total_arcs += len(arcs)
            total_lines += len(lines)
            if status_callback:
                status_callback(f"   ✅ {len(arcs)} arcos, {len(lines)} líneas")
        else:
            if status_callback:
                status_callback(f"   ⚠️ No se pudo convertir")
    
    # NO ELIMINAMOS las splines originales, las dejamos para comparar
    
    if status_callback:
        status_callback(f"💾 Guardando archivo...")
    
    # Guardar el archivo
    try:
        doc.saveas(output_file)
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Error al guardar: {e}")
        return -1
    
    if status_callback:
        status_callback(f"✅ ¡COMPLETADO! {converted_count} curvas → {total_arcs} arcos, {total_lines} líneas")
        status_callback(f"📌 Las splines originales se conservan en sus capas originales")
        status_callback(f"📌 Los nuevos arcos/líneas están en la capa 'ARCOS_CONVERTIDOS' (ROJO)")
    
    return converted_count


# ============================================================================
#                         INTERFAZ GRÁFICA
# ============================================================================

class DXFConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor DXF: Splines a Arcos (Capa ROJA)")
        self.root.geometry("800x650")
        
        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()
        self.tolerance = tk.DoubleVar(value=0.1)
        self.is_running = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Título
        titulo = tk.Label(self.root, text="CONVERSOR DXF - SPLINES A ARCOS", 
                         font=("Arial", 16, "bold"), fg="#2c3e50")
        titulo.pack(pady=10)
        
        # Subtítulo
        subtitulo = tk.Label(self.root, text="Los arcos convertidos se guardan en capa ROJA (sin eliminar originales)", 
                            font=("Arial", 10), fg="#e74c3c")
        subtitulo.pack(pady=5)
        
        # --- Archivo de entrada ---
        frame1 = tk.LabelFrame(self.root, text="1. Archivo de entrada", padx=10, pady=10)
        frame1.pack(pady=5, padx=20, fill="x")
        
        tk.Entry(frame1, textvariable=self.input_file_path, state='readonly', width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(frame1, text="Examinar", command=self.select_input, bg="#3498db", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # --- Parámetros ---
        frame2 = tk.LabelFrame(self.root, text="2. Parámetros", padx=10, pady=10)
        frame2.pack(pady=5, padx=20, fill="x")
        
        tk.Label(frame2, text="Tolerancia (mm):").pack(side=tk.LEFT, padx=5)
        tk.Spinbox(frame2, from_=0.001, to=5.0, increment=0.05, 
                  textvariable=self.tolerance, width=12).pack(side=tk.LEFT, padx=5)
        tk.Label(frame2, text="(0.01 = preciso | 1.0 = rápido)", font=("Arial", 8), fg="#7f8c8d").pack(side=tk.LEFT, padx=10)
        
        # --- Archivo de salida ---
        frame3 = tk.LabelFrame(self.root, text="3. Archivo de salida", padx=10, pady=10)
        frame3.pack(pady=5, padx=20, fill="x")
        
        tk.Entry(frame3, textvariable=self.output_file_path, state='readonly', width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(frame3, text="Guardar", command=self.select_output, bg="#2ecc71", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # --- Progreso ---
        frame4 = tk.LabelFrame(self.root, text="4. Progreso", padx=10, pady=10)
        frame4.pack(pady=5, padx=20, fill="both", expand=True)
        
        self.progress = Progressbar(frame4, orient="horizontal", length=750, mode="determinate")
        self.progress.pack(pady=5, fill="x")
        
        self.status_text = tk.Text(frame4, height=12, font=("Consolas", 9), state='disabled')
        self.status_text.pack(pady=5, fill="both", expand=True)
        
        scroll = tk.Scrollbar(frame4, orient="vertical", command=self.status_text.yview)
        scroll.pack(side=tk.RIGHT, fill="y")
        self.status_text.config(yscrollcommand=scroll.set)
        
        # --- BOTÓN CONVERTIR ---
        self.convert_btn = tk.Button(
            self.root,
            text="🔄 CONVERTIR",
            command=self.start_conversion,
            bg="#e67e22",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=50,
            pady=15
        )
        self.convert_btn.pack(pady=15)
        
        # --- Estado ---
        self.status_label = tk.Label(self.root, text="✅ Listo", font=("Arial", 10), fg="#27ae60")
        self.status_label.pack(pady=5)
    
    def select_input(self):
        path = filedialog.askopenfilename(filetypes=[("DXF files", "*.dxf")])
        if path:
            self.input_file_path.set(path)
            base = os.path.splitext(path)[0]
            self.output_file_path.set(f"{base}_convertido.dxf")
            self.add_status(f"📂 Cargado: {os.path.basename(path)}")
    
    def select_output(self):
        if not self.input_file_path.get():
            messagebox.showwarning("Atención", "Primero selecciona un archivo de entrada")
            return
        path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF files", "*.dxf")])
        if path:
            self.output_file_path.set(path)
    
    def add_status(self, msg):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, msg + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')
        self.root.update()
    
    def update_progress(self, current, total):
        if total > 0:
            pct = int((current / total) * 100)
            self.progress['value'] = pct
            self.root.update()
    
    def update_status(self, msg):
        self.status_label.config(text=msg[:70])
        self.add_status(msg)
        self.root.update()
    
    def start_conversion(self):
        if self.is_running:
            return
        
        if not self.input_file_path.get():
            messagebox.showerror("Error", "Selecciona un archivo de entrada")
            return
        
        if not self.output_file_path.get():
            messagebox.showerror("Error", "Especifica un archivo de salida")
            return
        
        self.is_running = True
        self.convert_btn.config(state='disabled', text="⏳ TRABAJANDO...")
        self.progress['value'] = 0
        
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state='disabled')
        
        thread = threading.Thread(target=self.run_conversion, daemon=True)
        thread.start()
    
    def run_conversion(self):
        try:
            start_time = time.time()
            result = convert_dxf_with_progress(
                self.input_file_path.get(),
                self.output_file_path.get(),
                self.tolerance.get(),
                status_callback=self.update_status,
                progress_callback=self.update_progress
            )
            elapsed = time.time() - start_time
            self.root.after(0, lambda r=result, e=elapsed: self.finish_conversion(r, e))
        except Exception as ex:
            import traceback
            error_msg = str(ex) + "\n" + traceback.format_exc()
            self.root.after(0, lambda msg=error_msg: self.error_conversion(msg))
    
    def finish_conversion(self, result, elapsed):
        self.is_running = False
        self.convert_btn.config(state='normal', text="🔄 CONVERTIR")
        
        if result >= 0:
            if result == 0:
                messagebox.showinfo("Completado", "No se encontraron curvas para convertir")
                self.status_label.config(text="⚠️ No hay curvas para convertir", fg="#f39c12")
            else:
                messagebox.showinfo(
                    "¡Éxito!", 
                    f"✅ {result} curvas convertidas en {elapsed:.1f} segundos\n\n"
                    f"📌 Los nuevos arcos/líneas están en la capa 'ARCOS_CONVERTIDOS' (ROJO)\n"
                    f"📌 Las splines originales se conservan"
                )
                self.status_label.config(text=f"✅ {result} curvas convertidas en {elapsed:.1f}s", fg="#27ae60")
                self.progress['value'] = 100
        else:
            self.status_label.config(text="❌ Error en conversión", fg="#e74c3c")
    
    def error_conversion(self, msg):
        self.is_running = False
        self.convert_btn.config(state='normal', text="🔄 CONVERTIR")
        self.status_label.config(text=f"❌ Error en conversión", fg="#e74c3c")
        self.add_status(f"❌ ERROR: {msg}")
        messagebox.showerror("Error", f"Error en la conversión:\n\n{msg[:500]}")


# ============================================================================
#                         PUNTO DE ENTRADA
# ============================================================================

def main():
    root = tk.Tk()
    app = DXFConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()