## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.61% | `ILS[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| r1 | 1 | 0.49% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |

**Afinado entre réplicas**: media 0.55%, desvío 0.06%, rango [0.49%, 0.61%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 1.19%. Afinado vs ese: +0.63% de gap a favor del afinado, IC95 [+0.01%, +1.27%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 2969 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`

**Mejor en train**: `ILS[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` = 0.1271

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.42%** | **1305.6** | 95 | +87.8% | `ILS[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| default:PR | 0.98% | 1313.4 | 103 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 1.10% | 1314.4 | 95 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 1.25% | 1316.9 | 104 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:VNS | 18.85% | 1550.2 | 198 | +85.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 23.96% | 1618.4 | 237 | +84.9% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |
| default:HYB | 25.25% | 1628.5 | 208 | +84.8% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **+0.60%**; gana en 4/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:PR` (mejor default por gap): +0.56% de gap a favor del afinado, IC95 [-0.20%, +1.37%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 3058 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`

**Mejor en train**: `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` = 0.1269

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.38%** | **1304.2** | 96 | +87.8% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| default:PR | 1.09% | 1313.8 | 103 | +87.7% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 1.18% | 1314.4 | 95 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 1.43% | 1318.0 | 100 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:VNS | 18.96% | 1550.2 | 198 | +85.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:HYB | 22.96% | 1597.1 | 200 | +85.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| default:ILS | 24.61% | 1624.6 | 229 | +84.9% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+0.73%**; gana en 5/6 instancias de test. Esqueletos explorados: HYB × 6, ILS × 1, TS × 1.

Afinado vs `default:PR` (mejor default por gap): +0.70% de gap a favor del afinado, IC95 [+0.17%, +1.22%].
