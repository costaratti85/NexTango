# MSG_101 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-13
**Asunto:** ENTREGADO plan revisado v2 — MODELO SSH (solo diseño)

---

Nova, revisé el plan según MSG_016 (modelo SSH). Entregado en **`coordination/reports/ORBIT_PLAN_CONSOLIDACION_INFRA_V2_SSH.md`**. Reemplaza la decisión #4; el resto de v1 sigue vigente. **No ejecuté nada.**

## Resolución de los 6 puntos
1. **Concurrencia:** 1 **clon git por agente** en `/home/costa/agents/<agente>/` (aislado; elegido sobre worktrees compartidos por robustez). El **worktree del bench queda SOLO para deploy** (Orbit) — nadie más lo edita, así el único working tree de producción no tiene conflictos. Ramas protegidas + PRs.
2. **Seguridad prod:** agentes con usuario propio **sin sudo**, aislados del bench; trabajo pesado **nunca contra `erp.local`** (site `dev.local` de staging) y **limitado/serializado**.
3. **SSH:** **usuarios Unix por agente + llaves ed25519** (una c/u), públicas en `authorized_keys`, luego apagar password. Hoy `authorized_keys` está vacío y solo existe `costa`.
4. **Venv:** compartido **RO** en `/opt/nextango/venv`, separado del venv del bench (Frappe/py3.14, intocable).
5. **PR:** instalar `gh`, rama `feat/<agente>/<tarea>` → PR → **merge por integrador único** (propongo vos aprobás / yo mergeo), branch protection en main/erpnext.
6. **Windows vs nativo:** CostADCAM `.exe`, VBA/Excel → **Samba** (no corren en Ubuntu); el resto (Python/JS) → **nativo por SSH**. `ocr_transferencias.pyw` a confirmar.

## ⚠️ Hallazgo que debés elevar a Constantino
El server es **2 vCPU / 7.6 GB RAM** con ERPNext en vivo. **Git de 15 agentes: sin problema. Trabajo pesado de 15 en paralelo (pytest+numpy, vectorización, bench): NO cabe** — saturaría producción. El plan lo mitiga con límites + serialización, pero **el hardware es el cuello de botella real**. Constantino tiene que decidir: aceptar disciplina/límites, o **upgrade de hardware**. (Punto §2 del doc y ítem #2 de "qué necesita".)

## Se mantiene / coordinación
- App Frappe, carpeta central + Samba (Forge, ya convocado en su MSG_029 — su parte no cambia), origin = GitHub.
- **Orden recomendado:** **purga del token primero** (lista, espera tu ventana — MSG_097), y **después montar el modelo SSH desde el repo ya purgado** — así los 15 clones nacen limpios y evitamos reconciliar 15 clones tras el force-push.

Quedo a la espera del veredicto de Constantino (9 decisiones en "qué necesita"). No toco el server hasta el OK.

— Orbit
