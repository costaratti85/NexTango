# Cargar artículos a ERPNext — las opciones explicadas (para decidir juntos)

**De:** Forge · **Para:** Constantino (vía Nova) · **Fecha:** 2026-07-14
**Objetivo:** que entiendas TODAS las formas de cargar artículos antes de decidir, y que veas qué **ya está cargado hoy**. No cargué ni cambié nada — esto es solo relevamiento + explicación.

---

## 0. Lo primero: qué hay HOY en ERPNext (dato real, recién consultado)

**Ya hay 2.193 artículos cargados en ERPNext. De esos, 2.189 vinieron del sync de Tango** (tienen guardado su "ID de Tango"). Es decir: **la carga grande YA se hizo y sigue ahí.** No estás partiendo de cero.

| Dato | Valor |
|---|---|
| Artículos (Items) totales en ERPNext | **2.193** |
| De Tango (con su `ID de Tango` guardado) | **2.189** |
| Sueltos (sin ID de Tango, probablemente de ejemplo/manuales) | 4 |

Repartidos así por categoría (los grupos que armó el sync):
- **Tubos y Perfiles:** 1.564
- **Insumos:** 219
- **Materiales:** 188
- **Chapas y Flejes:** 168
- **Ferretería:** 50

> Traducción: si volvés a correr el sync, **no duplica** — reconoce cada artículo por su código y lo actualiza. Así que lo que decidamos es más bien *cómo seguir* (corregir categorías, sumar los que falten, cambiar el criterio), no "cargar todo de nuevo".

---

## 1. Data Import (subir un Excel/CSV desde la pantalla de ERPNext)

**Qué es:** una pantalla de ERPNext donde bajás una plantilla Excel, la llenás con tus artículos (una fila por artículo) y la subís. ERPNext crea o actualiza los artículos según lo que pusiste.

**Cómo es en la práctica:**
- Elegís el tipo "Item" (Artículo), bajás la plantilla, la completás en Excel, la subís.
- Podés elegir "Crear nuevos" o "Actualizar existentes".
- Antes de aplicar, muestra una **previsualización** y avisa fila por fila si algo está mal (te deja corregir y reintentar).

**Ventajas:**
- No necesitás programar nada; lo hacés vos desde el navegador.
- Bueno para tandas **chicas o medianas** y para correcciones puntuales (ej.: cambiar la categoría de 200 artículos).
- Es visual y perdona errores (te los marca).

**Desventajas / límites:**
- Para **miles** de filas se vuelve lento y a veces hay que partirlo en tandas (500–1000 por vez) para que no se corte.
- Sos vos quien arma el Excel con las columnas EXACTAS que ERPNext espera (si una categoría no existe, falla esa fila).
- No es lo ideal para una sincronización **repetida y automática** (para eso está la opción 3).

**Cuándo conviene:** cargas manuales, correcciones, o sumar un lote nuevo que tenés en Excel.

---

## 2. Carga por programa (API REST / carga masiva programática)

**Qué es:** en vez de subir un Excel a mano, un **programa** le manda los artículos a ERPNext uno por uno (o de a bloques) por su "puerta de entrada de datos" (la API).

**Ventajas:**
- Ideal para **volúmenes grandes** y para repetir la carga cada vez que haga falta, sin trabajo manual.
- Se puede automatizar (ej.: "cada noche traé de Tango los artículos nuevos/cambiados").
- Control total: se decide exactamente cómo se traduce cada dato.

**Desventajas:**
- Requiere que alguien (nosotros) escriba y mantenga ese programa.
- No lo operás "a mano": corre solo o se dispara con un botón.

**Cuándo conviene:** cuando la fuente es Tango y querés que ERPNext se mantenga sincronizado en el tiempo. **Esto es exactamente lo que ya existe hoy** (opción 3).

---

## 3. El sync que YA construimos (Tango → ERPNext) — cómo funciona

Ya hay un programa hecho (`article_push.py`) que trae los artículos de Tango y los mete en ERPNext. **Es el que cargó los 2.189 de arriba.** Cómo se comporta:

- **Reconoce cada artículo por su código** (el mismo código que tiene en Tango, ej. `01-01-01-02-005`). Por eso **no duplica**: si el artículo ya está, lo actualiza; si no está, lo crea.
- Guarda el **ID interno de Tango** en cada artículo (campo "Tango ID"), para poder cruzarlos siempre.
- **Traduce automáticamente:**
  - La **familia de Tango → categoría de ERPNext**. Hoy el criterio es:
    | Familia en Tango | Categoría en ERPNext |
    |---|---|
    | 01 - PERFILERIA / 02 - TUBOS ESTRUCTURALES | Tubos y Perfiles |
    | 07 - CHAPA / 05 - METAL DESPLEGADO | Chapas y Flejes |
    | 06 - FERRETERIA | Ferretería |
    | 04 - MALLAS ACINDAR | Materiales |
    | 50 - GRUPO B&D | Insumos |
    | (cualquier otra) | Materiales (por defecto) |
  - La **unidad** (unidad/kg/m/m²) a la unidad equivalente de ERPNext.
- Por ahora marca los artículos como **"no lleva stock"** (no controla existencias). Esto se puede cambiar si querés llevar stock.

**Lo importante para vos:** este criterio de categorías es una **decisión** que tomamos nosotros y **se puede rehacer** según cómo tengas TU lista organizada. Si tus categorías/subcategorías reales son otras, ajustamos esta tabla y volvemos a correr el sync (que corrige sin duplicar).

---

## 4. Cómo se manejan CATEGORÍAS y SUBCATEGORÍAS en ERPNext

En ERPNext las categorías se llaman **"Grupos de artículo" (Item Group)** y funcionan como un **árbol** (categoría → subcategoría → sub-subcategoría, sin límite de niveles):

- Un grupo puede ser **contenedor** (agrupa otros, no tiene artículos directos) o **hoja** (es donde cuelgan los artículos).
- **Cada artículo pertenece a UN solo grupo** (el más específico). No se le ponen dos categorías a la vez; la jerarquía la da el árbol de grupos por encima.
- Ejemplo: un caño estructural iría en `Materiales → Tubos y Perfiles`. El artículo apunta a "Tubos y Perfiles", y "Tubos y Perfiles" cuelga de "Materiales".

**El árbol que hay hoy en ERPNext** (ya creado):
```
Materiales
  ├─ Barras
  ├─ Chapas y Flejes      (168 artículos)
  └─ Tubos y Perfiles     (1.564 artículos)
Insumos
  ├─ Consumibles
  └─ Ferretería           (50 artículos)
Servicios
  ├─ Corte Láser · Corte Plasma · Oxicorte · Grabado · Plegado
Piezas
  ├─ Paneles Decorativos · Piezas Cortadas · Piezas Plegadas
(+ grupos por defecto de ERPNext: Products, Raw Material, Services, etc.)
```
> Detalle técnico menor a revisar cuando diseñemos la carga: algunos grupos "padre" están marcados como hoja en vez de contenedor. No rompe nada (los artículos están bien ubicados), pero conviene ordenarlo. Lo anoto y lo arreglo en la ejecución.

**Cómo pensarlo vos:** decime tus categorías y subcategorías tal como las tenés en la cabeza (o en Tango), y las volcamos a este árbol. La estructura de ERPNext banca cualquier jerarquía que uses.

---

## 5. Campos de un artículo: cuáles son y cuáles son OBLIGATORIOS

Un artículo en ERPNext tiene muchos campos posibles, pero para existir necesita **solo 4**:

| Campo (ERPNext) | Qué es | ¿Obligatorio? | En Tango sale de… |
|---|---|---|---|
| **Código** (`item_code`) | El código único del artículo | **SÍ** | el "Código" de Tango |
| **Nombre** (`item_name`) | La descripción/nombre | **SÍ** (si no, usa el código) | la "Descripción" |
| **Grupo** (`item_group`) | La categoría (del árbol de arriba) | **SÍ** | la "Familia", traducida |
| **Unidad de medida** (`stock_uom`) | unidad / kg / metro / m²… | **SÍ** | la unidad de Tango |
| Descripción larga | Texto extra | No | Descripción + sinónimo |
| ¿Lleva stock? | Si controla existencias | No (hoy = no) | — |
| Precios, impuestos, proveedor… | Todo lo comercial | No | otras tablas de Tango |

**Resumen:** con **Código + Nombre + Categoría + Unidad** ya se crea un artículo. Todo lo demás es opcional y se puede sumar después.

---

## 6. El Excel que me pasaste — qué es realmente ⚠

Leí `/home/costa/Python/OCR Proveedores/Artículos (1).xlsx` (solo lectura). **Ojo con esto:**

- **NO es tu lista de artículos con datos.** Es la **plantilla vacía de "actualización masiva" de Tango**: tiene la hoja "Artículos" con los **títulos de 98 columnas pero CERO filas de datos**.
- Es el formato que Tango te da para *llenar y volver a subir a Tango* (no para exportar lo que ya tenés). Internamente está atado al proceso de artículos de Tango (STA11, nº 87).
- Las otras 80 hojas del archivo son **listas de referencia** para los desplegables (clientes: 8.453; proveedores: 613; actividades AFIP: 899; etc.). No son artículos.

**Qué SÍ nos da:** el **mapa completo de las 98 columnas** que Tango maneja por artículo. Las que nos importan para cargar a ERPNext son pocas:

| Columna Tango (de las 98) | Va a ERPNext como |
|---|---|
| **Código** | Código del artículo |
| **Descripción** / Descripción adicional / Sinónimo | Nombre / descripción larga |
| **Tipo** y **Escala** (+ códigos de valor de escala 1 y 2) | definen variantes/medidas — a decidir cómo tratarlas |
| **Lleva stock**, Método/Orden de descarga | si controla existencias |
| **Código de UM de stock** / UM de ventas | Unidad de medida |
| Códigos de IVA / impuestos / % utilidad / % bonificación | precios e impuestos (fase posterior) |
| Código de proveedor habitual | proveedor (fase posterior) |

> El resto de las 98 (percepciones, turismo, exportación, NCM, comprobantes electrónicos, etc.) son para AFIP/casos que probablemente no necesitemos al principio.

**Conclusión del archivo:** sirve para entender la estructura, **pero no tiene datos para cargar.** Si querés trabajar desde tu lista real, hay 3 fuentes posibles (lo decidís vos):
1. **Un export de Tango CON datos** (la misma plantilla pero llena, o un listado de artículos).
2. **Directo de la API de Tango** (proceso 87) — es lo que ya usa el sync.
3. **Lo que ya está en ERPNext** (los 2.189) — revisarlo y corregir sobre eso.

---

## 7. Lo que necesito de vos para diseñar la carga juntos

1. **Contame cómo tenés armada TU lista**: ¿cuáles son tus categorías y subcategorías "de verdad"? ¿coinciden con las familias de Tango o querés otra organización?
2. **¿La fuente es Tango** (seguimos con el sync automático) **o tenés un Excel propio con los datos**? Si es Excel, pasámelo *con las filas llenas* (este estaba vacío).
3. **¿Querés llevar stock** de estos artículos o alcanzan como catálogo de precios/compra?
4. **¿Sumamos precios/impuestos/proveedor** ahora o en una segunda etapa?

Con eso diseñamos la carga a medida (probablemente ajustar el criterio de categorías del sync y volver a correrlo, que corrige sin duplicar).

---

### En una frase
**La carga grande ya está hecha (2.189 artículos de Tango en ERPNext).** El Excel que me pasaste es la plantilla vacía de Tango, no datos. Lo que sigue es **decidir tus categorías/subcategorías reales** y ajustar sobre lo cargado — no empezar de cero.

— Forge
