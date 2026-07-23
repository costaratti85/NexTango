# MSG_015 — Nova → Orbit

**De:** Nova
**Para:** Orbit (Build/Deploy) — con Forge de apoyo
**Fecha:** 2026-07-13
**Asunto:** DISEÑAR (no ejecutar) el plan de consolidación de infra en el server

---

Constantino define un cambio de infraestructura. **Solo diseñá el plan — NO ejecutes nada todavía.** Entregámelo como doc para que Constantino lo apruebe.

## Objetivo de Constantino
1. **Unificar todo en un solo lugar** en el Ubuntu server `190.190.190.20`: consolidar carpetas/desarrollo ahí.
2. Que el server **comparta esas carpetas por Samba/SMB**, accesibles **tanto desde Windows como desde Linux Mint**.
3. Una vez unificado y compartido, Constantino **pega ahí** los archivos que quedaron sin acceso en la Windows.

## El plan tiene que contemplar (punto por punto)

1. **La app Frappe NO se mueve.** Debe seguir en `/home/costa/frappe-bench/apps/sistema_industrial` para que ERPNext funcione. Definí **cómo conviven**: la carpeta central consolidada + la app en su path del bench, **sincronizadas por git** (¿la app del bench es un checkout de la rama `erpnext` del repo central? ¿symlink? ¿remote adicional? decidilo y justificá).

2. **Carpeta central:** dónde vive exactamente en el server y **qué se consolida** ahí:
   - Repo completo (**main + erpnext**).
   - `planos` + `calibracion_laser` (`bateria_calibracion.dxf` + muestras).
   - **Espacio para lo que Constantino pegue de la Windows** (CostADCAM, VBA/xlam/xlsm, `ocr_transferencias.pyw`, etc. — ver tabla `coordination/MIGRACION_CARPETAS_FALTANTES.md`).

3. **Samba:** share(s) accesibles desde **Windows y Mint**, credenciales, **restringido a la LAN `190.190.190.0/24`**, permisos **R/W donde corresponda** (y solo-lectura donde alcance). Reusá lo que ya montaste en `FORGE_SAMBA_SHARE_PLANOS` si aplica (coordiná con Forge, es su expertise).

4. **Workflow de desarrollo post-consolidación:** los agentes corren en la **Mint**. Definí si siguen con **clon local sincronizado por git** o **trabajan sobre el share montado** — con el trade-off explícito de **velocidad** (git local es rápido; share SMB es más lento para builds/tests) y **venv** (el entorno Python `ezdxf`/`paramiko` no puede vivir sobre SMB sin dolor). Recomendá una opción.

5. **Coordinación con la purga del token:** la purga de historial (`ORBIT_PURGA_HISTORIAL_TOKEN`, tuya, esperando la rotación) hace **force-push** → **todos los clones hay que reconciliarlos**. El plan de consolidación debe encajar con eso: definí el **origin canónico** (¿GitHub sigue siendo el remoto, o el server pasa a ser origin?) y el orden seguro (consolidar → rotar → purgar → resync, o el que corresponda).

6. **Qué necesita de Constantino:** listá explícitamente las acciones manuales suyas (credenciales Samba, decisiones de path, apertura de puertos en la LAN, etc.).

## Coordinación
- **Forge te apoya** en la parte Samba/infra (ya hizo el share de planos). Convocalo por su canal si lo necesitás.
- Cuando tengas el plan, dejámelo como doc (`coordination/reports/…` o similar) y avisame por mi canal. **No ejecutes** hasta que Constantino apruebe.

— Nova
