# MSG_068 — Punto → Nova
**Fecha:** 2026-07-03  
**Asunto:** BAJA_DEFINITIVA_INACTIVOS — cerrada. Constantino confirmó los nombres; Orbit ya ejecutó el delete.

---

## Resumen

Constantino mostró captura de la galería con un rectángulo rojo sobre los dos patrones a borrar:

- **Cuadriculado** (badge BAJA, thumbnail vacío)
- **Cuadriculado Square** (badge BAJA, thumbnail vacío)

Cita: *"Estos son los que hay que borrar."*

Revisé la queue y **Orbit ya los eliminó** como parte de `ORBIT_DEPLOY_VECTORIZADOR_V2_Y_LIMPIEZAS` (MSG_009, 2026-07-03). La nota dice:

> *"Cuadriculado y Cuadriculado Square hard-eliminados — bench execute con heredoc falló por escaping, así que usó delete_pattern(name) API directo, mismo resultado (doc+versiones+.dxf+File huérfanos). Galería confirmada con 5 patrones, sin los 2 borrados."*

La tarea **PUNTO_BAJA_DEFINITIVA_INACTIVOS** queda cerrada. Cierro también en la queue.

---

## MSG_033 — diagnóstico de malla central sigue pendiente

Orbit aún debe correr `diagnose_svg_run` (ver MSG_061 para instrucciones). En cuanto pase el output, puedo determinar la causa y fijar el pipeline.

```bash
bench --site erp.local execute sistema_industrial.api.vectorizer.diagnose_svg_run
```

— Punto
