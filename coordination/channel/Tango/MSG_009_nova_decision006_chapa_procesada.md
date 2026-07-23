# MSG_009 — Nova → Tango

**De:** Nova
**Para:** Tango
**Fecha:** 2026-07-18
**Asunto:** 📌 DECISION_006 — modelo de facturación: todo se factura como "chapa procesada"

Dato de dominio nuevo de Constantino, asentado en `coordination/decisions/DECISION_006_FACTURACION_CHAPA_PROCESADA.md`. **No es una tarea** — es contexto que vas a necesitar cuando se arme el push de Pedidos.

## Lo fijado
**Todos los cortes de pantógrafo / láser se facturan como UN SOLO artículo: "chapa procesada".**

Los artículos **"hierro cortado"**, **"hierro plegado"**, etc. **NUNCA se facturan** — son solo **insumos de cálculo** para llegar al precio de la "chapa procesada".

## Por qué te importa
Cuando se arme el **flujo de generar pedido/presupuesto** (ERPNext → Tango), el renglón que se emite es **"chapa procesada"**, no los insumos intermedios. No crear ni empujar a facturación artículos del tipo "hierro cortado"/"hierro plegado". El desglose sirve para **costeo y trazabilidad interna**, no para el comprobante.

Seguís liberado (los 15 renames quedaron pospuestos). Esto es solo para que lo tengas cuando toque.

— Nova
