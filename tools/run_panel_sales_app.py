"""Launch the local Nextango panel sales app."""

from pathlib import Path
import sys
import socket


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps" / "sistema_industrial"
if str(APP_PATH) not in sys.path:
    sys.path.insert(0, str(APP_PATH))

from sistema_industrial.presets.panel_sales_local_app import run_server

PORT = 8765


def _kill_port(port: int) -> None:
    """Kill any process currently listening on the given port (Windows + Unix)."""
    import subprocess, os
    if os.name == "nt":
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True
        )
        pids = set()
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pids.add(parts[-1])
        for pid in pids:
            if pid.isdigit():
                subprocess.run(["taskkill", "/PID", pid, "/F"],
                               capture_output=True)
    else:
        subprocess.run(["fuser", "-k", f"{port}/tcp"],
                       capture_output=True)


if __name__ == "__main__":
    _kill_port(PORT)
    run_server()
