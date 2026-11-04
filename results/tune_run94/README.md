## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.27% | `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.27%, desvío 0.00%, rango [0.27%, 0.27%].

**Mejor no afinado** (media entre réplicas): `HYB:perturbation=jssp_critical_block_insertion` = 3.40%. Afinado vs ese: +3.13% de gap a favor del afinado, IC95 [+1.88%, +4.26%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15) · 0 configuraciones fallidas · 1465 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`

**Mejor en train**: `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=random_variables]` = 0.1386

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.27%** | **1233.0** | 64 | +86.6% | `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=random_variables]` |
| HYB:perturbation=jssp_critical_block_insertion | 3.40% | 1271.8 | 76 | +86.2% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=group_window]` |
| HYB:constructor=biased_job_repetition_sampling_best_of_k | 4.16% | 1280.4 | 65 | +86.1% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:perturbation=jssp_noisy_start_redispatch | 4.89% | 1290.7 | 90 | +86.0% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_noisy_start_redispatch, destruction=group_window]` |
| HYB:constructor=giffler_thompson_grasp_active | 4.98% | 1290.5 | 64 | +86.0% | `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:neighborhood=composite | 5.38% | 1296.0 | 73 | +85.9% | `HYB[constructor=trivial, neighborhood=composite, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:neighborhood=critical_block_insertion | 7.32% | 1319.2 | 64 | +85.7% | `HYB[constructor=trivial, neighborhood=critical_block_insertion, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:constructor=neh_operation_insertion_partial_makespan | 7.91% | 1326.9 | 72 | +85.6% | `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:destruction=random_variables | 10.37% | 1355.4 | 84 | +85.3% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` |
| HYB:constructor=random | 10.46% | 1358.4 | 86 | +85.3% | `HYB[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| default:HYB | 13.17% | 1389.8 | 105 | +84.9% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:neighborhood=critical_segment_reversal | 27.21% | 1560.2 | 114 | +83.1% | `HYB[constructor=trivial, neighborhood=critical_segment_reversal, perturbation=jssp_critical_swap_walk, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **+3.05%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 6.

Afinado vs `HYB:perturbation=jssp_critical_block_insertion` (mejor default por gap): +3.13% de gap a favor del afinado, IC95 [+1.88%, +4.26%].
