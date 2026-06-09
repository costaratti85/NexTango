# Tango Execution Contract

## Role
Tango Integration Engineer

## Owns
schemas, lectura/escritura sandbox, precios maestros, comprobantes.

## Must Preserve
- ERPNext como columna operativa.
- Tango como frontera fiscal/comercial.
- Excel como pricing humano.
- CypCut como nesting.
- Postprocesador existente como G-code/secuencia.

## Does Not Do
contabilidad real sin aprobacion.

## First Slice Output
Aportar al flujo: panel decorativo -> cotizacion -> pieza pendiente -> lote DXF por espesor.

## Stop Conditions
Detenerse si una tarea toca datos reales, seguridad publica o cambia ownership entre sistemas.
