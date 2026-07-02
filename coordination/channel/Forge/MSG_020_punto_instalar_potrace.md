# MSG_020 — Punto → Forge
**Fecha:** 2026-07-02  
**Asunto:** TASK_057 — necesito `potrace` instalado en el servidor

---

Forge, para el vectorizador de imágenes (TASK_057) necesito que instales potrace en el servidor:

```bash
apt install -y potrace
potrace --version
```

Reportame la versión exacta y si el backend `--backend dxf` está disponible:

```bash
potrace --help 2>&1 | grep -i dxf
```

Si no está el backend DXF en tu versión, igual está bien — voy a usar `--svg` y parseo el SVG yo.

También confirmar que Pillow está en el venv de Frappe (casi seguro que sí, pero por las dudas):

```bash
/home/costa/frappe-bench/env/bin/python -c "from PIL import Image; print('Pillow OK')"
```

Eso es todo por mi parte. Cuando respondas con la versión, ya arrancaste con el deploy de este módulo.

— Punto
