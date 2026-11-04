## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.00% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.00%, desvío 0.00%, rango [0.00%, 0.00%].

**Mejor no afinado** (media entre réplicas): `HYB:perturbation=jssp_critical_block_insertion` = 0.00%. Afinado vs ese: +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15) · 0 configuraciones fallidas · 40 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp_active`, `biased_job_repetition_sampling_best_of_k`, `neh_operation_insertion_partial_makespan`, `critical_arc_adjacent_swap`, `critical_block_insertion`, `critical_segment_reversal`, `jssp_critical_swap_walk`, `jssp_noisy_start_redispatch`, `jssp_critical_block_insertion`, `swap_cycle_relink`, `disjunctive_arc_flip_relink`, `lis_insertion_relink`, `critical_path_window_destruction`, `time_window_cross_machine_destruction`, `related_job_cluster_destruction`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` = 1000000000000.0000

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **nan%** | **1000000000000.0** | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` |
| default:HYB | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=random | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=random, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=giffler_thompson_grasp_active | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=biased_job_repetition_sampling_best_of_k | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=biased_job_repetition_sampling_best_of_k, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:constructor=neh_operation_insertion_partial_makespan | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:neighborhood=critical_block_insertion | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_block_insertion, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:neighborhood=critical_segment_reversal | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_segment_reversal, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:neighborhood=composite | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=composite, perturbation=jssp_critical_swap_walk, destruction=critical_path_window_destruction]` |
| HYB:perturbation=jssp_noisy_start_redispatch | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_noisy_start_redispatch, destruction=critical_path_window_destruction]` |
| HYB:perturbation=jssp_critical_block_insertion | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion, destruction=critical_path_window_destruction]` |
| HYB:destruction=time_window_cross_machine_destruction | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=time_window_cross_machine_destruction]` |
| HYB:destruction=related_job_cluster_destruction | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=related_job_cluster_destruction]` |
| HYB:destruction=group_window | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=group_window]` |
| HYB:destruction=random_variables | nan% | 1000000000000.0 | 0 | -10854620350.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk, destruction=random_variables]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): +nan% de gap a favor del afinado, IC95 [+nan%, +nan%] — **no se distingue del ruido** con estas instancias.
