# Execution Commands

Crear repo local:
```bash
git init
git add .
git commit -m "Initial SistemaIndustrial Nextango seed"
```

Correr tests:
```bash
PYTHONPATH=apps/sistema_industrial pytest -q
```

Correr demo:
```bash
PYTHONPATH=apps/sistema_industrial python tools/demo_panel_to_cut_batch.py
```

Limpiar generados:
```bash
rm -rf .pytest_cache **/__pycache__ outputs
rm -f quotation_payload.json cut_queue.json *.dxf *.manifest.json
```

Crear remote:
```bash
git remote add origin https://github.com/TU_USUARIO/Sistema_Industrial_Nextango.git
git branch -M main
git push -u origin main
```
