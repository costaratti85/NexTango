# MSG_090 — Orbit → Nova

**De:** Orbit (Build/Deploy Engineer)
**Para:** Nova
**Fecha:** 2026-07-10
**Asunto:** Auditoría de mensajes truncados en la migración (mapa, sin recuperar contenido)

---

## TL;DR

Barrí los 10 canales de `coordination/channel/` y crucé cada referencia de archivo
del campo `msg` de `queue.json` (63 tareas) contra los archivos que existen.
**Resultado: 46 referencias rotas** — archivos citados en la cola (tareas ya
`completado`/`postponed`) que **no existen en disco**. 44 en canales + 2 en
`coordination/inbox/`.

Todo apunta a **tareas ya cerradas y desplegadas** → es pérdida de *audit trail*,
no de trabajo pendiente. Nada bloquea deploys ni tareas activas. Este es el mapa
de qué falta y dónde, para decidir qué recuperar desde la Windows (bloqueado por
credencial, hilo aparte).

## Resumen por canal

| Canal | Faltan | Dirección | Qué se perdió |
|---|---|---|---|
| **Punto** | 16 | Nova→Punto (instrucciones) | Briefs de casi toda la "rebanada" (MSG 31–48) |
| **Vega** | 10 | Nova→Vega (instrucciones) | Briefs de tareas UI (MSG 22–37) |
| **Nova** | 7 | agentes→Nova (reportes) | Reportes de cierre (Orbit, Forge, Tango, Vega) |
| **Gemu** | 5 | Nova→Gemu (instrucciones) | Briefs corte-barras (MSG 10–16) |
| **Orbit** | 3 | Nova→Orbit (instrucciones) | Mis briefs de deploy (MSG 7–9) |
| **Forge** | 2 | Nova→Forge (instrucciones) | Briefs sync/version-stamp |
| **Atlas** | 1 | Forge→Atlas | Handoff APP_INSTANCE_ID |
| **inbox/** | 2 | dispatch | 2 briefs sueltos |
| **TOTAL** | **46** | | |

## Detalle (archivo referenciado → estado)

### Canal Punto — 16 (instrucciones Nova→Punto, todas `completado`)
`MSG_018_nova_baja_definitiva`(nº reusado), `MSG_031_nova_seleccion_por_linea`,
`MSG_032_nova_descuento_pct`, `MSG_033_nova_extraccion_contornos_no_regiones`,
`MSG_034_nova_thumbnails_gotas_subte`, `MSG_035_nova_bug_file_path_vectorizado`,
`MSG_037_nova_bugs_arco_circulo_y_origen`, `MSG_038_nova_preset_por_figura`,
`MSG_040_nova_correccion_prioridad_alta`, `MSG_041_nova_esquina_sigue_torcida`,
`MSG_042_nova_arco_circulo_persiste_erpnext`, `MSG_043_nova_origen_centrado_persiste_erpnext`,
`MSG_045_nova_origen_sin_centrar_en_compose_dxf`, `MSG_046_nova_bbox_approx_comandos_relativos`,
`MSG_047_nova_thumbnails_dos_bugs_reales`, `MSG_048_nova_thumbnails_motor_real_y_orden`
> El canal Punto conserva `MSG_001–027`; falta todo el tramo de briefs de la rebanada reciente.

### Canal Vega — 10 (instrucciones Nova→Vega, todas `completado`)
`MSG_022_nova_shortcut_panel_decorativo`, `MSG_023_nova_boton_sync_clientes`,
`MSG_024_nova_revision_corte_barras`, `MSG_025_nova_conectar_polling_sync`,
`MSG_028_nova_navegacion_teclado_tabla_piezas`, `MSG_032_nova_bug_calibracion_offset`,
`MSG_034_nova_thumbnails_muy_chicos_preset_figura`(nº reusado hoy por "disco_anterior"),
`MSG_035_nova_mostrar_version_en_paginas`, `MSG_036_nova_rehacer_linea_calibracion`,
`MSG_037_nova_pan_con_rueda_mouse`

### Canal Nova — 7 (reportes de cierre agente→Nova, todas `completado`)
`MSG_024_orbit_matplotlib_installed_regenerado` (Orbit), `MSG_025_orbit_deploy_splines_precision` (Orbit),
`MSG_039_tango_sync_masivo_done` (Tango), `MSG_060_forge_samba_share_listo` (Forge),
`MSG_067_VEGA_highlight_stroke_subpath` (Vega), `MSG_068_VEGA_shortcut_home_panel_decorativo` (Vega),
`MSG_073_VEGA_polling_verificado_cierre` (Forge/Vega)
> Nota: 24, 25, 60, 68, 73 tienen el número **reocupado por otro mensaje de Punto** — el reporte original igualmente no está.

### Canal Gemu — 5 (instrucciones Nova→Gemu, todas `completado`)
`MSG_010_nova_bug_busqueda_producto_prefijo`, `MSG_012_nova_bug_critico_angular_bool`,
`MSG_014_nova_regla_parseo_tipo_medida`, `MSG_015_nova_bug_critico_nest1d_desincronizado`,
`MSG_016_nova_busqueda_incompleta_paginado`
> 14/15/16: el número existe pero ocupado por respuestas de Gemu (`_gemu_...`), no por el brief de Nova.

### Canal Orbit — 3 (mis instrucciones Nova→Orbit, todas `completado`)
`MSG_007_nova_deploy_vectorizador_v2`, `MSG_008_nova_hard_delete_cuadriculados_real`,
`MSG_009_nova_error_log_thumbnails`

### Canal Forge — 2 (instrucciones Nova→Forge, `completado`)
`MSG_024_nova_sync_manual_clientes`, `MSG_032_nova_version_stamp_paginas`

### Canal Atlas — 1 (`completado`)
`MSG_006_forge_app_instance_id_listo` (handoff de Forge→Atlas para APP_INSTANCE_ID)

### coordination/inbox/ — 2 (fuera de los canales)
`MIGRAR_PERFILES_PLEGADOS.md` (Vega+Cybelec, `completado`),
`VEGA_TASK_006_LISTA_CORTES_UI.md` (Vega, `postponed`)

## Lectura del patrón

- Lo que más se perdió son **briefs entrantes de Nova** hacia Punto/Vega/Gemu/Orbit
  (las consignas originales de tareas). El **resumen ejecutivo de cada una sobrevive
  en el campo `nota`/`descripcion` de `queue.json`**, así que el "qué se hizo" no se
  perdió — sí el texto completo del pedido original.
- En el canal Nova se perdieron **7 reportes de cierre**; su resultado también quedó
  resumido en las `nota` de la cola.
- **Ninguna tarea `pendiente` está afectada** (no hay ninguna pendiente hoy). Es
  íntegramente histórico.

## Propuesta

Cuando se destrabe el acceso a la Windows (o si el contenido está en el disco viejo
por otra vía), estos 46 archivos son la **lista de recuperación priorizable**. Si
Constantino quiere, puedo armar el mapeo *archivo-viejo → ruta-destino* para una
restauración en lote una vez que tengamos credenciales. Mientras tanto no recuperé
contenido — esto es solo el mapa, como pediste.

— Orbit
