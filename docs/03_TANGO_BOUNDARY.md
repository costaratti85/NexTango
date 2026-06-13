# Tango Boundary

Tango Gestión queda como autoridad fiscal, contable y comercial argentina.

## Tango owns

Clientes, proveedores, artículos, códigos, códigos de barra, precios publicados, facturas, notas de crédito y contabilidad.

## Mecanismo de integración

La integración con Tango es via API (cliente HTTP contra la API de Tango Gestión).
No se usa Excel como mecanismo de integración principal.

## Flujos

ERPNext puede generar pedidos importables a Tango.
Tango puede facturar directo.
Toda factura o nota de crédito de Tango debe sincronizar stock/estado en ERPNext via API.
