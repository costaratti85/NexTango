"""Verifica que config/user_input.py del motor de paneles no importa tkinter
a nivel módulo — debe poder importarse en un servidor sin display (headless).
"""
import sys
from importlib import import_module

from sistema_industrial.presets.legacy_panel_adapter import (
    find_legacy_panel_dir,
    _legacy_import_context,
)


def test_user_input_importable_without_tkinter():
    """Importar config.user_input NO debe requerir tkinter."""
    legacy_dir = find_legacy_panel_dir()

    # Bloquea tkinter + submodules para simular servidor sin python3-tk
    blocked = {
        "tkinter": None,
        "tkinter.filedialog": None,
        "tkinter.ttk": None,
    }
    # Borra cualquier versión previa cacheada en sys.modules
    previously_loaded = {}
    for mod in list(sys.modules.keys()):
        if mod == "config.user_input" or mod.startswith("config.user_input."):
            previously_loaded[mod] = sys.modules.pop(mod)

    original = {}
    for key, val in blocked.items():
        if key in sys.modules:
            original[key] = sys.modules[key]
        sys.modules[key] = val  # type: ignore[assignment]

    try:
        with _legacy_import_context(legacy_dir):
            # Debe importar sin levantar ModuleNotFoundError / ImportError
            mod = import_module("config.user_input")

        # Las funciones de cálculo puro deben existir y ser llamables
        assert callable(mod.parse_sheet_size)
        assert callable(mod.ask_batch_settings)

        # parse_sheet_size no necesita tkinter
        w, h, q = mod.parse_sheet_size("350x500x3")
        assert w == 350.0
        assert h == 500.0
        assert q == 3

    finally:
        # Restaura sys.modules
        for key in blocked:
            if key in original:
                sys.modules[key] = original[key]
            else:
                sys.modules.pop(key, None)
        # Restaura módulos que limpiamos antes del test
        sys.modules.update(previously_loaded)
