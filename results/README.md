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
| runs 15–22 (solo en el log de Actions) | 25 sep | corridas 15 y 16 | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 | ruido del tuning: 2 semillas del tuner × con/sin re-evaluación final |
| [`tune_run23/`](tune_run23/) | 25 sep | corrida 16 | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 × 3 réplicas | réplicas en paralelo; gemelo con numéricos por defecto |
| [`tune_run24/`](tune_run24/) | 25 sep | corrida 16 | SA, ILS, VNS | 10+10, 10×15 | 5 s | 40 × 3 réplicas | ¿más instancias bajan el ruido? |
| [`tune_run25/`](tune_run25/) | 25 sep | corrida 16 | SA, ILS, VNS | 5+5, 10×15 | 5 s | 40 × 3 réplicas | sondeo inicial de un solo componente |
| [`tune_run26/`](tune_run26/) | 26 sep | corrida 16 | SA, ILS, VNS | 10+10, 10×15 | 5 s | 40 × 3 réplicas | sondeo + re-evaluación por elección distinta |
| [`tune_run27/`](tune_run27/) | 26 sep | corrida 16 | SA, ILS, VNS | 10+10, 10×15 | 5 s | 40 × 3 réplicas | réplicas nuevas con `prefer_defaults` |
| [`tune_run28/`](tune_run28/) | 26 sep | ciclo CVRP rutas (modelo 34, componentes 37) | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | ciclo completo, representación de rutas |
| [`tune_run29/`](tune_run29/) | 26 sep | ciclo CVRP gran tour (modelo 33, componentes 38) | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | ciclo completo, gran tour + Split |
| [`tune_run30/`](tune_run30/) | 26 sep | CVRP escrito a mano | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | referencia para el ciclo completo |
| [`tune_run31/`](tune_run31/) | 26 sep | ciclo CVRP rutas, 2.ª generación (componentes 39) | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | variación entre generaciones |
| [`tune_run32/`](tune_run32/) | 26 sep | ciclo CVRP gran tour, 2.ª generación (componentes 40) | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | variación entre generaciones |
| [`tune_run33/`](tune_run33/) | 27 sep | ciclo CVRP rutas, 2.ª generación optimizada (corrida 41) | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | efecto de la optimización al volver a afinar |
| [`tune_run35/`](tune_run35/) | 27 sep | ciclo CVRP gran tour, 2.ª generación optimizada (modelo de la corrida 47, componentes de la 42) | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | efecto de la optimización, memoria acotada |
| [`tune_run36/`](tune_run36/) | 27 sep | lo mismo que la run 35 | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | selección final en carrera |

Cada carpeta trae su `README.md` con las tablas completas, los JSON con cada trial y el
costo por instancia, y el `tune.log`. La run 3 de Actions se canceló (no cabía en el
límite de tiempo) y quedó relanzada como la 4. La run 34 (gran tour optimizado, corrida 42) no
dejó resultados: el modelo tenía una caché sin límite y los tres runners se quedaron sin memoria. Runs 9–14, en orden: corridas 11, 12, 13, 14,
15 y 16 (`generated/clsp_scratch3`, `…3_planner`, `…4`, `…4_planner`, `…5`, `…5_planner`).
Las runs 15–22 terminaron el tuning pero no pudieron crear su rama (`GITHUB_TOKEN` no puede
empujar una rama cuya historia cambia `.github/workflows`); las cifras de abajo salen del log
de cada job. El workflow ahora arma la rama de resultados sobre `main`.

## Lo que dicen del framework

### Tuning: el ruido entre semillas del tuner es de 3 a 4.5 puntos, y la re-evaluación no lo quita

Runs 15–22: los catálogos de las corridas 15 (`clsp_scratch5`) y 16 (`…5_planner`), mismas
instancias, semilla del tuner 0 o 1, selección final por el mínimo de una semilla
(`reeval_top=0`) o re-evaluando los 5 mejores trials y el mejor default con 2 semillas más
(`reeval_top=5`). Gap en test; la última columna compara el afinado con la mejor
configuración no afinada (default o default con un componente cambiado), IC95 por bootstrap.

| Run | Catálogo | Re-eval. | Semilla | Elegido | Gap afinado | Mejor default | Afinado vs mejor no afinado |
|---|---|---|---|---|---|---|---|
| 15 | corrida 15 | no | 0 | SA | 5,56 % | 9,90 % | +3,31 [+1,11, +5,57] |
| 16 | corrida 15 | no | 1 | SA | 8,82 % | 9,92 % | −0,20 [−2,29, +1,56] |
| 17 | corrida 15 | 5 | 0 | SA | **4,38 %** | 9,90 % | +4,49 [+2,72, +6,01] |
| 18 | corrida 15 | 5 | 1 | VNS | 8,31 % | 10,05 % | +0,75 [−0,78, +2,29] |
| 19 | corrida 16 | no | 0 | SA | 4,92 % | 10,83 % | −0,61 [−1,50, +0,15] |
| 20 | corrida 16 | no | 1 | SA | 9,42 % | 10,90 % | −5,17 [−6,87, −3,40] |
| 21 | corrida 16 | 5 | 0 | ILS | 9,45 % | 10,38 % | −5,20 [−6,69, −3,70] |
| 22 | corrida 16 | 5 | 1 | SA | 6,55 % | 10,90 % | −2,30 [−3,04, −1,16] |

- **La semilla del tuner pesa más que todo lo demás**: con el mismo catálogo y el mismo
  modo, las dos semillas difieren en 3,3, 3,9, 4,5 y 2,9 puntos. Con 5 instancias de train y
  40 trials, comparar dos catálogos con una sola corrida de tuning (como en las runs 9–14) no
  distingue diferencias menores a ~4 puntos.
- **La re-evaluación final ayuda poco y no siempre**: mejora en 3 de 4 pares (5,56 → 4,38;
  8,82 → 8,31; 9,42 → 6,55) y empeora en uno (4,92 → 9,45, run 21: los 5 mejores trials de esa
  búsqueda eran ILS, y re-evaluar solo elige entre lo que la búsqueda encontró).
- **Afinar los numéricos empeora una buena elección de componentes.** En el catálogo 16,
  `SA[greedy_forward_cover_cost, remove_redundant_setup]` con TODOS los parámetros por defecto
  queda en 4,25 %, mejor que cualquiera de las cuatro corridas de tuning. Las runs 19 y 22
  eligieron esos mismos componentes, pero con los numéricos afinados en 5 instancias quedaron
  en 4,92 y 6,55 %. Siempre le gana al default del esqueleto (el afinado queda 0,9–5,9 puntos
  por debajo de `default:SA`), pero no a "los componentes elegidos, sin afinar".

Cambio en el framework: la selección final re-evalúa además, por cada elección de componentes
entre los k mejores, su **gemelo con numéricos por defecto** (`defaults_twin` en
`tuning/optuna_tuner.py`); si gana en train, se elige ese. En la run 22 ese gemelo es la
configuración de 4,25 %. Queda abierto el problema de fondo: con 5 instancias de train el
tuner sobreajusta los parámetros continuos; más instancias, o racing (irace), lo atacan mejor
que más trials. La referencia del MIP (CBC, 60 s) también varía entre runs (2.ª instancia:
69 668–70 193), lo que mueve el gap medio ~0,15 puntos.

**Run 23** (catálogo 16, 5+5, re-evaluación de 5, 3 réplicas en paralelo, `results/tune_run23/`):
gap del afinado 10,35 / 11,30 / **4,34 %** (media 8,66 %, desvío 3,1). En la réplica 2 el elegido
fue el gemelo con numéricos por defecto, que es exactamente la mejor configuración no afinada
(4,34 %): el mecanismo funciona cuando la búsqueda llegó a esos componentes. En las réplicas 0 y
1 los 5 mejores trials usaban otros constructores (`clustered_item_windowing`,
`greedy_capacity_pressure_balance`, `critical_period_seeding`): TPE se quedó en ellos desde los
primeros trials y nunca evaluó bien `greedy_forward_cover_cost`. El problema no es solo la
selección final sino la exploración de los componentes. Cambio: **sondeo inicial** (`--screen`,
por defecto un tercio de los trials): después de los defaults se encolan variantes de un solo
componente, intercaladas entre esqueletos y slots, las mismas que se usan como referencia en test.

**Runs 24 y 25** (mismo catálogo, 3 réplicas cada una):

| Run | Instancias | Sondeo | Gap por réplica | Media | Desvío | Mejor no afinado |
|---|---|---|---|---|---|---|
| 23 | 5+5 | no | 10,35 / 11,30 / 4,34 % | 8,66 % | 3,08 | 4,34 % |
| 25 | 5+5 | sí (13) | 11,10 / 5,68 / 6,85 % | 7,88 % | 2,33 | 4,31 % |
| 24 | 10+10 | no | 8,62 / 4,82 / 5,33 % | 6,26 % | 1,68 | 4,82 % |
| 26 | 10+10 | sí (13) + re-evaluación por elección | **4,84 / 6,10 / 4,84 %** | **5,26 %** | **0,59** | 4,84 % |
| 27 | 10+10 | ídem + `prefer_defaults`, semillas 3–5 | **4,82 / 4,85 / 4,84 %** | **4,84 %** | **0,01** | 4,84 % |

- **Duplicar las instancias corta el desvío a la mitad** (3,1 → 1,7) y baja la media 2,4 puntos:
  en 2 de 3 réplicas el tuner eligió los componentes buenos.
- **El sondeo ayuda poco**: el constructor bueno entró en los trials de las 3 réplicas, pero en la
  réplica 0 su variante por defecto costó en train 0,759, y la misma configuración, en las mismas
  instancias, costó 0,669 y 0,671 en las otras dos réplicas. Solo cambia la semilla de
  evaluación. **El ruido de evaluar un trial con una semilla es mayor que la diferencia entre
  constructores**, y con eso la elección buena queda 5.ª o 6.ª en train.
- Cambio: la selección final re-evalúa el mejor trial de cada una de las k mejores **elecciones de
  componentes distintas** (antes, los k mejores trials, que suelen ser la misma elección con otros
  numéricos). Con k = 5, la elección buena habría entrado en 7 de las 9 réplicas de las runs
  23–25 (antes, en 5).

**Run 26** (10+10, sondeo y re-evaluación por elección distinta): las 3 réplicas eligen los mismos
componentes, `SA[greedy_forward_cover_cost, remove_redundant_setup]`, y el desvío baja a 0,6
(3,1 en la run 23). En dos réplicas el elegido es la variante del sondeo con los numéricos por
defecto, que es exactamente la mejor configuración no afinada (4,84 %). En la tercera, los
numéricos afinados le ganaron a su gemelo en train por 0,0008 (0,6845 contra 0,6853) y en test
quedaron 1,3 puntos peor. Lo que queda abierto: en ninguna de las 12 réplicas de las runs 23–26 los
numéricos afinados le ganaron en test a los defaults de los mismos componentes. Con este
presupuesto el tuning sirve para **elegir componentes**, no para afinar parámetros continuos; una
regla que prefiera los defaults cuando la diferencia en train está dentro del ruido de la
re-evaluación cerraría ese último punto. Implementada (`prefer_defaults`, `--defaults-margin`):
si el ganador de la re-evaluación es un trial afinado, se elige su gemelo con numéricos por
defecto salvo que el afinado gane por más de 0,5 % y de dos errores estándar de la diferencia
pareada por semilla. En la réplica 1 de la run 26 (0,1 % de diferencia) habría elegido el gemelo.

**Run 27** (lo mismo con 3 réplicas nuevas, semillas del tuner 3–5): 4,82 / 4,85 / 4,84 %, desvío
0,01. Las tres eligen los componentes buenos con los numéricos por defecto: dos por la variante
del sondeo, una por el gemelo, que ganó la re-evaluación sin necesitar la regla. Entre las runs
23 y 27, con el mismo catálogo y las mismas instancias, el desvío entre réplicas pasó de 3,1 a
0,01 puntos, y el afinado pasó de quedar 4,3 puntos por debajo de la mejor configuración no
afinada a igualarla. Lo que lo resolvió, en orden de efecto: más instancias de train (10 en vez
de 5), re-evaluar elecciones de componentes distintas en vez de los mejores trials, y el sondeo
de variantes de un solo componente al inicio.

### Ciclo completo: modelo generado → componentes → tuning (CVRP, rutas contra gran tour)

Primera corrida de punta a punta sin nada escrito a mano salvo el generador de instancias y
los casos: el LLM genera el modelo por piezas con la representación pedida (incluida la vista
constructiva), después genera desde cero puntajes, vecindarios, perturbaciones y destrucciones
viendo solo el código de ese modelo, y el tuner afina (30 clientes, 10+10 instancias, SA/ILS/
VNS/LNS_MIP, 3 réplicas, sondeo y re-evaluación por elección distinta).

| Etapa | Rutas | Gran tour |
|---|---|---|
| Modelo (corridas 34 / 33) | heurística 1, MIP 3, constructiva 1 ronda; 23 mil tokens | heurística 1, MIP 5, constructiva 1; 43 mil |
| Componentes (37 / 38) | 10/12: 3 puntajes, 1 vecindario, 3 perturbaciones, 3 destrucciones; 44 mil | 8/12: 2 puntajes, 3 vecindarios, 1 perturbación, 2 destrucciones; 58 mil |
| Tuning (runs 28 / 29) | 6,21 / 5,59 / 6,26 % (desvío 0,3) | 6,02 / 5,35 / 3,20 % (desvío 1,2) |
| Elegido | las 3 réplicas: ILS con `swap_customers_across_routes` | SA o VNS con `two_opt_reversal_neighborhood` |
| Afinado vs mejor no afinado | −0,54 [−2,29, +1,29] (ruido) | +2,03 [+1,03, +2,93] |

Comparación entre variantes (`scripts/compare_packs.py`, mejor conocido común a las 6 réplicas):
gran tour queda **3,0 puntos de gap por debajo** de rutas, IC95 [1,4, 4,6] sobre las 10
instancias de test. Los costos se comparan directamente porque los dos modelos generados pasan
los mismos casos de prueba.

Cómo leerlo: la diferencia es entre dos solvers generados enteros, no solo entre dos
representaciones. El catálogo de rutas tiene un único vecindario (un intercambio entre rutas; los
otros dos se abandonaron por `undo` mal implementados), y el de gran tour tiene 2-opt, que es el
que eligen las tres réplicas. En la representación de gran tour los movimientos son de
permutación, más fáciles de escribir bien, y eso también es un efecto de la representación. Para
separarlos harían falta más corridas de componentes por variante. Pendiente: el mismo tuning con
los componentes escritos a mano del CVRP como referencia.

Arreglos del framework que salieron de esta corrida: el prompt de la vista MIP muestra la
representación y la regla de ida y vuelta de los decodificadores; el mensaje de cobertura de
variables nombra lo que sobra en `to_assignment` o `aux_values`; la firma de diversidad de los
puntajes compara transiciones (con acciones "próximo cliente", el conjunto de acciones elegidas
era siempre el mismo y tres ideas distintas daban similitud 1,00); y las ramas de los modelos
rechazados se guardan.

**Segunda generación de componentes y referencia escrita a mano** (runs 30–32; mismos modelos,
otro catálogo generado por variante: corridas 39 y 40; referencia: el catálogo escrito a mano del
CVRP con su modelo, mismas instancias y presupuesto). Gaps contra el mejor conocido común de cada
par; diferencias pareadas por instancia con IC95:

| Comparación | Resultado |
|---|---|
| Gran tour − rutas, 1.ª generación (29 − 28) | −3,0 puntos [−4,6, −1,4] |
| Gran tour − rutas, 2.ª generación (32 − 31) | −1,3 [−2,2, −0,4] |
| Rutas, 2.ª − 1.ª generación (31 − 28) | −3,9 [−5,4, −2,4] |
| Gran tour, 2.ª − 1.ª generación (32 − 29) | −2,2 [−3,1, −1,2] |
| Ciclo − escrito a mano: rutas 1.ª / 2.ª | +8,6 [+7,0, +10,0] / +4,6 [+4,0, +5,2] |
| Ciclo − escrito a mano: gran tour 1.ª / 2.ª | +5,5 [+5,0, +5,9] / +3,3 [+2,6, +4,0] |

Por réplica, en su propia corrida: escrito a mano 1,24 / 0,46 / 2,22 % (VNS o ILS con `relocate`);
rutas 2.ª generación 3,46 / 3,60 / 3,02 % (ILS con 2-opt* entre rutas, que la 1.ª generación no
tenía); gran tour 2.ª generación 2,67 / 3,44 / 4,08 % (SA con 2-opt sobre el tour).

- **Gran tour queda por delante con los dos catálogos**, pero la ventaja baja de 3,0 a 1,3 puntos
  cuando rutas consigue un segundo vecindario. La representación importa, menos de lo que parecía.
- **Qué catálogo salió pesa más que la representación**: con el mismo modelo, otra generación de
  componentes mejora 2,2 a 3,9 puntos. Para comparar representaciones hacen falta varias
  generaciones por variante, igual que hicieron falta varias réplicas del tuning.
- **El ciclo completo queda 3,3 a 8,6 puntos por detrás de los componentes escritos a mano**
  (1,3 % de gap medio). La brecha se cierra entre generaciones (de 5,5–8,6 a 3,3–4,6), pero sigue
  siendo grande: los componentes escritos a mano mueven clientes con `delta` en O(1) y el
  constructor de inserción más barata es fuerte; los generados evalúan con el objetivo completo
  (en gran tour, un Split por movimiento), y con 5 s por corrida hacen muchos menos movimientos.
  Pendiente: medir movimientos por segundo, y pedir en el prompt de vecindarios un `delta`
  incremental cuando la representación lo permite.

**Etapa de optimización** (corridas 41 y 42 sobre los catálogos de la 2.ª generación; `llm.cycle
optimize`). Se midió la velocidad (`scripts/throughput.py`): el modelo de rutas generado evaluaba
4,9 mil soluciones/s y el de gran tour 219 (la referencia en la misma representación: 75 mil y 11
mil), y todos los vecindarios recalculaban el objetivo completo en cada `delta`. La etapa pide
versiones más rápidas y las acepta solo si dan las mismas salidas que las aceptadas (pruebas
diferenciales) y son al menos 1,5 veces más rápidas. Resultado: modelo de rutas 4,9 → 51 mil
evaluaciones/s, modelo de gran tour 219 → 4,5 mil; los tres vecindarios de gran tour 4–5 mil → 24–26
mil `delta`/s; los de rutas no ganaron 1,5× sobre el modelo ya rápido; de los puntajes, 1 de 6.

Efecto en la calidad, sin volver a afinar (`scripts/reevaluate_configs.py`: la configuración que
eligió cada réplica de las runs 31 y 32, mismas instancias de test, semillas y 5 s, catálogo antes y
después de optimizar, las dos en la misma máquina y de a una a la vez; gap contra el mejor conocido
guardado de cada run):

| Variante | Antes de optimizar | Optimizado | Mejora |
|---|---|---|---|
| Rutas (run 31) | 2,04 % | 1,19 % | +0,85 puntos |
| Gran tour (run 32) | 3,25 % | 0,01 % | +3,24 puntos |

- **La velocidad pesaba**: con el mismo algoritmo y las mismas decisiones del tuner, solo más
  rápido, gran tour gana 3,2 puntos y rutas 0,85. Gana más donde el modelo era más lento (el Split
  por evaluación del gran tour).
- La medición de "antes" en esta máquina da peor que en Actions (los 5 s rinden distinto), por eso
  se compara antes y después en la misma máquina y sin otras corridas en paralelo. Con otra corrida
  en paralelo, el "antes" del gran tour empeoraba 0,1 puntos más.
- Pendiente: afinar de nuevo sobre los catálogos optimizados (el tuner podría elegir otra cosa con
  más movimientos por segundo) y compararlos con la referencia escrita a mano con el mismo mejor
  conocido.
- **Rutas, afinando de nuevo** (run 33 contra 31, mismo mejor conocido): 4,96 → 5,03 % de gap,
  diferencia +0,07 [−0,88, +0,92], **ruido**. La réplica que eligió lo mismo que la run 31 (ILS con
  2-opt* entre rutas y el kick de inversión) mejora ~2 puntos (2,76 % contra 4,6–5,2 %), pero las
  otras dos eligieron VNS y quedaron peor (6,4 y 6,0 %). Lo que gana el catálogo más rápido lo
  pierde el tuner eligiendo: con 40 trials, la selección sigue siendo la mayor fuente de ruido.
  Contra el escrito a mano (run 30): +4,65 [+3,80, +5,55].
- **Gran tour: la caché que agotó la memoria.** La run 34 murió en los tres runners (58 min a
  2 h 12). El modelo optimizado en la corrida 42 memoizaba el Split con `lru_cache(maxsize=None)`
  a nivel de módulo, con el tour como clave: en 5 s no se nota, en horas de tuning cada tour
  distinto queda en memoria. Las pruebas de equivalencia y velocidad miraban salidas y tiempo, no
  memoria. Arreglo: `core/validation/resources.py` mide con `tracemalloc` la memoria retenida al
  evaluar 10 mil soluciones nuevas después de llenar las cachés acotadas (modelo: ≤ 1 MB; un
  componente, reconstruido en cada tanda, ≤ 1,5 MB), y los prompts piden `maxsize ≤ 8192`. Con la
  regla, el modelo de la corrida 42 retiene 11,5 MB y se rechaza; el de referencia escrito a mano
  (`maxsize=8192`), 0,3 MB. El modelo de rutas de la corrida 41 (`maxsize=200000`) también la
  violaría, aunque en la práctica cupo en la run 33. Se rehízo la optimización del gran tour
  (corrida 47): 222 → 1,6 mil evaluaciones/s con cachés acotadas (la versión que perdía memoria
  hacía 4,5 mil).
- **Gran tour, afinando de nuevo** (run 35, memoria acotada): las tres réplicas terminaron (la run
  34 no) y eligen 2-opt sobre el tour con SA o VNS.

| Comparación (mismo mejor conocido por par) | Gap afinado | Diferencia por instancia |
|---|---|---|
| Gran tour optimizado (35) contra sin optimizar (32) | 4,26 → 1,88 % | −2,38 [−3,19, −1,68] |
| Gran tour optimizado (35) contra escrito a mano (30) | 2,18 contra 1,30 % | +0,87 [+0,37, +1,31] |
| Rutas optimizado (33) contra gran tour optimizado (35) | 5,62 contra 1,85 % | +3,77 [+2,73, +4,92] |

  - **La brecha con lo escrito a mano baja de 3,3 a 0,9 puntos** en gran tour; es la primera vez
    que el ciclo completo (modelo, componentes y aceleración, todo generado) queda a menos de un
    punto de la referencia. Las réplicas también se ponen de acuerdo (desvío 0,22 contra 0,58).
  - En rutas la optimización no se vio al afinar (run 33, ruido del tuner), y gran tour queda 3,8
    puntos por delante: con modelos rápidos las dos, la representación vuelve a pesar.
  - El afinado casi no le gana al mejor no afinado (+0,41 [−0,06, +0,88]): con un solo vecindario
    bueno, el tuner tiene poco que elegir.

**De dónde sale la brecha con lo escrito a mano** (`scripts/diagnose_gap.py`; datos en
`tune_run35/diagnose_gap_vs_run30.json`). Las configuraciones elegidas por cada réplica de las
runs 30 y 35, en las mismas 10 instancias de test y la misma máquina, a 1,25–20 s, contando
iteraciones y llamadas a los componentes. Gap contra el mejor conocido común; diferencia pareada
contra la media de las tres configuraciones escritas a mano:

| Presupuesto | VNS generado (r0) | SA generados (r1 / r2) | Escrito a mano (media) |
|---|---|---|---|
| 1,25 s | 4,69 % (+2,29 [+1,15, +3,86]) | 4,11 / 4,68 % | 2,39 % |
| 5 s | 0,91 % (−0,36 [−1,12, +0,51]) | 2,07 / 1,73 % | 1,26 % |
| 20 s | 0,44 % (−0,33 [−0,81, +0,11]) | 2,07 / 1,68 % | 0,77 % |

- **Los componentes generados no son el problema**: con VNS, el catálogo generado iguala a lo
  escrito a mano desde los 5 s y queda por delante a 20 s (sin separarse del ruido).
- **La brecha está en las dos réplicas que eligieron SA.** Con un solo vecindario (2-opt sobre el
  tour), SA se estanca: 2,07 % a 5, 10 y 20 s. No es la velocidad: con el modelo de referencia
  del gran tour (4 a 6 veces más iteraciones) se estanca en 1,89 %. Tampoco es solo el
  enfriamiento: el SA enfría por iteraciones (con los parámetros elegidos, los defaults, la
  temperatura se vuelve despreciable en ~1500 iteraciones, menos de 1 s), pero repartirlo en los
  5 s no mejora (2,64 / 1,82 %). VNS sale de ese óptimo local con sus sacudidas; lo escrito a mano
  nunca eligió SA.
- **La velocidad pesa en presupuestos cortos**: a 1,25 s el generado va 2,1 puntos atrás. El Split
  del modelo generado es O(n³) (todos los segmentos, sin corte por capacidad, y el costo de cada
  ruta recalculado entero); el de referencia es O(n·L) y corta cuando se acaba la capacidad. Corrección
  posterior: el corte sí pasa la prueba de equivalencia (mismas salidas en todas las soluciones
  de prueba) y acelera el modelo 3,3 veces (2,2 → 7,1 mil evaluaciones/s); no era la prueba, el
  LLM no lo encontró. El prompt de la optimización ahora sugiere la poda. Primer intento con la
  sugerencia (corrida 48): rechazado en las 3 rondas. El LLM escribió un costo incremental con
  aristas sumadas dos veces y sin el corte; el reporte decía "costo equivocado en un caso
  oculto", sin nombrar la función, y la ronda 3 corrigió `cost_terms` (que estaba bien) y dejó el
  módulo idéntico a la ronda 2. Arreglos: la prueba diferencial contra el modelo aceptado va
  primero (nombra la función y la solución donde difiere) y una corrección que no cambia nada se
  señala en el siguiente pedido. Segundo intento (corrida 49, 4 rondas): las cuatro con el mismo
  `TypeError: 'int' object is not subscriptable`, sin ubicación. Arreglo: todo error que lanza el
  código validado se informa con la función, la línea y el código donde ocurrió
  (`describe_exception`, en las 14 capas que informaban solo el tipo y el mensaje). Tercer intento
  (corrida 50): aceptado en la primera ronda, 2,1 → 7,2 mil evaluaciones/s (3,4×): costo de ruta
  incremental en el Split (O(n³) → O(n²)), todavía sin el corte por capacidad. La versión de la
  corrida 47 queda como `parts_opt_run47.py`.
- **Rutas con memoria acotada** (corrida 51): el modelo de la corrida 41 (`lru_cache` de 200 mil
  entradas) violaba la regla; reoptimizado desde el original, aceptado en la primera ronda:
  4,8 → 40,9 mil evaluaciones/s (8,4×) con cachés de 8192 (la de la 41 hacía 51 mil).
- **Qué elige el tuner sigue siendo la mayor fuente de ruido**: cada réplica eligió un esqueleto
  distinto, y en esta máquina VNS le saca 0,8–1,2 puntos a los SA a 5 s. Si las tres hubieran
  elegido VNS, el ciclo quedaría a la par de lo escrito a mano (en esta máquina, 0,36 puntos por
  delante a 5 s).

Arreglos que salen de aquí: un SA que enfríe según el tiempo y no según las iteraciones (con
cualquier velocidad del modelo usaría todo el presupuesto); en el tuner, que la selección final
reevalúe con más semillas cuando las mejores configuraciones difieren en el esqueleto (hecho: carrera, abajo); y en la
optimización del modelo, sugerir la poda (descartar segmentos imposibles en vez de penalizarlos;
hecho, y no hacía falta relajar la prueba de equivalencia).

**SA con enfriamiento por tiempo** (nuevo default, `SA.cooling = time`: T = T0 · T_end^(t/presupuesto)).
Las dos configuraciones SA de la run 35, en las mismas instancias de test y a 5 s (una semilla):
2,07 → 0,96 % y 1,73 → 1,60 % con `T_end = 10⁻³` (el default); con `10⁻⁴`, 2,35 y 1,58 %. El tuner
afina `T_end`; las configuraciones anteriores, sin `SA.cooling`, siguen enfriando por iteraciones.

**Selección final en carrera** (run 36: lo mismo que la 35, con `--race-seeds 6`). Después de las 2
semillas extra de siempre, los candidatos que pierden contra el líder por más que el ruido salen y
los empatados siguen recibiendo semillas:

| | Run 35 (sin carrera) | Run 36 (carrera) |
|---|---|---|
| Elegido | VNS / SA / SA | VNS / VNS / VNS |
| Gap afinado, mejor conocido común | 1,99 % | 1,34 % (−0,64 [−1,01, −0,27]) |
| Contra lo escrito a mano (run 30) | +0,87 [+0,37, +1,31] | +0,23 [−0,02, +0,48], **ruido** |
| Desvío entre réplicas | 0,22 | 0,14 |
| Tiempo de tuning por réplica | 53–56 min | 56–67 min (+4 a +19 %) |

- De 10 candidatos por réplica, 7 a 9 salen después de las 2 semillas de siempre: la carrera
  solo gasta en los que quedan cerca. En dos réplicas llegaron al tope de 6 semillas extra un
  VNS y un SA todavía empatados, y ganó VNS por la media.
- **Con esto, el ciclo completo en gran tour ya no se distingue de lo escrito a mano.**
- Cautela: en dos réplicas los finalistas (un VNS y un SA) siguen empatados en train aun con 7
  semillas, y ganó VNS por la media, no por una diferencia significativa.
- No es el objetivo del tuner: en las instancias de train, las configuraciones de la run 35 se
  separan tanto como en test (VNS 0,17 %, los SA 1,49 y 1,35 % de gap contra el mejor de los
  tres; en cociente con la partida trivial, 0,4718 contra 0,4781 y 0,4771). En la run 35 las
  réplicas r1 y r2 no eligieron SA por una señal débil sino porque ningún VNS llegó a sus
  candidatos finales: la trayectoria de TPE no lo probó con buenos parámetros.

### Ciclo completo en el CLSP (representación de setups)

**Modelo por piezas** (corrida 52): vista heurística en la ronda 1, vista MIP en la 6 (la última;
rechazos por familias que no coinciden, términos del objetivo y la partición de grupos), 70 mil
tokens. **La vista constructiva no se aceptó** en 6 rondas: oscila entre ofrecer todas las
acciones (completaciones al azar infactibles por demanda) y ofrecer solo la segura (todas las
construcciones al azar iguales, el puntaje no tendría qué elegir). Sin ella el ciclo sigue con
constructores completos. Arreglo en el contrato de la vista constructiva: filtrar los candidatos
con una prueba de completabilidad (una acción entra si después todavía existe una completación
factible, p.ej. la "más permisiva": activar todo lo que falta). También: esos rechazos salían
rotulados "vista MIP".

### Reparación localizada: correcciones más cortas, no más componentes rescatados

Desde la corrida 43, una corrección trae solo las funciones o métodos que cambian y
`llm/patching.py` los reemplaza por nombre en el módulo rechazado (`undo` de los vecindarios ya
no se pide). Corridas 43 y 44: la mitad de las respuestas traían el método solo
(`def perturb(self, …)`), a veces con la sangría de la clase; lo sangrado no parseaba y lo suelto
quedaba como función del módulo, sin corregir nada. Arreglado (un método con `self` va a la
clase que lo define), se repitieron como 45 y 46. Mismos modelos y prompts que las corridas
37–40 (correcciones con el módulo completo):

| Corrida | Aceptados | Correcciones | Rescatadas | Tokens de salida por corrección | Tokens de la corrida |
|---|---|---|---|---|---|
| 37 / 39 rutas (módulo completo) | 10 / 9 de 12 | 7 / 11 | 2 / 3 | 1126 / 1312 | 44 / 57 mil |
| 38 / 40 gran tour (módulo completo) | 8 / 8 | 10 / 9 | 1 / 1 | 1342 / 1507 | 58 / 59 mil |
| 45 rutas (parches) | 12 | 1 | 1 | 702 | 29 mil |
| 46 gran tour (parches) | 9 | 8 | 1 (7 como parche) | 1071 | 52 mil |

- **Cada corrección sale 20–45 % más corta**: el LLM ya no reescribe lo que pasaba. La entrada no
  cambia (el módulo rechazado sigue en el prompt como contexto).
- **No rescata más componentes.** Casi todos los rechazos son de calidad (el operador no mejora
  o no perturba lo suficiente en su esqueleto), y eso es un problema de la idea, no de una
  función. El parche sirve para errores localizados (un `delta` sin la penalización, un índice
  mal puesto); las corridas tuvieron pocos de esos. Los rechazos sintácticos quedaron en 0 en las
  dos (3 en cada corrida de rutas antes), con una muestra chica.
- La rutas 45 aceptó 12 de 12 con una sola corrección: variación entre generaciones, no efecto de
  los parches (ya se vio que otra generación cambia 2 a 4 puntos).

### ProblemModel del CLSP por piezas: de 4 rechazos a aceptado a la primera, por arreglos del framework

El CLSP pone a prueba otra cosa que el CVRP: la solución es el plan de setups y el costo sale de
un LP (producción e inventario), así que la vista MIP tiene variables auxiliares continuas.
Referencia en `examples/lotsizing/model_parts.py`; 6 casos de 2×3 a 4×3 con el óptimo por fuerza
bruta, igual al del MIP escrito a mano en los 6.

| Corrida | Heurística | MIP | Llamadas | Tokens | Qué lo frenó | Arreglo en el framework |
|---|---|---|---|---|---|---|
| 25 | ronda 1 | — | — | — | la vista MIP redefinió un auxiliar de la heurística; la excepción tumbó el validador | rechazar redefiniciones; excepción = rechazo |
| 27 | ronda 4 | ✘ 4 rondas | 8 | 63 mil | redefinía `COMPONENT`/`build_component`: se usaba el prompt de sistema de los componentes | prompt de sistema propio del modelo |
| 28 | ronda 1 | ✘ 4 rondas | 5 | 33 mil | faltante `short_i_t` en el balance, fuera del objetivo ("le falta una restricción") | nombrar las auxiliares que absorben la violación |
| 29 | ronda 2 | ✘ 4 rondas | 6 | 39 mil | cotas `inf` (PuLP las rechaza); signos del balance; el faltante gratis otra vez | cotas infinitas aceptadas |
| 30 | **ronda 1** | **ronda 1** | 2 | 12 mil | — | — |

La corrida 30 coincide con el modelo escrito a mano en las 3 micro-instancias del chequeo
cruzado. Sobre una instancia 10×15, 5 s, evaluando todo con el modelo escrito a mano:

| Esqueleto | Modelo a mano | Piezas de referencia | Piezas generadas (30) |
|---|---|---|---|
| SA | 84 779 | 84 480 | 88 093 |
| ILS | 88 828 | 86 685 | 89 829 |
| VNS | 91 469 | 91 562 | 89 433 |
| LNS_MIP | 77 924 | 77 924 | **74 814** |
| FIX_OPT | 77 805 | 77 805 | 77 270 |

Todas las soluciones son factibles. Los esqueletos heurísticos varían en ±4 % entre modelos (la
penalización y la velocidad de evaluación cambian la trayectoria); las matheurísticas quedan
iguales o mejores con el MIP generado. Su `variable_groups` agrupa los períodos de a 4 intercalados
(t mod 4): cumple la regla y FIX_OPT funciona, aunque la referencia usa un grupo por período.

Lo que dice del framework: los rechazos de las corridas 25–29 fueron casi todos del framework,
no del problema (un prompt de sistema equivocado, una excepción sin atrapar, cotas infinitas, un
reporte que no decía dónde mirar). Con las piezas y los casos, cada falla quedó localizada en una
función y una familia, y por eso se pudo arreglar en una tarde.

### Segundo problema (CVRP): el validador tenía suposiciones del CLSP

Corridas de generación 18 y 20 (`generated/cvrp_scratch`, `…2`), desde cero: 11 y 10 de 15
componentes aceptados, pero solo 1 de 3 vecindarios en cada una. Los rechazos venían del
framework: soluciones "al azar" leídas de asignaciones 0/1 (en el CVRP no forman rutas; ahora
el modelo puede dar `random_solution`), feedback sin el movimiento ni la solución, exigir
movimientos o cambios en CADA solución de prueba (2-opt no tiene movimientos en una ruta de un
cliente), la monotonía de la destrucción medida en la micro-instancia y una partida de
validación degenerada (una ruta por cliente). Corregido eso, cada idea de vecindario,
destrucción y perturbación de la corrida 20 tiene al menos una versión que pasa.

### ProblemModel generado: por piezas y con casos de prueba, el error llega localizado

| Corrida | Modo | Rondas | Llamadas | Tiempo | Tokens | Óptimo vs referencia |
|---|---|---|---|---|---|---|
| 19 | de una pieza | 2 | 2 | 40 s | 11 mil | igual en 3 micro-instancias |
| 21 | por piezas, 6 casos (1 visible) | heurística 1, MIP 2 | 3 | 43 s | 15 mil | igual |
| 22 | por piezas, 6 casos (1 visible) | heurística 1, MIP 2 | 3 | 70 s | 17 mil | igual |
| 26 | por piezas, grupos ≥ 4 en tamaño real | heurística 1, MIP 1 | 2 | 26 s | 9 mil | igual |

El rechazo de la corrida 19 decía que el MIP declaraba infactible la solución trivial, sin
decir qué restricción; el de la 21 nombra familia, restricción y valor ("la familia
'capacidad' rechaza una solución factible: restricción 8 (u_2 − u_1 + 23·x_1_2 ≥ 9) vale −1").
Los esqueletos corren sobre los modelos generados con los mismos costos que sobre el de
referencia, salvo FIX_OPT: en la 21 `variable_groups` devolvía un grupo con todos los arcos, y
en la 22, ya exigidos 2 grupos con a lo sumo el 60 %, la lista partida en dos mitades. FIX_OPT
libera de a 2 grupos por defecto, así que cada subproblema era el MIP completo (15 clientes,
4 s: 1235 contra 682 con los sectores de referencia). Ahora se piden al menos 4 grupos y
ninguno con más de un tercio de las variables estructurales. Las dos corridas pasaron la
vista heurística a la primera contra 5 casos ocultos.

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
