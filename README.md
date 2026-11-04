# Solvers híbridos generados por LLM

Framework para armar, a partir de la descripción de un problema de optimización combinatoria, un solver
metaheurístico/matheurístico afinado: el LLM escribe en C++ el modelo del problema y los componentes de búsqueda; el
framework pone los esqueletos (en C++), la validación autónoma de todo lo que escribe el LLM y la configuración
automática (irace). Los resultados contra la literatura están en [`results/README.md`](results/README.md).

## El pipeline

```
lo humano por problema           el LLM (validado)                        configuración y evaluación
──────────────────────           ─────────────────                        ──────────────────────────
instancia (formato, generador)   1. modelo C++        native_model_generator   5. irace / staged sobre
descripción (ModelSpec)              └ más rápido     native_model_optimizer      esqueleto + componentes
casos de prueba (cases.json)     2. componentes C++   native_generator            + parámetros (tuning.cli)
piezas de referencia en Python       └ más rápidos    native_optimizer         6. evaluación en benchmarks
  (oráculo + vista MIP)                                                           (scripts/*_eval.py)
```

1. **Modelo** (`llm/native_model_generator.py`): el LLM escribe el modelo C++ con el contrato genérico de
   `native/include/hsf/generic.hpp` (parseo de la instancia, solución trivial y al azar, violaciones por familia y
   términos del costo). `native/check_model.py` lo valida en un proceso aparte contra los casos visibles y ocultos y
   contra las piezas de referencia en Python en instancias generadas (mismas violaciones y mismo costo), y lo corrige
   con el LLM hasta `--rounds` rondas. `native_model_optimizer` pide una versión más rápida con las mismas salidas.
2. **Componentes** (`llm/native_generator.py`): constructores (`greedy_score`), vecindarios, perturbaciones y relinks
   en C++ sobre ese modelo (`native/generated.py` los compila juntos; las respuestas de corrección son ediciones,
   `native/edits.py`). `native/check.py` aplica las capas de `core/validation/` (contractual, calidad, diversidad
   contra los aceptados, aporte en combinación con cada esqueleto) en un proceso aparte. `native_optimizer` acelera
   los aceptados con pruebas diferenciales (`core/validation/equivalence.py`).
3. **Configuración** (`tuning/cli.py`): el espacio condicional (esqueleto → componentes de cada slot → parámetros,
   `config_space/`) se afina con irace (`--tuner irace`) o en tres etapas (`--tuner staged`, `tuning/staged.py`:
   primero la estructura, después irace en el espacio reducido). La configuración ganadora se mide en instancias
   de test contra los defaults de cada esqueleto. Las corridas son enteras en C++ (`core/native_runner.py`).

Los **esqueletos** son SA, ILS, VNS, TS, PR (path relinking con mejora tabú o ILS) y HYB (ILS en C++ alternado con
sub-MIPs en Python: destrucción + `MIPModelRepair`), en `native/include/hsf/core.hpp`, con su versión de referencia
en Python en `skeletons/` (misma semántica y parámetros, `core/assembler.py`).

## Organización

| directorio | qué hay |
|---|---|
| `core/` | contratos de los slots (`contracts.py`), registro de componentes, ensamblador, modelo por piezas (`model_parts.py`), packs (`problem_pack.py`, `packs.py`), catálogo (`catalog.py`), constructor greedy modular, `MIPModel`, validación por capas (`validation/`) |
| `skeletons/` | esqueletos en Python (referencia y HYB) |
| `native/` | contrato y esqueletos C++ (`include/hsf/`), compilación con caché, validación del modelo y de los componentes generados |
| `llm/` | cliente intercambiable (`client.py`: OpenAI, Anthropic, guionado) y la generación y optimización del modelo y de los componentes C++ |
| `tuning/`, `config_space/` | espacio de configuración, irace, configuración en etapas, evaluación en test |
| `examples/<problema>/` | lo humano de cada problema: `instance.py`, `llm_spec.py`, `cases.json`, `model_parts.py` y `pack.py`; `tune.py` es el CLI del tuning |
| `generated/<problema>_native/` | lo que escribió el LLM: modelo, componentes aceptados, transcripciones y estadísticas |
| `scripts/` | target-runner de irace, resúmenes de tuning y evaluación en benchmarks (Taillard, Uchoa, Trigeiro) |
| `results/` | resultados de las corridas |

## Problemas

| pack | problema | benchmark |
|---|---|---|
| `flowshop` | flow shop de permutación, flowtime total | Taillard |
| `flowshop_cmax` | flow shop de permutación, makespan | Taillard |
| `clsp` | lot sizing capacitado multi-ítem (con componentes y modelo Python a mano) | Trigeiro |
| `jobshop_gen` / `jobshop` | job shop, makespan (`jobshop`: catálogo y modelo C++ a mano) | Taillard |
| `cvrp_gen` / `cvrp` | CVRP con flota libre (`cvrp`: catálogo y modelo C++ a mano) | Uchoa X |

Un problema nuevo necesita la instancia (`to_text`/`parse`, generador), la descripción para el LLM (`ModelSpec`),
los casos de prueba y las piezas de referencia en Python (`model_parts.py`: oráculo de violaciones y costo, y la vista
MIP para HYB); `core.packs.parts_pack` arma el pack. Ver `examples/flowshop/`.

## Cómo correr

```bash
pip install -r requirements.txt          # el backend nativo necesita además g++
python -m pytest -q

export ANTHROPIC_API_KEY=...             # u OPENAI_API_KEY con --provider openai
P=flowshop; WS=generated/${P}_native
python -m llm.native_model_generator --problem $P --workspace $WS --provider anthropic
python -m llm.native_generator --problem $P --workspace $WS --provider anthropic --slots greedy_score neighborhood perturbation
python -m llm.native_optimizer --problem $P --workspace $WS --provider anthropic --slots neighborhood

# configuración (irace necesita R con el paquete irace: apt install r-cran-irace)
python -m examples.flowshop.tune --catalog generated --generated $WS --tuner irace --trials 70 --size 50x10,100x20 --scale-budget
python -m examples.flowshop.tune --catalog generated --generated $WS --tuner staged --trials 70

# evaluación en el benchmark con la configuración afinada
python -m scripts.pfsp_eval results/tune_runNN --generated $WS --native --t 60 --seeds 3
```

## GitHub Actions

| workflow | disparo | qué hace |
|---|---|---|
| `tests` | push, PR | `pytest` en Python 3.11 y 3.12 |
| `generar con LLM` | manual | `target`: `model`, `model_optimize`, `components` u `optimize` sobre `generated/<problema>_native`; deja lo generado en la rama `llm-generated/…` y abre un PR |
| `tuning (irace)` | manual | afina el catálogo `generated`, `handwritten` o los dos, evalúa en test y guarda los resultados en la rama `tuning/runN` (`results/tune_runN/`); réplicas en paralelo con `replicas` |

Los secretos van en *Settings → Secrets and variables → Actions*: `ANTHROPIC_API_KEY` (y `ANTHROPIC_WORKSPACE_ID` si
la clave no está asociada a un workspace) u `OPENAI_API_KEY`. Los precios por millón de tokens (`LLM_PRICE_IN`,
`LLM_PRICE_OUT`, como variables o inputs) agregan el costo estimado a las estadísticas.
