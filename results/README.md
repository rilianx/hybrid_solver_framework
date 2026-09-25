# Resultados

Corridas de tuning sobre el CLSP (Trigeiro), usado como banco de pruebas del
framework. La pregunta no es qué esqueleto conviene para el CLSP, sino qué dicen las
corridas sobre las piezas del framework: el validador, el filtro de diversidad, la
generación con LLM y la interfaz de los slots.

El "gap" es el gap relativo por instancia contra la mejor solución conocida, promediado
sobre las instancias de test (cada una pesa lo mismo). En todas las corridas con
`--ref-time`, esa mejor solución fue la del MIP completo.

## Corridas

| Carpeta | Fecha | Catálogo generado | Esqueletos | Instancias | Presupuesto | Trials | Qué responde |
|---|---|---|---|---|---|---|---|
| `tuning_run1.md` (+ `all.json`, `handwritten.json`, `comparison.json`) | ≤ 4 sep | corrida 7 | los 8 | 3+3, 10×15 | 5 s | 30 | corrida local de prueba |
| [`tune_run1/`](tune_run1/) | 4 sep | corrida 7 | los 8 | 5+5, 10×15 | 5 s | 60 | ¿el catálogo ampliado ayuda o diluye? |
| [`tune_run2/`](tune_run2/) | 23 sep | corrida 8 (con referencias) | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | componente generado vs de mano, mismo esqueleto |
| [`tune_run4/`](tune_run4/) | 23 sep | corrida 8 (con referencias) | SA, ILS, VNS | 5+5, 20×20 | 20 s | 30 | lo mismo con más presupuesto |
| [`tune_run5/`](tune_run5/) | 23 sep | **corrida 9 (desde cero)** | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | ¿el LLM llega solo a algo tan bueno como lo de mano? |
| [`tune_run6/`](tune_run6/) | 24 sep | **corrida 10 (desde cero, con `greedy_score`)** | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | ¿se repite? ¿constructor monolítico o modular? |
| [`tune_run7/`](tune_run7/) | 24 sep | corrida 11 (desde cero, **sin** planificador) | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | calidad sin planificador (solo generados) |
| [`tune_run8/`](tune_run8/) | 24 sep | corrida 12 (desde cero, **con** planificador) | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | calidad con planificador (solo generados) |
| [`tune_run9/`](tune_run9/)–[`tune_run14/`](tune_run14/) | 24 sep | corridas 11–16 (desde cero; 3 sin y 3 con planificador) | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | réplicas de la comparación del planificador, con muestreo de vecindarios |

Cada carpeta trae su `README.md` con las tablas completas, los JSON con cada trial y el
costo por instancia, y el `tune.log`. La run 3 de Actions se canceló (no cabía en el
límite de tiempo) y quedó relanzada como la 4. Runs 9–14, en orden: corridas 11, 12, 13, 14,
15 y 16 (`generated/clsp_scratch3`, `…3_planner`, `…4`, `…4_planner`, `…5`, `…5_planner`).

## Lo que dicen del framework

### Generación: sin ver los componentes de mano, el LLM los iguala y los supera

| Catálogo afinado (run 5) | Gap | Configuración elegida |
|---|---|---|
| solo a mano | 11,1 % | `lot_for_lot` + `setup_flip` |
| **solo generados desde cero** | **8,4 %** | `prefix_capacity_earliest_feasible` + `backward_merge_setup` |
| ambos | 8,6 % | la misma de arriba, toda generada |

- Lo generado desde cero gana en las 5 instancias de test (entre 1,0 y 4,3 puntos).
- Con ambos catálogos disponibles, el tuner eligió solo componentes generados.
- `backward_merge_setup` reinventa `setup_flip`: 77 de sus 83 movimientos que mejoran
  desde la partida coinciden con los de `setup_flip` (que tiene 95). En el mismo
  esqueleto rinde mejor: 8,5 % contra 11,2 %, y gana en las 5 instancias.

### Replicación (run 6, otra generación desde cero): lo generado sigue a la par o por encima

| Catálogo afinado (run 6) | Gap | Configuración elegida |
|---|---|---|
| solo a mano | 8,1 % | `greedy_unit_marginal_cost` (de mano) + `setup_flip` en SA |
| solo generados desde cero | 7,5 % | ILS con `greedy_setup_consolidation_balance` + `merge_with_previous_setup` + `item_break_repair` |
| ambos | **6,9 %** | `greedy_unit_marginal_cost` (de mano) + `merge_with_previous_setup` (generado) en SA |

El catálogo de mano es ahora más fuerte (8,1 % contra 11,1 % en la run 5) porque incluye
el constructor greedy con costo marginal. Aun así, solo generados queda 0,5 puntos por
debajo en gap y gana en 3 de 5 instancias; la mezcla, que combina un puntaje de mano con un
vecindario generado, es la mejor. La ventaja es menor y menos consistente que en la run 5.

`merge_with_previous_setup` es inerte en SA partiendo de lot-for-lot (51,9 %) y es parte de
la mejor configuración partiendo del constructor greedy: la utilidad de un componente
depende de con qué se combina, otra razón para validar por combinación y no aislado.

### Constructor modular: los puntajes le ganan a los constructores monolíticos

En la run 6, con SA y `setup_flip` fijos, cambiando solo el constructor:

| Constructor | Tipo | Gap |
|---|---|---|
| `greedy_unit_marginal_cost` | puntaje de mano | 6,5 % |
| `greedy_amortized_unit_cost` | puntaje generado | 7,1 % |
| `greedy_setup_consolidation_balance` | puntaje generado | 7,5 % |
| `greedy_deadline_pressure` | puntaje generado | 9,6 % |
| `saturation_balancer_constructor` | monolítico generado | 11,3 % |
| `lot_for_lot` | de mano | 11,3 % |
| `backward_inventory_constructor` | monolítico generado | 14,6 % |
| `forward_urgency_constructor` | monolítico generado | 15,9 % |

Los tres puntajes generados superan a los tres constructores monolíticos generados, y el
mejor queda a 0,5 puntos del puntaje de mano. Ningún monolítico generado mejora a
lot-for-lot. El tuner eligió un constructor greedy en los tres catálogos. Costo de
generación en la corrida 10: los monolíticos salieron a la primera (10,6 mil tokens) y los
puntajes costaron 19,9 mil, pero sus 5 rechazos fueron un bug de interfaz ya corregido
(importaban `CoverAction` desde `problem_model`, donde no estaba); sin él habrían pasado a
la primera.

### Planificador: más rápido y más caro en tokens; la ventaja en calidad no se replica

Tres generaciones desde cero por brazo, con los mismos cinco slots, y un tuning de solo
generados para cada una (runs 9–14, mismas instancias de test). Gap contra una referencia
común: el mejor costo por instancia entre el MIP de 60 s y todas las corridas de las 6 runs.

| | Sin planificador (11, 13, 15) | Con planificador (12, 14, 16) |
|---|---|---|
| Tiempo de pared de la generación | 202 · 253 · 170 s | **45 · 94 · 195 s** |
| Tokens | **68 · 61 · 53 mil** | 118 · 160 · 193 mil |
| Componentes aceptados (de 15) | 14 · 13 · 13 | 12 · 15 · 14 |
| Gap del afinado | 9,2 · 6,4 · 4,4 % (**media 6,7 %**) | 7,6 · 6,5 · 10,7 % (media 8,3 %) |
| Mejor configuración por defecto | 9,2 · 6,3 · 9,0 % (media 8,2 %) | 6,9 · 7,4 · 4,3 % (**media 6,2 %**) |

Por pares, el planificador gana en 4/5, 1/5 y 0/5 instancias en el afinado, y en 4/5, 1/5 y
5/5 en la mejor configuración por defecto. Según qué se mire gana uno u otro brazo, siempre
por menos que la variación entre réplicas del mismo brazo (4,4–9,2 % sin planificador). La
ventaja de las runs 7 y 8 (7,8 % contra 11,9 %) era una sola réplica. Lo que sí se sostiene
es el costo: el planificador tarda menos en 2 de 3 corridas y gasta entre 2 y 3 veces más
tokens. Con este banco de pruebas, el planificador se justifica por tiempo de pared, no por
calidad.

La variación del propio tuner es del mismo orden: en la run 13 el afinado queda 4,6 puntos
por debajo de su mejor default y en la run 14, 6,4 puntos por encima. Con 40 trials y 5
instancias de entrenamiento, comparar catálogos por el afinado de una sola corrida es ruidoso.

### Filtro de diversidad: exigirlo contra el catálogo dejaba fuera lo mejor

Con referencias (corrida 8), el filtro exigía que cada componente fuera distinto de los
de mano (Jaccard ≤ 0,8 y ≥ 25 % de mejoras nuevas). `backward_merge_setup` solo tiene
un 7 % de mejoras nuevas respecto de `setup_flip`, así que ese filtro lo habría
rechazado. Las runs 2 y 4 ("lo de mano gana en todos los slots": `setup_flip` 11,2 % vs
`merge_consecutive_setups` 17,5 % en la run 2) medían ese filtro, no la capacidad del
LLM.

**Implementado** (`--catalog-diversity annotate`, por defecto): la diversidad se exige entre
los componentes de una misma corrida y el parecido con el catálogo se anota sin rechazar.

### Validador: aprueba componentes que no sirven en todos sus esqueletos

`drop_single_setup` y `left_shift_setup_chain` declaran compatibilidad con SA, ILS y
VNS. En ILS funcionan (41–42 % de gap en la run 2, cerca del 39 % de `setup_flip`), pero en SA quedan en +0,0 %
frente a lot-for-lot, en las runs 2 y 4. El filtro de calidad mira el componente
aislado, no dentro de cada esqueleto que declara.

**Implementado** (`core/validation/combination.py`): aporte de cada vecindario sobre un
vecindario nulo, en cada esqueleto donde es el único motor, desde lot-for-lot y desde el
greedy. Sobre los catálogos de las corridas 8 y 10 quita VNS a `drop_single_setup`,
`left_shift_setup_chain` y `shift_setup_to_adjacent_period` (en la run 2, esos vecindarios en
VNS quedaron por debajo del VNS por defecto) y conserva SA, donde sí aportan partiendo del
greedy. `merge_with_previous_setup` es inerte con sus parámetros por defecto y útil con otros,
por eso el chequeo prueba configuraciones al azar antes de rechazar.

**ILS y perturbaciones, ahora también.** En ILS la resta contra el nulo mezclaba velocidad con
aporte (`setup_flip` salía en −7 %), así que el vecindario se mide por lo que hace ahí: cuánto
mejora su búsqueda local la partida y perturbaciones factibles de ella (`setup_flip` +8 % desde
lot-for-lot, +3 % desde el greedy). Para las perturbaciones se probó medir la mejora de un ILS
de 1, 3 y 10 s desde un óptimo local: todas salían en ~0, incluida `item_break_repair`, que el
tuner eligió en la run 6; con un `delta` que cuesta un LP (~15 ms), la búsqueda local interna
no alcanza a recuperarse de una patada. El criterio quedó en capacidad: fracción de patadas
que, tras la búsqueda local, terminan en otra solución factible (menos la de patadas nulas).
Todas las perturbaciones reales pasan (25–100 %); rechaza las que la búsqueda local deshace o
que dejan soluciones infactibles. Se encontró además que el ILS no aplicaba la búsqueda local
a la solución inicial (desde el greedy, cualquier perturbación salía peor que el nulo): corregido.

**Error del espacio de configuración (corregido).** La poda por esqueleto funcionaba, pero el
espacio tenía un solo parámetro `neighborhood` para SA, ILS y VNS, así que el tuner podía
combinar VNS con un vecindario al que se le había quitado VNS: en las runs 9–14 se perdieron
entre 0 y 5 de los 40 trials por eso. Ahora, si los esqueletos que usan un slot no admiten
los mismos componentes, el slot se parte en un parámetro por grupo de esqueletos
(`neighborhood__SA_ILS`, …) que se pliega a `neighborhood` al armar la configuración.

### Validador: la admisión al catálogo no revisaba factibilidad en tamaño realista (corregido)

En la run 5 entró al catálogo `batch_covering_merge`, un constructor que la generación
había abandonado tras 5 rondas y que es infactible en 10×15. El tuner perdió 12 de sus
40 trials en él (aparecen con gap del orden de 10⁹ %, la penalización). La causa era que
la admisión leniente no construía la sonda 10×15. Ya está corregido: el modo leniente
relaja solo la exigencia de mejorar desde la partida.

### Interfaz de los slots: evaluar el vecindario completo no escalaba (corregido)

ILS y VNS quedaban en ~40 % de gap en la run 2 y en ~42 % en la run 4, con 4 veces más
tiempo. Su búsqueda local recorría el vecindario completo en el orden de `moves`, cortado por
tiempo, así que con un `delta` caro (un LP en el CLSP) evaluaba siempre los mismos primeros
movimientos. Ahora los esqueletos piden movimientos al azar o muestras (`core/neighborhood.py`;
un vecindario puede implementar `sample(sol, k, rng)`) y la búsqueda local de ILS, VNS y
GRASP evalúa muestras de `ls_sample` movimientos (parámetro del tuner, default 32).

| `setup_flip`, 10×15, 5 s, desde lot-for-lot | Recorrido completo | Muestra de 32 |
|---|---|---|
| ILS | 39,0 % | 21,3 % |
| VNS | 39,2 % | 18,1 % |
| GRASP | 43,6 % | 29,4 % |

Desde el greedy no cambia (6,9–9,3 %). En las runs 9–14 el mejor ILS queda en 7,6–12,3 % y el
mejor VNS en 7,7–12,1 %, contra ~40 % antes; SA sigue siendo el mejor esqueleto en las seis,
y lo elige el tuner en cinco. Las runs 9 y 10 reafinan los catálogos de las runs 7 y 8 con
este código: 11,9 → 9,2 % y 7,8 → 7,6 %.

### Generación: el constructor monolítico es caro e irregular

En la corrida 9 el constructor se llevó 65 mil de 99 mil tokens, con 11 rechazos y 1 de 3
aceptado, casi todos por factibilidad; en la corrida 10 salió a la primera. Con el
constructor modular (`core/construction.py`) la factibilidad queda en la vista del problema
y el LLM escribe solo un puntaje; en 360 construcciones de prueba ninguna fue infactible y en
la run 6 los puntajes generados superaron a los constructores monolíticos generados.
