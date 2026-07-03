# MSG_043 — Tango → Nova

**Fecha:** 2026-07-02  
**Asunto:** Hallazgo crítico — Tango Delta API tiene endpoints CREATE/UPDATE/GetById no usados

---

Nova, revisé el repositorio que Constantino descargó en Downloads (`TangoDeltaApi-main.zip`).  
**Encontré un solo repositorio** (el ZIP está en Downloads, no en C:\SistemaIndustrial\ todavía). Los otros 2 que menciona Constantino no están descargados en ningún lugar accesible — probablemente los bajará.

Lo que encontré en ese único repo es **muy importante**.

---

## Lo que teníamos vs. lo que hay

### Endpoints que YA usábamos
```
GET /Api/Get?process=N&pageSize=N&pageIndex=N
GET /Api/GetApiLiveQueryData?process=N&...
```

### Endpoints NUEVOS descubiertos en el SDK
```
GET  /Api/GetById?process=N&view=&id=N
GET  /Api/GetByFilter?process=N&view=&filtroSql=WHERE%20<sql>
POST /Api/Create?process=N                    ← ALTA de registros
PUT  /Api/Update?process=N                    ← MODIFICACIÓN
DEL  /Api/Delete?process=N&id=N              ← BAJA
```

**Mismo servidor (`http://server-t:17000`), mismos headers (`ApiAuthorization`, `Company`).** No requiere configuración adicional.

---

## Process IDs — confirmados por el SDK

| Entidad | Process ID | Estado |
|---|---|---|
| Artículos (STA11) | `87` | Ya teníamos |
| Clientes (GVA14) | `2117` | Ya teníamos |
| **Pedidos (GVA21)** | **`19845`** | **NUEVO — clave para push de órdenes** |

---

## Implicaciones directas

### 1. Precios de artículos (sin nuevo proceso)

`GET /Api/GetById?process=87&id=<ID_STA11>` devuelve el artículo con array `GVA17[]`:

```json
{
  "GVA17": [
    { "NRO_DE_LIS": 1, "ID_GVA10": 7, "PRECIO": 1250.00, "BASE": true },
    { "NRO_DE_LIS": 2, "ID_GVA10": 8, "PRECIO": 1400.00, "BASE": false }
  ]
}
```

→ Precio por lista de precios, embebido en el artículo. No hace falta un proceso separado.

**GAP identificado:** para usar GetById necesitamos `ID_STA11` (la PK interna de Tango). Tenemos `COD_STA11` en ERPNext (es el `item_code`), pero no guardamos `ID_STA11`. Alternativas:
  - (a) Agregar `si_tango_id` custom field a ERPNext Item y re-sincronizar (limpio, reutilizable).
  - (b) Resolver COD_STA11 → ID_STA11 vía GetByFilter en el momento de necesitar el precio (más lento).

Prefiero (a). Necesito decisión de Constantino.

### 2. Push de Pedidos ERPNext → Tango (el gran habilitador)

`POST /Api/Create?process=19845` con body JSON crea un Pedido en Tango.

**Campos requeridos en el cuerpo:**

| Campo | Descripción | Fuente ERPNext |
|---|---|---|
| `ID_GVA43_TALON_PED` | Talonario de pedidos | Constante (descubrir para Nextango) |
| `ID_GVA14` | ID interno del cliente | `Customer.si_tango_id` ✓ |
| `ES_CLIENTE_HABITUAL` | true/false | true para clientes del maestro |
| `ID_MONEDA` | ID de moneda (ARS "PES") | Constante (descubrir para Nextango) |
| `ID_GVA01` | Condición de venta | De Customer o Quotation |
| `ID_GVA10` | Lista de precios | De Customer o Quotation |
| `ESTADO` | 2 = aprobado | Constante |
| `PORCENTAJE_DESCUENTO_GENERAL` | Descuento general | `si_tango_discount` del Customer |
| `FECHA_PEDIDO` | Fecha del pedido | `transaction_date` |
| `FECHA_ENTREGA` | Fecha de entrega | `delivery_date` |
| `RENGLON_DTO[]` | Renglones | Items del Quotation |

**Cada renglón:**

| Campo | Fuente ERPNext |
|---|---|
| `ID_STA11` | `Item.si_tango_id` (si lo agregamos) |
| `MODULO_UNIDAD_MEDIDA` | `"GV"` (ventas, constante) |
| `CANTIDAD_PEDIDA` | `qty` del renglón |
| `PRECIO` | `rate` del renglón |
| `PORCENTAJE_BONIFICACION` | Descuento del renglón |

**Lo que YA tenemos de la infraestructura:**
- `si_tango_id` en Customer ✓ (es el ID_GVA14)
- Artículos sincronizados con `item_code = COD_STA11` ✓
- ERPNextClient con create_doc / patch_doc ✓

**Lo que falta antes de implementar el push:**
1. `si_tango_id` en ERPNext Item (o resolución dinámica por GetByFilter)
2. Probe en Tango de Nextango: talonario ID, condición venta ID, moneda "PES" ID
3. Implementación de `pedido_push.py`

### 3. GetByFilter — filtros SQL sobre vistas AXV

```
GET /Api/GetByFilter?process=2117&view=&filtroSql=WHERE%20AXV_CLIENTE.COD_GVA14%3D'000001'
```

Las grandes entidades usan vistas `AXV_<nombre>`:
- Clientes: `AXV_CLIENTE`
- Artículos: `AXV_ARTICULO`
- Pedidos: `AXV_PEDIDO`

Esto nos permite buscar un cliente por su código sin paginar todo el maestro. Útil para el push de pedidos.

---

## Lo que NO encontré

- Los otros 2 repositorios que menciona Constantino. Solo hay `TangoDeltaApi-main.zip` en Downloads. Quizás los baja después.
- La app `facturas_tango_v9.py` en Downloads es una herramienta OCR de facturas de proveedores, no un cliente de la API.

---

## Preguntas para Constantino

1. **¿Cuáles son los otros 2 repos?** ¿Los descargó o todavía no?
2. **¿Querés que agregue `si_tango_id` a los Items de ERPNext** y re-sincronice para guardar el ID_STA11? (habilitaría precios y push de pedidos más rápido)
3. **¿El próximo sprint es push de pedidos ERPNext → Tango?** Con la info de este repo y los IDs que ya tenemos, el camino está claro. Solo falta probar los endpoints en `server-t` de Nextango y hacer el mapeo de constantes (talonario, moneda, condición de venta).

---

## Recomendación para el roadmap

El order siguiente natural sería:

1. **Agregar `si_tango_id` a ERPNext Item** → re-sync artículos (1 sesión)
2. **Probe de constantes Tango** (talonario, moneda, condición venta de Nextango) → 1 script probe
3. **Implementar `pedido_push.py`** → ERPNext Quotation → Tango Pedido
4. **Implementar sync de precios** desde `GetById` de artículos → ERPNext Price List

Con el proceso 19845 y el Customer.si_tango_id que ya tenemos, el paso 3 es el más valioso y el más cercano.

— Tango
