# Solvers híbridos generados por LLM

Framework para armar, a partir de la descripción de un problema de optimización combinatoria, un solver
metaheurístico/matheurístico afinado: el LLM escribe en C++ el modelo del problema y los componentes de búsqueda; el
framework pone los esqueletos (en C++), la validación autónoma de todo lo que escribe el LLM y la configuración
automática (irace). Los resultados contra la literatura están en [`results/README.md`](results/README.md); el método
se explica en [`docs/borrador_tecnico.md`](docs/borrador_tecnico.md) y el estado del trabajo, con los pasos que faltan,
en [`docs/guia_para_continuar.md`](docs/guia_para_continuar.md).

## El pipeline

```
lo humano por problema           el LLM (validado)                        configuración y evaluación
──────────────────────           ─────────────────                        ──────────────────────────
instancia (formato, generador)   1. modelo C++        native_model_generator   5. irace / staged sobre
descripción (ModelSpec)              └ más rápido     native_model_optimizer      esqueleto + componentes
casos de prueba (cases.json)     2. componentes C++   native_generator            + parámetros (tuning.cli)
oráculo en Python (model_parts:      └ más rápidos    native_optimizer         6. evaluación en benchmarks
  violaciones y costo)           3. vista MIP Python  native_mip_generator        (scripts/bench_eval.py)
```

1. **Modelo** (`llm/native_model_generator.py`): el LLM escribe el modelo C++ con el contrato genérico de
   `native/include/hsf/generic.hpp` (parseo de la instancia, solución trivial y al azar, violaciones por familia y
   términos del costo). La solución es siempre `vector<vector<int>>`, con la forma de la respuesta de los casos (una
   lista de listas, también cuando el problema tiene un solo vector). `native/check_model.py` lo valida en un proceso aparte contra los casos visibles y ocultos y
   contra el oráculo en Python en instancias generadas (mismas violaciones y mismo costo), y lo corrige
   con el LLM hasta `--rounds` rondas. `native_model_optimizer` pide una versión más rápida con las mismas salidas.
2. **Componentes** (`llm/native_generator.py`): constructores, vecindarios, perturbaciones y relinks
   en C++ sobre ese modelo. Se le pueden pedir también destrucciones para HYB (`--slots destruction`), pero por defecto
   el tuning usa solo las genéricas (`--generated-destructions` para incluirlas): en CLSP, job shop y CVRP las
   generadas no les ganaron (`native/generated.py` los compila juntos; las respuestas de corrección son ediciones,
   `native/edits.py`). `native/check.py` aplica las capas de `core/validation/` (contractual, calidad, diversidad
   contra los aceptados, aporte en combinación con cada esqueleto) en un proceso aparte; la contractual incluye el
   chequeo de forma (`well_formed` del oráculo) sobre todo lo que devuelve un componente. El prompt lleva la
   representación de la solución (`answer_format` de la descripción). `native_optimizer` acelera
   los aceptados con pruebas diferenciales (`core/validation/equivalence.py`).
3. **Vista MIP** (`llm/native_mip_generator.py`, opcional): la formulación en Python que usa HYB en sus sub-MIPs
   (variables, restricciones por familia, términos del objetivo y grupos de variables), validada contra el oráculo y
   los casos (`check_mip_view`, `check_mip_optimum`). Queda en `<workspace>/mip/mip.py`; sin ella el problema no
   tiene sub-MIP y HYB no entra al espacio. No hay vista MIP escrita a mano: en CLSP, job shop y CVRP la generada
   rinde igual que la de referencia que había (tunings 92–97, `results/README.md`).
4. **Configuración** (`tuning/cli.py`): el espacio condicional (esqueleto → componentes de cada slot → parámetros,
   `config_space/`) se afina con irace (`--tuner irace`) o en tres etapas (`--tuner staged`, `tuning/staged.py`:
   primero la estructura, después irace en el espacio reducido). La configuración ganadora se mide en instancias
   de test contra los defaults de cada esqueleto. Las corridas son enteras en C++ (`core/native_runner.py`).

Los **esqueletos** son SA, ILS, VNS, TS, PR (path relinking con mejora tabú o ILS) y HYB (ILS en C++ alternado con
sub-MIPs en Python sobre la vista MIP generada: destrucción + `MIPModelRepair`), en `native/include/hsf/core.hpp`, con su versión de referencia
en Python en `skeletons/` (misma semántica y parámetros, `core/assembler.py`; la usa la validación por combinación).

## Organización

| directorio | qué hay |
|---|---|
| `core/` | contratos de los slots (`contracts.py`), registro de componentes, ensamblador, modelo por piezas (`model_parts.py`), packs (`problem_pack.py`, `packs.py`), catálogo (`catalog.py`), `MIPModel`, validación por capas (`validation/`) |
| `skeletons/` | esqueletos en Python (referencia y HYB) |
| `native/` | contrato y esqueletos C++ (`include/hsf/`), compilación con caché, validación del modelo y de los componentes generados |
| `llm/` | cliente intercambiable (`client.py`: OpenAI, Anthropic, guionado) y la generación y optimización del modelo y de los componentes C++ |
| `tuning/`, `config_space/` | espacio de configuración, irace, configuración en etapas, evaluación en test |
| `examples/<problema>/` | lo humano de cada problema: `instance.py`, `llm_spec.py`, `cases.json`, `model_parts.py` y `pack.py`; `tune.py` es el CLI del tuning |
| `generated/v2/<problema>/` | lo que escribió el LLM con el protocolo v2 (los 7 problemas igual): modelo, componentes aceptados, vista MIP, transcripciones y estadísticas |
| `generated/<problema>_native/` | generaciones anteriores, con las que se hicieron los tunings hasta el 108 |
| `scripts/` | target-runner de irace, resúmenes de tuning y evaluación en benchmarks (`bench_eval.py`) |
| `results/` | resultados de las corridas; `llm_sota/`, los resultados publicados de los métodos con LLM (ReEvo, MCTS-AHD, EoH, CO-Bench, FrontierCO) |
| `docs/` | borrador técnico y guía para continuar (copias de los documentos en claude.ai) |

## Problemas

| pack | problema | benchmark (`bench_eval`) | ejemplo de `--size` (instancias generadas) |
|---|---|---|---|
| `flowshop` | flow shop de permutación, flowtime total | Taillard (`flowshop`) | `50x10` (trabajos × máquinas) |
| `flowshop_cmax` | flow shop de permutación, makespan | Taillard (`flowshop_cmax`) | ídem |
| `clsp` | lot sizing capacitado multi-ítem | Trigeiro (`clsp`) | `20x20` (ítems × períodos) |
| `jobshop` | job shop, makespan | Taillard ta01–ta80 y OR-Library, 162 (`jobshop`) | `15x15` |
| `cvrp` | CVRP con flota libre | Uchoa X, 100 (`cvrp`); FrontierCO, 45 (`cvrp_frontierco`); test de ReEvo (`cvrp_reevo`) y de MCTS-AHD (`cvrp_mcts_ahd`) | `x100` como las X, `u50` en el cuadrado unitario como ReEvo |
| `mkp` | mochila multidimensional 0/1 | OR-Library: mknap1, mknap2, mknapcb1–9 (`mkp`); test de ReEvo/MCTS-AHD (`mkp_reevo`, `fetch --reevo`) | `250x5` como Chu y Beasley, `n100x5` normalizado como ReEvo |
| `sscflp` | localización de centros con capacidad y fuente única | Holmberg, Díaz-Fernández, Yang, TB4, OR-Library, 217 (`sscflp`); capa–c y TBED1 con `fetch --large` | `20x100` (centros × clientes) |

Cada conjunto trae su script de descarga (`examples/<problema>/fetch.py`) y sus referencias con la fuente
(`best_known.json`). Las del job shop son las de Weise (2020); las del SSCFLP, Guastaroba y Speranza (2014) y Kong
(2021), y en Díaz-Fernández, donde no hay tabla publicada, CBC (`python -m examples.sscflp.best_known --cbc D-`); en los
test de ReEvo y MCTS-AHD, HGS para el CVRP (`examples/cvrp/reference.py`) y CBC para el MKP.

En los siete, el modelo C++, los componentes y la vista MIP (salvo en los flow shop) los escribió el LLM
(`generated/v2/<problema>`). Un problema nuevo necesita la instancia (`to_text`/`parse`, generador), la descripción para el LLM (`ModelSpec`), los casos de prueba y
el oráculo en Python (`model_parts.py`: violaciones por familia, términos del costo y, opcional, `well_formed`). La
descripción tiene que decir cuál es la solución trivial: la validación compara la penalización del modelo,
10·(|costo de la trivial| + 1), con la del oráculo;
`core.packs.parts_pack` arma el pack con los componentes base del framework (`base_components`): las partidas trivial
y al azar y, con la vista MIP generada, dos destrucciones genéricas sobre `variable_groups` (una ventana de grupos consecutivos y
variables al azar), así HYB está disponible aunque el LLM no haya escrito destrucciones. Ver `examples/flowshop/`.

## Cómo correr

```bash
pip install -r requirements.txt          # el backend nativo necesita además g++
python -m pytest -q

export ANTHROPIC_API_KEY=...             # u OPENAI_API_KEY con --provider openai
P=flowshop; WS=generated/v2/${P}
python -m llm.native_model_generator --problem $P --workspace $WS --provider anthropic
python -m llm.native_generator --problem $P --workspace $WS --provider anthropic --slots constructor neighborhood perturbation
python -m llm.native_optimizer --problem $P --workspace $WS --provider anthropic --slots neighborhood
python -m llm.native_mip_generator --problem $P --workspace $WS --provider anthropic   # opcional: HYB
# por defecto los prompts llevan prototipos de lo que el LLM solo usa (llm/outline.py); --full-prompts, el código completo

# configuración (irace necesita R con el paquete irace: apt install r-cran-irace)
# una configuración por tipo de instancia; --scale-budget da más tiempo a las más grandes (budget_scale del pack)
python -m examples.flowshop.tune --generated $WS --tuner irace --trials 80 --size 100x20 --scale-budget
python -m examples.flowshop.tune --generated $WS --tuner staged --trials 70

# evaluación en el benchmark con la configuración afinada; el tiempo crece con el tamaño (n·m/2·t ms, en el CVRP
# n·t/100 s) o es fijo con --budget (10 s como CO-Bench). Benchmarks: flowshop, flowshop_cmax, jobshop, clsp, cvrp,
# cvrp_frontierco, cvrp_reevo, cvrp_mcts_ahd, sscflp, mkp, mkp_reevo
python -m scripts.bench_eval flowshop results/tune_runNN --generated $WS --t 60 --seeds 3
```

## GitHub Actions

| workflow | disparo | qué hace |
|---|---|---|
| `tests` | push, PR | `pytest` en Python 3.11 y 3.12 |
| `generar con LLM` | manual | `target`: `model`, `model_optimize`, `components`, `optimize` o `mip` sobre `workspace` (vacío = `generated/<problema>_native`; el protocolo v2 usa `generated/v2/<problema>`); deja lo generado en la rama `llm-generated/…` y, con `open_pr`, abre un PR |
| `tuning (irace)` | manual | afina el catálogo de `generated_dir` (`extra_args: --scale-budget` para escalar el tiempo), evalúa en test y guarda los resultados en la rama `tuning/runN` (`results/tune_runN/`); réplicas en paralelo con `replicas` |

Los secretos van en *Settings → Secrets and variables → Actions*: `ANTHROPIC_API_KEY` (y `ANTHROPIC_WORKSPACE_ID` si
la clave no está asociada a un workspace) u `OPENAI_API_KEY`. Los precios por millón de tokens (`LLM_PRICE_IN`,
`LLM_PRICE_OUT`, como variables o inputs) agregan el costo estimado a las estadísticas.
