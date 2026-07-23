# MSG_113 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** DXF de referencia de CypCut — NO está en el server todavía (bloqueo para validar)

## Lo busqué a fondo — no está
Rastreé por SSH (`costa@190.190.190.20`):
- `/home/costa/planos/` y todas sus subcarpetas (`calibracion_laser`, `generico/patrones`).
- **TODOS** los `.dxf` modificados hoy (jul 14) en **todo el disco** → el único es mi propio
  demo (`demo_latin_square_1000x2000.dxf`).
- Confirmé que el share Samba `\\190.190.190.20\planos` = `/home/costa/planos` (revisé smb.conf),
  así que no es un tema de que apunte a otra carpeta.

**Conclusión:** el DXF de referencia (“un cuadrado en cada capa”, exportado de CypCut)
**todavía no fue pegado al server.** No puedo validar contra un archivo que no existe.

Intenté inferir la convención desde archivos existentes, pero no sirven:
- `bateria_calibracion.dxf` (que sí corté en CypCut) tiene **todo en capa "0"** — era la batería
  de tiempos, sin flycut escalonado. No revela cómo nombra CypCut las capas de flycut.

## Me adelanté igual — todo listo para cotejo instantáneo
1. **Documenté mi formato exacto** (lo que produce el generador hoy), para comparar al toque:
   - DXF R2010. Tabla LAYER declara: **"0","1",…,"8"** (colores ACI 7,2,3,4,5,6,7,8,9) +
     **"CONTORNO"** + "Defpoints".
   - Agujeros en capas **"0".."8"** (cuadrado latino); contorno en **"CONTORNO"**.
2. **Herramienta de cotejo lista** (`tools/inspeccionar_capas.py`, commit 6b6a96c): dumpea la
   tabla LAYER + capas usadas de cualquier DXF y marca diferencias entre dos archivos. Apenas
   tenga el de referencia corro `python tools/inspeccionar_capas.py <ref_cypcut>.dxf demo.dxf`
   y sale la diferencia exacta de nombres/estructura.

## Lo que necesito (bloqueo)
**Que Constantino exporte desde CypCut el DXF de referencia y lo pegue en**
`\\190.190.190.20\planos\` (cualquier subcarpeta sirve; idealmente `calibracion_laser\`).
Apenas esté, en minutos confirmo si mi formato coincide o qué ajusto.

## Mi principal sospecha a validar
Que CypCut **no use la capa "0"** para flycut (en CAD es la capa por defecto). Si el DXF de
referencia arranca las capas en **"1"**, remapeo `capa = (col+fila)%9 + 1` (cambio de una línea)
y redeployo. Pero **no lo toco a ciegas** — espero ver el archivo real primero.

— Punto
