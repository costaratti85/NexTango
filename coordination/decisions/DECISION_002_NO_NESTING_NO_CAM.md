# Decision 002 - No nesting, no CAM

SistemaIndustrial no implementa nesting, G-code ni CAM.

El output del sistema son archivos DXF con las piezas a cortar y/o plegar, compilados por material/espesor.

Lo que ocurre después del DXF (nesting en máquina, secuencia de corte, G-code) es responsabilidad
de herramientas externas y está fuera del scope de SistemaIndustrial.

Ningún agente debe implementar ni mantener lógica de nesting, toolpaths ni G-code.
