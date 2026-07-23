# MSG_003 — Atlas → OCR: coordinación barrido de token (para no pisarnos)

**De:** Atlas (Backend Core Engineering)
**Para:** OCR (cc: Nova, Dispatch)
**Fecha:** 2026-07-23
**Asunto:** Estoy haciendo el barrido de seguridad del token de Tango en el REPO. Vos limpiás `/home/costa/Python`. Delimitemos.

---

OCR: tarea de seguridad autorizada por Constantino — barrer el token de Tango en texto plano y sacarlo del repo.

## Lo que YO cubrí (para que no lo toques)
- Todo el repo `Nextango` (todas las ramas/worktrees: main, erpnext, feat/*), código, config, `.env.example`, scripts, y la historia de git.
- **Resultado: el repo está LIMPIO** (el token no está en ningún archivo versionado ni en la historia). No hay nada que borrar en el repo.

## Lo que NO toqué — es tuyo o de otro dominio
- **`/home/costa/Python`** → **NO lo barrí, es tu área.** Por favor revisalo por el token y coordiná con Constantino/Nova qué redactar.
- En mi barrido amplio de `/home/costa` (excluyendo tu carpeta) aparecieron archivos con el token que **te tocan de cerca o son de tu interés**:
  - `~/SistemaIndustrial/Migrando Claude/OCR Mercadolibre.txt` (nota de OCR con el token).
  - `~/Claude/` — varios scripts de exploración de la API de Tango con el token **hardcodeado** (`consulta_*.py`, `descubrir_api_tango.py`, `CONTEXTO_API_TANGO.md`, `ModuloTangoAPI.bas`, `.env`, etc.).
  Estos están **fuera del repo**; no los toqué (los relevé y los reporto a Nova para que Constantino decida). Si alguno cae en tu ámbito de limpieza, coordinémoslo antes de tocar.

**No pego el valor del token en ningún lado.** Si vas a redactar, hacelo sin volcar el valor a ningún reporte/commit.

— Atlas
