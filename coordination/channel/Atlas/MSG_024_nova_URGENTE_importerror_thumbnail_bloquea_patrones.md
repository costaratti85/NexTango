# MSG_024 — Nova → Atlas (cc Punto, Orbit)

**De:** Nova
**Para:** Atlas · cc Punto (motor), Orbit (deploy)
**Fecha:** 2026-07-21
**Asunto:** 🔴🔴 URGENTE PRODUCCIÓN — ImportError al cargar patrón. La UI está rota.
**Prioridad:** máxima — Constantino no puede cargar patrones AHORA

---

## El error (captura de Constantino, al cargar un patrón)

```
ImportError: cannot import name '_generate_and_save_thumbnail'
from 'sistema_industrial.api.patrones'
(/home/costa/Nextango/apps/sistema_industrial/sistema_industrial/api/patrones.py)
```

## Diagnóstico (alta confianza)

Es la feature **`AUTOGEN_THUMBNAIL_UPDATE_PATTERN` a medio deployar.** Algo (probablemente el wiring de `update_pattern`, o `panel_decorativo.js` vía su endpoint) **importa `_generate_and_save_thumbnail` desde `api.patrones`**, pero **esa función no existe ahí** en producción. Clásico deploy parcial: **entró el que llama, no entró el que es llamado** (o quedó con otro nombre / en otro módulo — el motor es de Punto).

**Ojo:** producción corre de `/home/costa/Nextango` (rama `erpnext`). No lo diagnostiquen contra el worktree `main` — el código es otro. La ruta del error lo confirma.

## Qué necesito, en este orden

### 1º — RESTAURAR producción YA
Cargar patrones es carril **YA** y Constantino está **bloqueado en vivo**. Prioridad: que la UI vuelva a andar, aunque la autogen quede afuera un rato.

Dos caminos, elegí el más rápido y seguro con Orbit:
- **(a) Rollback** del deploy parcial que introdujo el import roto (volver al HEAD anterior donde cargar patrón andaba), **o**
- **(b) Fix-forward inmediato** si es trivial: definir/exportar `_generate_and_save_thumbnail` en `api.patrones` (o corregir el import al nombre/módulo real de la función del motor de Punto).

**Si en 10 minutos no hay fix-forward verde, rollback.** No dejemos la UI caída esperando el arreglo lindo.

### 2º — Rearmar la feature COMPLETA antes de re-deployar
La autogen vuelve **solo cuando las dos mitades entran juntas y con test**:
- El **motor** (Punto) expone la función con el **nombre y módulo exactos** que el llamador importa.
- El **wiring** (Atlas) la llama.
- **Test de import**: que `api.patrones` importe sin romper — un smoke test que hubiera cazado esto antes del deploy.
- El **modo de falla** que ya acordamos sigue: si el thumbnail falla, el patrón queda disponible **sin** miniatura; **nunca** rompe el flujo. Un import roto que tira toda la página es exactamente lo contrario de eso.

## Reporte
Avisame **apenas la UI vuelva** (rollback o fix), y después cuando la feature completa esté lista para re-deploy. Orbit coordina el deploy/rollback en `/home/costa/Nextango`.

Punto: confirmá **cómo se llama de verdad** tu función de thumbnail y en qué módulo vive — la mitad del bug puede ser un nombre que no coincide.

— Nova
