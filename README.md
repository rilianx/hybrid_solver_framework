# Núcleo — Solvers híbridos generados por LLM

Implementación del ítem 1 del plan de trabajo de la propuesta
(`propuesta_solvers_hibridos_llm.md`, §9): *"definir los Protocols de
los slots, el esqueleto genérico y tres especializaciones (SA, ILS,
LNS-MIP). Exportador del espacio de configuración a irace y Optuna."*

## Qué hay implementado

- **`core/contracts.py`** — Protocols de `ProblemModel` (§3, el puente
  heurístico/matemático) y de cada slot de la tabla de la §4:
  Constructor, Vecindario, Evaluador, Aceptación, Memoria,
  Perturbación, Destrucción, Reparación heurística, Reparación MIP,
  Política de fijación, Parada.
- **`core/component.py`** — `ComponentSpec`/`ComponentRegistry`: valida
  y registra el bloque de metadatos `COMPONENT` (§4) que cada
  componente generado por el LLM debe declarar.
- **`core/skeleton.py`** — `TrajectorySkeleton`: el único bucle de
  control del núcleo, exactamente el pseudocódigo de la §2. SA, ILS y
  LNS-MIP no reimplementan el bucle: solo configuran su
  `candidate_generator` y `state_updaters`.
- **`core/common_components.py`** — Aceptación (mejor-siempre,
  aceptar-siempre, umbral) y Parada (iteraciones, tiempo, sin-mejora)
  de propósito general, reusables por cualquier problema.
- **`skeletons/sa.py`, `skeletons/ils.py`, `skeletons/lns_mip.py`** —
  Las tres especializaciones pedidas. `ils.py` incluye además
  `hill_climb`, la búsqueda local interna reusable como slot "LS" de
  ILS.
- **`config_space/`** — `build_config_space` arma el espacio
  jerárquico y condicional de la §8 (raíz `skeleton`, un parámetro
  categórico por slot condicionado a qué esqueletos lo usan, y los
  parámetros propios de cada componente condicionados a su elección).
  `irace_export.py` lo traduce a `parameters.txt`; `optuna_export.py`
  lo recorre en modo *define-by-run* contra cualquier objeto
  `trial`-like (Optuna real o un doble de prueba).
- **`core/mip.py`** — `MIPModel`: la interfaz mínima
  (`variables()`, `solve(fixed, integer, relaxed, time_limit)`) que las
  matheurísticas exigen a lo que devuelve `ProblemModel.build_mip`.
  Es el único punto de contacto con el solver (PuLP/CBC hoy).
- **`core/fixing_policies.py`** — `SlidingWindowPolicy` (agenda de
  Relax-and-Fix con ventana y solapamiento) y `consecutive_blocks`
  (bloques de Fix-and-Optimize), genéricas sobre `variable_groups`.
- **`skeletons/relax_and_fix.py`** — `RelaxAndFixConstructor`: cumple
  el `Protocol` `Constructor`, así que ocupa el slot `constructor` de
  cualquier otro esqueleto (el híbrido Relax-and-Fix → Fix-and-Optimize
  de §5.2 sale gratis).
- **`skeletons/fix_and_optimize.py`** — `build_fix_and_optimize`:
  LNS-MIP con destrucción estructurada por bloques, sobre el mismo
  `TrajectorySkeleton`.
- **`skeletons/ts.py`, `vns.py`, `grasp.py`, `local_branching.py`** — Los
  esqueletos restantes de §5: Tabu Search (con `TabuMemory` genérica sobre
  movimientos hashables, tenencia y aspiración; prohíbe el inverso si el
  vecindario expone `inverse(m)`), VNS (lista ordenada de vecindarios para
  el shake, LS con `hill_climb`, k cíclico en `state.extra`), GRASP+LS
  (reinicios: construir con `rng` + LS, conservar el mejor) y Local
  Branching (el `MIPModel` acepta `near=(x̄, k)`: Σ|x−x̄| ≤ k; k crece con
  `k_step` si no hay mejora y vuelve a k0 si la hay). Todos son
  configuraciones del mismo `TrajectorySkeleton`, registrados en
  `Assembler.SKELETONS`.
- **`skeletons/mip_perturbation.py`** — MIP-guided Perturbation (§5.2): ILS cuya
  perturbación resuelve el MIP. La destrucción elige la zona, se fijan al valor
  contrario `flips` variables de la zona que estaban en 1 (obliga a moverse), el
  sub-MIP acomoda el resto y después hace búsqueda local el vecindario. Con él son
  9 esqueletos en el espacio de diseño.
- **`core/problem_pack.py`** — `ProblemPack`: lo que el framework recibe de un
  problema (ProblemModel, catálogo de referencia, spec para el LLM, contextos de
  validación, generador de instancias, partida trivial). `llm.catalog`, `llm.cli`,
  `llm.model_cli` y `tuning.cli` son genéricos sobre el pack; hay dos:
  `examples/lotsizing/pack.py` (CLSP) y `examples/cvrp/pack.py` (CVRP).
- **`core/validation/`** — Las cinco capas de validación autónoma de §7:
  *sintáctica* (import, esquema `COMPONENT`, métodos del Protocol del
  slot), *contractual* (propiedades de la tabla §4 por slot, muestreadas
  sobre micro-instancias con semillas fijas: `undo∘apply = id`, `delta`
  consistente, `free_vars ⊆ variables`, `repair_mip` respeta fijas y no
  empeora, agenda de fijación es partición y cubre todo, parada eventual…),
  *semántica MIP* (la solución trivial fijada en el MIP es factible, su
  objetivo coincide con el heurístico, óptimo MIP vs fuerza bruta en
  micro-instancias), *operativa* (corre bajo presupuesto en un hilo con
  timeout, sin excepciones ni fugas de tiempo; `repair_mip` respeta
  `time_limit`) y *calidad mínima* (mejora al constructor aleatorio y no es
  inerte). `ValidationReport.feedback()` es el texto que se devuelve al LLM
  para corregir (§6). Se detiene en la primera capa que falla. Tras la capa
  contractual, `check_component_quality` aplica un gate de *sentido* por
  slot (constructor no mucho peor que la solución trivial; vecindario con
  al menos un movimiento de mejora desde soluciones típicas y aleatorias;
  `strength`/`ratio` monótonos en perturbación/destrucción): la primera
  corrida real con `gpt-5.4-mini` aceptó 12/12 componentes a la primera,
  lo que mostró que la capa contractual sola detecta errores de
  implementación pero no de diseño. Tras la segunda corrida (11/12, 7
  rechazos; ver `claude/resultados_generacion_llm.md` en el proyecto) se
  agregaron: **feedback con detalle de infactibilidad** (el `ProblemModel`
  puede exponer `explain_infeasibility(sol)`; para el CLSP dice ítem, período
  y cantidad faltante y recuerda la regla sin-backlog — lo que le faltó al
  constructor abandonado tras 3 rondas); **modo estricto para vecindarios**
  (`require_improving_from_start`: en generación exige mejoras desde la
  solución de partida, no solo desde aleatorias; los tres vecindarios
  generados que resultaron inertes en SA ahora se rechazan y vuelven al
  modelo con la explicación, pero el catálogo los admite en modo leniente
  porque su utilidad en combinación la decide el tuning); y **solución trivial
  garantizada factible** en los micro-contextos (lot-for-lot o, si no alcanza
  la capacidad, Relax-and-Fix). El prompt de vecindarios y perturbaciones
  ahora incluye una micro-instancia con su solución de partida dibujada.
  Tras la corrida 5 (9/12; vecindarios 0/3 → 3/3 con el gate agregado "basta un
  contexto") se corrigieron dos cosas más: `explain_infeasibility` **distingue
  capacidad saturada de setup faltante** ("el período 1 está SATURADO, usa 43,0 de
  41,3: no falta un setup, falta ADELANTAR producción a t=0, que tiene 41 libres"),
  porque tres constructores murieron por 1,67 unidades sin que el mensaje dijera
  dónde estaba la holgura; y el umbral del gate de constructor pasó a ser
  configurable con default laxo (`constructor_max_relative_gap = 1.0`), porque la
  referencia puede ser Relax-and-Fix (basada en MIP) y el 25% anterior le exigía a
  un greedy calidad de matheurística — además hacía que el generador cortara en ese
  reproche de calidad y nunca reportara la infactibilidad real de otra instancia.
  Y el hallazgo con más filo de la corrida 5: con el gate estricto los vecindarios
  pasaron de inertes (+0,0%) a **útiles** (+30,3% a +30,9%, dos de ellos por encima
  del `setup_flip` escrito a mano), pero la **diversidad se derrumbó** (Jaccard
  0,75–1,00 entre sí y con el de referencia). Exigir mejora desde la partida embudona
  al modelo hacia el único movimiento elemental que funciona. De ahí
  **`core/validation/diversity.py`** y el gate `<slot>.distinct_from_accepted`: firma
  estructural del componente (vecinos alcanzables desde una solución fija; conjuntos
  de `free_vars`; soluciones perturbadas) comparada por Jaccard contra los ya
  aceptados **y contra el catálogo existente**, con un mensaje que pide una idea
  algorítmica distinta y enumera ejes por los que variar. `benchmark_components`
  reutiliza las mismas firmas.
- **`llm/`** — Ciclo generar → validar → corregir de §6, como funciones
  planas (sin framework de orquestación por ahora; ver nota abajo).
  `client.py`: `LLMClient` intercambiable con `OpenAIClient`
  (default `gpt-5.4-mini`, Responses API), `AnthropicClient`,
  `ScriptedClient` (tests) y `TranscriptClient` (graba cada llamada).
  `prompts.py`: un prompt por slot con el `Protocol` exacto extraído del
  código, las propiedades que verificará el validador, un ejemplo few-shot
  de *otro* problema (knapsack, `fewshot.py`), la descripción del problema
  (`ProblemSpec`) y pedido explícito de diversidad; el prompt de corrección
  reenvía el módulo y el `feedback()`. `parser.py`: extrae los bloques
  ```python```, lee `COMPONENT["name"]` por AST y guarda cada módulo por
  ronda. `generator.py`: `generate_slot` y `GenerationStats` (aceptados,
  rechazos por capa, rondas por componente, llamadas y segundos de LLM —
  lo que §9.3 pide medir). Convención de módulo generado: `COMPONENT` +
  clase + `build_component(problem, **params)`.
- **`core/assembler.py`** — El pegamento de §8: `Assembler(problem_factory,
  registry)` conoce qué slots y parámetros propios tiene cada esqueleto
  (`SKELETONS`: SA, ILS, LNS_MIP, FIX_OPT, TS, VNS, GRASP, LOCAL_BRANCH), construye el `ConfigSpace`
  completo a partir del catálogo, y dado un punto del espacio
  (`{"skeleton": ..., "<slot>": <componente>, "<componente>.<param>": ...}`)
  instancia los componentes con `ComponentSpec.make(problem, **params)` y
  arma la variante con `MaxTimeStop(budget)`. `evaluate(config, instancias,
  budget)` es el *target runner*: costo medio, penalizado si la variante
  falla o devuelve infactible. Convención: todo componente del catálogo es
  una fábrica `impl(problem, **params)` (la misma `build_component` de los
  módulos generados por LLM), así los generados entran sin adaptación
  (`llm.register_generated`).
- **`examples/lotsizing/catalog.py`, `random_search.py`** — catálogo del
  CLSP (componentes a mano como fábricas + generados aceptados, recargados y
  revalidados desde `generated/clsp/`) y una búsqueda aleatoria sobre el
  espacio completo: el baseline contra el que se compararán irace/Optuna.
- **`examples/lotsizing/llm_spec.py`, `generate.py`** — `ProblemSpec` del
  CLSP, micro-contextos de validación, y CLI que genera con un LLM real
  (`OPENAI_API_KEY` u `--provider anthropic`) dejando módulos, transcripción
  y `stats.json` en `generated/clsp/`.
- **`examples/knapsack/`** — Primer piloto (mochila 0/1), el problema
  más simple posible para ejercitar SA / ILS / LNS-MIP y el export a
  irace/Optuna.
- **`examples/lotsizing/`** — Piloto con estructura temporal (§9.2):
  CLSP multi-ítem capacitado. Vista estructural = matriz de setups;
  `objective` resuelve el LP de cantidades/inventarios con setups fijos
  (cacheado) y penaliza faltantes; `variable_groups` = períodos. Incluye
  destrucción por ventana de períodos y un generador de instancias al
  estilo Trigeiro et al. (utilización 0.9–0.98, TBO vía EOQ, tiempos de
  setup) que CBC no cierra en 30 s. La demo compara, con el mismo
  presupuesto de tiempo de pared por variante, lot-for-lot, Relax-and-Fix,
  SA, ILS, LNS-MIP (destrucción aleatoria vs por ventana), Relax-and-Fix →
  Fix-and-Optimize y el MIP completo.
- **Representaciones alternativas** — cada representación de la solución es
  un problema distinto para el framework (su pack, sus componentes, su
  tuning), descrita en `ModelSpec.representation`; las variantes de un
  problema comparten instancia y casos de prueba, así que sus costos se
  comparan directamente (`scripts/compare_packs.py`). Primera variante:
  `examples/cvrp/tour_parts.py`, el CVRP como gran tour + Split (Prins), una
  representación con decodificador (`ModelSpec.decoder`): el validador exige
  que la decodificación no sea peor que la respuesta del caso y acepta que
  una respuesta infactible no sea representable.
- **Ciclo completo** (`llm/cycle.py`; diagrama de estados en
  [`docs/ciclo_completo.md`](docs/ciclo_completo.md)) — de la descripción y los casos a un
  solver afinado, por representación: `model` genera el ProblemModel por
  piezas, `components` genera desde cero constructores, vecindarios,
  perturbaciones y destrucciones sobre ese modelo (el LLM ve el código de las
  piezas), `tune` afina con el tuner de siempre. El pack de cada variante se
  arma sobre las piezas (`parts_pack`) con las instancias y casos del pack base
  (`ProblemPack.variants`); `--reference` usa las piezas de referencia. En
  Actions: input `variant` de `generate.yml` y `tune.yml`. La vista
  constructiva es la tercera etapa de la generación del modelo por piezas
  (`empty_partial`, `candidates`, `apply_action`, …; validada con
  construcciones al azar que deben dar siempre soluciones factibles): con ella
  el ciclo genera puntajes para el constructor greedy modular. Etapa opcional
  `optimize` (`llm/optimizer.py`): versiones más rápidas del modelo y de los
  componentes aceptados, que se aceptan solo si dan las mismas salidas que la
  versión aceptada (pruebas diferenciales, `core/validation/equivalence.py`) y
  son al menos 1,5 veces más rápidas. `scripts/throughput.py` mide la velocidad
  de un catálogo; `scripts/reevaluate_configs.py` reevalúa en test lo que eligió
  una corrida de tuning con el catálogo actual, sin volver a afinar.
  Reparación localizada (`llm/patching.py`): en cada corrección (componentes,
  etapas del modelo por piezas, optimización) el LLM devuelve solo las
  funciones o métodos que cambia; se reemplazan por nombre en el módulo
  rechazado (los métodos dentro de su clase, las definiciones nuevas se
  agregan) y el módulo entero se vuelve a validar. Una respuesta que trae el
  módulo completo lo reemplaza. El `undo` de los vecindarios es opcional.
  La optimización exige además memoria acotada (`core/validation/resources.py`):
  la memoria retenida no puede crecer al evaluar soluciones nuevas (una caché
  `lru_cache(maxsize=None)` de módulo agotó los runners en la run 34).
- **`core/beam_search.py`, esqueleto `CONSTRUCT`, vista MIP opcional y `examples/cpmp/`** —
  estrategias constructivas y un problema sin formulación MIP en el ciclo (ver *Estrategias
  constructivas*).
- **`examples/validation_demo.py`** — componentes correctos y rotos pasando
  por las capas, con el feedback que recibiría el LLM.
- **`tests/`** — 273 tests (`pytest`): contratos, esqueleto genérico,
  exportadores, políticas de fijación, verificación cruzada heurística↔MIP,
  integración de ambos pilotos con el sub-MIP real, y las capas de
  validación aceptando componentes correctos y rechazando rotos (delta mal
  calculado, undo incorrecto, destrucción que inventa variables, sub-MIP
  que ignora fijas, parada que nunca llega, fuga de tiempo, variante inerte),
  el ciclo LLM con un cliente guionado (componente correcto + roto en la
  ronda 1, corrección en la ronda 2, abandono tras `max_rounds`), y el
  ensamblador (default de cada esqueleto corre, configs muestreadas del
  espacio se evalúan, configs inválidas se penalizan, un componente generado
  entra al catálogo, aparece en el espacio y se recarga desde disco).

## Cómo correr

```bash
pip install -r requirements.txt
python -m examples.knapsack.demo    # SA / ILS / LNS-MIP + export irace/Optuna
python -m examples.lotsizing.demo   # CLSP Trigeiro 15×20, 20 s por variante (~3 min)
python -m examples.lotsizing.demo --easy
python -m examples.validation_demo  # capas de validación con componentes rotos
python -m examples.lotsizing.random_search --configs 12 --budget 5   # espacio completo, target-runner
python -m pytest -q                 # 273 passed (~265 s)

# segundo problema: CVRP con flota libre (mismos CLI, otro pack)
python -m examples.cvrp.tune --catalog handwritten --size 30 --trials 30 --ref-time 60

export OPENAI_API_KEY=...
python -m examples.lotsizing.generate --slots neighborhood destruction --n 3   # generación real
python -m examples.cvrp.generate --from-scratch --slots greedy_score neighborhood destruction perturbation
python -m examples.cvrp.generate_model    # el ProblemModel completo (§6.1), con chequeo cruzado contra el de mano
# desde cero: sin ver los componentes escritos a mano (ni diversidad contra el catálogo, ni pistas de setup_flip)
python -m examples.lotsizing.generate --from-scratch --workspace generated/clsp_scratch --slots neighborhood destruction constructor perturbation
# con planificador: ideas en texto, implementación y corrección en paralelo, diversidad al unir
python -m examples.lotsizing.generate --planner --workers 3 --replans 1 --slots neighborhood destruction constructor perturbation

# opcional: precios en USD por millón de tokens, para estimar el costo de la corrida
export LLM_PRICE_IN=0.25 LLM_PRICE_OUT=2.00

# tuning real (§8): Optuna sobre el espacio completo, con y sin componentes LLM,
# evaluado en instancias de TEST; --irace escribe además un escenario irace
python -m examples.lotsizing.tune --trials 40 --budget 5 --train 3 --test 3 --catalog both --irace tuning_out/irace
# solo generados vs a mano vs ambos (--catalog three), con los generados desde cero
python -m examples.lotsizing.tune --catalog three --generated generated/clsp_scratch --skeletons SA ILS VNS --ref-time 60
# esqueleto fijo: compara cada componente generado contra el de mano en igualdad de condiciones
python -m examples.lotsizing.tune --skeletons SA ILS VNS --trials 40 --budget 20 --items 20 --periods 20 --ref-time 60
```

**Tuner.** `tuning/` conecta `Assembler.config_space()` (el espacio) con
`Assembler.evaluate()` (el target runner). `tune_with_optuna` corre TPE
define-by-run sobre el espacio condicional (`suggest_from_space`), encolando el
default de cada esqueleto como primeros trials: el tuner no puede quedar por
debajo de "elegir el esqueleto por defecto", y si queda, es un hallazgo.
`evaluate_on_test` mide la configuración ganadora en instancias que el tuner no
vio, con varias semillas, contra el default de cada esqueleto: el costo de train
del ganador es optimista por construcción y la pregunta de §10 —¿el catálogo
ampliado **ayuda o diluye**?— solo se responde ahí. `examples.lotsizing.tune`
hace las dos corridas (`handwritten` / `all`) y escribe `tuning_out/comparison.json`.
El costo de un trial es la media por instancia de `costo / lot-for-lot`
(`--objective ratio`, el default; `raw` es el costo medio en bruto), porque en la
primera corrida de 60 trials una sola instancia dominaba la varianza. En test,
cada configuración se resume además como **gap relativo por instancia** contra la
mejor solución conocida: el mínimo entre todas las corridas de test de ambos
catálogos y, con `--ref-time S`, el MIP completo con S segundos
(`tuning.best_known_costs`). Con `--skeletons SA ILS …` el espacio se restringe a
esos esqueletos y los baselines de test pasan a ser una variante por componente de
cada slot, con los demás slots en su default (`tuning.one_slot_baselines`). Es la
comparación que el espacio completo no da: con presupuestos cortos siempre gana un
matheurístico y el tuner descarta los vecindarios y perturbaciones generados por el
esqueleto, no por su calidad. `mip_time_share` (LNS_MIP, FIX_OPT, LOCAL_BRANCH) ya
no tiene piso de 1 s: con 5 s de presupuesto todo su rango antiguo caía en 1–2 s y
el parámetro era inerte; el rango nuevo, log [0.04, 1], mantiene como default el
1 s que se usaba de hecho.
Para irace, `tuning.irace_scenario` genera `parameters.txt`, `instances.txt`,
`scenario.txt` y el `target-runner` (`scripts/irace_target_runner.py`, que
parsea `--param=valor` con los tipos del espacio); irace corre afuera, en R.

**Contador de tokens.** Cada cliente que la API informa (`OpenAIClient`,
`AnthropicClient`) acumula `TokenUsage` —entrada, salida, entrada servida desde
caché y tokens de razonamiento— y `GenerationStats.tokens` los suma por slot,
incluidas las rondas de corrección. Van a `stats.json` (por slot y en `_run`,
con el total de la corrida), a la tabla de `scripts/stats_summary.py` y a cada
`transcript/call_NNN.json`. Los precios **no** están cableados, porque cambian y
dependen del proveedor: si defines `LLM_PRICE_IN` / `LLM_PRICE_OUT` (USD por
millón de tokens) se agrega el costo estimado; si no, se informan solo los
tokens. Un cliente que no cuenta tokens (`ScriptedClient` en los tests) deja el
contador en cero sin romper nada.

**Validación por combinación** (`core/validation/combination.py`). Tras las capas aisladas,
cada vecindario y cada perturbación se prueban en la sonda 10×15 dentro de cada esqueleto que
declaran, desde lot-for-lot y desde el constructor greedy. En SA, VNS, TS y GRASP el
vecindario corre 1 s y se mide su aporte sobre el mismo esqueleto con un vecindario nulo. En
ILS esa resta mezclaba velocidad con aporte, así que el vecindario se mide por lo que hace
ahí: cuánto mejora su búsqueda local (con muestreo) la partida y perturbaciones factibles de
ella. La perturbación se juzga por capacidad: desde un óptimo local de cada partida, qué
fracción de patadas seguidas de búsqueda local termina en otra solución factible (medir la
mejora de un ILS de pocos segundos no discriminaba). Se quitan de `compatible_skeletons` los
esqueletos sin aporte desde ninguna partida y, si no queda ninguno, se rechaza; si no aporta
con los parámetros por defecto se prueban tres configuraciones al azar. Los aportes quedan en
`stats.json` (`combinations`). Se usa en la generación y en la admisión al catálogo.

**Muestreo de vecindarios** (`core/neighborhood.py`). Los esqueletos piden movimientos con
`random_move` (SA, shake de VNS) y `sample_moves` (búsqueda local, TS) en vez de recorrer
`moves` completo. Un vecindario puede implementar `sample(sol, k, rng)` si sabe muestrear sin
enumerar (el validador lo verifica); si no, se enumera y se muestrea. La búsqueda local de
ILS, VNS y GRASP evalúa muestras de `ls_sample` movimientos (parámetro del esqueleto, 4–256,
default 32). Motivo: cuando `delta` cuesta un LP, el recorrido completo cortado por tiempo
evaluaba siempre los mismos primeros movimientos; con `setup_flip` en 10×15 y 5 s, desde
lot-for-lot, ILS pasa de 39 % a 21 % de gap y VNS de 39 % a 18 %.

**Diversidad contra el catálogo** (`generate.py --catalog-diversity`). Por defecto
(`annotate`) la diversidad se exige solo entre los componentes de la misma corrida, y el
parecido de cada aceptado con el catálogo se anota en `stats.json` (`catalog_overlap`) sin
rechazarlo: los dos quedan en el catálogo y el tuner elige. `reject` es el comportamiento
anterior. Motivo: en las runs de tuning 5 y 6, el gate contra el catálogo habría rechazado un
`setup_flip` reinventado que rinde mejor que el original.

**Constructor modular** (`core/construction.py`, slot `greedy_score`). El bucle greedy y la
regla de selección (`greedy`, RCL-α de GRASP, `roulette`) son del framework; el problema aporta
una vista constructiva (`ConstructionView`: estado parcial, candidatos, aplicar, completo y un
cierre de respaldo) y el LLM genera solo el puntaje de una acción. Cada puntaje entra al
catálogo como constructor `greedy_<nombre>` con la regla y α como parámetros del tuner. En el
CLSP la acción es "cubrir demanda pendiente de (i, t) produciendo en s ≤ t", recorriendo los
deadlines en orden, y los candidatos se filtran con una condición necesaria de capacidad
acumulada (con tiempos de setup, decidir si un parcial se puede completar es NP-completo); el
cierre de respaldo fija los setups decididos y resuelve el resto con el MIP. En 360
construcciones de prueba (Trigeiro 0,95 y 0,98, instancias aleatorias, hasta 20×20) no hizo
falta el respaldo ni una vez.

**Planificador** (`llm/planner.py`, `--planner`). Un planificador propone las ideas de
cada slot en texto, sin código; cada idea se implementa, valida y corrige en paralelo con
la idea fija en el prompt de corrección, y el gate de diversidad se aplica al unir (si
faltan componentes se replanifica, mostrando las ideas aceptadas y las descartadas con su
motivo). Los slots también corren en paralelo. Usa hilos: la validación pesada es CBC, que
corre como proceso aparte, y los clientes guardan `last_usage` por hilo.

Sobre orquestación: el ciclo es un bucle determinista corto, así que se
implementó en Python plano. Si más adelante el flujo se vuelve un grafo
(ramas paralelas por slot, decisión diversidad-vs-corrección según tasas,
checkpoints de sesiones caras, paso humano), cada función de `llm/generator.py`
es directamente un nodo y `GenerationStats` el estado: migrar a LangGraph
sería mecánico.

## Estrategias constructivas

Un constructor es cualquier objeto con `build(inst, rng) -> Solution` y ocupa el slot
`constructor` de todos los esqueletos. El constructor modular (`core/construction.py`) pone
el bucle y la regla de selección; el problema aporta la vista constructiva y el LLM, el puntaje
(`greedy_score`). Encima de eso:

- **Beam search constructiva** (`core/beam_search.py`, `BeamSearchConstructor`). Es un
  constructor hermano de `GreedyConstructor`: misma vista y mismo puntaje. En cada nivel
  expande los parciales del haz (todos los candidatos, o los `branching` de menor puntaje) y
  conserva los `beam_width` de menor valor. El valor se da de dos formas:
  - **Greedy** (`evaluation="rollout"`): el hijo se completa con el greedy de un puntaje y vale
    el objetivo de esa solución. Cada rollout es una solución candidata, así que nunca queda
    peor que el greedy desde la raíz. Con `beam_width=1` es el *pilot method*.
  - **Clásica** (`evaluation="score"`): el valor es el puntaje acumulado.

  Si la vista da `lower_bound`, se podan los parciales que no pueden mejorar; si da `key`, se
  descartan los repetidos. En el modelo por piezas son las piezas opcionales
  `partial_lower_bound` y `partial_key`, y el validador comprueba que la cota no supere el
  costo alcanzado. Con `ProblemPack.beam_constructors=True`, cada puntaje entra además como
  `beam_<nombre>`, con `beam_width` y `branching` para el tuner. Está apagado en el CLSP y el
  CVRP, donde un rollout cuesta LPs.
- **Políticas constructivas: puntajes con memoria** (slot `construction_policy`,
  `core.contracts.ConstructionPolicy`: `init(parcial)`, `score(parcial, memoria, acción)`,
  `update(parcial, memoria, acción)`). Un `greedy_score` solo ve (parcial, acción) y no puede
  sostener un plan. Muchas heurísticas constructivas sí lo hacen: FRG sabe "estoy vaciando la
  pila s y cada contenedor ya tiene destino". La memoria viaja junto al parcial. El greedy la
  actualiza con la acción elegida; la beam search lleva una por nodo (la del puntaje que ordena
  y la del rollout), actualizada con la acción de ese hijo aunque la política no la hubiera
  elegido: ahí la política decide si abandona su plan. `as_policy` adapta un `greedy_score`,
  así que el bucle es uno solo. Se valida que la memoria sea inmutable y hashable, que `score`
  y `update` sean deterministas y no modifiquen nada, y que el greedy que arman sea factible y
  termine. Entra al catálogo como `greedy_<nombre>` / `beam_<nombre>`, se genera con el LLM
  (prompt con su pista y un ejemplo de mochila en dos fases) y el ciclo sin vista MIP la pide
  junto a `greedy_score`.
- **Esqueleto `CONSTRUCT`** (`core.assembler.CONSTRUCTIVE_SKELETONS`): solo el constructor,
  sin búsqueda, con `multistart` opcional. Sirve para comparar y afinar estrategias
  constructivas por sí solas, y para problemas sin vecindarios ni MIP. No está en `SKELETONS`,
  así que el espacio de los packs existentes no cambia; un pack lo pide con
  `ProblemPack.skeletons`.
- **Vista MIP opcional** en el modelo por piezas (`ModelSpec.mip = False`). El ciclo genera
  la vista heurística y la constructiva y se salta la MIP. El pack de la variante queda solo
  con `CONSTRUCT`, con beam search; el ciclo genera `greedy_score` (o `constructor` si la vista
  constructiva no se aceptó); `PartsModel.build_mip` avisa con `NotImplementedError`.

### Piloto: CPMP (Container Pre-Marshalling Problem)

`examples/cpmp/` es el primer problema del ciclo sin vista MIP. Lo que recibe el framework es:

- la instancia (`instance.py`: clase, lector de los benchmarks CVS/BF y generadores);
- la descripción (`llm_spec.make_model_spec`, variante `moves`);
- `cases.json`: 6 micro-instancias con soluciones de ejemplo (óptima, alternativa, con un
  rodeo, infactibles por `orden` y por `movimiento`) y el óptimo EXACTO por búsqueda en
  anchura (`cases.py`).

```bash
python -m llm.cycle model      --problem cpmp --variant moves --workspace generated/cpmp_moves_cycle
python -m llm.cycle components --problem cpmp --variant moves --workspace generated/cpmp_moves_cycle
python -m llm.cycle tune       --problem cpmp --variant moves --workspace generated/cpmp_moves_cycle -- --size 5x5
```

En Actions: `generate.yml` con `problem=cpmp`, `variant=moves`. Todo lo demás es referencia
escrita a mano (`--reference`):

- `model_parts.py`: el modelo por piezas, con una vista constructiva neutral. Ofrece todos los
  movimientos válidos que no vuelven a un layout ya recorrido, con tope de 4N + 10, y el
  respaldo es una búsqueda best-first por mal puestos.
- `problem_model.py`, `layout.py`, `construction.py`, `catalog.py`, `pack.py`: lo mismo como
  `ProblemModel` de clase, con un pack propio. Si el respaldo no ordena (pasa en 6×6 o más),
  la construcción queda infactible, sin último recurso, para que un puntaje malo no herede
  la calidad de otro algoritmo.
- `frg.py`: **FRG** (*A fill-and-reduce greedy algorithm for the container pre-marshalling
  problem*, Araya y Toledo, Oper. Res. 23:51, 2023), como componente de referencia, igual que
  `setup_flip` en el CLSP. Entra como constructor (`frg`) y como política con memoria
  (`frg_policy`, slot `construction_policy`). Su memoria es el estado de FRG congelado (sr, A,
  Sd, veces que se redujo cada pila) y da 0 al movimiento que haría FRG. El greedy del
  framework con esa política reproduce FRG, y la beam search con `rollout=frg_policy` es
  BS-FRG, sin código propio. La asignación de la §4.3.2
  está reconstruida desde el texto del paper y no reproduce su efecto: se usa solo como
  respaldo cuando FRG sin ella no termina (`assignment="fallback"`). Las reducciones
  compuestas de BS*-FRG no están en la vista: son una idea de diseño, candidata a un slot de
  macroacciones generado.

`python -m examples.cpmp.demo --beam 5` compara estrategias sobre la vista de referencia, con
10 instancias al estilo CVS por tamaño. Movimientos medios (menor es mejor):

| Estrategia | 3×5 | 5×5 |
|---|---|---|
| cota inferior (mal puestos) | 4,4 | 6,7 |
| `best_first` (respaldo neutral) | 21,6 | 13,3 |
| FRG (referencia a mano) | 11,8 | 11,9 |
| greedy `frg_policy` | 16,7 | 11,9 |
| greedy `destination_rank` (miope) | 53,1 | 75,8 |
| beam clásica `destination_rank`, nb = 5 | 47,9 | 69,7 |
| beam greedy `destination_rank`, nb = 5 | 12,0 | 13,7 |
| BS-FRG (beam greedy, rollout `frg_policy`), nb = 5 | 9,2 | 10,2 |

- **La beam search greedy es lo que más aporta, con cualquier puntaje.** Un puntaje miope
  baja de 53 a 12 movimientos en 3×5, y BS-FRG baja los de FRG un 22 % en 3×5 y un 14 % en 5×5.
- **Los puntajes miopes de un solo movimiento son débiles en el CPMP.** Pasean los mismos mal
  puestos entre pilas desordenadas; FRG no, porque sostiene un plan (reducir una pila). La
  capa de calidad lo detecta: rechaza `destination_rank` y cuatro puntajes "tipo LLM" que
  probé, que costaban entre 2,7 y 9,7 veces la partida trivial. La pregunta abierta es si un
  LLM real encuentra puntajes con plan (el parcial trae los movimientos hechos) o si hace
  falta un slot de macroacciones.
- `greedy frg_policy` queda peor que FRG en 3×5 porque la vista no deja volver a un layout ya
  recorrido, y FRG sin asignación a veces lo necesita (es su ciclo de no terminación).
- 5×7 y 6×6 no están en la tabla: la corrida en Python no terminó en 30 minutos.

**Una política simple con plan** (la de `tests/test_construction_policy.py`: dejar bien
puesto lo que se pueda y, si no, vaciar la pila desordenada más baja, que la memoria recuerda;
8 instancias al estilo CVS por tamaño):

| | 3×5 | 5×5 | 6×6 |
|---|---|---|---|
| greedy `destination_rank` (miope) | 51,6 | 75,1 | 82,3 |
| greedy con la política | 31,6 | 37,9 | 90,1 |
| beam con la política, nb = 5 | 12,3 | 12,0 | 23,3 |
| FRG | 9,8 | 11,9 | 24,0 |
| BS-FRG, nb = 5 | 8,8 | 10,1 | 21,8 |

La memoria reduce a la mitad los movimientos del greedy en 3×5 y 5×5, pero no en 6×6. Con
beam search, la política queda a la par de FRG en 5×5 y le gana en 6×6. Como constructor greedy
por sí sola sigue siendo débil, y la capa de calidad la rechaza (2,5 veces la partida trivial).

**Corridas reales del ciclo en el CPMP (58–64, OpenAI).**

- **58:** modelo aceptado a la primera, pero la vista ciclaba con un puntaje constante (ver
  abajo).
- **60:** vista rechazada en 4 rondas.
- **61:** solo la vista, aceptada en la ronda 5. Es una vista neutral parecida a la de
  referencia: guarda los layouts recorridos y tiene un tope de pasos.
- **62:** generación de componentes sobre ese modelo, con unos 46 mil tokens:
  - `greedy_score` (sin memoria): 0 de 3 aceptados, con 9 rechazos por calidad;
  - `construction_policy` (con memoria): 2 de 3. Las dos sostienen un plan de verdad.
    `blocking_chain_unwinder_policy` guarda una pila fuente y una etapa: primero saca los
    bloqueadores y después termina la pila. `reserve_buffer_then_repair_policy` guarda una
    pila tampón y alterna una fase de acumulación con una de reparación.

Con 8 instancias al estilo CVS de 4×4 (cota inferior 2,6 movimientos):

| | greedy | beam, nb = 3 |
|---|---|---|
| `blocking_chain_unwinder_policy` (política, aceptada) | 21,8 | 4,9 |
| `reserve_buffer_then_repair_policy` (política, aceptada) | 31,5 | 5,8 |
| `target_stack_clearance_policy` (política, rechazada) | 20,6 | 5,9 |
| `blocking_reduction_with_safe_landing` (puntaje, rechazado) | 24,1 | 5,5 |
| `urgency_pressure_balance` (puntaje, rechazado) | 59,5 | 7,6 |
| `order_preservation_refuge_choice` (puntaje, rechazado) | 66,6 | 14,5 |
| partida trivial del modelo generado (A*) | 6,4 | |
| FRG / BS-FRG (a mano) | 4,4 | 4,1 |

Lo que muestra:

- Con beam search, la mejor política generada queda a medio movimiento de FRG, sin haber visto
  nada de FRG.
- Como greedy solas, todas son débiles; la calidad aparece con la beam search.
- Las políticas superan a los puntajes sin memoria sobre todo como greedy. Con beam, la ventaja
  es menor: un puntaje rechazado da 5,5, a la par de ellas.

Dos ajustes que salieron de aquí:

1. **Calidad por greedy o por beam search** (`ValidationContext.constructive_beam`). En un
   pack que registra `beam_<nombre>` (el CPMP de mano y el ciclo sin vista MIP), un puntaje o
   una política débil como greedy igual entra si pasa dos condiciones dentro de una beam search
   de ancho 3: queda cerca de la partida trivial y mejora a la misma beam search con un puntaje
   constante. La segunda condición hace falta porque en micro-instancias la beam search sola ya
   hace mucho: con un puntaje constante baja de 56 a 9,5 movimientos. Con esto la política
   simple con plan y `destination_rank` entran por la vía de la beam search, y el puntaje
   constante se rechaza.
2. **Optimización de un modelo sin vista MIP.** `optimize` medía solo evaluaciones de
   `violations` + `cost_terms` por segundo, que en el CPMP generado son baratas (200 en 4 ms).
   Lo lento es `trivial_solution`: 30,8 s en una instancia de 5×5, y también la usa el respaldo
   de la vista. Sin vista MIP, ahora se optimiza una unidad de trabajo constructivo:
   `trivial_solution`, 2 construcciones al azar y 200 evaluaciones (`model_speed`). El prompt
   muestra el perfil de tiempos por pieza (`parts_profile`). Además, `PartsModel` recuerda la
   penalización por modelo e instancia: el ensamblador crea uno por instancia en cada
   evaluación, y recalcular la partida trivial dominaba el tiempo.

**Corrida 63: `optimize` del modelo CPMP generado.** El job se cortó a los 45 min con una sola
versión propuesta. Esa versión agregaba `lru_cache` y copias más baratas: `trivial_solution`
bajó de 34 a 26 s en 5×5 (1,3×, bajo el 1,5× pedido). Casi todo ese tiempo se iba en validarla
contra los casos antes de medir su velocidad: la vista constructiva completa con
`trivial_solution`, y en una instancia de 5×5 una sola llamada llega a 145 s. El cuello de
botella real era de complejidad: una best-first que toma `min(frontera)` y lo quita con `remove`
en cada expansión. Con un heapq y un contador de inserción el orden es el mismo, empates
incluidos, y la salida es idéntica (0,14 s contra 35 s, 0,32 s contra 145 s). Ajustes:

- **Primero lo barato.** El orden de las pruebas es equivalencia, después velocidad y al final
  la validación contra los casos. Una versión que no es más rápida se rechaza sin llegar a la
  validación.
- **El oráculo no se recalcula.** `_Oracle` memoriza la `trivial_solution` del modelo aceptado
  por instancia; la prueba diferencial la pedía varias veces por instancia y ronda.
- **Presupuesto.** `optimize_model(deadline=...)` usa el de la etapa (`--max-minutes`). La
  primera ronda corre siempre; las siguientes, solo si queda al menos lo que tardó la anterior.
- **Prompt.** Si una pieza se lleva el 70 % del tiempo o más, el prompt lo dice. Las técnicas
  incluyen la cola de prioridad con desempate por inserción. Las velocidades bajo 1/s se
  muestran también en segundos por unidad (el prompt decía "0.00 unidades/s").

**Corrida 64: la misma optimización, con esos ajustes.** Se aceptó en la ronda 3, en 15 min y
con unos 23 mil tokens. Las rondas 1 y 2 se rechazaron en la prueba diferencial porque
`violations` contaba distinto los movimientos inválidos. La versión aceptada usa un heapq con
un contador de nodo, la técnica del prompt. Pasó de 0,0013 a 6,2 unidades de trabajo
constructivo/s en el runner. Localmente, en otras 3 instancias de 5×5, `trivial_solution` da la
misma salida en 0,14 s contra 31 s y en 0,2 s contra 124 s. El modelo optimizado reemplaza al
de la corrida 61 en `generated/cpmp_moves_cycle/model/parts.py`; el anterior queda en
`parts_slow.py`.

**Validación de la vista constructiva generada: un puntaje constante no puede ciclar.** En la
corrida 58 la vista del CPMP que escribió el LLM ofrecía movimientos que no empeoran el
desorden. Pasó las construcciones al azar (que escapan de un ciclo tarde o temprano), pero con
un puntaje constante iba y volvía para siempre. `check_construction_view` recorre además
eligiendo siempre el primer y el último candidato, y rechaza volver a un estado ya visitado
(según `partial_key`, si la vista lo da). Las vistas ya aceptadas del CLSP (corrida 54) y del
CVRP (33 y 34) siguen pasando. En la corrida 60, con el chequeo, la vista del CPMP se rechazó
en las 4 rondas: el LLM oscila entre ciclar, recortar tanto los candidatos que no queda qué
elegir, y un respaldo infactible.

## Correr en GitHub Actions

Cuatro workflows en `.github/workflows/`:

| workflow | disparo | qué hace |
|---|---|---|
| `tests` | push, PR | `pytest` en Python 3.11 y 3.12; verifica primero que haya un solver MIP disponible. Sin secretos, así que corre en PRs de forks. |
| `generar componentes con LLM` | **manual** | Corre `examples.lotsizing.generate` con los slots, `n`, rondas, proveedor y modelo que elijas; los inputs `price_in`/`price_out` (o las *variables* de repo `LLM_PRICE_IN`/`LLM_PRICE_OUT`) agregan el costo estimado al resumen. Escribe la tabla de aceptación por capa y los reportes del validador en el *summary* de la corrida, sube `generated/` como artefacto y abre un PR con los módulos generados. |
| `benchmark` | **manual** | Utilidad y diversidad por componente, y/o la comparación de los ocho esqueletos. |
| `tuning (Optuna) sobre el catálogo` | **manual** | Afina con el catálogo a mano y con el ampliado, evalúa ambos ganadores en test y responde "¿ayuda o diluye?" en el *summary*. Inputs para fijar esqueletos, tamaño de instancia (`20x20`) y segundos del MIP de referencia. Commitea los resultados en la rama `tuning/runN` (carpeta `results/tune_runN/`, con un `README.md` del resumen) y además los sube como artefacto, que expira a los 30 días. |

Los dos últimos son `workflow_dispatch` a propósito: cada corrida de generación
gasta llamadas de API, así que nunca se disparan por push ni por schedule.

**Configuración**: en *Settings → Secrets and variables → Actions* agrega
`OPENAI_API_KEY` (o `ANTHROPIC_API_KEY`). Si el PR automático debe poder
crearse, habilita *Settings → Actions → General → Allow GitHub Actions to
create and approve pull requests*.

Dos advertencias sobre el benchmark en Actions: los runners son compartidos, así
que los presupuestos de tiempo de pared **no** son comparables entre corridas ni
contra tu máquina —sirven para comparar componentes y esqueletos dentro de una
misma corrida—; y CBC en un runner de 2 vCPU es más lento que en un portátil, de
modo que las matheurísticas resuelven menos sub-MIPs con el mismo presupuesto.

## Resultado de referencia (CLSP Trigeiro 15×20, util. 0.95, TBO 3, 20 s/variante)

| Variante | Costo |
|---|---|
| Lot-for-lot (constructor) | 235 256 |
| Relax-and-Fix (constructor, 3 s) | 156 940 |
| SA (lot-for-lot + setup_flip) | 165 613 |
| ILS (HC first-improvement) | 219 624 |
| LNS-MIP, destrucción aleatoria | 153 037 |
| **LNS-MIP, destrucción por ventana de períodos** | **151 804** |
| Relax-and-Fix → Fix-and-Optimize | 153 230 |
| MIP completo (CBC, 20 s) | 158 960 |

Con instancias duras las variantes ya discriminan: el componente de
destrucción que usa la estructura temporal gana, y las matheurísticas
superan al MIP completo con el mismo tiempo (§10, primera pregunta).

## Los 8 esqueletos con configuración por defecto (CLSP Trigeiro 15×20, 20 s)

| Esqueleto (componentes a mano) | Costo |
|---|---|
| FIX_OPT (lot-for-lot + sliding_window) | 154 433 |
| LOCAL_BRANCH (lot-for-lot) | 157 746 |
| LNS_MIP (lot-for-lot + period_window) | 162 123 |
| SA (setup_flip) | 170 406 |
| ILS / VNS / TS / GRASP (setup_flip) | 219–222 k |

TS, VNS y GRASP con un solo vecindario de flips y un constructor
determinista son débiles por construcción (GRASP degenera en "construir
una vez + LS"); son los esqueletos que más ganan con los vecindarios y
constructores aleatorizados que genera el LLM.

**Hallazgo de modelado**: con la penalización de faltante fija en 1000 por
unidad, en instancias Trigeiro (setup ≈ 1000) LNS-MIP encontraba planes
*infactibles* con mejor objetivo penalizado — dejar medio pedido sin cubrir
era más barato que un setup. `shortage_penalty(inst)` ahora escala con la
instancia (20 × (setup más caro + inventario de una unidad todo el
horizonte)). Es exactamente el tipo de error sutil de formulación que §7
capa 3 quiere atrapar, y aquí lo atrapó el `evaluate` del ensamblador al
devolver la penalización por infactibilidad.

## Qué falta (siguientes pasos del plan, §9)

1. ~~Correr la generación real~~ — hecho, en el CLSP (corridas 1–16) y en el CVRP
   (18 y 20); los aceptados entran solos al catálogo vía `load_generated`.
2. ~~Tuning real~~ — hecho con Optuna (`tuning/`, workflow `tune.yml`), con selección
   final por re-evaluación (`--reeval-top`) y comparación pareada con IC95 en test;
   irace queda preparado (escenario + target-runner) para correr afuera.
3. ~~Segundo problema~~ — CVRP (`examples/cvrp`). Destapó suposiciones del CLSP en el
   framework (texto de los prompts y del validador, "soluciones al azar" leídas desde
   una asignación 0/1), ya separadas: ver `results/README.md`.
4. ~~MIP-guided Perturbation~~ (`MIP_PERTURB`) y ~~generación LLM del `ProblemModel`
   completo~~ (§6.1, `llm/model_generator.py`): en el CVRP, aceptado en la ronda 2 y
   con el mismo óptimo MIP que el modelo escrito a mano en las micro-instancias.
5. Pendiente: generar los componentes para un `ProblemModel` generado (hoy los
   componentes se generan contra el modelo de referencia del pack), y más instancias o
   presupuesto para que las comparaciones entre catálogos tengan potencia estadística.
