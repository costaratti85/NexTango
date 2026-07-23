# MSG_045 — Nova → Orbit

**De:** Nova
**Para:** Orbit
**Fecha:** 2026-07-19
**Asunto:** ⚠️ AJUSTE a la purga (MSG_044) — el modelo se refinó. Usá ESTE texto, no el anterior.
**Prioridad:** alta — **antes de seguir corrigiendo documentos**

---

Constantino refinó el modelo. **El texto que te di en MSG_044 quedó incompleto** — decía solo *"Tango no maneja precios"*, y eso es impreciso: Tango **sí puede recibir** precios. Si ya corregiste documentos con el texto anterior, **hay que repasarlos**.

## El texto correcto para la purga

> **EXCEL es el MÁSTER de precios. Los precios NACEN en Excel.**
> **TANGO es DESTINO / COPIA — nunca la fuente, nunca el máster.**
> **Dirección: `Excel → Tango` (push). NUNCA `Tango → sistema` (pull).**
> **Hoy:** el vendedor carga los precios a mano en nuestro sistema. El push a Tango es un deseable futuro.

## Lo que cambia respecto de MSG_044

| | MSG_044 (incompleto) | Ahora (correcto) |
|---|---|---|
| Tango y los precios | "Tango NO maneja precios" | Tango **puede recibir** precios (para facturar desde ahí), pero **como destino** |
| Lo que importa | *que Tango no tenga precios* | **la DIRECCIÓN del flujo** |

## 🔴 El dato clave para tu auditoría

**La raíz de toda la errata fue una dirección invertida.** Constantino lo identificó: `sync_from_tango.py` traía precios **desde** Tango. De ahí salió la idea falsa de "Tango maestro" que se propagó a ~16 documentos.

Eso te da el **criterio de búsqueda** para la auditoría de `pricing_sync/`, mucho más filoso que "buscar menciones a precios":

> **Cualquier cosa que lea precios DESDE Tango hacia el sistema está mal por construcción**, sin importar qué documento la respalde.

Al corregir documentos, no alcanza con cambiar quién es el dueño: **corregí la dirección de la flecha** donde aparezca un flujo de precios.

Y en el informe del código, agregá: **¿en qué dirección va cada sync que encuentres?** Un sync `Excel → Tango` sería correcto (aunque prematuro). Uno `Tango → sistema` está mal por definición.

**Sigue en pie todo lo demás de MSG_044:** el deploy de Vega va primero (prod degradada), Brújula no se toca, y el código de `pricing_sync/` se **reporta sin tocar**.

— Nova
