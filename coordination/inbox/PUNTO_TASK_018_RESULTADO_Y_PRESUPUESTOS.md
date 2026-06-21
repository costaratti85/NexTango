# PUNTO_TASK_018 — DXF descargable desde presupuesto + lista de presupuestos + nombre de cliente

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

Tres mejoras relacionadas con el flujo post-generación:

1. Hoy: generar panel → resultado con botón "Descargar DXF" y botón "Ver presupuesto". Si el usuario va a ver el presupuesto sin descargar el DXF primero, ya no tiene forma de volver a descargarlo.
2. Los presupuestos ya se guardan como `PRES_NNNN.json` en `Programas_hechos/Panel Decorativo/presupuestos/`, pero no hay una página que los liste ni permita borrarlos.
3. El presupuesto no tiene campo para nombre de cliente.

---

## Cambio 1: Botón "Descargar DXF" en la página `/presupuesto`

La página `/presupuesto` lee `last_generate.json` que ya tiene la ruta del DXF generado. Agregar en esa página un botón "Descargar DXF" que sirva el archivo.

El DXF se descarga desde un endpoint existente o nuevo: `GET /download_dxf?path=...` (o similar). Verificar que el path es un archivo dentro del directorio de outputs antes de servirlo (seguridad básica).

---

## Cambio 2: Página de lista de presupuestos (`/presupuestos`)

Nueva página accesible desde el link "Presupuestos" del topbar (hoy ese link apunta a `/presupuesto` — redirigir a `/presupuestos` en plural).

La página lista todos los archivos `PRES_NNNN.json` del directorio `presupuestos/`, ordenados por número descendente (más reciente primero).

Por cada presupuesto mostrar:
- Número (`PRES_NNNN`)
- Fecha
- Nombre de cliente (si existe)
- Total ($)
- Botón "Ver" → abre el presupuesto
- Botón "Borrar" → elimina el JSON (con confirmación)

---

## Cambio 3: Campo "Nombre de cliente" en el presupuesto

En la página `/presupuesto`:
- Agregar un campo de texto editable "Cliente:" arriba de la tabla
- Al escribir y salir del campo (blur), guardar el valor en el `PRES_NNNN.json` correspondiente via `POST /api/presupuestos/:id/cliente`
- El campo es opcional — si está vacío se muestra "Sin nombre" en la lista

---

## Notas

- `last_generate.json` contiene la info del último panel generado. La página `/presupuesto` ya usa este archivo. El número de presupuesto se asigna y el `PRES_NNNN.json` se crea cuando el usuario visita `/presupuesto`.
- El link del topbar "Presupuestos" debe apuntar a `/presupuestos` (lista), no a `/presupuesto` (último).

---

## Criterio de aceptación

1. Desde `/presupuesto` se puede descargar el DXF del panel generado
2. `/presupuestos` lista todos los presupuestos guardados con fecha, cliente y total
3. Desde la lista se puede ver cada presupuesto individual y borrarlo
4. El campo de cliente se puede editar y persiste al recargar la página
5. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_018_REPORT.md`
