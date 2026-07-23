# MSG_115 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-14
**Asunto:** DXF de prueba de 14 capas — listo en el server

Para que Constantino verifique empíricamente el límite de capas de CypCut.

## Archivo (en el server)
```
/home/costa/planos/test_14_capas.dxf
\\190.190.190.20\planos\test_14_capas.dxf
```

## Qué contiene
- **14 cuadrados** de 20×20mm en fila, uno por capa.
- **Capas "1" a "14"** (base 1), como **atributo `layer` de cada entidad**, **sin declararlas
  en la tabla LAYER** — MISMO formato exacto que la referencia `cypcut_capas.dxf` (LWPOLYLINE
  cerrada, versión R2004). Verificado con el inspector.
- De izquierda a derecha: cuadrado 1 = capa "1", …, cuadrado 14 = capa "14".

## Qué probar
Abrir en CypCut y confirmar **hasta cuántas capas levanta** (¿las 14, o corta en 9?). Con eso
resolvemos la duda de MSG_114: si el módulo del flycut se queda en 9 o lo subo a 14.

**NO toqué el generador del flycut** — esto es solo el archivo de prueba, como pediste. El
módulo sigue en 9 hasta que confirmes el límite real.

— Punto
