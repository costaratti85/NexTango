# PUNTO_TASK_020 — Thumbnail debe mostrar panel generado, no el patrón directo

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta — sprint abierto

---

## Síntoma

El thumbnail de cada patrón muestra el patrón sin repetir (la figura del DXF directamente). Lo correcto es mostrar un panel de 300×300mm con margen de 15mm generado con ese patrón — es decir, el patrón replicado/teselado como quedaría en un panel real.

## Contexto

En TASK_016, Punto implementó `_render_dxf_thumbnail()` que renderiza el DXF del patrón directamente con ezdxf + matplotlib para evitar el bug del bbox incorrecto del motor legacy. Ese fix resolvió el crash, pero el resultado visual no es el correcto: el thumbnail debe representar cómo va a quedar el panel, no el archivo fuente.

## Lo que debe hacer el thumbnail

Generar un panel de **300×300mm con margen de 15mm** usando el motor de tiling (igual que un panel real), y renderizar ese resultado como PNG. Si el motor falla para algún patrón (ej. por bbox incorrecto como pasaba antes), manejar el error con gracia — mostrar el patrón directo como fallback, no romper.

## Criterio de aceptación

1. El thumbnail de Subte muestra el patrón Subte repetido en una grilla de 300×300mm
2. El thumbnail de Philo muestra el patrón Philo repetido en 300×300mm
3. Si el motor falla para algún patrón, el thumbnail muestra el DXF directo (fallback, no error)
4. Tests existentes siguen pasando
5. Reportar en `coordination/reports/PUNTO_TASK_020_REPORT.md`
