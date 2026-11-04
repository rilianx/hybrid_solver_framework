## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.64% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=related_job_cluster_destruction]` |

**Afinado entre réplicas**: media 0.64%, desvío 0.00%, rango [0.64%, 0.64%].

**Mejor no afinado** (media entre réplicas): `HYB:perturbation=jssp_critical_block_insertion` = 4.11%. Afinado vs ese: +3.47% de gap a favor del afinado, IC95 [+1.68%, +5.50%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15) · 0 configuraciones fallidas · 2050 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`, `critical_path_window_destruction`, `time_window_cross_machine_destruction`, `related_job_cluster_destruction`

**Mejor en train**: `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=related_job_cluster_destruction]` = 0.1388

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.64%** | **1236.5** | 57 | +86.6% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=related_job_cluster_destruction]` |
| HYB:perturbation=jssp_critical_block_insertion | 4.11% | 1279.7 | 78 | +86.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=critical_path_window_destruction]` |
| HYB:neighborhood=composite | 4.35% | 1282.6 | 76 | +86.1% | `HYB[constructor=trivial, neighborhood=composite, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:perturbation=jssp_noisy_start_redispatch | 4.42% | 1284.1 | 90 | +86.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_noisy_start_redispatch, destruction=critical_path_window_destruction]` |
| HYB:constructor=biased_job_repetition_sampling_best_of_k | 4.85% | 1287.8 | 63 | +86.0% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=giffler_thompson_grasp_active | 4.96% | 1289.9 | 73 | +86.0% | `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:neighborhood=critical_block_insertion | 7.37% | 1318.9 | 67 | +85.7% | `HYB[constructor=trivial, neighborhood=critical_block_insertion, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=neh_operation_insertion_partial_makespan | 7.99% | 1327.2 | 77 | +85.6% | `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=random | 9.75% | 1349.1 | 94 | +85.4% | `HYB[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:destruction=group_window | 12.52% | 1381.1 | 107 | +85.0% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:destruction=random_variables | 14.71% | 1408.2 | 152 | +84.7% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` |
| default:HYB | 15.25% | 1416.0 | 157 | +84.6% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:destruction=related_job_cluster_destruction | 15.46% | 1418.4 | 154 | +84.6% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=related_job_cluster_destruction]` |
| HYB:destruction=time_window_cross_machine_destruction | 16.10% | 1426.3 | 151 | +84.5% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=time_window_cross_machine_destruction]` |
| HYB:neighborhood=critical_segment_reversal | 28.09% | 1571.4 | 142 | +82.9% | `HYB[constructor=trivial, neighborhood=critical_segment_reversal, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |

Ganancia del afinado sobre el mejor default: **+3.37%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `HYB:perturbation=jssp_critical_block_insertion` (mejor default por gap): +3.47% de gap a favor del afinado, IC95 [+1.68%, +5.50%].
