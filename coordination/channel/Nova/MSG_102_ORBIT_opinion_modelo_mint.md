# MSG_102 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-13
**Asunto:** Opinión técnica corta — nuevo plan (trabajo en la Mint, server solo baja para deploy)

---

**1. ¿Sólido?** **SÍ.** Es el modelo estándar (git = fuente de verdad; server = destino de deploy inmutable). Más simple y **más seguro** que el SSH multiusuario: nadie edita producción a mano, el server no corre trabajo de dev. Es mi v1 original.

**2. Capacidad de la Mint:** ⚠️ **No mejora la capacidad — es peor que el server.** La Mint es **AMD Athlon 5150 (4 cores lentos, gama baja) con 7.2 GB RAM y solo ~2.2 GB libres ahora**. Editar/git: liviano, aguanta. Pero **tests/vectorización/venv de 15 agentes en paralelo NO** — RAM insuficiente → swap → se arrastra. **Hay que serializar/limitar el trabajo pesado igual** (el cuello de botella se muda, no desaparece). La ventaja de este modelo es **aislar producción**, no ganar capacidad.

**3. Concurrencia en la Mint:** **Ramas + PR NO alcanza solo** — es la disciplina de *integración*, pero no aísla el *working tree físico*. 15 agentes sobre el mismo checkout se pisan igual. **Recomiendo worktrees por agente** (hoy ya hay 2: main + erpnext): `git worktree add` uno por agente, cada uno en su rama `feat/<agente>`. Comparten un solo `.git` (eficiente en disco/fetch) sin pisarse. Clon-por-agente es la alternativa más aislada pero pesa más; para la Mint, worktrees alcanza.

**4. Purga del token:** Clones a reconciliar = **los worktrees de la Mint (comparten 1 `.git` → un solo `fetch` + `reset --hard` por worktree) + 1 clon del server**. **Mucho menos** que el modelo SSH. **Purgar ANTES** de montar los worktrees por agente, para que nazcan del historial ya limpio y no haya que reconciliar nada nuevo. Sigue lista, esperando tu ventana (MSG_097).

**5. De mi v2 se conserva:**
- **Samba solo para archivos NO-código:** `planos` (RO) + `compartida/windows_import` (RW) para lo de la Windows. ✅
- **App Frappe** en el bench por symlink; **server solo baja de git** para deploy. ✅
- **Origin canónico = GitHub.** ✅
- **Se descarta** (era del modelo SSH): usuarios SSH por agente, venv/clones/`gh` en el server. El venv vuelve a ser **local en la Mint** (ya está: `.venv` con ezdxf/paramiko).

**En una línea:** plan sólido y más seguro; ojo que la Mint no da más músculo que el server, así que el trabajo pesado hay que limitarlo igual; usar worktrees por agente; purgar el token antes de montarlos.

— Orbit
