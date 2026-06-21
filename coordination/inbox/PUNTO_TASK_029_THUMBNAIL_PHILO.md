# PUNTO_TASK_029 — Thumbnail Philo no se genera + posible pérdida del patrón original

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Contexto

Constantino siguió estos pasos:

1. Cargó el patrón **Philo** en formato splines (DXF original)
2. Lo convirtió usando el conversor del sistema
3. El conversor sugirió el nombre `Philo (convertido)` para guardar
4. Constantino borró la sugerencia y escribió `Philo` — mismo nombre que el original
5. Resultado esperado: dos patrones en la galería (`Philo` y `Philo (convertido)`)
6. Resultado real: el original desapareció — solo quedó uno (probablemente el convertido pisó al original)

## Síntomas actuales

1. **El thumbnail de Philo no se genera** — aparece vacío o no aparece en la galería
2. **El patrón original con splines posiblemente fue sobreescrito** por el archivo convertido al usar el mismo nombre

## Pedido

1. Investigar si el archivo DXF de Philo fue sobreescrito y en qué estado está actualmente
2. Investigar por qué el thumbnail no se genera para Philo
3. Determinar si ambos problemas están relacionados o son independientes
4. Corregir la generación de thumbnail
5. Si el patrón original se perdió por sobreescritura, evaluar si hay forma de recuperarlo (backup, historial git, etc.)
6. Evaluar si el conversor debería advertir cuando el nombre elegido ya existe — para evitar sobreescrituras accidentales

## Reporte

`coordination/reports/PUNTO_TASK_029_REPORT.md` y mensaje en `coordination/channel/Nova/`.
