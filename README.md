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
  para corregir (§6). Se detiene en la primera capa que falla.
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
- **`tests/`** — 70 tests (`pytest`): contratos, esqueleto genérico,
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
python -m pytest -q                 # 70 passed (~20 s)

export OPENAI_API_KEY=...
python -m examples.lotsizing.generate --slots neighborhood destruction --n 3   # generación real
```

Sobre orquestación: el ciclo es un bucle determinista corto, así que se
implementó en Python plano. Si más adelante el flujo se vuelve un grafo
(ramas paralelas por slot, decisión diversidad-vs-corrección según tasas,
checkpoints de sesiones caras, paso humano), cada función de `llm/generator.py`
es directamente un nodo y `GenerationStats` el estado: migrar a LangGraph
sería mecánico.

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

## Qué falta (siguientes pasos del plan, §9)

1. **Correr la generación real** con `gpt-5.4-mini` (`examples.lotsizing.generate`)
   y analizar `stats.json`; los aceptados entran solos al catálogo de
   `random_search`/`Assembler` vía `load_generated`.
2. **Tuning real** con irace/Optuna: `Assembler.evaluate` ya es el target
   runner y `config_space()` el espacio; falta solo el adaptador
   (`suggest_from_space` para Optuna, `to_irace_parameters` + script
   `target-runner` para irace) y la separación train/test.
3. Esqueletos restantes de §5: TS, VNS, GRASP+LS, Local Branching,
   MIP-guided Perturbation — cada uno una entrada en `SKELETONS` más una
   rama en `Assembler.assemble`.
