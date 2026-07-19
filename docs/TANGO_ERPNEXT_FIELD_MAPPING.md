> ⚠️ **CORRECCIÓN 2026-07-19 — DECISION_011.** Este documento contiene la errata **"Tango maestro de precios"** (precios a/desde Tango, sync de precios Tango, cache de precios Tango). **ES FALSO: Tango NO maneja precios.** El pricing se hace en **EXCEL**; hoy el **vendedor los carga a mano** en el sistema (ERPNext). Tango es **fiscal/facturación**. Todo tramo de este doc que diga "precios a/desde Tango", "Tango maestro/publicados de precios" o "sync/cache de precios Tango" **queda SIN EFECTO**. Ver `coordination/decisions/DECISION_011_PAGINA_PRECIOS_SOLO_LECTURA.md`.

---

# Mapeo Tango Gestión → ERPNext

Fuente de verdad: Tango para artículos, clientes, precios y documentos fiscales.
ERPNext consume estos datos como mirror de solo lectura (salvo stock operativo y pedidos).

---

## Artículos — Tango STA11 → ERPNext Item

| Campo Tango     | Tipo    | Campo ERPNext            | Notas                                      |
|-----------------|---------|---------------------------|--------------------------------------------|
| `COD_STA11`     | string  | `item_code`              | Clave primaria visible                     |
| `DESCRIPCIO`    | string  | `item_name`, `description` |                                           |
| `SINONIMO`      | string  | `description` (apéndice) | Descripción adicional                      |
| `COD_BARRA`     | string  | `barcodes[].barcode`     | Tabla hija de Item                         |
| `FAMILIA`       | string  | `item_group` (nivel 1)   | Ver jerarquía de grupos abajo              |
| `GRUPO`         | string  | `item_group` (nivel 2)   | Subgrupo dentro de FAMILIA                 |
| `CLASIFICACION` | string  | `item_group` (nivel 3)   | Solo si existe en Tango                    |
| `ID_STA11`      | int     | `custom_tango_id`        | Campo custom en ERPNext, solo lectura      |
| `FECHA_ALTA`    | date    | —                        | No se mapea (usar git blame / Tango audit) |
| `COMENTARIOS`   | string  | —                        | Ignorado en sync                           |
| `PERFIL`        | string  | —                        | Por definir si aplica                      |
| —               | —       | `is_stock_item`          | True para materiales, False para servicios |
| —               | —       | `stock_uom`              | Derivado de UNIDAD_MEDIDA o default "unidad" |

### Proceso API
- **Process ID**: `87`
- **Endpoint**: `GET /Api/Get?process=87&pageSize=100&pageIndex=N`
- **Headers**: `ApiAuthorization: <token>`, `Company: 25`

### Ferretería
Artículos cuyo `COD_STA11` empieza con `06-` → `item_group = "Ferretería"` (override de FAMILIA/GRUPO).

---

## Clientes — Tango GVA14 → ERPNext Customer

> **Process ID aún no confirmado.** Ejecutar `python tools/probe_tango_clientes.py`
> para descubrirlo. El script busca campos `CUIT`, `RAZON_SOCIAL`, `COD_GVA14`.

| Campo Tango         | Tipo    | Campo ERPNext                   | Notas                                        |
|---------------------|---------|---------------------------------|----------------------------------------------|
| `COD_GVA14`         | string  | `customer_name` (código)        | O campo custom `customer_code` si ERPNext usa nombre |
| `RAZON_SOCIAL`      | string  | `customer_name`                 | Nombre legal                                 |
| `NOMBRE`            | string  | `customer_name`                 | Alternativa si no hay RAZON_SOCIAL           |
| `CUIT`              | string  | `tax_id` (custom)               | 11 dígitos sin guiones                       |
| `CONDICION_IVA`     | string  | `custom_vat_condition`          | RI / Monotributo / Exento / Consumidor Final |
| `DOMICILIO`         | string  | `address_line1` (Address link)  | Crear Address vinculado al Customer          |
| `LOCALIDAD`         | string  | `city`                          |                                              |
| `PROVINCIA`         | string  | `state`                         |                                              |
| `COD_POST`          | string  | `pincode`                       |                                              |
| `TELEFONO`          | string  | `phone` (Contact link)          |                                              |
| `EMAIL`             | string  | `email_id` (Contact link)       |                                              |
| `COD_CPG`           | string  | `payment_terms`                 | Mapear a Payment Terms de ERPNext            |
| `LIMITE_CRED`       | float   | `credit_limit`                  |                                              |
| `ID_GVA14`          | int     | `custom_tango_id`               | Campo custom, solo lectura                   |
| `INHABILITADO`      | string  | `disabled`                      | "S" → disabled=1                            |

### Estructura en ERPNext
Un cliente de Tango genera **3 documentos** en ERPNext:
1. **Customer** — datos principales
2. **Address** — domicilio (link al Customer)
3. **Contact** — teléfono y email (link al Customer)

---

## Precios — Tango → ERPNext Price List

> Process ID para listas de precio no confirmado. Investigar junto al probe de clientes.

| Campo Tango    | Campo ERPNext                    |
|----------------|----------------------------------|
| `COD_STA11`    | `item_code`                      |
| `PRECIO`       | `price_list_rate`                |
| `MONEDA`       | `currency` (ARS por defecto)     |
| `LISTA`        | `price_list` (nombre de lista)   |

La lista de precios de Tango es **solo lectura** en ERPNext.
Los cambios de precio se originan en Tango y se sincronizan hacia ERPNext.

---

## Documentos Fiscales — Tango → ERPNext

Tango es la autoridad fiscal. Cada factura/NC en Tango genera una actualización en ERPNext:

| Evento Tango                | Acción ERPNext                                    |
|-----------------------------|---------------------------------------------------|
| Factura emitida             | Crear Sales Invoice (estado: Submitted)           |
| Nota de crédito emitida     | Crear Credit Note vinculada a la factura          |
| Factura → stock descuenta   | Actualizar stock en depósito "Producto Terminado" |

---

## Campos custom a crear en ERPNext

Estos campos no existen en ERPNext base y deben crearse via Custom Field:

| DocType   | Field Name         | Type    | Label              |
|-----------|--------------------|---------|--------------------|
| Item      | `custom_tango_id`  | Int     | Tango ID (STA11)   |
| Customer  | `custom_tango_id`  | Int     | Tango ID (GVA14)   |
| Customer  | `custom_cuit`      | Data    | CUIT               |
| Customer  | `custom_vat_condition` | Select | Condición IVA   |

---

## Estructura mínima ERPNext (bootstrap)

Ejecutar `python tools/erpnext_bootstrap.py` para crear automáticamente:

### Item Groups
```
All Item Groups
├── Materiales
│   ├── Chapas y Flejes
│   ├── Tubos y Perfiles
│   └── Barras
├── Servicios
│   ├── Corte Láser
│   ├── Corte Plasma
│   ├── Oxicorte
│   ├── Plegado
│   └── Grabado
├── Piezas
│   ├── Paneles Decorativos
│   ├── Piezas Cortadas
│   └── Piezas Plegadas
└── Insumos
    ├── Ferretería
    └── Consumibles
```

### Warehouses
```
Almacén Principal - NXT
├── Materia Prima - NXT
├── Producción WIP - NXT
├── Producto Terminado - NXT
└── Merma y Retazos - NXT
Devoluciones - NXT
```

### UoMs
`kg`, `g`, `m`, `m2`, `m3`, `mm`, `hora`, `minuto`, `unidad`, `pieza`, `lote`, `plancha`

### Cost Centers
```
Nextango - NXT
├── Producción - NXT
│   ├── Corte Láser - NXT
│   ├── Corte Plasma - NXT
│   ├── Oxicorte - NXT
│   └── Plegado - NXT
└── Administración - NXT
```