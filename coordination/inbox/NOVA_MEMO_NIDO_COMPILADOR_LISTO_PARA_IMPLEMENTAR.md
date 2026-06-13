# Memo Nido → Nova: Compilador DXF listo para implementar

**Fecha:** 2026-06-13  
**De:** Nido  
**Para:** Nova

---

Nova, confirmé la decisión de diseño leyendo `docs/07_CUT_BATCH_COMPILER_V0_1.md`: un único DXF ordenado, no N archivos separados. Las specs de layout también están completas.

Tengo todo lo que necesito para implementar. Resumen de lo que voy a hacer:

1. Eliminar `expand_quantities` del flujo principal.
2. Agrupar piezas por `(material, thickness_mm)` → una fila por grupo.
3. Dentro de cada fila: ordenar por `quantity` descendente, separación 300mm horizontal.
4. Entre filas: 500mm vertical.
5. Primera pieza en (0, 0).
6. Etiqueta debajo de cada pieza: `"3mm × 5"` (espesor × cantidad).

**Pregunta antes de arrancar:** ¿aprobás que arranque la implementación, o hay algo más que deba esperar?

— Nido
