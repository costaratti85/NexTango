# MSG_055 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** TASK_057 vectorizador — entregado

```
$ git log origin/erpnext --oneline -1
fee6108 Punto: TASK_057 vectorizador — runner/composer/api + tipo Vectorizado en SI Patron
```

---

## Qué se entregó

### Archivos nuevos en erpnext

| Archivo | Descripción |
|---------|-------------|
| `vectorize/__init__.py` | Paquete |
| `vectorize/runner.py` | Pipeline potrace: imagen → PBM → 5 SVG → figuras con variantes |
| `vectorize/composer.py` | SVG paths → LINE entities → DXF layer CUT |
| `api/vectorizer.py` | `vectorize_image()` + `compose_pattern()` whitelisted |

### Cambios en si_patron.json

- `tipo` Select: agrega `Vectorizado`
- `archivo_dxf` visible también para tipo `Vectorizado`

---

## Contratos publicados antes de implementar

- `MSG_018` → Vega (contrato shapes exactas de r.message)
- `MSG_020` → Forge (pedido `apt install potrace`)

---

## Flujo técnico

1. **`vectorize_image(file_url)`**:
   - Resuelve el File de Frappe → path absoluto
   - Crea `runs_root/{run_id}/` en `<site>/private/vectorize_runs/`
   - Para cada preset: binariza con Pillow (umbral configurable) → PBM → `potrace --svg` → parsea paths cerrados con `xml.etree.ElementTree`
   - Matchea figuras entre presets por cercanía de bbox-center (tol_factor=0.35)
   - Guarda `manifest.json` con `d`, `svg_preview`, `metrics` por variante
   - Devuelve el manifest (run_id + figuras con variantes)

2. **`compose_pattern(run_id, selecciones, ...)`**:
   - Lee manifest del run
   - Para cada figura seleccionada: parsea `d` del SVG → segmentos de línea (beziers cúbicos discretizados con 20 pasos)
   - Escribe DXF con ezdxf, layer CUT
   - Copia a `/planos/generico/patrones/` (o cliente)
   - Crea/actualiza SI Patron con `tipo=Vectorizado`, `activo=1`, `spline_count=0`

---

## Presets definidos (5)

| Nombre | turdsize | alphamax | opttolerance | Umbral |
|--------|----------|----------|--------------|--------|
| Ultra-Fino | 2 | 0.5 | 0.1 | 128 |
| Fino | 5 | 0.8 | 0.2 | 128 |
| Medio | 10 | 1.0 | 0.3 | 128 |
| Grueso | 20 | 1.2 | 0.5 | 128 |
| Umbral-Claro | 5 | 0.8 | 0.2 | 200 |

---

## Para Forge

```bash
# Sin bench migrate (no hay doctype nuevo, solo cambio de opciones en Select)
# Solo confirmar que potrace está instalado (MSG_020):
apt install -y potrace
potrace --version

# Verificar Pillow:
/home/costa/frappe-bench/env/bin/python -c "from PIL import Image; print('OK')"

# Pull + restart:
cd /home/costa/Nextango-erpnext && git pull
bench restart
```

---

## Limitación conocida

El DXF usa coordenadas SVG (Y apunta hacia abajo). Para patrones decorativos simétricos/abstractos no importa. Si el cliente necesita orientación vertical correcta, puede espejar en CypCut.

— Punto
