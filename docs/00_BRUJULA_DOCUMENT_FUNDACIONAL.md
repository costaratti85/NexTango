# Documento fundacional de Sistema Industrial

> Escrito por Brújula — conversación original antes del equipo de agentes.
> Este documento es el norte completo del proyecto a largo plazo.
> Ningún agente puede contradecirlo. Toda decisión técnica debe ser coherente con él.

---

## 1. Problema de negocio que resuelve

Sistema Industrial debe resolver un problema operativo real de una metalúrgica: convertir pedidos comerciales, piezas a fabricar, cortes, plegados, perfiles, materiales, estados de taller y facturación en un flujo único, ordenado, trazable y escalable.

La empresa vende recursos industriales combinados: chapa, cortes, plegados, perfiles, barras, caños, productos comerciales, tiempo de máquina, conocimiento técnico, capacidad de producción, organización operativa.

Hoy gran parte de ese conocimiento vive en las personas. El sistema debe capturarlo y volverlo repetible, trazable, auditable, escalable, enseñable y conectable.

El objetivo no es reemplazar de golpe la forma de trabajar, sino convertir lo que ya funciona en un sistema más claro, ordenado y automatizable.

## 2. Reglas de negocio inamovibles

1. ERPNext es columna operativa — Sistema Industrial vive como app Frappe sobre ERPNext
2. Tango es dueño fiscal/contable — no reemplazar en facturación, contabilidad ni comprobantes
3. Excel se respeta como pricing humano — no eliminar abruptamente
4. Tango es maestro de precios finales — ERPNext sincroniza copia
5. CypCut hace nesting — no reimplementar
6. El postprocesador propio hace G-code — no reimplementar
7. El sistema acompaña a la empresa — tecnología se adapta a la operación, no al revés
8. Humano puede forzar decisión — el sistema sugiere, el humano decide, el sistema audita
9. Toda acción importante debe ser trazable — quién, cuándo, qué, desde qué rol
10. No duplicar lógica entre módulos — cada módulo tiene un dueño
11. El estado por pieza es central — no alcanza con el estado del pedido
12. Producción se organiza por lógica de taller — material, espesor, máquina, matriz, prioridad
13. Cliente externo nunca ve datos ajenos — seguridad obligatoria antes de portal público

## 3. Flujos completos definidos

### Flujo comercial básico
Usuario → cliente → cotización → ítems (piezas paramétricas, paneles, biblioteca cliente, perfiles, comerciales) → cálculo automático de recursos → precios desde Tango → cotización ERPNext → preparación para fabricación si se confirma

### Flujo de panel decorativo (primera rebanada)
Tipo de panel → medidas (ancho, alto, espesor, material, cantidad) → reglas del patrón (margen, offset X/Y, modo sin cortar centrado O cortar en borde) → geometría generada → cálculo (chapa, área, peso, perímetro, metros de corte, perforaciones) → cotización ERPNext → DXF → pieza disponible para lote de corte

### Flujo de piezas paramétricas
Tipo → parámetros → material → espesor → cantidad → perforaciones → geometría → recursos → cotización → tareas productivas → disponible para corte/plegado

### Flujo de biblioteca de piezas de cliente
Cliente → su biblioteca → piezas guardadas → seleccionar → cantidad → agregar al pedido → trazabilidad (cliente, pieza, revisión, historial, archivos)

### Flujo de corte lineal
Perfil/caño/barra → enteros o fracciones → lista de cortes → optimización → cálculo (barras enteras, sobrantes, desperdicio, cortes, servicio) → cotización. Regla: si última barra supera ~65% del largo estándar, sugerir cobrar barra entera.

### Flujo de lote de corte por espesor
Pantografista → proceso (láser/plasma/oxicorte) → material → espesor → piezas pendientes compatibles → selección → compilar DXF ordenado → CypCut hace nesting → postprocesador hace G-code → registrar avance

### Flujo de guillotina
Sistema detecta pieza rectangular sin perforaciones → sugiere guillotina → genera tarea → fuera del lote láser salvo override humano

### Flujo de plegado
Sistema detecta piezas con pliegues → genera tareas de plegado → plegador filtra por matriz/punzón/espesor → registra avance parcial o completo

### Flujo de estados por pieza
pedida → cotizada → aprobada → en lote de corte → cortada parcial → cortada completa → pendiente plegado → plegada parcial → plegada completa → observada → lista → entregada parcial → entregada

### Flujo de producción por taller
Operario → identificarse → rol activo (láser/plasma/oxicorte/guillotina/plegado/almacén) → ver tareas pendientes → filtrar → registrar avance parcial

### Flujo OCR proveedores
Factura → OCR QR → identifica proveedor → recuerda posición de campos → OCR artículos → si nuevo: agregar a Tango → si existente: stock a ERPNext + precio a Excel → pricing en Excel → precios a Tango

## 4. Cálculos automáticos requeridos

- Recursos industriales: superficie de chapa, peso, perímetro de corte, metros de láser, cantidad de contornos, pliegues, tiempo estimado, barras, metros lineales, desperdicio, cortes
- Cotización: precio por recurso × cantidad → subtotales → total
- Decisión de proceso: rectángulo sin perforaciones → guillotina; espesor alto → oxicorte; general → láser/plasma
- Producción: cantidad hecha/pendiente, porcentaje avance, agrupamientos por material/herramienta

## 5. Archivos a generar

- DXF de pieza individual
- DXF de lote de corte (ordenado, 300mm entre piezas, 500mm entre filas de espesor, etiquetas con espesor y cantidad)
- Orden de taller
- Manifiesto JSON por pedido/lote
- Cotización en ERPNext
- Datos para Tango (facturación, artículos, precios)
- Reportes de producción

## 6. Decisiones de diseño fundamentales

1. **Pedido ≠ Lote de corte** — el pedido pertenece a un cliente, el lote pertenece a producción y mezcla piezas de varios pedidos
2. **Recurso industrial como unidad económica** — el sistema vende chapa, corte, plegado, metro lineal, tiempo de máquina
3. **Roles dinámicos** — un usuario puede tener varios roles, elige el rol activo al trabajar
4. **Rebanadas finas de punta a punta** — no módulos gigantes aislados
5. **Módulos con dueños claros** — Backend Core (Atlas), Production/MES (Lechu), CAD/DXF (Punto/Nido), Corte lineal (Gemu), CRM/Tango (Tango agent), Frontend/UX (Vega), Build (Orbit), ERPNext (Forge)

## 7. Norte a largo plazo

El vendedor cotiza mejor. El cliente pide más fácil. El taller se organiza por espesor/proceso. El pantografista genera lotes claros. El plegador agrupa por herramienta. Administración factura sin duplicar carga. La dirección tiene trazabilidad y control. La empresa crece sin depender solo de memoria humana.

**El objetivo no es un programa. Es una plataforma que convierte la operación real en un flujo digital coherente, confiable y evolutivo.**
