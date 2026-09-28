# Núcleo — Solvers híbridos generados por LLM

Implementación del ítem 1 del plan de trabajo de la propuesta
(`propuesta_solvers_hibridos_llm.md`, §9): *"definir los Protocols de
los slots, el esqueleto genérico y tres especializaciones (SA, ILS,
LNS-MIP). Exportador del espacio de configuración a irace y Optuna."*

> **Rama `claude/readme-estrategias-constructivas-*`.** Esta rama se enfoca en las
> **estrategias constructivas**: el slot `constructor`, el constructor modular con
> `greedy_score` y los esqueletos que dependen de la construcción (GRASP, Relax-and-Fix).
> La sección [Estrategias constructivas](#estrategias-constructivas) reúne lo que hay,
> lo que muestran los resultados, los huecos detectados al revisar este README y el plan
> de trabajo de la rama.

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
  (`SKELETONS`: SA, ILS, LNS_MIP, FIX_OPT, TS, VNS, GRASP, LOCAL_BRANCH, MIP_PERTURB), construye el `ConfigSpace`
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
- **`examples/validation_demo.py`** — componentes correctos y rotos pasando
  por las capas, con el feedback que recibiría el LLM.
- **`examples/cpmp/`** — Piloto constructivo: CPMP con FRG y BS-FRG sobre la beam search
  genérica (ver *Estrategias constructivas*).
- **`tests/`** — 213 tests (`pytest`): contratos, esqueleto genérico,
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
python -m examples.cpmp.demo --beam 5 20   # CPMP: FRG, greedy con puntajes y beam search (BS-FRG)
python -m examples.lotsizing.random_search --configs 12 --budget 5   # espacio completo, target-runner
python -m pytest -q                 # 213 passed (~130 s)

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

Foco de esta rama. Un constructor es cualquier objeto con `build(inst, rng) -> Solution`
(`Protocol` `Constructor` de `core/contracts.py`): ocupa el slot `constructor` de los nueve
esqueletos y, en GRASP, es el motor de cada reinicio.

### Qué hay hoy

| Estrategia | Dónde | Cómo entra al espacio de diseño |
|---|---|---|
| Trivial (lot-for-lot en CLSP, `singleton_routes` en CVRP) | `examples/lotsizing/components.py`, `examples/cvrp/catalog.py` | constructor de mano; también es la partida trivial del pack |
| **Greedy modular**: bucle del framework + `greedy_score` del problema o del LLM | `core/construction.py` (`GreedyConstructor`) | cada puntaje se registra como constructor `greedy_<nombre>` (`llm.catalog.greedy_constructor_spec`) |
| Reglas de selección `greedy`, `rcl` (RCL-α de GRASP) y `roulette` | `core/construction.py` (`RULES`) | parámetros `rule` y `alpha` del constructor, los elige el tuner |
| Puntajes de mano: `unit_marginal_cost`, `latest_source` (CLSP); `cheapest_insertion`, `nearest_from_depot` (CVRP) | `examples/*/construction.py` | slot `greedy_score` |
| Vista constructiva (`ConstructionView`: parcial, candidatos, aplicar, completo, respaldo) | `examples/lotsizing/construction.py`, `examples/cvrp/construction.py` | la escribe el problema; la factibilidad vive aquí, no en el puntaje |
| **Relax-and-Fix** (matheurístico) | `skeletons/relax_and_fix.py` + `core/fixing_policies.py` | constructor con `fallback`; da el híbrido Relax-and-Fix → Fix-and-Optimize |
| Constructores monolíticos generados por el LLM | `generated/clsp*/constructor/` | slot `constructor` directo |
| GRASP+LS (multiarranque) | `skeletons/grasp.py` | esqueleto; solo tiene sentido con un constructor que use `rng` |
| **Beam search constructiva**: clásica (puntaje acumulado) o *greedy* (cada hijo se evalúa con un rollout hasta el final; `beam_width=1` es el *pilot method*) | `core/beam_search.py` (`BeamSearchConstructor`) | `beam_<puntaje>` con `beam_width` y `branching` como parámetros del tuner, si el pack pone `beam_constructors=True` |
| **FRG y BS-FRG** para el CPMP (Araya y Toledo 2023) | `examples/cpmp/` | FRG como constructor, como puntaje (`frg_policy`) y como rollout de la beam search |

Validación específica: `check_greedy_score` (finito, determinista, no modifica el parcial),
factibilidad del constructor en la sonda de tamaño realista, gate de calidad contra la
solución trivial (`constructor_max_relative_gap`, default 1,0) y firma de diversidad del
puntaje (acciones que elige el greedy, Jaccard; `diversity.greedy_score_signature`).

### Qué dicen los resultados

- **Los puntajes ganan a los constructores monolíticos** (run 6, SA + `setup_flip` fijos,
  `results/README.md`): los tres puntajes generados (7,1–9,6 % de gap) superan a los tres
  monolíticos generados (11,3–15,9 %), ninguno de los cuales mejora a lot-for-lot (11,3 %).
  El puntaje de mano `unit_marginal_cost` sigue primero (6,5 %).
- **El monolítico es caro e irregular de generar**: en la corrida 9 se llevó 65 mil de 99 mil
  tokens con 11 rechazos, casi todos por factibilidad. Con el modular la factibilidad es de la
  vista: 0 respaldos en 360 construcciones de prueba.
- **La partida importa más que el vecindario en varios esqueletos**: desde el greedy, ILS/VNS
  quedan en 6,9–9,3 % con o sin muestreo; desde lot-for-lot, 18–39 %. Un mismo vecindario
  (`merge_with_previous_setup`) es inerte desde lot-for-lot y parte de la mejor configuración
  desde el greedy.
- **GRASP es débil con constructores deterministas** (219–222 k en la tabla de los esqueletos):
  degenera en "construir una vez + LS".

### Huecos detectados al revisar

1. **El puntaje no tiene memoria ni mirada adelante**: la única estrategia constructiva
   genérica era greedy de un paso. *Beam search* y *pilot method* ya están
   (`core/beam_search.py`, ver abajo); faltan *look-ahead* acotado y *regret-k*.
2. **No hay reconstrucción parcial**: *Iterated Greedy* (destruir parte y reconstruir con el
   mismo greedy) no existe; hoy "destruir" solo se usa hacia el sub-MIP (LNS-MIP). La vista
   no tiene una operación para volver de una solución completa a un parcial.
3. **La RCL es estática**: `alpha` lo fija el tuner para toda la corrida; no hay GRASP
   reactivo (α adaptativo según calidad) ni sesgo aprendido entre reinicios (memoria tipo
   ACO / *path relinking*).
4. **El gate y la firma de diversidad del puntaje usan solo la regla `greedy`**: un puntaje
   útil únicamente con `rcl` o `roulette` (p. ej. uno casi plano) no se evalúa en su uso
   real; tampoco se mide la diversidad de las soluciones que produce con `rng`, que es lo
   que GRASP necesita.
5. **Relax-and-Fix no se genera ni se afina como estrategia constructiva**: la política de
   ventana (`SlidingWindowPolicy`) es de mano y su tamaño/solapamiento no se cruza con los
   puntajes greedy en una misma comparación de constructores.
6. **La comparación aislada de constructores es parcial**: `benchmark_components` ya mide la
   solución sin búsqueda (costo y factibilidad, semilla 0), pero solo en el CLSP, sin tiempo
   de construcción, sin respaldos (`fallbacks`) y sin variar la regla ni la semilla.

### Plan de la rama

1. **Benchmark de constructores**: ampliar la tabla sin búsqueda de `benchmark_components`
   (gap de la partida, tiempo, respaldos, diversidad entre semillas, por regla) y llevarla al
   CVRP; exponerla en el workflow `benchmark`.
2. ~~**Beam search sobre la vista existente**~~ — hecho: `BeamSearchConstructor`, constructor
   hermano de `GreedyConstructor`, con el CPMP como piloto (sección siguiente). Quedan
   *look-ahead* de profundidad fija y *regret-k* como reglas del greedy, y un `ProblemPack`
   del CPMP (vecindarios, micro-contextos) para generar puntajes con el LLM y afinar BS-FRG.
3. **Iterated Greedy**: operación opcional `ConstructionView.partial_from(sol, keep)` y un
   esqueleto `IG` (destruir d componentes, reconstruir con el greedy, aceptar) sobre
   `TrajectorySkeleton`.
4. **GRASP reactivo**: α elegido de un conjunto con probabilidades actualizadas por la calidad
   media de cada α, dentro de `build_grasp`.
5. **Validación acorde al uso**: gate y firma del puntaje también con `rcl`, y diversidad
   entre semillas para constructores declarados compatibles con GRASP.
6. **Generación**: el prompt de `greedy_score` pide puntajes pensados para cada estrategia
   (un paso, *look-ahead*, reconstrucción) y el planificador reparte las ideas entre ellas.

Cada punto entra con tests en `tests/` y, si cambia prompts o validación, con un caso del
cliente guionado.

### Beam search constructiva y el piloto CPMP

`core/beam_search.py` (`BeamSearchConstructor`) es un constructor hermano de
`GreedyConstructor` sobre la misma `ConstructionView`. En cada nivel se expanden los parciales
del haz: todos los candidatos, o los `branching` de menor puntaje. De los hijos se conservan
los `beam_width` de menor valor. Hay dos formas de dar el valor:

- `evaluation="rollout"`, o **beam search greedy**: el hijo se completa con un greedy y vale
  el objetivo de esa solución. Cada rollout es una solución candidata, así que el resultado
  nunca es peor que el greedy desde la raíz. Con `beam_width=1` es el *pilot method*. El
  rollout puede ser un `GreedyScore` o `"complete"`, que usa `view.complete`, el respaldo
  del problema, cuando ese respaldo es una heurística completa.
- `evaluation="score"`, la beam search clásica: el valor es el puntaje acumulado, sin
  completar. Es más barata.

Si la vista expone `lower_bound(parcial)`, se podan los parciales que no pueden mejorar a la
mejor solución. Si expone `key(parcial)`, se descartan los repetidos dentro de un nivel.
`llm.catalog.beam_constructor_spec` registra cada puntaje como `beam_<nombre>`, con
`beam_width` y `branching` para el tuner. Esto solo ocurre si el pack pone
`beam_constructors=True`; está apagado por defecto porque en el CLSP cada rollout cuesta LPs.

**CPMP** (`examples/cpmp/`, sin vista MIP todavía). Se basa en *A fill-and-reduce greedy
algorithm for the container pre-marshalling problem* (Araya y Toledo, Oper. Res. 23:51, 2023):

- `frg.py` implementa FRG: movimientos BG que llenan pilas ordenadas y reducciones con su
  criterio de parada, más las mejoras de la §4.3 (no crear pilas ordenadas llenas;
  `unblocking_assignment` + `gen_seq`).
- `construction.py` define la vista. Ofrece las acciones de BS*-FRG: movimientos simples con
  los `k` mejores destinos de `select_destination` por pila, la iteración de FRG (que
  conserva el estado sr/A/Sd) y las reducciones compuestas R_s. `complete` corre FRG, así
  que **BS-FRG no necesita código propio**: es
  `BeamSearchConstructor(P, rollout="complete", beam_width=nb)`.
- FRG también entra como puntaje (`frg_policy`: el greedy del framework con ese puntaje
  *es* FRG) y como constructor (`FRGConstructor`).

La asignación de la §4.3.2 está reconstruida desde el texto del paper y no reproduce su
efecto. Evita que FRG no termine, pero cuesta movimientos donde FRG⁻ ya termina, así que se
usa como respaldo (`assignment="fallback"`). Ver `examples/cpmp/frg.py`.

`python -m examples.cpmp.demo --beam 5 20` usa 10 instancias al estilo CVS por tamaño (S×H,
N = S·(H−2)). La tabla da los movimientos medios (menor es mejor); FRG⁻ no termina en 2 de
las 10 instancias de 3×5, y su media es sobre las 8 restantes:

| Estrategia | 3×5 | 5×5 | 5×7 | 6×6 |
|---|---|---|---|---|
| cota inferior (mal puestos) | 4,4 | 6,7 | 15,9 | 13,9 |
| FRG⁻ | 11,4 (2 fallas) | 11,9 | 39,3 | 24,6 |
| FRG (asignación de respaldo) | 11,8 | 11,9 | 36,9 | 24,6 |
| greedy `fill_first` | 11,3 | 11,9 | 41,6 | 25,5 |
| beam clásica `fill_first`, nb = 20 | 9,3 | 11,2 | 32,4 | 22,6 |
| BSs-FRG, nb = 5 | 9,1 | 10,3 | 29,5 | 21,8 |
| BS*-FRG, nb = 5 | 9,3 | 10,2 | 30,0 | 21,3 |
| BSs-FRG, nb = 20 | 9,1 | 10,1 | 28,7 | 20,9 |
| BS*-FRG, nb = 20 | 9,1 | 10,1 | 28,4 | 20,9 |

Con haces pequeños, la beam search greedy baja los movimientos de FRG entre 13 y 21 % con
nb = 5 y entre 15 y 23 % con nb = 20. A
igual ancho, le gana a la beam clásica: evaluar un hijo por la solución completa que produce
vale más que por el puntaje acumulado. El costo es un rollout por hijo: en 5×7, 0,5 s por
instancia con nb = 5 y 1,5 s con nb = 20, en Python. En estos tamaños BS* y BSs quedan
parejos; el paper reporta la ventaja de BS* con nb ≥ 100, que aquí no se probó.

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
