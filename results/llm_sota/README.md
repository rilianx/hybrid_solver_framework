# Resultados publicados de los métodos con LLM

Transcritos de los papers (texto de los PDF de arXiv, versión más reciente), sin ejecutar nada. Cada valor en los JSON
trae paper, tabla y página, y si se leyó directamente o se infirió. Las dudas están en los `*_notas.md`.

| archivo | papers |
|---|---|
| `llm_ahd.json` | ReEvo (NeurIPS 2024), MCTS-AHD (ICML 2025), HSEvo (AAAI 2025), EoH (ICML 2024) |
| `cobench_frontierco.json` | CO-Bench (AAAI 2026), FrontierCO (ICLR 2026) |

## Qué hay por problema y contra qué instancias nuestras se compara

| problema | resultados publicados | nuestras instancias |
|---|---|---|
| CVRP | MCTS-AHD tabla 2 (ACO; CVRP50/100; EoH, ReEvo, MCTS-AHD con GPT-4o-mini); FrontierCO tabla 7 (Golden "easy", Arnold "hard"; FunSearch, Self-Refine, ReEvo, HGS) | `examples/cvrp/mcts_ahd/`, `examples/cvrp/frontierco/` |
| MKP | MCTS-AHD tabla 2 (ACO; MKP100/200); CO-Bench tabla 24 (OR-Library) | `examples/mkp/reevo/` (= los de MCTS-AHD), `examples/mkp/orlib/` |
| flow shop | EoH tablas 3 y 12 (GLS; Taillard makespan); CO-Bench tabla 17 | `examples/flowshop/taillard/` |
| job shop | CO-Bench tabla 21 (Taillard ta01–ta80) | `examples/jobshop/bench/` |
| facility location | FrontierCO tabla 8 (CFLP, demanda divisible: i1000 "easy", p2000 "hard"); CO-Bench tabla 7 (cap de la OR-Library, demanda divisible) | `examples/sscflp/bench/` (i1000 con `--large`; fuente única) |

## Cuidados al comparar

- MCTS-AHD: su gap es contra el mejor método de cada columna, no contra un solver; comparar el objetivo medio. Sus
  test50/100 de CVRP no son los de ReEvo (otro orden del generador; `examples/cvrp/fetch.py`); los de MKP sí.
- CO-Bench: score = min(h, h*)/max(h, h*) promediado por archivo; en job shop y flow shop la referencia es la cota
  inferior del encabezado de Taillard. Todos los agentes con o3-mini, 64 iteraciones, 10 s por instancia.
- FrontierCO: gap primal |c − c*| / max(|c|, |c*|); 64 iteraciones; hasta 3600 s por instancia; o4-mini en Self-Refine
  (en FunSearch y ReEvo no lo dice). En CFLP la demanda es divisible: nuestras i1000 de fuente única son otro problema
  (su óptimo es mayor o igual).
- ReEvo (paper propio): GPT-3.5-turbo, 100 evaluaciones; CVRP y MKP con ACO solo en figuras.

## Referencias propias para los conjuntos sin óptimo publicado

| conjunto | referencia | media | lo publicado, con gap contra nuestra referencia |
|---|---|---|---|
| CVRP50 de MCTS-AHD (64) | HGS, mejor de 3 semillas × 10 s | 8.014 | MCTS-AHD 9.286 (+15.9 %), DeepACO 8.888 (+10.9 %), ReEvo 9.327 (+16.4 %), EoH 9.359 (+16.8 %) |
| CVRP100 de MCTS-AHD (64) | ídem | 12.838 | MCTS-AHD 15.782 (+22.9 %), DeepACO 14.932 (+16.3 %), ReEvo 16.092 (+25.3 %), EoH 15.681 (+22.1 %) |
| MKP100 de ReEvo/MCTS-AHD (64) | óptimo (CBC) | 23.346 | MCTS-AHD 23.269 (−0.33 %), ReEvo 23.245, EoH 23.139 |
| MKP200 (64) | óptimo (CBC) | 42.939 | MCTS-AHD 42.498 (−1.03 %), ReEvo 42.416, EoH 41.994 |

(`examples/cvrp/mcts_ahd/best_known.json`, `examples/cvrp/reevo/best_known.json`, `examples/mkp/reevo_best_known.json`.)
