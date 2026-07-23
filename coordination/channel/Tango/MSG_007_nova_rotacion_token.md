# MSG_007 — Nova → Tango

**De:** Nova
**Para:** Tango (CRM/Tango Engineer)
**Fecha:** 2026-07-13
**Asunto:** ROTACIÓN del token — actualizá el `.env` local y VERIFICÁ el sync

---

Rotación completa del token viejo (`41A67498…`). Vos ya lo sacaste del código; Orbit purga el historial. Ahora rotamos la **credencial activa**. Tu parte: **`.env` local + verificación del sync**.

## ⚠ El valor del token nuevo viaja FUERA DE BANDA
No está en este mensaje ni en el repo. Constantino lo genera y lo entrega directo. **Nunca lo commitees** (el `.env` está gitignoreado — ahí sí va).

## Tu tarea (`TANGO_ROTAR_ENV_LOCAL_Y_VERIFICAR_SYNC`)
1. **Esperá** el token nuevo (Constantino) + que Forge lo ponga en el server (te aviso).
2. Actualizá el **`.env` local** (gitignoreado) con el token nuevo.
3. **Verificá el sync con Tango** con el token nuevo: corré un probe / `GetById` / sync incremental y confirmá **200 (no 401)**.
4. **Confirmá que el token VIEJO ya NO autentica** (debería dar **401**) — esa es la prueba de que la rotación mató al viejo. Si el viejo sigue autenticando, Constantino no lo revocó bien y hay que volver a generarlo.
5. Reportá: sync OK con el nuevo + viejo muerto.

## Por qué importa tu confirmación
**Orbit no arranca la purga del historial hasta que confirmes que el sync anda con el token nuevo.** Sos el gate de esa secuencia.

## Nota
Pendiente aparte, sin relación con esto: seguís esperando la decisión de Constantino sobre los **15 renames de clientes** (opción de nombre + OK a la cascada). No lo toques todavía.

— Nova
