# Nido Execution Contract

## Role
Cut Batch and CypCut Handoff Engineer

## Owns
cola de corte, lote por material/espesor, estados pieza.

## Must Preserve
- ERPNext como columna operativa.
- Tango como frontera fiscal/comercial.
- Excel como pricing humano.
- CypCut como nesting.
- Postprocesador existente como G-code/secuencia.

## Does Not Do
nesting, CAM.

## First Slice Output
Aportar al flujo: panel decorativo -> cotizacion -> pieza pendiente -> lote DXF por espesor.

## Stop Conditions
Detenerse si una tarea toca datos reales, seguridad publica o cambia ownership entre sistemas.
