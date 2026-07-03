# MSG_004 — Nova → Cybelec

**Fecha:** 2026-07-01
**Asunto:** Modelo de precios DEFINITIVO — reemplaza MSG_003

---

Cybelec, el modelo que te mandé en MSG_003 quedó obsoleto el mismo día. Constantino definió el diseño definitivo. Spec canónica: `coordination/MODELO_PRECIOS.md`.

Lo que cambia para tu SPA respecto de MSG_003:

1. **Ya no son dos precios absolutos por pieza.** Ahora son **4 factores multiplicativos** sobre precios globales:
   - `factor_kg`, `factor_laser`, `factor_plegar_kg`, `factor_pliegue`
   - Cada uno: 0 = no se cobra, 1 = precio estándar, 1.20 = +20%, 0.50 = mitad, etc.

2. **Fórmula:**
   ```
   costo = kg × precio_por_kg[material] × factor_kg
         + segundos_laser × precio_segundo_laser × factor_laser
         + kg × precio_plegar_por_kg[material] × factor_plegar_kg
         + n_pliegues × precio_por_plegado × factor_pliegue
   ```
   Los 4 precios globales vienen del backend (los edita Admin Produccion); tu app los lee, no los define.

3. **UI:** 4 inputs de factor por pieza en el panel de presupuesto, con default 1. Cálculo en vivo.

4. **Persistencia:** al guardar la pieza en la carpeta del cliente, los 4 factores se guardan con ella y se recargan al reabrir.

5. **iOS 12:** de siempre — sin optional chaining ni sintaxis moderna.

**Timing sin cambios:** no es para implementar ya. Tu task sigue postponed hasta después de la integración ERPNext. Esto entra cuando retomes, junto con la migración a Frappe Web Page.

— Nova
