# MSG_032 — Nova → Punto

**De:** Nova
**Para:** Punto
**Fecha:** 2026-07-13
**Asunto:** Generar thumbnails de los patrones con MOTOR NATIVO (parámetros definidos)

---

## Pedido de Constantino
Generá los **thumbnails de los patrones con el motor NATIVO**, para los **tres motores nativos**.

## Parámetros a usar (los mismos para los tres)
- **Agujero:** 10 mm
- **Distancia entre agujeros:** 15 mm
- **Margen:** 20 mm
- **Panel:** 300 × 300 mm

## Hipótesis de Constantino (para orientar, no es diagnóstico cerrado)
> "Intuyo que como para que exista un patrón hay que definir parámetros, y no se definieron, quedaron los thumbnails sin hacer, por no tener patrón."

O sea: los thumbnails no se generaron porque el patrón no tenía parámetros definidos (sin parámetros no existe el patrón → no hay geometría que renderizar). Al definir estos parámetros, el patrón debería existir y el thumbnail nativo generarse.

## Qué necesito de vos
1. Confirmame **cuáles son los tres motores nativos** (para que quede claro sobre qué generás).
2. Definí esos parámetros y **generá los thumbnails con el motor nativo** (no el render DXF/fallback).
3. Verificá que aparezcan en la galería/admin-patrones.
4. Reportá: si la hipótesis era correcta (faltaban parámetros) o si la causa era otra, y qué commit/deploy queda.

Prioridad media (Panel Decorativo, en paralelo a la rebanada de precio).

— Nova
