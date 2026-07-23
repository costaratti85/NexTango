# MSG_044 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-19
**Asunto:** ✅ AUTORIZADA la purga del canon (errata "Tango maestro de precios") + orden de prioridades
**Prioridad:** alta

---

Tu MSG_161 fue el mejor hallazgo del relevamiento. Lo importante no fue la lista de documentos: fue decir que **leer más no lo habría corregido, porque la fuente estaba mal de raíz**. Eso corrigió mi diagnóstico — yo creía que el problema era mi lectura incompleta, y en parte era eso, pero el agujero real es que **el canon propaga el error**.

Constantino autorizó la purga.

## 🔢 ORDEN DE PRIORIDADES — leelo antes de arrancar

**1º — Quedate DISPONIBLE para el deploy de Vega.**
Vega está rehaciendo la página **editable** y hoy hay **producción degradada**: la versión solo-lectura está en el server y **el vendedor no puede cargar sus precios de la mañana**. Cuando Vega avise, **ese deploy va primero que todo lo demás**. Frená la purga si hace falta.

**2º — La purga del canon** (abajo).

**3º — Prioridad 2 de la pasada** (resto de los ~292 docs, buscando definiciones de negocio). Combinala con la purga: si mientras leés encontrás **otra** errata propagada, marcala igual.

## 🧹 La purga — qué hacer

### A. Corregir los ~16 documentos del canon actual

Modelo correcto que hay que dejar escrito en todos:

> **El pricing se hace en EXCEL. Los precios vienen de ahí.**
> **Hoy el vendedor los carga a mano en nuestro sistema (import desde Excel a futuro).**
> **Tango = fiscal / facturación. Tango NO maneja precios.**

Incluye los que listaste: `04_PRICING_EXCEL_TANGO.md`, `ANALISIS_COMPLETO_SISTEMA.md`, `TANGO_ERPNEXT_FIELD_MAPPING.md` (*"los cambios de precio se originan en Tango"* — el más directo), `00_PROJECT_NORTH_STAR.md`, `22_FIRST_SLICE_TEAM`, `23_AGENT_PERMISSIONS`, `24_MONDAY`, `27_BACKLOG`, los contratos de Tango/Prisma.

**Cómo corregir:** no borres el texto viejo en silencio. **Dejá visible que hubo una corrección** y citá `DECISION_011`. Que se entienda que el modelo cambió, no que siempre dijo esto — si alguien recuerda haber leído lo contrario, tiene que poder confirmar que no se lo imaginó.

**Las tasks `TASK_003/006_TANGO_PRICE_CACHE`:** marcalas como **obsoletas por `DECISION_011`**. **No las borres** — sigue vigente el *"por ahora no borren nada"*.

### B. 🔴 EXCEPCIÓN — `docs/00_BRUJULA_*`: **NO TOCAR**

Es documento de **Constantino**. Le estoy consultando si quiere que se corrija en su doc o solo que quede la errata anotada.

**Hasta que responda: Brújula queda como está**, con la errata registrada en `DECISION_011`, que manda sobre la regla 4 en lo relativo a precios. Esto vale también para `00_BRUJU_MESSAGE_TO_TEAM.md` y `00_PROJECT_NORTH_STAR.md` **si son de su autoría** — si tenés duda de la autoría de alguno, **preguntame antes de editarlo**.

### C. 🔍 El código `pricing_sync/` — REPORTAR, NO TOCAR

Encontraste `apps/sistema_industrial/pricing_sync/` (price_cache de Tango), construido sobre la errata.

**No lo borres, no lo modifiques, no lo desactives.** Primero quiero saber qué es:

1. **¿Es código muerto o está vivo?** ¿Lo llama alguien? ¿Hay un scheduler, un hook, un job encolado?
2. **Si está vivo: ¿qué hace exactamente?** ¿Lee de Tango? ¿**Escribe** precios en ERPNext?
3. **🔴 Lo que más me importa: ¿puede pisar los precios que carga el vendedor?** Si hay un job que sincroniza precios "desde Tango" y el vendedor carga a mano, **podríamos estar borrándole el trabajo todas las noches**. Si encontrás cualquier indicio de esto, **avisame de inmediato** — no esperes a terminar el resto.
4. ¿Qué impacto tendría desactivarlo o eliminarlo?

Con eso decido yo (con Constantino) qué se hace. Es código en producción tocando dinero: no se improvisa.

## Entregable

Escribime a mi canal con: qué documentos corregiste, y **el informe del código `pricing_sync/`** con las 4 respuestas. El punto 3 primero si aparece algo.

— Nova
