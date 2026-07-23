# MSG_118 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** 🎯 RESUELTO el misterio de las capas CypCut — es XDATA FS_CYPCUT (Channel), no el color

Hice el diff profundo entre `cypcut_capas.dxf` (funciona) y `test_14_capas.dxf` (no funciona).

## Qué encontré (el hallazgo)
CypCut NO asigna la capa de proceso ni por el **nombre de capa** ni por el **color**.
La asigna por un **dato extendido (XDATA) en cada entidad**, con application id **`FS_CYPCUT`**:

```
1001 FS_CYPCUT
1000 Channel
1070 N          ← el CANAL de proceso (capa "1" → Channel 1, … "14" → Channel 14)
1000 LeadIn / LeadOut / IsFill / PathStart / ToolCompensation  (parámetros de corte)
```

- El export de CypCut tiene ese XDATA en las 14 entidades, con `Channel` = número de capa.
- **Mi `test_14_capas.dxf` no tenía NADA de XDATA** → por eso CypCut no separaba las capas.

## La hipótesis del color quedó descartada
En **ambos** archivos las 14 entidades son BYLAYER (sin color propio) y las capas 1–14 no
están declaradas en la tabla LAYER. Estructuralmente son casi idénticos. La ÚNICA diferencia
real es el XDATA `FS_CYPCUT`. (De paso: esto coincide con una divergencia que yo mismo había
anotado — la versión erpnext de mi generador nunca escribió el XDATA FS_CYPCUT; la vieja de
`main` sí. Se perdió en la migración, igual que el Latin Square.)

## Test nuevo para que Constantino verifique
Generé un DXF replicando el XDATA **exacto** del export (verificado: mi XDATA == el de CypCut,
canal por canal):
```
/home/costa/planos/test_14_capas_xdata.dxf
\\190.190.190.20\planos\test_14_capas_xdata.dxf
```
14 cuadrados, cada uno con `FS_CYPCUT / Channel = 1..14`.
**Constantino: abrilo en CypCut y confirmá si ahora SÍ se separan las 14 capas.**

## Plan (cuando confirmes)
Aplico el XDATA `FS_CYPCUT` al generador del flycut (`_write_cuadriculado_square_to_doc`):
por cada agujero, además del atributo `layer`, escribo `Channel = capa` (1..9 del cuadrado
latino). Registro el APPID, agrego el XDATA, actualizo tests, y ahí sí coordino el deploy.

**NO toqué el generador todavía** — como pediste, primero que Constantino valide el test. El
flycut no se deploya hasta confirmar esto.

## Bonus
De paso resuelve la duda del límite de capas: si el `test_14_capas_xdata.dxf` levanta las 14,
el límite real es ≥14 (no 9) y podría subir el módulo. Lo confirmamos con la misma prueba.

— Punto
