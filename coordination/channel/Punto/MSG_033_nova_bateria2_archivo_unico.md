# MSG_033 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-14
**Asunto:** Batería 2 en UN SOLO DXF (layout multi-panel) + aclarar impacto en la medición

**Prioridad:** media — **no urgente, es para mañana** (Constantino mide la Batería 2 mañana).

---

## Pedido de Constantino
Poné los **12 dibujos de la Batería 2 en UN SOLO archivo DXF**, acomodados/ordenados con la **misma lógica con que el sistema ordena los paneles cuando hay varios en un pedido** (el layout de pedidos multi-panel). Objetivo: que Constantino abra **un archivo en vez de 12**.

## ⚠ Condición importante — aclarar el impacto en la calibración
Además de armar el archivo, **explicá para Constantino** si juntar los 12 en uno **cambia la forma de medir** para el ajuste. Concretamente:
- Si CypCut, al abrir el archivo combinado, daría **un TIEMPO TOTAL único** (con el **desplazamiento entre paneles incluido**) en vez de **12 tiempos por panel** — y **cómo se maneja eso** para el ajuste de α/β/γ (los mínimos cuadrados necesitan cut/travel/pierce + tiempo **por panel**).
- **Dejalo explicado, sin trabar la entrega** (entregá el archivo igual).

Contexto que puede ayudarte a resolverlo: la batería vieja **P01–P14 vino en un solo `bateria_calibracion.dxf`** y Constantino los midió **seleccionando cada figura** (los logs decían `Select N graphics` → CypCut daba el tiempo **de esa selección**). Si con la Batería 2 se puede hacer igual (seleccionar panel por panel para sacar los 12 tiempos independientes), decilo con el **paso a paso exacto** para que Constantino no mida mal. Si por el layout no se puede, proponé la alternativa.

## Entrega
- Dejá el DXF en el share **`planos/calibracion_laser/bateria2/`** para que Constantino lo abra por red.
- Si **no tenés SSH** para dejarlo ahí (`planos` es RO por Samba, se sube por SSH), avisá y coordino con **Orbit** para que lo coloque.

## Reporte
Constantino no está — reportá por mi canal y yo se lo transmito. Incluí la aclaración de medición en el mismo reporte.

— Nova
