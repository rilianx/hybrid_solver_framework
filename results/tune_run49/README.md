## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.98% | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| r1 | 1 | 1.66% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| r2 | 2 | 2.33% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |

**Afinado entre réplicas**: media 1.99%, desvío 0.28%, rango [1.66%, 2.33%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=dispatch_token_insertion` = 1.92%. Afinado vs ese: -0.07% de gap a favor del afinado, IC95 [-0.51%, +0.37%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop_operations 10x10) · 0 configuraciones fallidas · 3812 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_block_neighborhood_destruction`, `related_jobs_shaw_destruction`, `time_window_destruction`, `earliest_completion_compact`, `makespan_lower_bound_lookahead`, `most_work_remaining_with_start_penalty`, `critical_block_adjacent_swap`, `critical_block_reinsertion`, `dispatch_token_insertion`, `contiguous_segment_shuffle`, `critical_arc_reversal_kick`, `random_distinct_pair_swaps`

**Mejor en train**: `SA[constructor=random, neighborhood=dispatch_token_insertion]` = 0.7631 (mejor default: 0.7773, `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.97%** | **850.5** | 43 | +23.5% | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| SA:neighborhood=dispatch_token_insertion | 1.90% | 850.0 | 45 | +23.5% | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| ILS:perturbation=random_distinct_pair_swaps | 2.93% | 858.9 | 51 | +22.7% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=random_distinct_pair_swaps]` |
| SA:constructor=greedy_most_work_remaining_with_start_penalty | 3.14% | 860.4 | 50 | +22.6% | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=greedy_earliest_completion_compact | 3.17% | 860.7 | 49 | +22.6% | `SA[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap]` |
| VNS:constructor=greedy_earliest_completion_compact | 3.37% | 862.5 | 53 | +22.4% | `VNS[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap]` |
| default:SA | 3.61% | 864.3 | 46 | +22.2% | `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| VNS:constructor=greedy_most_work_remaining_with_start_penalty | 3.82% | 865.9 | 45 | +22.1% | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap]` |
| ILS:perturbation=critical_arc_reversal_kick | 4.14% | 868.9 | 53 | +21.8% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=critical_arc_reversal_kick]` |
| default:VNS | 4.44% | 871.4 | 51 | +21.6% | `VNS[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| VNS:neighborhood=dispatch_token_insertion | 4.45% | 871.3 | 48 | +21.6% | `VNS[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| ILS:neighborhood=dispatch_token_insertion | 4.99% | 875.8 | 50 | +21.2% | `ILS[constructor=trivial, neighborhood=dispatch_token_insertion, perturbation=contiguous_segment_shuffle]` |
| SA:constructor=random | 5.19% | 877.5 | 50 | +21.1% | `SA[constructor=random, neighborhood=critical_block_adjacent_swap]` |
| VNS:constructor=random | 5.33% | 878.8 | 53 | +20.9% | `VNS[constructor=random, neighborhood=critical_block_adjacent_swap]` |
| VNS:neighborhood=critical_block_reinsertion | 5.92% | 883.9 | 59 | +20.5% | `VNS[constructor=trivial, neighborhood=critical_block_reinsertion]` |
| LNS_MIP:constructor=greedy_earliest_completion_compact | 5.92% | 883.6 | 50 | +20.5% | `LNS_MIP[constructor=greedy_earliest_completion_compact, destruction=critical_block_neighborhood_destruction]` |
| default:ILS | 6.32% | 887.1 | 59 | +20.2% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| ILS:neighborhood=critical_block_reinsertion | 7.03% | 892.9 | 52 | +19.7% | `ILS[constructor=trivial, neighborhood=critical_block_reinsertion, perturbation=contiguous_segment_shuffle]` |
| ILS:constructor=greedy_earliest_completion_compact | 7.36% | 896.2 | 68 | +19.4% | `ILS[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| ILS:constructor=greedy_most_work_remaining_with_start_penalty | 7.98% | 900.6 | 47 | +19.0% | `ILS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:constructor=greedy_most_work_remaining_with_start_penalty | 8.03% | 901.2 | 65 | +18.9% | `LNS_MIP[constructor=greedy_most_work_remaining_with_start_penalty, destruction=critical_block_neighborhood_destruction]` |
| VNS:constructor=greedy_makespan_lower_bound_lookahead | 8.06% | 901.1 | 56 | +18.9% | `VNS[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=greedy_makespan_lower_bound_lookahead | 8.06% | 901.5 | 57 | +18.9% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap]` |
| ILS:constructor=random | 8.53% | 905.4 | 63 | +18.6% | `ILS[constructor=random, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:destruction=related_jobs_shaw_destruction | 9.25% | 911.5 | 67 | +18.0% | `LNS_MIP[constructor=trivial, destruction=related_jobs_shaw_destruction]` |
| default:LNS_MIP | 9.75% | 915.8 | 71 | +17.6% | `LNS_MIP[constructor=trivial, destruction=critical_block_neighborhood_destruction]` |
| LNS_MIP:destruction=time_window_destruction | 9.78% | 916.0 | 73 | +17.6% | `LNS_MIP[constructor=trivial, destruction=time_window_destruction]` |
| SA:neighborhood=critical_block_reinsertion | 11.06% | 926.6 | 58 | +16.6% | `SA[constructor=trivial, neighborhood=critical_block_reinsertion]` |
| LNS_MIP:constructor=random | 11.85% | 933.4 | 83 | +16.0% | `LNS_MIP[constructor=random, destruction=critical_block_neighborhood_destruction]` |
| ILS:constructor=greedy_makespan_lower_bound_lookahead | 17.19% | 976.7 | 74 | +12.1% | `ILS[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:constructor=greedy_makespan_lower_bound_lookahead | 19.52% | 995.9 | 81 | +10.4% | `LNS_MIP[constructor=greedy_makespan_lower_bound_lookahead, destruction=critical_block_neighborhood_destruction]` |

Ganancia del afinado sobre el mejor default: **-0.06%**; gana en 4/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=dispatch_token_insertion` (mejor default por gap): -0.07% de gap a favor del afinado, IC95 [-0.61%, +0.49%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 39 (numéricos por defecto) ✔ | 0.7631 | 0.7641, 0.7624, 0.7631, 0.7608, 0.7652, 0.7623, 0.7640 | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| 16 | 0.7636 | 0.7637, 0.7646, 0.7613, 0.7655, 0.7638, 0.7651, 0.7612 | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| 25 (numéricos por defecto) | 0.7637 | 0.7604, 0.7651, 0.7627, 0.7594, 0.7652, 0.7678, 0.7653 | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
| 20 (numéricos por defecto) | 0.7639 | 0.7597, 0.7648, 0.7641, 0.7677, 0.7675, 0.7621, 0.7618 | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| 25 | 0.7693 | 0.7613, 0.7684, 0.7725, 0.7749 | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
| 39 | 0.7715 | 0.7684, 0.7696, 0.7766 | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| 20 | 0.7723 | 0.7719, 0.7656, 0.7795 | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| 0* | 0.7782 | 0.7773, 0.7782, 0.7791 | `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop_operations 10x10) · 0 configuraciones fallidas · 4128 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_block_neighborhood_destruction`, `related_jobs_shaw_destruction`, `time_window_destruction`, `earliest_completion_compact`, `makespan_lower_bound_lookahead`, `most_work_remaining_with_start_penalty`, `critical_block_adjacent_swap`, `critical_block_reinsertion`, `dispatch_token_insertion`, `contiguous_segment_shuffle`, `critical_arc_reversal_kick`, `random_distinct_pair_swaps`

**Mejor en train**: `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` = 0.7629 (mejor default: 0.7699, `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.45%** | **847.9** | 45 | +23.7% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| SA:neighborhood=dispatch_token_insertion | 1.11% | 845.0 | 44 | +24.0% | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| ILS:perturbation=random_distinct_pair_swaps | 2.40% | 856.1 | 49 | +23.0% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=random_distinct_pair_swaps]` |
| VNS:constructor=greedy_earliest_completion_compact | 2.98% | 860.9 | 51 | +22.6% | `VNS[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=greedy_most_work_remaining_with_start_penalty | 2.99% | 860.7 | 47 | +22.6% | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=greedy_earliest_completion_compact | 3.01% | 861.1 | 48 | +22.5% | `SA[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap]` |
| default:SA | 3.13% | 862.0 | 48 | +22.5% | `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| VNS:constructor=greedy_most_work_remaining_with_start_penalty | 3.44% | 864.3 | 45 | +22.2% | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap]` |
| ILS:perturbation=critical_arc_reversal_kick | 3.89% | 868.4 | 52 | +21.9% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=critical_arc_reversal_kick]` |
| SA:constructor=random | 4.00% | 869.3 | 52 | +21.8% | `SA[constructor=random, neighborhood=critical_block_adjacent_swap]` |
| VNS:neighborhood=dispatch_token_insertion | 4.02% | 869.4 | 48 | +21.8% | `VNS[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| default:VNS | 4.21% | 871.1 | 51 | +21.6% | `VNS[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| ILS:neighborhood=dispatch_token_insertion | 4.66% | 874.7 | 51 | +21.3% | `ILS[constructor=trivial, neighborhood=dispatch_token_insertion, perturbation=contiguous_segment_shuffle]` |
| VNS:constructor=random | 5.10% | 878.6 | 53 | +21.0% | `VNS[constructor=random, neighborhood=critical_block_adjacent_swap]` |
| LNS_MIP:constructor=greedy_earliest_completion_compact | 5.24% | 879.7 | 53 | +20.9% | `LNS_MIP[constructor=greedy_earliest_completion_compact, destruction=critical_block_neighborhood_destruction]` |
| VNS:neighborhood=critical_block_reinsertion | 5.57% | 882.7 | 59 | +20.6% | `VNS[constructor=trivial, neighborhood=critical_block_reinsertion]` |
| default:ILS | 6.12% | 887.1 | 59 | +20.2% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| SA:constructor=greedy_makespan_lower_bound_lookahead | 6.66% | 891.3 | 58 | +19.8% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap]` |
| ILS:neighborhood=critical_block_reinsertion | 6.80% | 892.7 | 51 | +19.7% | `ILS[constructor=trivial, neighborhood=critical_block_reinsertion, perturbation=contiguous_segment_shuffle]` |
| ILS:constructor=greedy_earliest_completion_compact | 7.16% | 896.2 | 68 | +19.4% | `ILS[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:constructor=greedy_most_work_remaining_with_start_penalty | 7.47% | 898.2 | 60 | +19.2% | `LNS_MIP[constructor=greedy_most_work_remaining_with_start_penalty, destruction=critical_block_neighborhood_destruction]` |
| VNS:constructor=greedy_makespan_lower_bound_lookahead | 7.71% | 899.8 | 57 | +19.1% | `VNS[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap]` |
| ILS:constructor=greedy_most_work_remaining_with_start_penalty | 7.71% | 900.0 | 47 | +19.0% | `ILS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| ILS:constructor=random | 8.19% | 904.3 | 63 | +18.7% | `ILS[constructor=random, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:destruction=related_jobs_shaw_destruction | 8.21% | 904.5 | 64 | +18.6% | `LNS_MIP[constructor=trivial, destruction=related_jobs_shaw_destruction]` |
| LNS_MIP:destruction=time_window_destruction | 8.29% | 905.4 | 68 | +18.6% | `LNS_MIP[constructor=trivial, destruction=time_window_destruction]` |
| default:LNS_MIP | 8.57% | 907.4 | 66 | +18.4% | `LNS_MIP[constructor=trivial, destruction=critical_block_neighborhood_destruction]` |
| SA:neighborhood=critical_block_reinsertion | 8.69% | 908.5 | 56 | +18.3% | `SA[constructor=trivial, neighborhood=critical_block_reinsertion]` |
| LNS_MIP:constructor=random | 9.50% | 915.7 | 68 | +17.6% | `LNS_MIP[constructor=random, destruction=critical_block_neighborhood_destruction]` |
| ILS:constructor=greedy_makespan_lower_bound_lookahead | 16.82% | 975.5 | 73 | +12.2% | `ILS[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:constructor=greedy_makespan_lower_bound_lookahead | 17.18% | 978.7 | 77 | +12.0% | `LNS_MIP[constructor=greedy_makespan_lower_bound_lookahead, destruction=critical_block_neighborhood_destruction]` |

Ganancia del afinado sobre el mejor default: **-0.35%**; gana en 3/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=dispatch_token_insertion` (mejor default por gap): -0.34% de gap a favor del afinado, IC95 [-0.89%, +0.17%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 19 (numéricos por defecto) ✔ | 0.7629 | 0.7588, 0.7716, 0.7648, 0.7608, 0.7610, 0.7620, 0.7610 | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| 35 (numéricos por defecto) | 0.7630 | 0.7652, 0.7628, 0.7602, 0.7618, 0.7696, 0.7612, 0.7602 | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| 29 | 0.7639 | 0.7587, 0.7649, 0.7679, 0.7665, 0.7632, 0.7638, 0.7623 | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| 19 | 0.7640 | 0.7634, 0.7624, 0.7651, 0.7595, 0.7698, 0.7672, 0.7605 | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| 29 (numéricos por defecto) | 0.7645 | 0.7628, 0.7684, 0.7639, 0.7659, 0.7652, 0.7650, 0.7606 | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| 35 | 0.7700 | 0.7682, 0.7681, 0.7738 | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| 34 | 0.7710 | 0.7698, 0.7754, 0.7678 | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
| 0* | 0.7729 | 0.7699, 0.7726, 0.7762 | `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| 34 (numéricos por defecto) | 0.7774 | 0.7717, 0.7774, 0.7830 | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop_operations 10x10) · 0 configuraciones fallidas · 4425 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_block_neighborhood_destruction`, `related_jobs_shaw_destruction`, `time_window_destruction`, `earliest_completion_compact`, `makespan_lower_bound_lookahead`, `most_work_remaining_with_start_penalty`, `critical_block_adjacent_swap`, `critical_block_reinsertion`, `dispatch_token_insertion`, `contiguous_segment_shuffle`, `critical_arc_reversal_kick`, `random_distinct_pair_swaps`

**Mejor en train**: `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` = 0.7642 (mejor default: 0.7809, `VNS[constructor=trivial, neighborhood=critical_block_adjacent_swap]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.09%** | **853.3** | 41 | +23.2% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| SA:neighborhood=dispatch_token_insertion | 2.30% | 855.3 | 46 | +23.1% | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| ILS:perturbation=random_distinct_pair_swaps | 3.04% | 861.6 | 49 | +22.5% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=random_distinct_pair_swaps]` |
| VNS:constructor=greedy_earliest_completion_compact | 3.21% | 863.2 | 53 | +22.3% | `VNS[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=greedy_earliest_completion_compact | 3.46% | 865.2 | 51 | +22.2% | `SA[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap]` |
| VNS:constructor=greedy_most_work_remaining_with_start_penalty | 3.67% | 866.7 | 46 | +22.0% | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap]` |
| default:SA | 4.28% | 872.0 | 53 | +21.6% | `SA[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| ILS:perturbation=critical_arc_reversal_kick | 4.30% | 872.2 | 53 | +21.5% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=critical_arc_reversal_kick]` |
| VNS:neighborhood=dispatch_token_insertion | 4.30% | 872.0 | 48 | +21.6% | `VNS[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| default:VNS | 4.34% | 872.5 | 51 | +21.5% | `VNS[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=greedy_most_work_remaining_with_start_penalty | 4.58% | 874.4 | 52 | +21.3% | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap]` |
| ILS:neighborhood=dispatch_token_insertion | 5.00% | 878.0 | 52 | +21.0% | `ILS[constructor=trivial, neighborhood=dispatch_token_insertion, perturbation=contiguous_segment_shuffle]` |
| VNS:constructor=random | 5.16% | 879.4 | 52 | +20.9% | `VNS[constructor=random, neighborhood=critical_block_adjacent_swap]` |
| SA:constructor=random | 5.70% | 883.9 | 53 | +20.5% | `SA[constructor=random, neighborhood=critical_block_adjacent_swap]` |
| LNS_MIP:constructor=greedy_earliest_completion_compact | 5.73% | 884.0 | 51 | +20.5% | `LNS_MIP[constructor=greedy_earliest_completion_compact, destruction=critical_block_neighborhood_destruction]` |
| VNS:neighborhood=critical_block_reinsertion | 5.94% | 886.0 | 58 | +20.3% | `VNS[constructor=trivial, neighborhood=critical_block_reinsertion]` |
| default:ILS | 6.32% | 889.1 | 57 | +20.0% | `ILS[constructor=trivial, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| ILS:neighborhood=critical_block_reinsertion | 7.08% | 895.4 | 52 | +19.5% | `ILS[constructor=trivial, neighborhood=critical_block_reinsertion, perturbation=contiguous_segment_shuffle]` |
| ILS:constructor=greedy_earliest_completion_compact | 7.32% | 897.8 | 69 | +19.2% | `ILS[constructor=greedy_earliest_completion_compact, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| ILS:constructor=greedy_most_work_remaining_with_start_penalty | 7.76% | 900.7 | 47 | +19.0% | `ILS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| VNS:constructor=greedy_makespan_lower_bound_lookahead | 8.28% | 904.9 | 55 | +18.6% | `VNS[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap]` |
| ILS:constructor=random | 8.44% | 906.7 | 64 | +18.4% | `ILS[constructor=random, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:constructor=greedy_most_work_remaining_with_start_penalty | 8.59% | 908.1 | 70 | +18.3% | `LNS_MIP[constructor=greedy_most_work_remaining_with_start_penalty, destruction=critical_block_neighborhood_destruction]` |
| SA:constructor=greedy_makespan_lower_bound_lookahead | 9.50% | 915.0 | 61 | +17.7% | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap]` |
| default:LNS_MIP | 9.66% | 917.0 | 71 | +17.5% | `LNS_MIP[constructor=trivial, destruction=critical_block_neighborhood_destruction]` |
| SA:neighborhood=critical_block_reinsertion | 10.36% | 922.9 | 63 | +17.0% | `SA[constructor=trivial, neighborhood=critical_block_reinsertion]` |
| LNS_MIP:destruction=related_jobs_shaw_destruction | 10.93% | 927.8 | 72 | +16.5% | `LNS_MIP[constructor=trivial, destruction=related_jobs_shaw_destruction]` |
| LNS_MIP:destruction=time_window_destruction | 11.24% | 930.3 | 74 | +16.3% | `LNS_MIP[constructor=trivial, destruction=time_window_destruction]` |
| LNS_MIP:constructor=random | 12.33% | 939.7 | 82 | +15.5% | `LNS_MIP[constructor=random, destruction=critical_block_neighborhood_destruction]` |
| ILS:constructor=greedy_makespan_lower_bound_lookahead | 17.29% | 979.7 | 72 | +11.9% | `ILS[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=critical_block_adjacent_swap, perturbation=contiguous_segment_shuffle]` |
| LNS_MIP:constructor=greedy_makespan_lower_bound_lookahead | 22.36% | 1020.7 | 85 | +8.2% | `LNS_MIP[constructor=greedy_makespan_lower_bound_lookahead, destruction=critical_block_neighborhood_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.24%**; gana en 6/10 instancias de test. Esqueletos explorados: SA × 22, ILS × 7, VNS × 6, LNS_MIP × 5.

Afinado vs `SA:neighborhood=dispatch_token_insertion` (mejor default por gap): +0.22% de gap a favor del afinado, IC95 [-0.63%, +1.06%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 30 (numéricos por defecto) ✔ | 0.7642 | 0.7669, 0.7640, 0.7616, 0.7609, 0.7690, 0.7648, 0.7623 | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| 16 | 0.7650 | 0.7592, 0.7679, 0.7691, 0.7630, 0.7621, 0.7724, 0.7616 | `SA[constructor=trivial, neighborhood=dispatch_token_insertion]` |
| 21 (numéricos por defecto) | 0.7652 | 0.7602, 0.7651, 0.7690, 0.7654, 0.7681, 0.7670, 0.7619 | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
| 39 (numéricos por defecto) | 0.7656 | 0.7663, 0.7638, 0.7682, 0.7603, 0.7729, 0.7649, 0.7628 | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| 39 | 0.7658 | 0.7615, 0.7632, 0.7614, 0.7690, 0.7659, 0.7721, 0.7678 | `SA[constructor=random, neighborhood=dispatch_token_insertion]` |
| 30 | 0.7662 | 0.7614, 0.7670, 0.7655, 0.7687, 0.7640, 0.7755, 0.7613 | `SA[constructor=greedy_makespan_lower_bound_lookahead, neighborhood=dispatch_token_insertion]` |
| 21 | 0.7716 | 0.7725, 0.7702, 0.7719 | `SA[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
| 33 | 0.7736 | 0.7756, 0.7784, 0.7669 | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
| 2* | 0.7744 | 0.7809, 0.7765, 0.7659 | `VNS[constructor=trivial, neighborhood=critical_block_adjacent_swap]` |
| 33 (numéricos por defecto) | 0.7768 | 0.7716, 0.7752, 0.7838 | `VNS[constructor=greedy_most_work_remaining_with_start_penalty, neighborhood=dispatch_token_insertion]` |
