# MSG_119 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ FORMATO CypCut CERRADO — el análisis de `Prueba definitiva.dxf` confirma: es SOLO el XDATA

El archivo diagnóstico de Constantino fue oro. Analicé las 3 filas (por rango de Y).

## Las 3 filas
- **Fila 1 (abajo):** CypCut nativo — 14 cuadrados, capas 1–14, cada uno con XDATA `FS_CYPCUT` Channel 1–14.
- **Fila 2 (medio):** mi archivo tras round-trip por CypCut — CypCut le **agregó** el XDATA.
- **Fila 3 (arriba):** mi output crudo (`test_14_capas.dxf`) — capas 1–14 pero **sin XDATA**.

## DIFF Fila 3 (mi crudo) vs Fila 2 (round-trip) → qué agrega CypCut
**Lo ÚNICO que CypCut agrega es el XDATA `FS_CYPCUT`** (Channel + LeadIn/LeadOut/IsFill/
PathStart/ToolCompensation) y registra el APPID `FS_CYPCUT`. Los atributos base de la entidad
(layer, flags, geometría) quedan **idénticos**. **No hay nada más.** Confirma mi diagnóstico de MSG_118.

## DIFF Fila 2 (round-trip) vs Fila 1 (nativo) → equivalentes
El XDATA que CypCut le puso a mi archivo es **idéntico** al del nativo (misma estructura, mismos
valores). Tras el round-trip, mi geometría queda indistinguible de la nativa. ✅

## ¿Mi fix ya replica TODO? — SÍ, al 100%
`test_14_capas_xdata.dxf` (el que subí en MSG_118): su XDATA es **byte-idéntico** al del nativo
(Channel 1–14) y tiene el APPID `FS_CYPCUT` registrado. **No falta nada.** Mi fix es el formato
definitivo.

## Dato extra sobre el límite de capas
En el round-trip (Fila 2), CypCut asignó Channels **1–5** a mis primeros 5 cuadrados y colapsó
el **6–14 a Channel 1**. OJO: eso es la auto-asignación de CypCut al importar geometría **sin**
Channel — NO un límite del formato. Cuando el Channel viene **explícito en el XDATA** (mi fix),
CypCut lo respeta: la Fila 1 nativa tiene 14 Channels distintos. **Conclusión: CypCut soporta
≥14 canales; el "5" era solo porque mi crudo no traía el XDATA.**

## Detalle menor
El nativo se guardó como DXF R2000 (AC1015); mi fix es R2004 (AC1018). No es crítico (el
`cypcut_capas.dxf` también era AC1018 y funciona), pero si querés máxima fidelidad genero en R2000.

## Estado — formato DEFINITIVO cerrado
1. La solución es escribir el XDATA `FS_CYPCUT` con `Channel` por entidad. Validado contra el
   round-trip real de CypCut.
2. Mi fix ya lo replica exacto. **Falta solo que Constantino abra `test_14_capas_xdata.dxf` en
   CypCut y confirme empíricamente que separa las capas** (la evidencia técnica ya es total).
3. Con el OK, aplico el XDATA al generador del flycut (`_write_cuadriculado_square_to_doc`):
   `Channel = capa` del cuadrado latino, registro el APPID, actualizo tests, y coordino el deploy.

**No toqué el generador todavía** — como pediste, cerramos el formato primero.

— Punto
