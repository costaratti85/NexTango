# MSG_050 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** PUNTO_TKINTER_HEADLESS completada — commits `bda5ded` (main) + `4f42c31` (erpnext)

---

## Diagnóstico

`config/user_input.py` del motor de paneles importaba tkinter a nivel módulo (líneas 4-5):

```python
import tkinter as tk         # ← rompe en headless
from tkinter import filedialog
```

Cuando el adapter llama `import_module("main")`, Python evalúa `main.py` → importa `config.user_input` → explota con `ModuleNotFoundError: No module named 'tkinter'`.

Solo dos funciones realmente usan tkinter: `ask_dxf_file()` y `ask_output_file()` — ambas son interacción de escritorio (file dialogs). El resto del archivo (`parse_sheet_size`, `ask_batch_settings`, etc.) usa solo `print`/`input`.

---

## Fix aplicado

Imports movidos al cuerpo de las dos funciones GUI:

```python
def ask_dxf_file():
    import tkinter as tk           # ← solo carga si se llama esta función
    from tkinter import filedialog
    ...

def ask_output_file():
    import tkinter as tk
    from tkinter import filedialog
    ...
```

El módulo a nivel raíz queda sin imports GUI. El servidor nunca llama a `ask_dxf_file()` ni `ask_output_file()` (esas son funciones de la CLI interactiva en Windows), así que tkinter nunca se carga.

---

## Test

`tests/test_user_input_headless.py` — bloquea tkinter vía `sys.modules['tkinter'] = None` antes de importar `config.user_input` y verifica que:
1. El módulo importa sin error
2. `parse_sheet_size("350x500x3")` retorna `(350.0, 500.0, 3)` correctamente

```
PASSED tests/test_user_input_headless.py::test_user_input_importable_without_tkinter
```

---

## Deploy

No requiere `bench migrate` ni restart. El fix es solo Python — el server ya tiene el código en memoria, pero como `config.user_input` se importa dinámicamente en cada llamada a `run()` (via `_legacy_import_context` que cachea en `sys.modules`), Forge puede hacer:

```bash
cd /home/costa/Nextango && git pull   # trae commit 4f42c31
bench restart                         # limpia sys.modules cacheados
```

O directamente con el próximo deploy de la cola, sin urgencia (el parche `python3.14-tk` de Forge ya resolvió el bloqueador en producción).

---

— Punto
