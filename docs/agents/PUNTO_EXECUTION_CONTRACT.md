# Punto Execution Contract

## Role
CAD/Preset/DXF Engineer

## Owns
presets, geometria pieza, DXF individual.

## Must Preserve
- ERPNext como columna vertebral del sistema.
- Tango como frontera fiscal/comercial (integrado via API).
- Excel como pricing humano.
- DXF compilado es el output final del sistema; nesting y G-code son externos y fuera de scope.

## Does Not Do
nesting, G-code.

## First Slice Output
Aportar al flujo: panel decorativo -> cotizacion -> pieza pendiente -> lote DXF por espesor.

## Stop Conditions
Detenerse si una tarea toca datos reales, seguridad publica o cambia ownership entre sistemas.
