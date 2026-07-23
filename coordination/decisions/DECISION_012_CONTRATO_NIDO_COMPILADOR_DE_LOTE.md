# DECISION_012 — Contrato de NIDO: compilador de lote de corte por demanda

**Fecha:** 2026-07-19 · **Definido por:** Constantino · **Registrado por:** Nova
**Estado:** Vigente — contrato de rol · **Nido sigue EN PAUSA** (ver §5)
**Corrige:** la hipótesis de "rol vaciado" del `COTEJO_ROLES_Y_CONTRATOS.md`

---

## 0. La corrección

El cotejo marcaba a Nido como **"rol vaciado por decisión"**: su contrato viejo decía *nesting*, y `DECISION_002` puso el nesting en CypCut.

**Eso era un error de lectura mío.** Nido **no perdió su rol**: el rol **estaba mal descrito**. Nunca fue nesting. Es lo que va **inmediatamente antes** del nesting.

> Estado correcto: **rol mal descrito → ahora corregido.** No "vaciado".

## 1. El rol

**NIDO = COMPILADOR DE LOTE DE CORTE POR DEMANDA.**

El pantografista/operador pide con un **criterio flexible**, y Nido genera **UN archivo CAD** con **todos los dibujos que cumplen ese criterio**, acomodados por **material**, **espesor** y **cantidad** de cada pieza.

Constantino: *es **la función más importante** para poder hacer los nestings.*

## 2. Dónde está parado — no solapa con CypCut

```
piezas del sistema → [ NIDO: compila el lote ] → archivo CAD → [ CypCut: nesting ] → [ CostADCAM: G-code ] → máquina
```

Nido está **aguas arriba** del nesting. Produce el **insumo** que CypCut después acomoda para aprovechar la chapa.

- Nido decide **qué piezas entran** al archivo y las ordena para que sean legibles y agrupables.
- CypCut decide **cómo se ubican** para aprovechar el material.

**No hay solapamiento con `DECISION_002`.** Nido no hace nesting, ni toolpaths, ni G-code.

## 3. Consultas a soportar

El criterio es **flexible y combinable**:

- Todos los dibujos de un **PEDIDO**.
- Todos los dibujos de un **ESPESOR** de un **MATERIAL**.
- Todos los pedidos que necesiten tal **MATRICERÍA** — para cortarlos **antes de que el plegador cambie la herramienta**.
- Un CAD con los pedidos que necesiten **POCOS SEGUNDOS DE MÁQUINA**.
- Etc. — la lista es **abierta**; el diseño debe permitir combinar criterios, no ser una lista cerrada de reportes.

La consulta por **matricería** es de lógica de taller pura (Brújula regla 12: producción se organiza por material, espesor, máquina, **matriz**, prioridad): el objetivo es agrupar el corte para no pagar cambios de herramienta en la plegadora.

## 4. Dependencias — 🔴 requisitos duros

### 4.1 Datos por pieza → depende de **MES (Lechu)**, hoy EN PAUSA

Cada pieza debe tener cargados:
- **material**
- **espesor**
- **cantidad**
- **matricería requerida**
- **pedido de origen**
- **segundos de máquina**

Sin ese modelo de piezas, Nido **no puede filtrar por nada**. Depende del modelo de piezas de **Lechu**, ligado a `DECISION_010` (estado por pieza, Pedido ≠ Lote).

### 4.2 Segundos de máquina → depende del **motor de cálculo de recursos** (simulador de Punto)

El criterio *"pocos segundos de máquina"* necesita un tiempo estimado **por pieza**.

**Nido es CONSUMIDOR de ese motor**, no lo implementa. No debe calcular tiempos por su cuenta (Brújula regla 10: no duplicar lógica).

## 5. Estado: EN PAUSA

**Este contrato NO reactiva a Nido.** `NIDO_COMPILADOR_DXF_BATCH` sigue en pausa por decisión de Constantino, y además está **técnicamente bloqueado** por §4.1 (MES en pausa).

Lo que sí queda fijado: **el rol, el alcance y los requisitos**. Cuando se retome, Nido no arranca de cero ni se re-deriva distinto.

Aplica también `DECISION_008` (300/500 mm y etiquetas) al archivo que produce.

## 6. Consecuencia sobre la estructura del equipo

Este contrato **refuerza** que el *cálculo de recursos / física de máquina* merece **rol propio**: no alimenta solo al **precio** — también alimenta a **Nido**. Ver `PROPUESTA_ARREGLOS_DE_ROLES.md` §B.1.
