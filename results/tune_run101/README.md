## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.11% | `ILS[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=composite, perturbation=jssp_critical_swap_walk]` |
| r1 | 1 | 0.48% | `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, relink=swap_cycle_relink]` |

**Afinado entre réplicas**: media 0.80%, desvío 0.32%, rango [0.48%, 1.11%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 1.58%. Afinado vs ese: +0.78% de gap a favor del afinado, IC95 [+0.12%, +1.39%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 2954 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`, `job_flowtime_power_tiebreak`, `critical_ops_count_tiebreak`

**Mejor en train**: `ILS[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=composite, perturbation=jssp_critical_swap_walk]` = 0.1273

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.42%** | **1307.2** | 97 | +87.8% | `ILS[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=composite, perturbation=jssp_critical_swap_walk]` |
| default:PR | 1.05% | 1316.0 | 105 | +87.7% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 1.05% | 1315.3 | 95 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 1.42% | 1320.3 | 100 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:VNS | 20.75% | 1575.1 | 193 | +85.3% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:HYB | 22.29% | 1597.2 | 226 | +85.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| default:ILS | 26.50% | 1652.0 | 219 | +84.6% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+0.61%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 7, HYB × 1.

Afinado vs `default:PR` (mejor default por gap): +0.63% de gap a favor del afinado, IC95 [-0.13%, +1.45%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 2845 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`, `job_flowtime_power_tiebreak`, `critical_ops_count_tiebreak`

**Mejor en train**: `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, relink=swap_cycle_relink]` = 0.1270

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.48%** | **1299.3** | 100 | +87.9% | `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, relink=swap_cycle_relink]` |
| default:PR | 1.41% | 1311.2 | 101 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 1.48% | 1311.8 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 1.65% | 1314.3 | 99 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:HYB | 17.96% | 1525.4 | 188 | +85.8% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| default:VNS | 18.01% | 1529.2 | 185 | +85.7% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 24.09% | 1612.0 | 247 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+0.91%**; gana en 5/6 instancias de test. Esqueletos explorados: PR × 8.

Afinado vs `default:PR` (mejor default por gap): +0.93% de gap a favor del afinado, IC95 [+0.26%, +1.64%].
