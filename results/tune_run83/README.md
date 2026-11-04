## Réplicas del tuning (3)

### Catálogo `generated`

60 trials · 30.0 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.04% | `PR[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, relink=lis_insertion_relink]` |
| r1 | 1 | 0.47% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, relink=swap_cycle_relink]` |
| r2 | 2 | 0.59% | `TS[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap]` |

**Afinado entre réplicas**: media 0.37%, desvío 0.24%, rango [0.04%, 0.59%].

**Mejor no afinado** (media entre réplicas): `default:SA` = 1.15%. Afinado vs ese: +0.78% de gap a favor del afinado, IC95 [+0.49%, +1.22%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 30.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15) · 0 configuraciones fallidas · 12284 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, relink=lis_insertion_relink]` = 0.1265

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.01%** | **1293.5** | 97 | +87.9% | `PR[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, relink=lis_insertion_relink]` |
| default:SA | 1.20% | 1308.7 | 97 | +87.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:TS | 1.21% | 1308.8 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:PR | 1.21% | 1308.8 | 97 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:VNS | 19.61% | 1552.0 | 197 | +85.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 19.88% | 1558.0 | 239 | +85.5% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+1.16%**; gana en 6/6 instancias de test. Esqueletos explorados: PR × 4, TS × 1.

Afinado vs `default:SA` (mejor default por gap): +1.18% de gap a favor del afinado, IC95 [+0.82%, +1.58%].

## Réplica r1

### Catálogo `generated`

60 trials · 30.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15) · 0 configuraciones fallidas · 12340 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, relink=swap_cycle_relink]` = 0.1266

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.04%** | **1298.8** | 95 | +87.9% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, relink=swap_cycle_relink]` |
| default:SA | 0.72% | 1308.0 | 102 | +87.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:PR | 0.80% | 1308.8 | 97 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 0.81% | 1308.8 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:VNS | 19.16% | 1552.0 | 197 | +85.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 19.86% | 1564.0 | 246 | +85.4% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+0.70%**; gana en 5/6 instancias de test. Esqueletos explorados: PR × 4, TS × 1.

Afinado vs `default:SA` (mejor default por gap): +0.68% de gap a favor del afinado, IC95 [+0.10%, +1.54%].

## Réplica r2

### Catálogo `generated`

60 trials · 30.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15) · 0 configuraciones fallidas · 12412 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap]` = 0.1267

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.14%** | **1300.3** | 93 | +87.9% | `TS[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 0.62% | 1307.0 | 99 | +87.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:PR | 0.78% | 1308.8 | 97 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 0.78% | 1308.8 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:VNS | 19.14% | 1552.0 | 197 | +85.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 19.84% | 1564.0 | 246 | +85.4% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+0.51%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 4, PR × 1.

Afinado vs `default:SA` (mejor default por gap): +0.48% de gap a favor del afinado, IC95 [+0.12%, +0.87%].
