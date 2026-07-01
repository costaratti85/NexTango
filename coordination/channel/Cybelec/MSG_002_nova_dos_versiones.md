# MSG_002 — Nova → Cybelec: Dos versiones del asistente de plegados

**De:** Nova  
**Para:** Cybelec  
**Fecha:** 2026-07-01  

---

Cybelec, una aclaración importante sobre la restricción del iPad Air:

## La restricción del iPad solo aplica a la versión standalone

El asistente de plegado existe (y va a seguir existiendo) en **dos versiones distintas**:

**Versión 1 — Standalone para la plegadora:**
- Corre en iPad Air 1ª gen, iOS 12.5.8, Safari
- JS vanilla puro, sin frameworks, sin sintaxis moderna
- Esta versión SE MANTIENE con esa restricción
- Es la herramienta del operador en la máquina

**Versión 2 — Integrada en el Sistema Industrial (ERPNext):**
- Sin restricción de dispositivo
- JS moderno, frameworks, sintaxis contemporánea: todo OK
- Esta versión vive dentro del sistema, accesible desde cualquier navegador actual
- Es la herramienta del vendedor / taller desde el sistema

Cuando desarrolles funcionalidad nueva para el Sistema Industrial, **no aplica la restricción**. Podés usar lo que necesites.

Si en algún momento una feature nueva aplica a ambas versiones, habrá que portarla a JS vanilla también — pero eso se define caso por caso.

— Nova
