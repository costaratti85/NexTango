# Agent Handoff Protocol

Cada agente trabaja por contrato y entrega reporte.

Entrada minima para un agente:
- Norte del proyecto.
- Contrato del agente.
- Tarea concreta.
- Archivos permitidos.
- Criterio de exito.

Salida obligatoria:
- Resumen corto.
- Archivos modificados.
- Tests ejecutados.
- Riesgos o bloqueos.
- Proximo paso recomendado.

Formato de reporte:
```markdown
# Reporte AGENTE - TAREA
## Hecho
## Archivos
## Tests
## Riesgos
## Proximo paso
```

Si una tarea toca otro dominio, el agente debe detenerse y pedir decision de Nova.
