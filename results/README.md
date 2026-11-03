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
| [`tune_run37/`](tune_run37/) | 27 sep | ciclo CVRP gran tour: modelo de la corrida 50, SA por tiempo, carrera | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | todos los arreglos juntos |
| [`tune_run38/`](tune_run38/) | 27 sep | ciclo CVRP rutas: modelo de la corrida 51, SA por tiempo, carrera | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | todos los arreglos juntos |
| [`tune_run39/`](tune_run39/) | 27 sep | CLSP escrito a mano | SA, ILS, VNS, LNS_MIP | 10+10, 10×15 | 5 s | 40 × 3 réplicas | referencia para el ciclo del CLSP |
| [`tune_run40/`](tune_run40/) | 28 sep | ciclo CLSP setups: modelo 52 (+54 constructiva, 57 memoria), componentes 55 | SA, ILS, VNS, LNS_MIP | 10+10, 10×15 | 5 s | 40 × 3 réplicas | ciclo completo en el segundo problema |
| [`tune_run41/`](tune_run41/) | 29 oct | ciclo CVRP rutas: componentes de Claude Opus 5.5 (corrida 91) sobre el modelo de la corrida 51 | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | otro LLM para los componentes |
| [`tune_run42/`](tune_run42/) | 29 oct | ciclo CVRP gran tour: componentes de Claude Opus 5.5 (corrida 92) sobre el modelo de la corrida 50 | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | otro LLM para los componentes |
| [`tune_run43/`](tune_run43/) | 29 oct | ciclo CLSP setups: componentes de Claude Opus 5.5 (corrida 93) sobre el modelo de la corrida 57 | SA, ILS, VNS, LNS_MIP | 10+10, 10×15 | 5 s | 40 × 3 réplicas | otro LLM para los componentes |
| [`tune_run44/`](tune_run44/) | 29 oct | ciclo completo con Opus 5.5: modelo (corrida 94) y componentes (97) de rutas | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | todo el ciclo con un solo LLM, sin optimización |
| [`tune_run45/`](tune_run45/) | 29 oct | ciclo completo con Opus 5.5: modelo (95) y componentes (98) de gran tour | SA, ILS, VNS, LNS_MIP | 10+10, 30 clientes | 5 s | 40 × 3 réplicas | todo el ciclo con un solo LLM, sin optimización |
| [`tune_run46/`](tune_run46/) | 29 oct | ciclo completo con Opus 5.5: modelo (96) y componentes (99) del CLSP | SA, ILS, VNS, LNS_MIP | 10+10, 10×15 | 5 s | 40 × 3 réplicas | todo el ciclo con un solo LLM, sin optimización |
| [`tune_run47/`](tune_run47/) | 29 oct | job shop (makespan): catálogo escrito a mano (secuencias, camino crítico) | SA, ILS, VNS, LNS_MIP | 10+10, 10×10 | 5 s | 40 × 3 réplicas | referencia del tercer problema |
| [`tune_run48/`](tune_run48/) | 29 oct | ciclo completo con Opus 5.5 en job shop, secuencias por máquina: modelo (100) y componentes (102) | SA, ILS, VNS, LNS_MIP | 10+10, 10×10 | 5 s | 40 × 3 réplicas | tercer problema, sin nada a mano salvo instancias y casos |
| [`tune_run49/`](tune_run49/) | 29 oct | ciclo completo con Opus 5.5 en job shop, permutación con repetición: modelo (101) y componentes (103) | SA, ILS, VNS, LNS_MIP | 10+10, 10×10 | 5 s | 40 × 3 réplicas | otra representación del tercer problema |
| [`tune_run50/`](tune_run50/) | 30 oct | job shop, catálogo a mano, **afinado y corrido en C++** (`--native`), Optuna | SA, ILS, VNS, TS | 10+10, 10×10 | 5 s | 40 × 3 réplicas | backend nativo |
| [`tune_run52/`](tune_run52/) | 30 oct | lo mismo con **irace** (`--tuner irace`, 700 experimentos) | SA, ILS, VNS, TS | 10+10, 10×10 | 5 s | 700 exp. × 3 réplicas | irace contra Optuna (la 51 falló por una ruta) |
| [`tune_run53/`](tune_run53/) | 30 oct | lo mismo con el TS genérico extendido (estimación, saltos atrás, mejor tabú si todos lo son) | SA, ILS, VNS, TS | 10+10, 10×10 | 5 s | 700 exp. × 3 réplicas | TS entra al espacio en serio |
| [`tune_run54/`](tune_run54/) | 30 oct | job shop, **componentes C++ generados por Opus 5.5** (corrida 104), irace en C++ | SA, ILS, VNS, TS | 10+10, 10×10 | 5 s | 700 exp. × 3 réplicas | paso 2: el LLM escribe C++ |
| [`tune_run55/`](tune_run55/) | 30 oct | job shop, catálogo a mano en C++, irace afinando en **15×15 con 10 s** | SA, ILS, VNS, TS | 10+10, 15×15 | 10 s | 700 exp. × 3 réplicas | afinar en el tamaño de Taillard |
| [`tune_run56/`](tune_run56/) | 30 oct | lo mismo con los componentes C++ de Opus (corrida 104) | SA, ILS, VNS, TS | 10+10, 15×15 | 10 s | 700 exp. × 3 réplicas | ídem |
| [`tune_run58/`](tune_run58/) | 31 oct | lo mismo con los componentes C++ **optimizados por el LLM** (corridas 106–108) | SA, ILS, VNS, TS | 10+10, 15×15 | 10 s | 700 exp. × 3 réplicas | etapa de optimización C++ |
| [`tune_run59/`](tune_run59/) | 1 nov | lo mismo con la inserción con delta incremental (corrida 111) | SA, ILS, VNS, TS | 10+10, 15×15 | 10 s | 700 exp. × 3 réplicas | ¿cambia el tuning un vecindario más rápido? |
| [`tune_run60/`](tune_run60/) | 1 nov | lo mismo con PR y los relinks del LLM (corrida 112) | SA, ILS, VNS, TS, PR | 10+10, 15×15 | 10 s | 700 exp. × 3 réplicas | ¿irace elige PR? |
| [`tune_run61/`](tune_run61/) | 1 nov | lo mismo afinando en 20×15 con 15 s | SA, ILS, VNS, TS, PR | 10+10, 20×15 | 15 s | 728 exp. × 3 réplicas | afinar más cerca de Taillard |
| [`tune_run71/`](tune_run71/) | 2 nov | CLSP con todo generado en C++ (modelo, componentes, optimización) | SA, ILS, VNS, TS, PR, HYB | 10+10, 10×15 | 10 s | ~1000 exp. × 3 réplicas | ¿la matheurística generada iguala a la escrita? |
| [`tune_run72/`](tune_run72/) | 2 nov | CLSP con el catálogo a mano en Python | SA, ILS, LNS_MIP, FIX_OPT, TS, VNS, GRASP, LOCAL_BRANCH, MIP_PERTURB | 10+10, 10×15 | 10 s | ~1000 exp. × 3 réplicas | referencia |

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

**Todo junto** (runs 37 y 38: modelos reoptimizados con memoria acotada, SA por tiempo, selección en
carrera; mismos catálogos de componentes que las runs 32–36):

| Comparación (mismo mejor conocido por par) | Gap afinado | Diferencia por instancia |
|---|---|---|
| Gran tour, run 37 contra run 36 | 0,58 contra 1,56 % | −0,98 [−1,18, −0,77] |
| **Gran tour (37) contra escrito a mano (30)** | **0,58 contra 1,33 %** | **−0,76 [−1,07, −0,43]** |
| Rutas, run 38 contra run 33 | 5,66 contra 5,03 % | +0,62 [−0,28, +1,38], ruido |
| Rutas (38) contra escrito a mano (30) | 6,58 contra 1,30 % | +5,28 [+4,59, +6,01] |

- **En gran tour el ciclo completo le gana a lo escrito a mano**, con las tres réplicas de acuerdo
  (VNS con 2-opt sobre el tour, desvío 0,11). La mejora sobre la run 36 viene del modelo 3,4 veces
  más rápido (corrida 50): el VNS generado ya igualaba a lo escrito a mano a 5 s y lo superaba con
  más tiempo; más velocidad es más tiempo.
- En rutas no cambia nada: el catálogo es el límite (su mejor vecindario es un intercambio entre
  rutas; lo escrito a mano tiene `relocate` con delta O(1)). Las réplicas se ponen de acuerdo
  (desvío 0,52 contra 1,62), pero en algo peor.

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

Repetir el modelo entero para reintentar la vista constructiva (corrida 53) se rechazó antes, en
la vista heurística (6 rondas: un `PulpError` y después un costo que no coincide en un caso
oculto): la variación entre generaciones. Arreglos: `llm.cycle model --construction-only` (input
`construction_only` de `generate.yml`) genera solo la vista constructiva sobre el modelo ya
aceptado; y el traceback de un error salta también las librerías instaladas (en la 53 los tres
marcos eran de PuLP y no se veía la línea del LLM).

Vista constructiva sola sobre el modelo de la 52, con la pista de completabilidad (corrida 54):
**aceptada en la primera ronda** (6,5 mil tokens; antes, 6 rondas rechazadas).

**Componentes** (corrida 55): 10 de 12 (3 puntajes, 1 vecindario, 3 perturbaciones, 3
destrucciones), 47 mil tokens, 6 correcciones como parche. **Optimización** (corrida 56): cortada
por el límite de 45 min del job. El modelo resuelve dos LP por evaluación (39 soluciones/s; la
referencia escrita a mano, uno, 62/s) y la medición de memoria hacía 30 mil evaluaciones por
candidato. Además, ese modelo se había aceptado en la etapa del modelo con dos
`lru_cache(maxsize=None)`: la regla de memoria solo corría en la optimización. Arreglos: una
revisión estática e instantánea de las cachés (`lru_cache` sin límite o con más de 8192 entradas,
en el módulo y un nivel adentro de lo que guarda) que corre también al aceptar modelos y
componentes, y la medición dinámica solo cuando cabe en 60 s. De los 353 componentes generados
hasta ahora, ninguno tiene una caché sin límite; de los modelos, el del CLSP y las versiones
optimizadas de las corridas 41 y 42. Si el modelo aceptado viola la regla, la optimización se lo
dice al LLM y pide solo no perder velocidad (0,8×) en vez de 1,5×.

Con eso (corrida 57), el modelo del CLSP se aceptó en la primera ronda con cachés acotadas y la
misma velocidad (43 → 40 evaluaciones/s). La optimización de componentes volvió a cortarse a los
45 min (cada `delta` resuelve LP) y, como las estadísticas se escribían al final, no quedó
registro; sus archivos a medio validar no se usan. Ahora la etapa guarda las estadísticas a medida
que avanza, no empieza componentes después de `--max-minutes` (35) y el log sale sin buffer.

**Tuning del ciclo contra lo escrito a mano** (runs 40 y 39, mismas instancias, presupuesto y tuner):

| | Escrito a mano (39) | Ciclo completo (40) |
|---|---|---|
| Elegido | LNS_MIP, `greedy_unit_marginal_cost` + `period_window` (las 3) | LNS_MIP con puntajes y destrucciones generados (2 elecciones distintas) |
| Gap afinado (mejor conocido común) | 0,68 % | 1,02 % |
| Diferencia por instancia | | +0,34 [+0,15, +0,53] |
| Desvío entre réplicas | 0,03 | 0,38 |

- **El ciclo completo queda a 0,34 puntos de lo escrito a mano en el CLSP**: modelo, vista
  constructiva, puntajes, destrucciones, todo generado. Dos de las tres réplicas (0,90 y 0,62 %)
  están a la par de la referencia; la tercera eligió otra destrucción y queda en 1,54 %.
- Los dos lados eligen LNS_MIP en todas las réplicas: con 10×15 el MIP de la vecindad es lo que
  manda, y ahí pesan la destrucción y el constructor inicial, no la velocidad del modelo (el LP por
  evaluación lo pagan los dos).
- El afinado no le gana al mejor no afinado del catálogo generado (−0,11 [−0,51, +0,27]).

### Componentes generados con Claude Opus 5.5: el ciclo le gana o empata a lo escrito a mano en los tres casos

Corrida 91: los componentes del ciclo de rutas con Claude Opus 5.5 (`effort: medium`, mismos prompts,
mismo modelo por piezas que las generaciones con GPT-5.4-mini). **12 de 12 aceptados en 5 llamadas**
(una corrección), 60 mil tokens, 0,70 USD (salida 0,58, entrada 0,13). Las generaciones con
GPT-5.4-mini en el mismo workspace: 9 a 12 de 12, 7 a 15 llamadas. Run 41: el mismo tuning que la
run 38 (modelo de la corrida 51, SA por tiempo, carrera), cambiando solo los componentes:

| Comparación (mismo mejor conocido por par) | Gap afinado | Diferencia por instancia |
|---|---|---|
| Componentes de Opus (41) contra los de GPT (38) | 0,74 contra 6,55 % | −5,81 [−6,78, −4,94] |
| **Componentes de Opus (41) contra escrito a mano (30)** | **0,77 contra 1,30 %** | **−0,53 [−0,88, −0,18]** |

- Las tres réplicas eligen ILS con `two_opt_intra_and_star` (2-opt dentro de cada ruta y entre
  rutas en un mismo vecindario) y `ruin_recreate_radial_blink` (ruina y recreación radial).
  Lo que le faltaba al catálogo de rutas era eso: con GPT su mejor vecindario era un intercambio
  de clientes entre rutas.
- **Gran tour** (corrida 92: 11 de 12, 9 llamadas, 0,80 USD; run 42, mismo tuning que la run 37):
  0,43 contra 0,58 % con los de GPT (−0,15 [−0,25, −0,04]) y **0,41 contra 1,32 % de lo escrito a
  mano (−0,90 [−1,23, −0,57])**. Las tres réplicas eligen VNS con 2-opt sobre el tour; aquí GPT ya
  tenía un buen vecindario y la mejora es menor que en rutas.
- **CLSP** (corrida 93: 12 de 12, 4 llamadas, 0,55 USD; run 43, mismo tuning que la run 40):
  0,53 contra 1,02 % con los de GPT (−0,49 [−0,79, −0,24]) y 0,53 contra 0,67 % de lo escrito a mano
  (−0,15 [−0,47, +0,15], ruido). Los dos lados eligen LNS_MIP; las destrucciones de Opus
  (`period_window_destruction`, `wasteful_cell_destruction`) igualan a la escrita a mano.

| Problema | Ciclo con GPT-5.4-mini | Ciclo con Claude Opus 5.5 | Escrito a mano |
|---|---|---|---|
| CVRP rutas | 6,55 % (run 38) | **0,74 %** (run 41) | 1,30 % (run 30) |
| CVRP gran tour | 0,58 % (run 37) | **0,43 %** (run 42) | 1,32 % (run 30) |
| CLSP | 1,02 % (run 40) | **0,53 %** (run 43) | 0,67 % (run 39) |

  (gap afinado medio de 3 réplicas; las diferencias contra lo escrito a mano usan el mejor conocido
  común de cada par, ver arriba.) **Con los componentes de Opus 5.5, el ciclo completo le gana a lo
  escrito a mano en las dos representaciones del CVRP y queda a la par en el CLSP**, por 0,55 a 0,80
  USD por generación de componentes.
- El costo de una generación es sobre todo de salida (83 %): reordenar los prompts para la caché
  ahorraría ~0,06 USD por corrida; el nivel de `effort` pesa más.

### Ciclo completo con Claude Opus 5.5: modelo y componentes, sin la etapa de optimización

Corridas 94–96 (modelo por piezas, `effort: medium`): los tres aceptados en la primera ronda de cada
etapa (vista heurística, MIP y constructiva), 3 llamadas y 0,25–0,32 USD cada uno; con GPT-5.4-mini
la vista MIP había llegado a 6 rondas y la constructiva del CLSP no se había aceptado. Sin pasar por
la optimización, ya son más rápidos que los de GPT optimizados y que los escritos a mano:

| Evaluaciones/s | Rutas | Gran tour | CLSP |
|---|---|---|---|
| Opus 5.5 | **62 687** | **12 215** | **182** |
| GPT, original | 6 429 | 369 | 47 (caché sin límite) |
| GPT, optimizado | 32 451 | 8 805 | 50 |
| Escrito a mano | 36 237 | 11 351 | 96 |

Corridas 97–99: componentes de Opus sobre esos modelos (rutas 12/12, gran tour 10/12, CLSP 12/12;
0,57–0,86 USD). Runs 44–46, mismo tuning que las anteriores:

| Problema | Opus todo (44–46) | Modelo GPT + componentes Opus (41–43) | Escrito a mano (30 / 39) | Opus todo − escrito a mano |
|---|---|---|---|---|
| CVRP rutas | 0,97 % | 0,77 % | 1,31 % | −0,34 [−0,80, +0,10] |
| CVRP gran tour | 0,47 % | 0,41 % | 1,31 % | **−0,84 [−1,23, −0,45]** |
| CLSP | 0,70 % | 0,53 % | 0,68 % | +0,02 [−0,24, +0,30] |

- Contra el modelo de GPT con componentes de Opus no se distingue del ruido en ninguno de los tres
  (+0,20, +0,06, +0,16 puntos, intervalos que cruzan cero). Contra lo escrito a mano: gana en gran
  tour, empata en rutas (una réplica en 1,44 %; las otras dos en 0,7 %) y en el CLSP.
- **Un solo LLM y un costo de 0,9–1,2 USD por problema** (modelo + componentes) dan lo mismo que la
  combinación que había costado varias corridas de GPT, la etapa de optimización y los arreglos de
  memoria. La velocidad extra del modelo no se traduce en gap porque los catálogos ya eran rápidos
  (en el CLSP manda el MIP de LNS_MIP).

### Tercer problema, job shop (makespan): el ciclo con Opus 5.5 queda por delante de lo escrito a mano

`examples/jobshop` entra directamente por piezas: no hay un `ProblemModel` monolítico, el del pack
base es el de las piezas de referencia. Dos representaciones con la misma instancia, casos y vista
MIP (disyuntiva big-M): `sequences` (una secuencia por máquina, plan semiactivo; un ciclo con las
rutas es la familia `orden`) y `operations` (permutación con repetición de Bierwirth, decodificador).
Seis casos de 3×3 a 4×4 con óptimo por fuerza bruta. El catálogo a mano usa la estructura clásica:
despacho (fin más temprano, más trabajo restante), intercambio N5 e inserción en bloques críticos,
patada en el camino crítico, destrucción por ventana de tiempo y por máquinas.

Opus 5.5, `effort: medium`:

| | Modelo | Componentes |
|---|---|---|
| `sequences` (100, 102) | 3 llamadas, todo en la ronda 1, 0,30 USD | 12/12, 0,79 USD |
| `operations` (101, 103) | 5 llamadas, 0,54 USD | 12/12, 0,76 USD |

En `operations` la vista heurística tardó 3 rondas: una respuesta con ciclo pasa por `from_answer`
a otra permutación y el modelo la reportó primero como `secuencia` y después invirtió el error; los
casos lo atraparon las dos veces. En las dos representaciones Opus llegó solo al camino crítico
(intercambios y reinserciones en bloques), sin ver el catálogo a mano.

Tuning 10×10 (gaps contra el mejor conocido común de cada par; diferencia por instancia con IC95):

| Comparación | Gaps | Diferencia |
|---|---|---|
| `sequences` (48) contra escrito a mano (47) | 2,56 contra 3,57 % | −1,01 [−2,53, +0,42] |
| `operations` (49) contra escrito a mano (47) | 2,00 contra 3,78 % | −1,77 [−3,83, +0,16] |
| **`operations` (49) contra `sequences` (48)** | **1,99 contra 2,75 %** | **−0,76 [−1,51, −0,03]** |

- Los dos catálogos generados quedan por delante del escrito a mano en las tres réplicas, pero con
  10 instancias el intervalo cruza cero apenas. La única diferencia que se separa del ruido es entre
  representaciones: la permutación con repetición le gana a las secuencias.
- Lo elegido: con secuencias, el mismo esquema que a mano (VNS/ILS desde el greedy de más trabajo
  restante, con una cota de la cola del trabajo, e intercambio en el camino crítico); con la
  permutación, SA con inserción de una operación en la permutación (`dispatch_token_insertion`),
  desde el greedy con cota inferior del makespan o desde una al azar. Toda permutación es factible,
  y SA se mueve sin chocar con ciclos.
- Costo del tercer problema completo: 1,1–1,3 USD por representación (modelo + componentes).

### Backend nativo (C++) e irace: el gap del job shop baja de 3,96 % a 0,20 %

El modelo del job shop y su catálogo a mano, portados a C++ (`examples/jobshop/native/`), pasan el
mismo validador y los mismos casos que las piezas de Python y coinciden con ellas en costo y
violaciones. Los esqueletos SA, ILS, VNS y TS en C++ tienen la semántica y los parámetros de Python.

Primero, las configuraciones que eligió la run 47 (afinadas en Python) corridas en C++
(`scripts/native_benchmark.py`, mismas 10 instancias): ~11 000 iteraciones/s contra ~220 en Python
(50–70×); gap 2,07 % con 1, 5 y 25 s, contra 3,39 % en Python con 5 s. La velocidad ayuda, pero esas
configuraciones (VNS/ILS con aceptación estricta) se estancan en menos de 1 s: estaban elegidas para
la velocidad de Python. Afinando en C++ (gaps contra el mejor conocido común de cada par):

| Comparación | Gaps | Diferencia |
|---|---|---|
| Optuna en C++ (50) contra Optuna en Python (47), catálogo a mano | 0,57 contra 3,96 % | **−3,40 [−5,69, −1,43]** |
| Optuna en C++ (50) contra catálogo generado en Python (49) | 0,64 contra 2,25 % | **−1,61 [−2,30, −0,96]** |
| **irace en C++ (52) contra Optuna en C++ (50)** | **0,20 contra 0,58 %** | **−0,38 [−0,70, −0,15]** |

- Las seis réplicas eligen SA con intercambio crítico (N5) desde un greedy; en Python SA no salía
  porque no alcanzaba a enfriar.
- irace le gana a Optuna con el mismo presupuesto aproximado: Optuna se queda en 2 de 3 réplicas con
  los numéricos por defecto de SA (T0 = 31,6, T_end = 0,001; su selección final prefiere los defaults
  si no se separan del ruido) y irace encuentra temperaturas más altas (T0 = 53–104, T_end = 0,05–0,09)
  y el greedy con RCL.
- Las tres diferencias se separan del ruido, las primeras del proyecto. El gap es contra el mejor
  conocido propio; falta medir contra las instancias de Taillard.

Run 53, con el TS genérico extendido (filtrado por estimación, saltos atrás a la élite y, si todos los
candidatos son tabú, el mejor de ellos; sin esto último TS quedaba quieto con N5 y daba 7 %): irace elige
TS en 2 de 3 réplicas (tenencia 14–23, estimación de Taillard para preseleccionar 6–9 candidatos, una con
saltos atrás) y SA en la otra. Gap 0,28 % contra 0,20 % de la run 52 (−0,08 [−0,34, +0,13], ruido).
En 10×10 con 5 s las configuraciones buenas ya quedan a 0,1–0,4 % del mejor conocido propio: para
separarlas hacen falta instancias más difíciles (15×15, 20×15, Taillard).

### Taillard: a 0,85 % del óptimo en 15×15 con 30 s

Las seis configuraciones de las runs 52 y 53 (afinadas en 10×10 con 5 s), en las instancias de
Taillard ta01–ta20 (`examples/jobshop/taillard/`, de JSPLIB), 30 s por corrida en C++, una semilla
(`scripts/taillard_eval.py`, `taillard_run52_53.json`). Gap contra el óptimo o la mejor cota superior
publicada en JSPLIB:

| configuración | ta01–10 (15×15) | ta11–20 (20×15) |
|---|---|---|
| run 52 r0, SA | 1,17 % | 2,29 % |
| run 52 r1, SA | 1,09 % | 2,45 % |
| **run 52 r2, SA** | **0,85 %** | **1,98 %** |
| run 53 r0, TS | 2,31 % | 2,84 % |
| run 53 r1, SA | 0,85 % | 2,31 % |
| run 53 r2, TS con saltos atrás | 1,21 % | 2,10 % |

- Lo afinado en 10×10 se transfiere: el mejor de las seis en cada instancia queda a 0,08–1,33 % en
  15×15 y a 0,82–2,42 % en 20×15. ta06 y ta07 a 2 y 1 unidades del óptimo.
- Todavía no es el estado del arte (las tabúes de la familia TSAB y los solvers CP llegan al óptimo o
  muy cerca en estas instancias), y el TS genérico queda detrás de SA: le falta lo que hace fuerte a
  TSAB (N5 con evaluación exacta incremental en vez de rehacer el plan, y la vuelta atrás con los
  movimientos no explorados). Las cotas de JSPLIB para ta11–20 pueden estar desactualizadas.

### Paso 2: Opus 5.5 escribe los componentes en C++ y empata con lo escrito a mano

Corrida 104 (`llm/native_generator.py`): el LLM ve la descripción, el header del modelo C++ (sin el
catálogo a mano ni sus helpers), el contrato del slot y reglas genéricas; ninguna pista de qué
vecindario usar ni cómo evaluarlo (un test lo verifica). 9 de 9 aceptados (una perturbación en la
ronda 2), 0,65 USD, 6,5 min. Llegó solo a lo clásico: intercambio adyacente en el camino crítico con
un parámetro `block_ends_only` (N1 o N5, a elección del tuner), inserción en los extremos de los
bloques con `tabu_key`, reconstrucción Giffler–Thompson con ruido como perturbación. No escribió
evaluación incremental ni `estimate`: delta exacto rehaciendo el plan, con el objetivo de la solución
actual en caché (la misma velocidad que el catálogo a mano: ~100 000–140 000 iteraciones/s de SA).

| | 10×10 (run 54 contra 52, mejor conocido común) | Taillard 15×15 (mejor réplica / mejor de 3 por instancia) | Taillard 20×15 |
|---|---|---|---|
| Componentes C++ de Opus (54) | 0,30 % | 0,95 % / 0,68 % | 3,00 % / 2,80 % |
| Escritos a mano en C++ (52) | 0,26 % | 0,85 % / 0,78 % | 1,98 % / 1,82 % |

- En 10×10 la diferencia es −0,04 [−0,22, +0,14] (ruido) y en 15×15 están a la par. En 20×15 el
  catálogo generado queda detrás (una semilla por instancia; la TS de la réplica 2 llega a 7,6 %). No es
  velocidad (iteraciones/s iguales): las configuraciones se afinaron en 10×10 con 5 s y transferirlas a
  instancias más grandes funciona peor con estos componentes; habría que afinar en 15×15 para separarlo.

Afinando en 15×15 con 10 s (runs 55 y 56) la desventaja en 20×15 desaparece: venía de transferir lo
afinado en 10×10. En el tuning, generado 0,73 % contra a mano 0,91 % (+0,18 [−0,06, +0,42], ruido); las
tres réplicas del generado eligen TS con su intercambio crítico desde una solución al azar. En Taillard
(`taillard_run55.json`, `taillard_run56.json`; 3 semillas, 30 s; diferencia a mano − generado por
instancia, IC95 por bootstrap sobre las 10 instancias de cada grupo):

| | generado (56) | a mano (55) | diferencia |
|---|---|---|---|
| 15×15, media de las 3 configuraciones y semillas | 1,07 % | 1,32 % | +0,25 [−0,32, +1,06] |
| 20×15, ídem | 1,97 % | 2,19 % | +0,22 [+0,02, +0,42] |
| 15×15, mejor de las 9 corridas por instancia | 0,47 % | 0,62 % | +0,15 [−0,04, +0,46] |
| 20×15, ídem | 1,25 % | 1,51 % | +0,27 [+0,02, +0,50] |

Con todo el ciclo hecho por el LLM en C++ (componentes) y el tuner (irace), el resultado iguala o supera
levemente al catálogo escrito a mano, también en Taillard. La distancia al estado del arte sigue ahí
(~1 % en 15×15 con 30 s): ninguno de los dos catálogos tiene evaluación incremental de N5.

### Etapa de optimización C++: el LLM llega solo a la evaluación incremental y a la estimación de Taillard

`llm/native_optimizer.py`: el componente aceptado es el oráculo; la versión nueva tiene que dar las mismas
salidas (movimientos y su orden, apply, delta), pasar las capas y ser más rápida, medido en C++. Lo que hizo
falta en el framework para que la optimización fuera útil, sin pistas del problema:

- **Decir cómo se usa el componente y medir eso.** La primera versión del prompt ofrecía `estimate` como
  opcional pero solo medía `delta`/s, y nunca decía que SA no llamaba a `delta` (evaluaba el objetivo
  completo). Ahora el prompt describe el uso por esqueleto y se miden dos cosas: `delta` exacto/s y
  candidatos revisados por segundo en un paso de TS (estimate de todos, delta de los 5 mejores). SA tiene
  `SA.eval` (objective | delta), afinable.
- **Perfil por método** (µs de moves por solución, delta, estimate y apply), **los componentes del mismo slot
  ya optimizados** como referencia (su propio código) y **pasadas encadenadas** (lo que mejoró se vuelve a
  optimizar con su versión nueva como oráculo, pidiendo 1,2× desde la segunda pasada).

| Corrida | Qué cambió | Intercambio crítico (N5) | Inserción en bloques |
|---|---|---|---|
| 106 (1,40 USD) | primera versión | 199 k → 580 k delta/s (incremental exacto) | 237 k → 404 k |
| 107 (1,56 USD) | uso por esqueleto, dos medidas | no pasa de 1,36× | **estimate con cabezas y colas**: paso de TS 432 k → 1,32 M |
| 108 (3,90 USD) | perfil, hermanos, 3 pasadas | 502 k → 937 k → 1,88 M → **2,40 M delta/s**, y **estimate** en la pasada 3 | paso de TS 1,31 M → 2,14 M → 2,56 M → **4,03 M** |

El tercer vecindario (intercambio de prioridad entre dos trabajos en todas las máquinas) no mejoró en
ninguna corrida; un intento con `estimate` se rechazó porque ordenaba como delta solo 21 de 49 pares.

Run 58 (irace en 15×15, 10 s, mismas condiciones que 55 y 56) con el catálogo optimizado: N5 en las tres
réplicas, dos con TS (una preselecciona con `estimate`) y una con SA en `SA.eval = delta`. Tuning: 0,66 %
contra 0,84 % sin optimizar (+0,18 [+0,04, +0,34]) y 0,58 % contra 0,94 % a mano (+0,36 [+0,04, +0,69]).
Taillard (`taillard_run58.json`; 3 semillas, 30 s; diferencia por instancia, IC95 bootstrap):

| | optimizado (58) | sin optimizar (56) | a mano (55) | 58 contra 56 | 58 contra 55 |
|---|---|---|---|---|---|
| 15×15, media de configuraciones y semillas | **0,75 %** | 1,07 % | 1,32 % | +0,33 [+0,13, +0,55] | +0,57 [+0,07, +1,39] |
| 20×15, ídem | **1,66 %** | 1,97 % | 2,19 % | +0,30 [+0,18, +0,43] | +0,53 [+0,35, +0,69] |
| 15×15, mejor de 9 por instancia | **0,34 %** | 0,47 % | 0,62 % | +0,13 [+0,02, +0,25] | +0,28 [+0,08, +0,56] |
| 20×15, ídem | **0,99 %** | 1,25 % | 1,51 % | +0,26 [+0,02, +0,47] | +0,53 [+0,28, +0,81] |

Todas las diferencias se separan del ruido. La mejor réplica (TS con N5 y saltos atrás) queda a 0,55 % del
óptimo en 15×15 y 1,46 % en 20×15 con 30 s. Todo el ciclo fue del LLM y del framework: componentes
(corrida 104), optimización (106–108) y tuning (irace).

**Respuestas como ediciones (corrida 109, 3,56 USD).** Cuarta pasada sobre el catálogo de la 108, con el LLM
devolviendo solo bloques buscar/reemplazar (`native/edits.py`). 8 de 9 respuestas llegaron como ediciones,
todas aplicables (0 fallos de edición). Pero el costo casi no bajó:

| Corrida | Llamadas | Entrada | Salida | Salida por llamada | Costo |
|---|---|---|---|---|---|
| 108 (componente completo) | 10 | 179 k | 159 k | 15,9 k | 3,90 USD |
| 109 (ediciones) | 9 | 190 k | 140 k | 15,6 k | 3,56 USD |

Los componentes miden 4–25 KB (≈1–7 k tokens); la salida por llamada (≈15 k) está dominada por el pensamiento
adaptativo, que con `effort: medium` no depende de cuánto código se devuelva. Las ediciones acortan la parte
visible, pero el ahorro real está en el esfuerzo de razonamiento o en el número de rondas, no en el formato.

Ningún vecindario mejoró: N5 llegó a 1,49× / 1,35× (pedía 1,5×), la inserción a 1,10×, y el tercero empeoró
en los tres intentos. Tras tres pasadas el margen se agotó: el catálogo de la 108 queda como está.

**Dónde se va el tiempo, y una medida que se dejaba engañar (corrida 110, 4,70 USD).** Un perfil (callgrind) de
las configuraciones de la run 58 (TS y SA con N5) muestra que el modelo compartido (`schedule`, `objective`) casi
no aparece: el tiempo está en el vecindario rehaciendo, para cada solución nueva, cabezas y colas. Se agregó una
tercera medida, `walk` (50 pasos como en TS desde cada solución, aplicando uno de los 5 mejores: la solución
siguiente es la que devolvió `apply`), la equivalencia recorre también una trayectoria, y el prompt sugiere dejar
listo en `apply` lo que necesitará la solución siguiente.

La corrida 110 aceptó un N5 con delta/s 3,3 M → 21,7 M y paso de TS 3,7 M → 13,9 M, pero `walk` 206 k → 204 k: el
LLM agregó una tabla hash de hasta 256 soluciones con los delta memorizados, y la medida repetía las mismas 6
soluciones en cada pasada. Arreglo: `bench` y `profile_neighborhood` generan soluciones nuevas en cada pasada
(fuera del tiempo medido). Con la medida corregida, en la misma máquina:

| N5 | delta/s | paso de TS | walk (pasos/s) |
|---|---|---|---|
| r1 (generado, corrida 104) | 442 k | 445 k | 51 k |
| r5 (optimizado, 106–108) | 1,44 M | 1,58 M | 222 k |
| r6 (corrida 110, no se usa) | 1,41 M | 1,65 M | 257 k |

Las cifras de las corridas 106–108 de arriba también estaban infladas por la misma repetición (2,40 M delta/s
era ~1,4 M), aunque la mejora es real (×3,3 en delta, ×4,4 en la trayectoria) y la confirman la run 58 y
Taillard. El r6 no se incorpora: con la medida justa no gana.

**Corrida 111 (5,96 USD, 16 llamadas, 475 k de entrada y 203 k de salida), ya con la medida justa.** Medido de
nuevo localmente, con soluciones nuevas en cada pasada:

| Vecindario | delta/s | paso de TS | walk (pasos/s) |
|---|---|---|---|
| inserción, r6 → **r8** (dos pasadas aceptadas) | 790 k → 3,14 M (×4,0) | 3,03 M → 4,58 M | 135 k → **230 k (×1,7)** |
| intercambio de prioridad, r1 → r2 | 321 k → 420 k | 317 k → 409 k | 7,8 k → 7,4 k |
| N5 (r5) | sin cambio: la trayectoria llegó a ×1,20 en 3 intentos | | |

La inserción ahora calcula delta de forma incremental y es la primera mejora que se ve en la trayectoria. N5 no
pasó: preparar una solución nueva (≈2,4 µs) sigue siendo la mayor parte del paso, y el LLM no llegó a actualizar
cabezas y colas desde `apply`. El intercambio de prioridad pasó por 1,5× en delta/s en la máquina del workflow
(localmente es 1,3×, sin cambio en la trayectoria). 15 de 16 respuestas de corrección fueron ediciones.

Run 59 (irace, mismas condiciones que la 58, catálogo con la inserción r8): las tres réplicas vuelven a elegir N5
(TS con `trivial`, TS con `greedy_lookahead_lower_bound` en RCL, SA con `SA.eval = delta`), igual que la 58; la
inserción no entra en ninguna. N5 es el mismo r5 en los dos catálogos, así que la diferencia de gap entre las
corridas (0,36 % contra 0,56 %, cada una contra el mejor conocido de sus propias réplicas) es del tuner, no del
catálogo. Una inserción 1,7× más rápida no alcanza a N5 (230 k contra 222 k pasos/s, pero un vecindario más
grande por paso); lo que movería el resultado es acelerar N5 en la trayectoria.

Por qué N5 no pasó en la 111: su primer intento mejoró solo la trayectoria (1,11×, delta y paso de TS iguales),
la marca de reutilizar en la solución siguiente lo que dejó `apply`; los otros dos llegaron a 1,16× y 1,20×. Pero
preparar una solución nueva es ~40 % del paso (1,85 de ~4,5 µs) y un intercambio cambia las cabezas de todos los
sucesores y las colas de todos los predecesores, así que el techo realista está en 1,2–1,3×, por debajo del 1,5×
pedido. Desde ahora la trayectoria pide el 40 % de la mejora de las demás medidas (1,2× en la primera pasada,
1,08× en las siguientes). No se volvió a correr.

Cuánto habría dado: un N5 1,2× más rápido equivale a 20 % más tiempo. Las tres configuraciones de la run 58 en
ta01–ta10 (15×15, 3 semillas) con 30 s y con 36 s (1,20× iteraciones): 0,705 % contra 0,698 % de gap, diferencia
+0,006 puntos, IC95 [−0,06, +0,06]. Nada medible: a esta altura de la búsqueda el tiempo extra casi no mejora.

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

### Path relinking (PR): un esqueleto genérico que le gana a la TS afinada sin afinarse

Esqueleto `PR` (`skeletons/pr.py`, `path_relinking` en `native/include/hsf/core.hpp`) y slot nuevo `relink`
(`distance(a, b)`, `step(cur, guide, rng)`; el validador exige distancia 0 consigo misma, simetría y que cada paso
la baje hasta llegar a la guía). Población de élite mejorada con tabú (el mismo paso de TS, `hsf::TabuStep`);
caminos entre dos de la población al azar, la mejor solución del tramo central se mejora y reemplaza a la peor si
no está repetida. Nada del problema: la idea de i-TSAB y TS/PR en el job shop y de GRASP con path relinking.

Para el job shop, un relink escrito a mano (`machine_order`): distancia = pares de trabajos ordenados distinto en
alguna máquina; un paso intercambia dos trabajos consecutivos que están al revés que en la guía. Prueba en
ta01–ta10 (15×15), 30 s, 3 semillas, catálogo a mano (N5 con estimate), en este contenedor
(`scripts/pr_vs_ts_taillard.py`, `taillard_pr_handwritten.json`). PR con los parámetros de tabú de la TS r1 de la
run 55 y el resto por defecto (población 10, 2 candidatos por paso del camino, banda 0,25), sin afinar:

| | gap medio | mejor de 3 por instancia | PR 10k mejor por (IC95) |
|---|---|---|---|
| TS afinada (run 55 r1) | 0,97 % | — | +0,50 [+0,16, +0,87], 8 de 10 instancias |
| TS afinada (run 55 r2) | 0,92 % | — | +0,45 [+0,10, +0,88], 7 de 10 |
| PR, 2000 iteraciones de tabú por mejora | 0,71 % | 0,54 % | +0,23 [+0,04, +0,44] |
| **PR, 10000 iteraciones** | **0,47 %** | **0,33 %** | |

Con el catálogo a mano, PR sin afinar queda por debajo de lo mejor del catálogo generado y optimizado con TS
afinada (run 58: 0,75 % de media, 0,55 % la mejor réplica). Es la diferencia que más movió el gap desde el paso a
C++. Pendiente: afinar PR con irace, probar con el catálogo generado y que el LLM escriba el relink.

### Paso 3: el LLM escribe el relink (corrida 112, 0,22 USD)

`llm.native_generator --slots relink` sobre el catálogo C++ existente: el LLM ve la descripción, el modelo C++, el
contrato `hsf::Relink` y cómo PR usa `distance` y `step` (genérico); nada del job shop. 3 de 3 aceptados en una
llamada, sin correcciones: `kendall_adjacent_swap_relink` (la misma idea que el escrito a mano),
`lis_insertion_relink` (distancia = trabajos fuera de la subsecuencia común más larga; un paso inserta uno en su
lugar) y `hamming_position_swap_relink` (posiciones distintas; un paso pone un trabajo en su posición de la guía).

Taillard ta01–ta10, 30 s, 3 semillas, PR con los mismos parámetros que con el relink a mano (sin afinar), ahora
sobre el N5 generado y optimizado (`scripts/pr_relinks_taillard.py`, `taillard_pr_generated.json`):

| | gap medio | mejor de 3 | iteraciones de tabú | TS afinada (run 55 r2) peor por |
|---|---|---|---|---|
| PR + relink a mano + N5 a mano | 0,47 % | 0,33 % | 0,67 M | +0,45 [+0,10, +0,88] |
| PR + **kendall** (LLM) + N5 (LLM) | **0,36 %** | **0,21 %** | 4,0 M | +0,56 [+0,28, +0,90], 9 de 10 |
| PR + **hamming** (LLM) + N5 (LLM) | 0,39 % | 0,21 % | 3,8 M | +0,53 [+0,25, +0,85], 9 de 10 |
| PR + **lis** (LLM) + N5 (LLM) | 0,42 % | 0,25 % | 3,9 M | +0,51 [+0,23, +0,84], 9 de 10 |

Los tres relinks del LLM quedan a la par entre sí y con el escrito a mano (diferencias de 0,06–0,11 puntos, IC95
que cruzan 0). Todo del LLM y del framework (N5, su optimización y el relink), el gap en 15×15 pasa de 0,75 % (run
58, TS afinada) a 0,36 % con PR sin afinar.

### Run 60: irace elige PR en las tres réplicas

Mismas condiciones que las runs 58 y 59, con PR disponible (8 parámetros y los tres relinks del LLM). Las tres
réplicas y todas sus élites son PR: r0 con `hamming` y la inserción optimizada en la corrida 111 (la primera vez
que el tuner la usa), r1 y r2 con `lis` y N5 / N1. Taillard (`taillard_run60.json`; 3 semillas, 30 s; diferencia
por instancia con IC95 bootstrap):

| | run 58 (TS) | run 60 (PR) | 58 − 60 |
|---|---|---|---|
| 15×15, media de configuraciones y semillas | 0,75 % | **0,44 %** | +0,31 [+0,19, +0,42], 9 de 10 |
| 15×15, mejor de 9 por instancia | 0,34 % | **0,01 %** (el óptimo en 9 de 10) | |
| 20×15, media | 1,66 % | 1,57 % | +0,10 [−0,23, +0,32], 8 de 10 |
| 20×15, mejor de 9 | 0,99 % | 0,86 % | |

La mejor réplica (r1: PR con `lis`, N5, población 22, ~15 000 iteraciones de tabú por mejora) da 0,34 % y 1,41 %.
En 15×15 la mejora es clara y el mejor de 9 corridas llega al óptimo en 9 de las 10 instancias; en 20×15 (afinado
en 15×15) mejora poco y sin separarse del ruido. PR sin afinar con `kendall` daba 0,36 % en 15×15: con 10 s por
corrida al afinar, irace prefiere mejoras tabú más cortas que las que convienen con 30 s.

### Run 61: afinar en 20×15 con 15 s

Como la 60 pero con instancias 20×15 y 15 s por corrida (3 h por réplica). Otra vez PR en las tres réplicas, con
mejoras tabú más largas (6000–16 500 iteraciones): r0 y r2 con `lis` y N5, r1 con `kendall` y la inserción
optimizada. Taillard (`taillard_run61.json`; 3 semillas, 30 s):

| | run 58 (TS) | run 60 (PR, 15×15, 10 s) | run 61 (PR, 20×15, 15 s) | 58 − 61 | 60 − 61 |
|---|---|---|---|---|---|
| 15×15, media | 0,75 % | 0,44 % | **0,36 %** | +0,39 [+0,23, +0,56] | +0,08 [−0,01, +0,19] |
| 15×15, mejor de 9 | 0,34 % | **0,01 %** | 0,13 % | | |
| 20×15, media | 1,66 % | 1,57 % | **1,29 %** | +0,38 [+0,20, +0,57] | +0,28 [+0,06, +0,57] |
| 20×15, mejor de 9 | 0,99 % | 0,86 % | **0,76 %** | | |

Afinar más cerca de las instancias de evaluación ayuda en 20×15 (significativo contra las dos) sin perder en
15×15. Mejores réplicas: r1 0,25 % en 15×15, r2 1,17 % en 20×15.

## CVRP en C++ (instancias X de Uchoa)

Modelo por rutas en C++ (`examples/cvrp/native/model.hpp`, lo que ve el LLM), 43 instancias X de 101 a 298
clientes (CVRPLIB vía PyVRP/Instances, `examples/cvrp/uchoa/`, mejores conocidas verificadas) e instancias de
entrenamiento como las X (`CVRPInstance.uchoa_like`, tamaño `x<n>`).

- **Corrida 113** (1,61 USD): 12 de 12 componentes aceptados. Vecindarios granulares (relocate, 2-opt* entre rutas,
  CROSS-exchange; solo hacia los k más cercanos), destrucción radial con reconstrucción con "blinks" (la idea de
  SISR), fusión de rutas cercanas con Split de Prins, tres relinks y tres puntajes greedy.
- **Corrida 114** (3,44 USD, optimización): pasos de trayectoria/s relocate 11,9 k → 21,4 k, 2-opt* 7,0 k → 17,4 k,
  CROSS 2,1 k → 6,3 k.
- **Run 65** (irace en `x150`, 10 s, 3 réplicas; las runs 62–64 fallaron: `pulp` en el target-runner y el límite de
  5 h): VNS en las tres réplicas, con el constructor greedy que empieza por el cliente más lejano.

Instancias X (`scripts/uchoa_eval.py`, `uchoa_run65.json`; 3 semillas, 30 s):

| | 101–149 | 150–199 | 200–298 | las 43 | mejor de 3 |
|---|---|---|---|---|---|
| run 65 r0 (VNS, CROSS) | 1,82 % | 3,14 % | 4,32 % | 3,41 % | 2,99 % |
| run 65 r1 (VNS, CROSS) | 1,96 % | 2,44 % | 3,93 % | 3,08 % | 2,61 % |
| run 65 r2 (VNS, relocate) | 1,66 % | 2,50 % | 3,79 % | 2,94 % | 2,48 % |
| PR sin afinar | 1,53 % | 2,52 % | 4,40 % | 3,23 % | 2,86 % |

Afinar no mejora a PR sin afinar (diferencia +0,09 [−0,35, +0,51]). A ~3 % el resultado está lejos del estado del
arte (HGS, ~0,1–0,3 % en estas instancias). Lo que falta, a la vista del catálogo: no hay un vecindario dentro de
cada ruta (2-opt intra-ruta), la búsqueda local usa un vecindario por vez (HGS combina todos en una sola descenso
granular) y el afinado se hizo con 10 s en 150 clientes.

### Mejoras del framework para el CVRP: vecindario compuesto, ILS con recocido y generación que ve el catálogo

- **Vecindario `composite`** (Python y C++): la unión de todos los vecindarios del catálogo, para revisar todos los
  operadores en el mismo paso (`hsf::Move` tiene un séptimo entero del framework con el vecindario de origen).
- **`ILS.accept = anneal`**: Metropolis con temperatura relativa al objetivo (`ILS.T_rel`), que baja al 1 % al final.
- **Generación que ve el catálogo existente**: el LLM ve el código de los componentes del slot que ya están y se le
  pide cubrir lo que no cubren. Corrida 115 (0,58 USD, 3 de 3): Or-opt intra-ruta con inversión, SWAP* y
  fusión/división de rutas por los extremos, justo lo que faltaba. Corrida 116 (3,35 USD, solo los nuevos con
  `--new-only`): pasos de trayectoria ×2,6–3,0.
- Compilación nativa segura con varios procesos a la vez (`os.replace`).

Prueba rápida (4 instancias X, 20 s, ILS con la destrucción radial): 7,6 % con los parámetros por defecto; 1,95 %
con intensidad 1 y muestra 256; 1,15–1,21 % con recocido (3 vecindarios); 0,85–0,93 % con recocido y los 6.

Run 66 (como la 65: `x150`, 10 s): TS con `composite` en dos réplicas, ILS con recocido y la destrucción radial en
la tercera. Instancias X (`uchoa_run66.json`; 3 semillas, 30 s):

| | 101–149 | 150–199 | 200–298 | las 43 | mejor de 3 |
|---|---|---|---|---|---|
| run 66 r0 (TS, composite) | 1,13 % | 1,81 % | 3,16 % | 2,33 % | 1,98 % |
| run 66 r1 (TS, composite) | 1,29 % | 2,13 % | 3,13 % | 2,42 % | 1,65 % |
| **run 66 r2 (ILS, recocido)** | **0,88 %** | **1,57 %** | **2,07 %** | **1,65 %** | **1,33 %** |
| ILS con recocido sin afinar | 0,92 % | 1,94 % | 2,42 % | 1,92 % | 1,55 % |

Run 65 → run 66 (media de las réplicas): 3,14 % → 2,13 %, −1,01 [−1,29, −0,74], mejor en 39 de 43. El mejor de las
12 corridas por instancia queda a 1,09 %. Sigue lejos de HGS (~0,1–0,3 %), y el gap crece con el tamaño: 30 s es
poco para 200–300 clientes (la regla usual en la literatura da 240–720 s a estas instancias).

### PR con mejora por ILS con recocido (`PR.improve = ils`)

La mejora de PR puede ser ILS con recocido (con la perturbación del catálogo, `PR.strength`, `PR.ls_sample`,
`PR.T_rel`; `PR.ts_iters` pasa a ser iteraciones de ILS) en vez de tabú. En las 4 instancias X de la prueba rápida
(20 s, relink por cadenas de sucesores, el resto como ILS con recocido sin afinar):

| | gap |
|---|---|
| ILS con recocido solo | **0,87 %** |
| PR + ILS, población 6, 1000 iteraciones por mejora | 1,59 % |
| PR + ILS, población 10, 3000 | 1,44 % |
| PR + ILS, población 4, 300 | 1,89 % |
| PR + ILS, población 4, 1000, T_rel 0,005 | 1,47 % |

En el CVRP, combinar soluciones de élite con estos relinks no ayuda: un recocido largo y continuo le gana a
recocidos cortos que reinician desde las soluciones del camino (mezclas peores). En el job shop PR sí ganó con tabú.
La opción queda para que el tuner la elija donde sirva.

### Penalización adaptativa (como HGS): no ayuda en los esqueletos de una trayectoria

`SK.pen_scale`, `SK.pen_adapt`, `SK.pen_target` (SA, ILS, VNS, TS; C++, `PenaltyControl`): la búsqueda corre sobre una
copia del modelo con el peso de las violaciones multiplicado por `pen_scale` y, con `pen_adapt`, ajustado para que la
fracción de soluciones factibles visitadas se acerque a `pen_target` (+20 % / −15 %, nunca por encima del original).
Al cambiar el peso se reconstruyen los componentes (pueden guardar el objetivo de la solución actual) y se devuelve la
mejor solución factible. Los vecindarios generados sí proponen movimientos infactibles y los evalúan con `M.penalty`.

4 instancias X × 3 semillas, 20 s (esta máquina es más lenta que la de las pruebas anteriores: ~27 k iteraciones de
ILS en vez de ~34 k):

| | sin control | adaptativa, desde 0,01 | adaptativa, desde 0,1, objetivo 30 % |
|---|---|---|---|
| ILS con recocido | **1,07 %** | 1,17 % | 1,15 % |
| TS con `composite` | **1,82 %** | 1,90 % | — |

En HGS el peso adaptativo trabaja junto con la población (subpoblaciones factible e infactible, reparación); en una
sola trayectoria, pasar por infactibles no paga. Queda como parámetro del tuner, apagado por defecto.

## CLSP en C++ con el modelo escrito por el LLM, y la matheurística híbrida HYB

**Modelo C++ del LLM** (`llm.native_model_generator`, corrida 117, 0,13 USD, aceptado en la primera ronda): con el
contrato genérico (`native/include/hsf/generic.hpp`) y sin ver ningún modelo escrito. Para el plan de producción con
los setups fijos (un LP en Python) escribió un **flujo de costo mínimo** (primero máxima demanda atendida, después
mínimo inventario): exacto, mismos costos que el LP en todos los casos, ocultos y generados, y 22× más rápido (1650
evaluaciones/s contra 74 en 10×15).

**Componentes C++** sobre ese modelo (corrida 118, 0,62 USD): 8 de 9 (encender/apagar un setup, consolidar lotes en
una ventana; perturbaciones con reparación por flujo, mover y fusionar lotes y reconstruir una ventana con
**Wagner-Whitin**; tres relinks).

**HYB** (`skeletons/hybrid.py`): ILS con recocido (en C++ con `solve_from`, que parte de una solución dada)
alternado con sub-MIPs sobre la parte que libera una destrucción. Prueba rápida, 5 instancias 10×15, 10 s, una
semilla, gap contra la mejor de todas, sin afinar:

| | gap | iteraciones |
|---|---|---|
| ILS (C++) | 2,97 % | 16 |
| **HYB (ILS en C++ + sub-MIP)** | 1,46 % | 33 |
| PR (C++) | 4,46 % | 218 |
| **LNS_MIP (Python, a mano)** | **1,01 %** | 39 |
| FIX_OPT (Python, a mano) | 3,94 % | 172 |

En el CLSP el cuello de botella es evaluar el modelo (un flujo por evaluación): ILS hace 16 iteraciones en 10 s. La
matheurística sigue siendo lo mejor, y HYB queda cerca de LNS_MIP sin afinar.

**Optimización del modelo C++** (`llm.native_model_optimizer`, corrida 119, 0,55 USD, 2 llamadas, las dos pasadas
aceptadas a la primera): misma salida que el modelo aceptado (también en soluciones rotas), red reducida (un nodo por
tramo entre setups) y flujo de costo mínimo primal-dual. Evaluaciones del objetivo/s 1148 → 4453 (×3,9); pasos de
trayectoria de los vecindarios del catálogo 4 → 32 por segundo (×8). La misma prueba rápida (5 instancias 10×15, 10 s):

| | antes | con el modelo optimizado |
|---|---|---|
| ILS (C++) | 2,97 % (16 iter.) | 1,55 % (127 iter.) |
| **HYB (ILS en C++ + sub-MIP)** | 1,46 % | **0,40 %** |
| PR (C++) | 4,46 % | 3,44 % |
| LNS_MIP (Python, a mano) | 1,01 % | 0,86 % |
| FIX_OPT (Python, a mano) | 3,94 % | 3,79 % |

Con el modelo más rápido, la matheurística híbrida con todo generado (modelo, componentes y su optimización) le gana a
la LNS_MIP de Python con los componentes a mano, sin afinar ninguna de las dos.

### Runs 71 y 72: la matheurística con todo generado iguala a la escrita a mano

irace en las mismas condiciones (10×15, 10 s, 10+10 instancias, 3 semillas de test, 3 réplicas). Run 71: lo
generado en C++ (modelo del LLM y su optimización, componentes del LLM), con HYB disponible. Run 72: el catálogo a mano
en Python con todas las matheurísticas. Las tres réplicas de la 71 eligen HYB (con la reconstrucción por Wagner-Whitin
como perturbación y la ventana de períodos como destrucción); las tres de la 72, LNS_MIP. Gap en test contra la mejor
de las seis réplicas en cada instancia (mismas instancias):

| | r0 | r1 | r2 | media |
|---|---|---|---|---|
| run 71, HYB (todo generado, C++) | 0,61 % | **0,17 %** | 0,28 % | **0,35 %** |
| run 72, LNS_MIP (a mano, Python) | 0,44 % | 1,23 % | 0,18 % | 0,61 % |

Diferencia (72 − 71, media de réplicas): +0,26 [−0,24, +0,98]: sin diferencia significativa, la 71 mejor en 4 de 10
instancias. Las mejores réplicas empatan (0,17 % y 0,18 %) y la generada varía menos entre réplicas. El ciclo
completo en C++ (modelo, componentes, optimización y la matheurística híbrida) llega al nivel de la matheurística
escrita a mano, sin una línea de código del problema escrita por una persona.

Las runs 62–64 y 67–70 fallaron en el target-runner de irace: R cambia `LD_LIBRARY_PATH` y el intérprete de Python
del CI cargaba otra libpython (al importar `ctypes`, que usa `pulp`). Arreglado pasándole el entorno del tuner.

## Flow shop de permutación con flowtime total (Taillard), todo generado en C++

Problema nuevo, elegido porque el estado del arte todavía se mueve (ALGirtct, IBS, MRSILS). Instancias de Taillard
(120, `examples/flowshop/taillard/`, de librallu/dogs-pfsp); mejor conocida = mínimo entre la literatura, ALGirtct e
IBS. Protocolo de la literatura: n·m/2·t ms por instancia (`scripts/pfsp_eval.py`). Gap (RPD) contra esa mejor
conocida, que es más exigente que la usada en los papers (sus ARPD están medidos contra la anterior).

- Corrida 120 (0,05 USD): el LLM escribe el modelo C++ (contrato genérico), aceptado a la primera.
- Corrida 121 (1,09 USD): 3 constructores (entre ellos un NEH para flowtime), 3 vecindarios, 3 relinks y 3
  perturbaciones (iterated greedy, inserciones múltiples, mezclar un segmento; revalidadas tras arreglar el validador
  sin vista MIP).
- Corrida 122 (3,64 USD): optimización C++. Los tres vecindarios ×3–4 en pasos de trayectoria (125→495, 251→748,
  246→937); la perturbación iterated greedy ×3,5. Las otras dos perturbaciones no llegaron a 1,5×.
- Tune 73 falló (faltaba `PFSPInstance.save`). Tune 74: irace en 50×10, 10 s, SA/ILS/TS/PR/VNS, 3 réplicas; llegó a
  ~1000 experimentos por réplica pero el job se cortó a las 5 h antes de evaluar en test (cada experimento de 10 s
  tomó ~18 s). Las élites se sacaron de `irace.Rdata` (`pfsp_tune74_elites.json`): todas ILS + iterated greedy +
  recocido con T_rel ≈ 0,03, un solo vecindario (intercambio o inserción con ventana), constructor por prioridades.

t = 60, una semilla, 50_10 / 100_20 (`pfsp_tune74_elites_t60.json`):

| | 50_10 | 100_20 |
|---|---|---|
| r2_83 (irace) | **0,42 %** | **0,98 %** |
| r2_126 (irace) | 0,43 % | 1,03 % |
| ILS_IG sin afinar (NEH, compuesto, T_rel 0,001) | 0,68 % | 1,23 % |
| IGA60 (lit., contra la BKS anterior) | 1,1 % | 1,54 % |
| ALGirtct60 (lit.) | 0,51 % | 1,15 % |
| MRSILS (lit.) | 0,47 % | 0,83 % |

Las 120 instancias, t = 60, una semilla (`pfsp_tune74_full_t60.json`, `pfsp_ils_untuned_full_t60.json`):

| clase | r2_83 | r2_126 | ILS_IG sin afinar |
|---|---|---|---|
| 20_5 / 20_10 / 20_20 | 0,00 % | 0,00 % | 0,00 % |
| 50_5 | **0,36 %** | 0,38 % | 0,45 % |
| 50_10 | **0,39 %** | 0,42 % | 0,61 % |
| 50_20 | **0,27 %** | 0,32 % | 0,79 % |
| 100_5 | 1,10 % | 0,91 % | **0,86 %** |
| 100_10 | 1,29 % | **1,22 %** | 1,38 % |
| 100_20 | 1,10 % | **0,99 %** | 1,13 % |
| 200_10 | 2,12 % | 1,88 % | **1,87 %** |
| 200_20 | 2,61 % | **2,04 %** | 2,10 % |
| 500_20 | 3,71 % | 3,42 % | **2,85 %** |
| media | 1,08 % | **0,97 %** | 1,00 % |

Sin mejores soluciones nuevas. Afinado en 50×10, el algoritmo queda al nivel del estado del arte en las clases de 50
trabajos y empeora en las grandes: los parámetros absolutos (ventana del vecindario, muestra de la búsqueda local) no
escalan con n. Falta afinar en tamaños mezclados (o con parámetros relativos a n) y con más semillas.

### Tune 75: afinar en tamaños mezclados con tiempo proporcional a n·m

irace en 50×10, 100×20 y 200×20 (4+4+4 instancias), `--scale-budget` (2,5 s en 50×10, 10 s en 100×20, 20 s en
200×20, como n·m/2·t), solo ILS, 84×12 experimentos por réplica, 3 réplicas; test con `--baselines defaults` (el tune
74 se había cortado por evaluar ~40 variantes en test). Las tres réplicas eligen ILS + iterated greedy + recocido
(dos con NEH e inserción, una con GRASP por LR e intercambio); 0,33 % en test contra 1,34 % del default.

Las 120 instancias de Taillard, t = 60, una semilla (`pfsp_tune75_full_t60.json`). Para comparar con la tabla de
Libralesso et al. (github.com/librallu/dogs-pfsp, `flowtime_taillard_ARPD.csv`) el gap se mide aquí contra SU
referencia (la mejor conocida de la literatura antes de 2022), no contra la mejor conocida actual:

| clase | r2 (t=60) | r1 | IGA60 | ALGirtct60 | ALGirtct240 | MRSILS (t≈60) |
|---|---|---|---|---|---|---|
| 20_* | 0,00 | 0,00 | 0,00–0,15 | 0,00 | 0,00 | 0,00 |
| 50_5 | **0,21** | 0,31 | 0,64 | 0,47 | 0,31 | 0,28 |
| 50_10 | 0,40 | 0,44 | 1,10 | 0,51 | **0,35** | 0,47 |
| 50_20 | 0,32 | 0,32 | 0,72 | 0,45 | **0,29** | 0,63 |
| 100_5 | 0,49 | 0,78 | 1,17 | 0,99 | 0,81 | **0,22** |
| 100_10 | 0,68 | 0,81 | 1,49 | 1,03 | 0,79 | **0,27** |
| 100_20 | **0,70** | 0,73 | 1,54 | 1,15 | 0,83 | 0,83 |
| 200_10 | 1,07 | 1,33 | 1,27 | 0,86 | 0,64 | **−0,71** |
| 200_20 | 1,13 | 1,10 | 1,09 | 0,70 | 0,39 | **−0,83** |
| 500_20 | 2,33 | 2,44 | 0,49 | 0,63 | 0,24 | **−1,90** |

Con el mismo tiempo (t = 60) el algoritmo generado le gana a ALGirtct60 en todas las clases de 50 y 100 trabajos
(100_20: 0,70 contra 1,15; mejor también que MRSILS ahí) y queda al nivel de ALGirtct con 4 veces más tiempo. En 200
y 500 trabajos sigue lejos: MRSILS y ALGirtct mejoran bastante la referencia y nosotros no. Media contra la mejor
conocida actual: r2 0,82 % (tune 74: 0,97 %; sin afinar: 1,00 %). Sin mejores soluciones nuevas.

## Flow shop con makespan (Taillard): el objetivo de los generadores con LLM

`examples/flowshop_cmax`: mismas 120 instancias, makespan. Mejores conocidas e IGirms (el iterated greedy de Ruiz,
t = 60/120/240) de github.com/librallu/dogs-pfsp. Todo generado como en el flowtime:

- Corrida 123 (0,05 USD): modelo C++ a la primera.
- Corrida 124 (0,83 USD): 11 de 12 componentes. El LLM usó por su cuenta la aceleración de Taillard (NEH con
  aceleración, inserción con aceleración, iterated greedy de destruir y reconstruir con aceleración).
- Corrida 125 (5,03 USD): optimización C++; inserción ×3,8 en delta/s (17,5 → 67 M/s), intercambio ×4, 2-opt ×4,6, el
  iterated greedy ×1,9.
- Framework: `ILS.ls_scope = full` (búsqueda local sobre el vecindario completo en orden, cíclica con primera mejora).
  Con la muestra de 256 movimientos la búsqueda local paraba demasiado pronto y el orden al azar deshacía la
  aceleración (50_10: 1,01 % → 0,35 %; 100_20: 2,36 % → ~1,0 %, sin afinar).
- Tune 76: irace en 50×10, 100×20 y 200×20 con tiempo ∝ n·m (como el tune 75). Las réplicas eligen ILS + iterated
  greedy con aceleración; dos con la inserción con aceleración y `ls_scope = full`.

Las 120 instancias, n·m/2·60 ms, una semilla (`pfsp_cmax_tune76_full_t60.json`), gap contra la mejor conocida:

| clase | r0 | **r1** | r2 | IGirms60 | IGirms120 | IGirms240 |
|---|---|---|---|---|---|---|
| 20_5 / 20_10 / 20_20 | 0,00 | 0,00 | 0,00 | 0,03 / 0,01 / 0,01 | 0,02 / 0,01 / 0,01 | 0,01 / 0,01 / 0,01 |
| 50_5 | 0,00 | 0,00 | 0,00 | 0 | 0 | 0 |
| 50_10 | 0,26 | **0,24** | 0,33 | 0,30 | 0,28 | 0,25 |
| 50_20 | 0,34 | **0,34** | 0,54 | 0,47 | 0,39 | 0,34 |
| 100_5 | 0,00 | 0,00 | 0,00 | 0 | 0 | 0 |
| 100_10 | 0,05 | **0,02** | 0,07 | 0,03 | 0,03 | 0,02 |
| 100_20 | 0,57 | **0,46** | 0,73 | 0,62 | 0,52 | 0,44 |
| 200_10 | 0,04 | 0,04 | 0,04 | 0,03 | 0,03 | 0,03 |
| 200_20 | 0,69 | **0,53** | 0,77 | 0,66 | 0,57 | 0,51 |
| 500_20 | 0,36 | 0,36 | 0,37 | 0,29 | 0,26 | 0,24 |
| media | 0,19 | **0,17** | 0,24 | 0,20 | 0,18 | 0,16 |

Con el mismo tiempo, r1 le gana al iterated greedy de Ruiz en 50_10, 50_20, 100_20 y 200_20 y queda al nivel de
IGirms con el doble de tiempo (media 0,17 contra 0,18); solo en 500_20 queda detrás. Ojo: IGirms se corrió en otra
máquina (la de Libralesso et al.); falta repetir con varias semillas.

Contra EoH (Liu et al., ICML 2024, apéndice D.3): su gap es contra las cotas de los encabezados de sus instancias
(`eoh_upper_bounds.json`, 0,30 % por encima de la mejor conocida actual en promedio) con 60 s por instancia. Contra
esas mismas cotas, con n·m/2·60 ms (3 s en 20×5, 15 s en 50×10, 60 s en 100×20):

| clase | r1 | EoH |
|---|---|---|
| 20_5 / 20_10 / 20_20 | −0,05 / −0,01 / 0,00 | 0,09 / 0,30 / 0,10 |
| 50_5 / 50_10 / 50_20 | 0,00 / −0,24 / −0,22 | 0,02 / 0,19 / 0,60 |
| 100_5 / 100_10 / 100_20 | −0,05 / −0,02 / −0,56 | −0,04 / 0,14 / 0,41 |
| 200_10 / 200_20 | 0,02 / −0,51 | 0,12 / 0,61 |
| media (110 instancias) | **−0,15** | 0,23 |

Mejor en las 11 clases, con menos tiempo en casi todas. Sin mejores soluciones nuevas.

Tune 76 r1 con 3 semillas (`pfsp_cmax_tune76_full_t60.json` semilla 0, `pfsp_cmax_tune76r1_seed1.json`,
`pfsp_cmax_tune76r1_seed2.json`), media por clase de las tres (entre paréntesis, cada semilla):

| clase | r1 (3 semillas) | IGirms60 | IGirms120 | IGirms240 |
|---|---|---|---|---|
| 50_10 | **0,24** (0,24 0,27 0,23) | 0,30 | 0,28 | 0,25 |
| 50_20 | **0,29** (0,34 0,29 0,25) | 0,47 | 0,39 | 0,34 |
| 100_10 | 0,02 (0,02 0,03 0,02) | 0,03 | 0,03 | 0,02 |
| 100_20 | **0,39** (0,46 0,40 0,32) | 0,62 | 0,52 | 0,44 |
| 200_10 | 0,04 (0,04 0,04 0,04) | 0,03 | 0,03 | 0,03 |
| 200_20 | **0,55** (0,53 0,56 0,56) | 0,66 | 0,57 | 0,51 |
| 500_20 | 0,31 (0,36 0,27 0,30) | 0,29 | 0,26 | 0,24 |
| media (120) | **0,155** (0,166 0,156 0,143) | 0,204 | 0,177 | 0,155 |

Con el mismo tiempo que IGirms60, el algoritmo generado iguala a IGirms con 4 veces más tiempo; las tres semillas
quedan por debajo de IGirms60 y de IGirms120.

### Flowtime en instancias grandes: vecindarios acotados (corridas 126–127, tune 77)

Con una indicación explícita del investigador (`--hint`, registrada en `stats_neighborhood.json`): en flowtime una
inserción cuesta O(n·m) y no hay aceleración de Taillard, así que se pidieron vecindarios acotados con anchos
relativos a n. Corrida 126 (0,44 USD): 3 de 3 aceptados (reubicación de bloques en ventana, reordenar una ventana por
reglas, intercambio de bloques no contiguos), con parámetros relativos (`win_frac`, `len_frac`). Corrida 127 (3,89
USD, medida en 500×20 con `bench_size`): ×8–13 en pasos de trayectoria. Tune 77 (50×10, 200×20, 500×20, base 1 s):
ninguna réplica elige los vecindarios acotados; todas eligen `ls_scope = full` acotada por tiempo. En t = 60
(`pfsp_large_t77_r0.json`): 100_20 0,84 % (tune 75: 1,00 %), 200_20 1,95 % (1,92 %), 500_20 2,78 % (2,86 %). Acotar
reduce cuántos movimientos se miran pero no el costo de cada uno; en 200 y 500 trabajos sigue la distancia con
MRSILS y ALGirtct.

### Cierre del flow shop

- Makespan: todo generado (modelo, componentes con la aceleración de Taillard y su optimización). Con 3 semillas y el
  tiempo de IGirms60, 0,155 % medio en las 120 instancias: igual que IGirms con 4 veces más tiempo, por delante en
  50_10, 50_20, 100_20 y 200_20. Contra las cotas de EoH, −0,15 % frente a su 0,23 %, mejor en las 11 clases con
  menos tiempo.
- Flowtime: competitivo hasta 100 trabajos (por delante de ALGirtct60 en todas esas clases, al nivel de ALGirtct240);
  en 200 y 500 trabajos queda 2–4 puntos detrás de MRSILS: el costo por movimiento y la falta de aceleraciones
  específicas, que el LLM no encontró ni con la indicación explícita.
- Lo que aportó el framework: `ls_scope = full` (búsqueda local completa en orden), tuning en tamaños mezclados con
  tiempo ∝ n·m (`--size a,b,c --scale-budget`), baselines de test baratos, `--hint` y `bench_size`.

## CLSP en instancias de la literatura: Trigeiro, Thomas y McClain (1989)

Instancias de strIPlib (`lotsizing/single-level/trigeiro/textbook`, LP de Zimpl) convertidas al formato del CLSP
(`examples/lotsizing/trigeiro_convert.py`): 68 F (6×15; F19N viene dañada) y las G30, G30b, G53, G57, G62, G69, G72.
Es el mismo modelo; en las G el tiempo por unidad ≠ 1 se absorbe midiendo cada ítem en unidades de tiempo (validado:
G30 da el mismo óptimo, 37 809, desde el LP original y desde la conversión). Referencias: CBC 600 s sobre los LP
originales (`trigeiro/cbc.json`: óptimo probado en 66 F, G30 y G30b) y, para las G, la tabla 9 de Degraeve y Jans
(ERS-2003-010-LIS, versión de trabajo de Operations Research 2007) con el branch-and-cut de Belvaux y Wolsey (2000,
900 s) y su branch-and-price (`trigeiro/reference.json`). Configuraciones: las 3 réplicas del tune 71 (HYB con todo
generado, afinado en instancias al azar de 10×15 con 10 s), sin re-afinar; 60 s por instancia, una semilla
(`scripts/clsp_trigeiro_eval.py`).

Instancias G, gap contra la mejor conocida (%):

| | G30 | G30b | G53 | G57 | G62 | G69 | G72 | media sin G30 |
|---|---|---|---|---|---|---|---|---|
| Belvaux y Wolsey (B&C, 900 s, 200 MHz) | – | 0,00 | 0,00 | 0,01 | 0,00 | 1,08 | 0,01 | 0,18 |
| Degraeve y Jans (B&P, 750 MHz) | 0,00 | 1,17 | 0,32 | 0,00 | 1,36 | 0,00 | 0,00 | 0,47 |
| CBC 600 s (hoy) | 0,00 | 0,00 | 0,72 | 1,65 | 1,59 | 4,31 | 5,13 | 2,23 |
| HYB generado r0 (60 s) | 0,64 | 0,12 | 0,99 | 0,68 | 0,15 | 0,47 | 1,66 | 0,68 |
| HYB generado, mejor de 3 réplicas | 0,33 | 0,00 | **−0,09** | 0,68 | 0,15 | 0,47 | 1,66 | 0,48 |

En G53 la réplica r2 encuentra 74 729, mejor que lo publicado por Belvaux y Wolsey (74 799) y Degraeve y Jans
(75 035).

Instancias F (68, contra el óptimo de CBC; `clsp_trigeiro_F_run71_60s.json`): r1 0,10 % medio y el óptimo en 49 de
68; r2 0,19 % (34 óptimos); r0 1,13 % (22 óptimos; una corrida infactible en F3N); la mejor de las 3, 0,04 % (52
óptimos).

Sin re-afinar para estas instancias ni tamaños, el HYB generado queda a la altura de los métodos exactos de los 2000
con el mejor de 3, muy por delante de CBC actual con 10 veces menos tiempo, pero detrás del branch-and-cut de Belvaux
y Wolsey; la variación entre réplicas es grande (r0 falla en F3N), así que falta afinar en tamaños de Trigeiro.
