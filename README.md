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
  `Assembler.SKELETONS`: 8 esqueletos en el espacio de diseño.
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
  (`SKELETONS`: SA, ILS, LNS_MIP, FIX_OPT), construye el `ConfigSpace`
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
- **`tests/`** — 88 tests (`pytest`): contratos, esqueleto genérico,
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
python -m pytest -q                 # 88 passed (~28 s)

export OPENAI_API_KEY=...
python -m examples.lotsizing.generate --slots neighborhood destruction --n 3   # generación real
```

Sobre orquestación: el ciclo es un bucle determinista corto, así que se
implementó en Python plano. Si más adelante el flujo se vuelve un grafo
(ramas paralelas por slot, decisión diversidad-vs-corrección según tasas,
checkpoints de sesiones caras, paso humano), cada función de `llm/generator.py`
es directamente un nodo y `GenerationStats` el estado: migrar a LangGraph
sería mecánico.

## Correr en GitHub Actions

Tres workflows en `.github/workflows/`:

| workflow | disparo | qué hace |
|---|---|---|
| `tests` | push, PR | `pytest` en Python 3.11 y 3.12; verifica primero que haya un solver MIP disponible. Sin secretos, así que corre en PRs de forks. |
| `generar componentes con LLM` | **manual** | Corre `examples.lotsizing.generate` con los slots, `n`, rondas, proveedor y modelo que elijas. Escribe la tabla de aceptación por capa y los reportes del validador en el *summary* de la corrida, sube `generated/` como artefacto y abre un PR con los módulos generados. |
| `benchmark` | **manual** | Utilidad y diversidad por componente, y/o la comparación de los ocho esqueletos. |

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

1. **Correr la generación real** con `gpt-5.4-mini` (`examples.lotsizing.generate`)
   y analizar `stats.json`; los aceptados entran solos al catálogo de
   `random_search`/`Assembler` vía `load_generated`.
2. **Tuning real** con irace/Optuna: `Assembler.evaluate` ya es el target
   runner y `config_space()` el espacio; falta solo el adaptador
   (`suggest_from_space` para Optuna, `to_irace_parameters` + script
   `target-runner` para irace) y la separación train/test.
3. MIP-guided Perturbation (§5.2), el único esqueleto de la tabla que
   falta; y generación LLM del `ProblemModel` completo (§6.1), donde la
   capa semántica tiene algo real que rechazar.
