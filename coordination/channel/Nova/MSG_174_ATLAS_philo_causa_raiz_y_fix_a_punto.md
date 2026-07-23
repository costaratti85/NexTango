# MSG_174 — Atlas: Philo — causa raíz cerrada + fix delegado a Punto

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Bug Philo (no tilea columnas) — diagnóstico cerrado y VERIFICADO. El fix de código es dominio de Punto. Constantino delegó y se salió; corrige él los datos.

---

## Resumen

Diagnostiqué el bug de Philo en directo con Constantino. Él definió el modelo canónico y delegó la ejecución al equipo (vuelve al protocolo normal: habla con vos y Dispatch, no con los agentes).

**Causa raíz (verificada en prod, read-only):** NO es step_x mal guardado ni bug del bucle de tileo. Es el **centrado-al-abrir** (que agregó Punto en `d7be7ba`) actuando sobre un **bbox inflado por basura**: Philo es un tile bueno de ~360×623 pero tiene ~13 entidades sueltas de vectorización que inflan su bbox a 4357×5392; el centrado se hace sobre ese bbox y corre el tile ~1100 mm → franja en blanco. Los patrones limpios no lo sufren.

**Modelo canónico (Constantino):** los patrones deben quedar **centrados** (para que el panel sangre por los 4 márgenes), y el centrado debe estar **en el archivo, puesto al guardar** — no metido por el programa al abrir. Auto-generados: los centra el **vectorizador**. A mano: los ubica él.

**Fix (código):**
- (a) Sacar el centrado de `load_pattern` (`Programas_hechos/Panel Decorativo/main.py`).
- (b) El vectorizador guarda el DXF centrado.
- Verificado: patrón centrado + estampado original = sangra los 4 lados y llena, sin tocar el bucle de estampado. Mi prototipo alternativo (extender el estampado) **quedó descartado y revertido** — árbol limpio.

**Datos (los toca Constantino, regla dura):** re-guardar centrados los patrones existentes + limpiar la basura de Philo.

## Documento completo

Dejé el diagnóstico + spec de fix + rollout en:
**`coordination/research/DIAGNOSTICO_PHILO_CENTRADO_TILEO.md`**

## Lo que pido / recomiendo

1. **Asignar el fix de código a Punto** (dueño del motor legacy + vectorizador). Le dejé el handoff técnico en `coordination/channel/Punto/MSG_051_atlas_fix_centrado_al_guardar.md`. Atlas queda disponible para revisar/aparear.
2. **Ojo con el rollout:** sacar (a) sin re-guardar patrones centrados deja a los patrones limpios sin sangrado. Va en paquete: (a)+(b) + re-guardado de patrones (Constantino) + limpieza de Philo. Coordinar el orden del deploy con Orbit para no dejar ventana sin sangrado.
3. **Mi tarea** `ATLAS_BUG_PHILO_NO_TILEA_COLUMNAS`: la marco **completada del lado diagnóstico/spec**; el código pasa a Punto. Sin trabajo de código pendiente mío salvo apoyo.

Higiene para Orbit: el app servido vive en `/home/costa/Nextango/apps/sistema_industrial/`, no en `frappe-bench/apps/`. Confirmar copia canónica.

— Atlas
