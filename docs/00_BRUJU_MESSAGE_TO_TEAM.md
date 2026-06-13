# Mensaje de Bruju (Brújula) al equipo de Sistema Industrial

Sistema Industrial no es solamente un software.

Es la construcción gradual de una plataforma operativa para una empresa metalúrgica real.

El objetivo no es reemplazar de golpe la forma de trabajar de la empresa, sino convertir lo que ya funciona en un sistema más claro, trazable, automatizable y escalable.

La arquitectura central es esta:

- ERPNext es la columna vertebral del sistema.
- Sistema Industrial es la capa metalúrgica especializada: presets, DXF, trazabilidad e integración.
- Tango es el sistema fiscal y contable, integrado via API.
- Excel sigue siendo, por ahora, la herramienta humana de pricing.

Por lo tanto, no debemos reinventar lo que ya está resuelto.

Nuestro trabajo es construir el puente inteligente entre pedido, cálculo industrial, DXF, producción, trazabilidad y facturación.

## Reglas fundamentales

1. No crear sistemas paralelos si ERPNext ya resuelve el dominio.
2. No tocar Tango más allá de la frontera fiscal, contable y de precios maestros.
3. No romper el flujo humano actual de precios en Excel.
4. No implementar nesting ni CAM. El output del sistema son archivos DXF; lo que ocurre después es externo y fuera de scope.
5. Priorizar rebanadas finas de punta a punta.
6. Cada módulo debe tener límites claros.
7. Cada decisión automática debe poder ser auditada.
8. Si un humano fuerza una decisión, el sistema la respeta y registra quién lo hizo.
9. El sistema debe poder responder siempre: qué se pidió, qué se cotizó, qué se cortó, qué falta, quién lo hizo y en qué estado está cada pieza.
10. La tecnología debe adaptarse a la empresa antes de pedirle a la empresa que se adapte a la tecnología.

La primera gran meta no es construir “todo”.

La primera gran meta es lograr que una pieza o panel decorativo pueda convertirse en una cotización real en ERPNext, con recursos calculados, precios consultados, DXF generado y trazabilidad lista para taller.

Después se ensancha.

El éxito del proyecto no va a depender solo de programar bien.

Va a depender de respetar la operación real, cuidar a las personas que trabajan hoy, no duplicar responsabilidades entre sistemas y mantener una arquitectura simple, modular y honesta.

Sistema Industrial debe ser una herramienta que ordene la fábrica sin violentarla.

Ese es el norte.
