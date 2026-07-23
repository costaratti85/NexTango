# MSG_145 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-17
**Asunto:** Adenda 3 (última) a MSG_142/143/144 — confirmación directa de la industria LÁSER

Terminaron de llegar los últimos hallazgos. Esta es la pieza más importante de toda la
investigación, la resumo corta porque ya mandé bastante detalle en los mensajes anteriores.

## El hallazgo más fuerte de toda la investigación
Encontré y leí completa una **patente real de Bystronic** (fabricante líder de máquinas de
corte láser — no un firmware de hobby como GRBL): *"Method... for Smart Corner Cutting"*
(US 11,980,966 B2, 2024). **Confirma, citándolo como práctica YA conocida en la industria
(no como su invención)**, que las máquinas láser comerciales reales **reducen la velocidad
en las esquinas en función de la curvatura/ángulo** — exactamente el mecanismo que venimos
proponiendo (Junction Deviation es la versión "poligonal" de esto; para curvas usan
directamente la fórmula de curvatura geométrica). Esto ya no es "una fórmula de firmwares
de impresoras 3D que esperamos que aplique" — es confirmación directa de que **la industria
del corte láser específicamente** ya asume esta física. Es la validación más fuerte que
tenemos de que el enfoque es el correcto para nuestro caso.

## Un dato de contraste, para tener como alternativa más simple si hiciera falta
El mismo paper de corte láser que dio el 13% de discrepancia (Hwang & Yang, IEOM 2023) —
en realidad usa un modelo MÁS SIMPLE que el que proponemos: trata **cada esquina como una
parada completa** (no gradual según el ángulo), y corrige el error resultante con Machine
Learning entrenado sobre 338 piezas reales, llegando a ~92-94% de precisión así. **Lo anoto
como una alternativa de respaldo**: si Junction Deviation resulta difícil de calibrar bien,
"parada completa + corrección estadística" es un camino más simple que la propia industria
usa en al menos un caso documentado — aunque es menos "físico" y no explicaría el mecanismo,
solo lo compensaría con datos.

## Sobre S-curve — confirma que no hace falta, cierra el tema
Los perfiles de 7 fases están bien documentados en la literatura general, pero el libro
específico de Biagiotti/Melchiorri no se pudo leer completo (pagado/bloqueado) — lo que sí
se confirmó con dos fuentes independientes es el criterio de cuándo el perfil colapsa (no
llega a velocidad de crucero, o ni siquiera a la aceleración máxima). Dado que ya sabemos
que GRBL (nuestra referencia) NO usa esto, este tema queda cerrado sin necesidad de más
profundidad — no lo vamos a implementar de entrada.

## Con esto, la investigación está completa
Los 3 temas pedidos, cada uno con nivel de confianza explícito. No cambia el plan de
MSG_142/144: empezar con Junction Deviation (validado ahora por la propia industria láser)
+ aceleración constante, calibrar contra Batería 2 + al menos 1 figura orgánica, y esperar
un resultado bueno en el orden de 10-15% de error (no <5%, según el benchmark real de láser).

Sigo sin ejecutar nada. Quedo esperando el visto bueno para arrancar la Etapa 1.

— Punto
