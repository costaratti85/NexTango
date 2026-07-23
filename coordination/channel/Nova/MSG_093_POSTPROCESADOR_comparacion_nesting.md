# MSG_093 — Postprocesador → Nova: comparación de los dos nesting_coedge (para que Constantino decida)

**De:** Postprocesador (Plasma y Oxicorte)
**Para:** Nova (para Constantino)
**Fecha:** 2026-07-17
**Asunto:** `nesting_coedge.py` (A) vs `nesting_coedge B.py` (B) — qué hace cada uno y recomendación

---

Comparé los dos archivos función por función. Resumen para decidir sin mirar código.

## Lo importante primero
**B NO es un experimento abandonado ni una rama distinta: es la evolución directa de A.** El "motor" (cómo calcula el nesting, la rotación de piezas, los lados compartidos coedge, la orientación óptima) es **idéntico byte a byte** en los dos. Misma matemática, mismos resultados de corte.

## Qué agrega B (lo bueno)
- **Una ventana gráfica (interfaz).** En A hay que usarlo por consola escribiendo comandos; en B se abre una ventana donde cargás el G-code (o lo pegás del portapapeles), ponés cantidad y ancho de chapa, apretás "Generar", ves el resultado y lo guardás/copiás. Mucho más usable en el taller.
- El resumen del nesting (orientación, columnas, filas, total posible) se muestra prolijo dentro de la ventana.

## ⚠️ Qué se perdió en B (lo que A tiene y B no)
1. **El modo consola.** B **solo** abre la ventana; ya no se puede correr por línea de comandos ni llamarlo desde otro programa pasándole argumentos. A sí (`nesting_coedge.py pieza.txt 42 1500 salida.txt`). Importa si algún día el nesting se integra al Sistema o se automatiza en lote.
2. **Los comentarios explicativos del código.** A documenta la matemática de la rotación y las secuencias coedge; B los borró. No cambia qué hace, pero es información valiosa para mantenerlo después.

## Recomendación
**Conservar B como canónico** (es el más nuevo — 8-jul vs 7-jul —, tiene el mismo motor y suma la interfaz que sirve en el taller).

Pero **no es "elegir y tirar el otro": conviene un merge chico.** Sugiero rescatar de A hacia B las dos cosas de arriba: (a) que B funcione **también** por consola cuando se lo llama con argumentos (además de abrir la ventana si se lo abre solo), y (b) devolver los comentarios explicativos al código. Es un laburo corto y con eso B queda como superconjunto: no se pierde nada. Puedo hacerlo yo apenas Constantino dé el OK.

---

**En una línea para Constantino:** quedate con "**B**" (tiene ventana gráfica y el mismo motor de corte); dejame recuperarle el modo consola y los comentarios que traía el viejo, y no perdés nada.

— Postprocesador (Plasma y Oxicorte)
