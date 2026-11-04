## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.37% | `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |

**Afinado entre réplicas**: media 0.37%, desvío 0.00%, rango [0.37%, 0.37%].

**Mejor no afinado** (media entre réplicas): `HYB:perturbation=jssp_noisy_start_redispatch` = 2.82%. Afinado vs ese: +2.45% de gap a favor del afinado, IC95 [+0.80%, +4.18%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15) · 0 configuraciones fallidas · 1496 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`

**Mejor en train**: `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` = 0.1379

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.37%** | **1232.2** | 55 | +86.6% | `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:perturbation=jssp_noisy_start_redispatch | 2.82% | 1263.2 | 79 | +86.3% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_noisy_start_redispatch, destruction=group_window]` |
| HYB:perturbation=jssp_critical_block_insertion | 3.38% | 1270.0 | 79 | +86.2% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=group_window]` |
| HYB:constructor=biased_job_repetition_sampling_best_of_k | 3.90% | 1275.6 | 63 | +86.2% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:neighborhood=composite | 4.07% | 1278.8 | 87 | +86.1% | `HYB[constructor=trivial, neighborhood=composite, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:constructor=giffler_thompson_grasp_active | 4.22% | 1279.8 | 67 | +86.1% | `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:neighborhood=critical_block_insertion | 6.51% | 1308.0 | 75 | +85.8% | `HYB[constructor=trivial, neighborhood=critical_block_insertion, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:constructor=neh_operation_insertion_partial_makespan | 6.80% | 1311.3 | 68 | +85.8% | `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:constructor=random | 8.46% | 1334.0 | 114 | +85.5% | `HYB[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:destruction=random_variables | 10.90% | 1359.9 | 109 | +85.2% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` |
| default:HYB | 12.58% | 1380.7 | 107 | +85.0% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:neighborhood=critical_segment_reversal | 25.68% | 1539.4 | 144 | +83.3% | `HYB[constructor=trivial, neighborhood=critical_segment_reversal, perturbation=jssp_critical_swap_walk, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **+2.45%**; gana en 5/6 instancias de test. Esqueletos explorados: HYB × 6.

Afinado vs `HYB:perturbation=jssp_noisy_start_redispatch` (mejor default por gap): +2.45% de gap a favor del afinado, IC95 [+0.80%, +4.18%].
