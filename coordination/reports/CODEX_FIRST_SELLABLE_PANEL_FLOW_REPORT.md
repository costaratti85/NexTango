# Reporte Codex - First Sellable Panel Flow

## Objetivo

Dejar una primera herramienta usable de venta interna para cargar un panel decorativo/preset, ejecutar el motor legacy intacto y obtener salida comercial/operativa local sin esperar ERPNext.

## Decision operativa

No se implemento en Frappe porque todavia no hay bench ERPNext listo en este repo. Se creo una interfaz local temporal con `http.server` de Python, sin dependencia nueva de UI.

Comando para Constantino:

```powershell
cd C:\SistemaIndustrial\Nextango
python tools/run_panel_sales_app.py
```

Luego abrir:

```text
http://127.0.0.1:8765
```

## Interfaz creada

Archivo:

- `tools/run_panel_sales_app.py`

Modulo de aplicacion:

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

La pantalla permite ingresar:

- cliente o referencia,
- nombre del trabajo,
- preset/tipo de panel,
- material,
- espesor,
- ancho,
- alto,
- cantidad,
- margen,
- diametro,
- distancia,
- observaciones.

Boton:

- `GENERAR COTIZACION / GENERAR PANEL`

## Flujo conectado

La interfaz llama a:

- `LegacyPanelService`
- `LegacyPanelAdapter`
- motor legacy en `Paneles decorativos funcionando`

No se modifico el algoritmo legacy ni ningun archivo dentro de `Paneles decorativos funcionando`.

## Salida generada

Carpeta:

- `outputs/panel_sales_demo/`

Archivos:

- `panel_result.json`
- `quotation_payload.json`
- `cut_piece_payload.json`
- `manifest.json`
- `VENTA-CLIENTE-DEMO-PANEL-VENTA-MOSTRADOR_legacy_panel.dxf`

La pantalla muestra:

- resumen del pedido,
- medidas,
- material y espesor,
- cantidad,
- ruta del DXF,
- recursos calculados,
- advertencias,
- links a archivos generados,
- proximos pasos operativos.

## Cambios de codigo

- `apps/sistema_industrial/sistema_industrial/presets/panel_service.py`
  - Agrega `job_name` y `observations` al input normalizado.
  - Incluye esos datos en el payload estilo ERPNext.
- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
  - Servidor HTTP local, formulario, validacion, ejecucion y render de resultado.
- `tools/run_panel_sales_app.py`
  - Lanzador simple sin requerir `PYTHONPATH`.
- `tests/test_panel_sales_local_app.py`
  - Tests de armado de input, generacion de archivos y POST HTTP real del formulario.

## Tests corridos

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python -m pytest -q
```

Resultado:

```text
23 passed, 7 warnings in 2.58s
```

Las warnings vienen de `ezdxf`/`pyparsing`.

## Demo de generacion corrida

Se genero una corrida local hacia:

- `outputs/panel_sales_demo/panel_result.json`
- `outputs/panel_sales_demo/quotation_payload.json`
- `outputs/panel_sales_demo/cut_piece_payload.json`
- `outputs/panel_sales_demo/manifest.json`
- `outputs/panel_sales_demo/VENTA-CLIENTE-DEMO-PANEL-VENTA-MOSTRADOR_legacy_panel.dxf`

## Limitaciones

- La interfaz local soporta hoy el preset `Tresbolillo circular`.
- No abre automaticamente el navegador; se ejecuta el comando y se abre `http://127.0.0.1:8765`.
- No persiste en ERPNext todavia.
- No consulta Tango real.
- El motor legacy devuelve `cut_length_mm=0` y `pierce_count=0`; se preserva tal cual y se muestra advertencia.
- `outputs/` esta ignorado por git; la herramienta regenera la carpeta cuando se usa.

## Limites respetados

- No se modifico el algoritmo legacy.
- No se toco ERPNext core.
- No se implemento nesting.
- No se implemento G-code.
- No se conecto Tango real.

## Proximos pasos

1. Agregar mas presets legacy al selector cuando se normalicen los DXF/rutas de entrada.
2. Guardar cada corrida en subcarpeta por cliente/trabajo para historial local.
3. Conectar este mismo servicio al DocType `SI Preset` cuando exista bench ERPNext.
4. Persistir DXF como File privado en Frappe.
5. Crear DocTypes reales para registrar `quotation_payload`, `cut_piece_payload` y manifest.
6. Definir permisos de vendedor/taller antes de exponerlo fuera de red interna.
