# DECISION_014 — Frontera Orbit ↔ Forge en infraestructura

**Fecha:** 2026-07-19 · **Decidida por:** Nova (autoridad delegada) · **Estado:** Vigente

El cotejo detectó **solapamiento**: Forge (ERPNext) implementó los shares **Samba**, que es infraestructura del sistema operativo — territorio de Orbit.

## La regla

> **Si es del sistema operativo, es de ORBIT. Si es de Frappe/ERPNext, es de FORGE.**

| Territorio | Dueño |
|---|---|
| Build, deploy, git, worktrees, historial, CI | **Orbit** |
| Sistema operativo del server, servicios, **Samba**, red, permisos, `/etc` | **Orbit** |
| Bench de Frappe, apps, migraciones, DocTypes, configuración de ERPNext | **Forge** |
| Deploy **de la app** al bench | **Orbit ejecuta** · Forge valida el estado del bench |

## El caso Samba

Era de Orbit. Lo hizo Forge por urgencia, y **quedó bien hecho**: no se revierte ni se rehace. **Retroactivamente correcto; a futuro va por Orbit.**

Esta decisión no es un reproche a Forge — es evitar que la próxima vez dos agentes toquen `/etc` sin saber quién manda.

## Excepciones

Si por urgencia uno tiene que entrar en el territorio del otro, **se hace y se avisa en el canal de Nova**. Prefiero una excepción registrada a un frente frenado. Lo que no quiero es que la excepción se vuelva la norma sin que nadie lo note.
