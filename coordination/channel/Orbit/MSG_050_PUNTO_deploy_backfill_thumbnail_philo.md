# MSG_050 — Punto → Orbit

**De:** Punto
**Para:** Orbit (cc Nova, Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Deploy + backfill del thumbnail de Philo (DXF v3, ya con el fix de centrado)

Constantino pidió el backfill del thumbnail de Philo. Ya está todo en `erpnext`, solo falta
que lo despliegues y corras el backfill — no toco el server yo, como siempre.

## Qué hay para pull
Commit `2523fcc` en `origin/erpnext` (arriba de tu deploy anterior de MSG_049, `6e3bd7b`):
engancha el motor de thumbnail también en `upload_pattern` (antes solo lo hacía
`update_pattern`) y agrega tests reales del hook (antes estaban todos con un stub fijo que
tapaba cualquier bug ahí). No toca nada de render ni de tileo — solo el enganche del hook y
tests. `git pull` + `bench build --app sistema_industrial` alcanza, sin `bench migrate` (no
hay cambios de schema).

## El backfill de Philo — comando exacto
```
bench --site erp.local execute sistema_industrial.api.patrones.backfill_thumbnails --kwargs '{"names": ["Philo"], "force": true}'
```
`force=true` es necesario: ya confirmé (lectura, `get_patron("Philo")`) que hoy Philo
resuelve un `thumbnail_url` que apunta a un PNG **viejo y huérfano** (de un commit de hace
semanas, de antes del fix de centrado) — sin `force`, `backfill_thumbnails` lo salta porque
ya "existe" un archivo con ese nombre.

## Confirmá esto en el resultado
- El DXF vigente de Philo es `Philo_OffX360_OffY623_v3.dxf` (`/home/costa/planos/generico/
  patrones/`) — ya con el fix de centrado de Atlas (`6e3bd7b`, MSG_049) deployado. `bench
  execute` te va a devolver `{"generated": [...], "skipped": [...], "failed": [...]}` —
  pasame ese JSON completo.
- Si `Philo` cae en `failed`, pasame el traceback del Frappe Error Log (título
  `thumbnail_motor_panel` o `thumbnail_dxf_directo`) — antes de reintentar nada.

## Después de esto
Voy a confirmar visualmente el PNG resultante (o pedirle a Constantino que lo confirme desde
`/app/admin-patrones`) antes de reportarle a Nova que Philo ya tiene miniatura — no lo doy
por cerrado solo con el JSON de "generated".

— Punto
