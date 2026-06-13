"""Launch the local Nextango panel sales app."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps" / "sistema_industrial"
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from sistema_industrial.presets.panel_sales_local_app import run_server


if __name__ == "__main__":
    run_server()
