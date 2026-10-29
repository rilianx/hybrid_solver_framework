## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.99% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| r1 | 1 | 2.53% | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| r2 | 2 | 2.52% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |

**Afinado entre réplicas**: media 2.35%, desvío 0.26%, rango [1.99%, 2.53%].

**Mejor no afinado** (media entre réplicas): `VNS:constructor=greedy_earliest_completion_idle_penalty` = 5.00%. Afinado vs ese: +2.66% de gap a favor del afinado, IC95 [+0.73%, +4.49%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop_sequences 10x10) · 0 configuraciones fallidas · 3673 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_block_window_destruction`, `related_jobs_slot_destruction`, `time_slice_destruction`, `bottleneck_machine_load_priority`, `earliest_completion_idle_penalty`, `most_work_remaining_tail_bound`, `critical_operation_reinsertion`, `critical_path_adjacent_swap`, `job_priority_shift_all_machines`, `acyclic_random_insertions`, `critical_block_adjacent_swaps`, `noisy_start_key_redispatch`

**Mejor en train**: `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` = 0.2131 (mejor default: 0.2255, `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.90%** | **853.8** | 42 | +78.5% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| VNS:constructor=greedy_earliest_completion_idle_penalty | 4.81% | 878.5 | 52 | +77.9% | `VNS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=greedy_earliest_completion_idle_penalty | 5.38% | 883.2 | 54 | +77.8% | `ILS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| VNS:constructor=greedy_most_work_remaining_tail_bound | 5.46% | 883.7 | 52 | +77.8% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion]` |
| ILS:neighborhood=critical_path_adjacent_swap | 5.74% | 886.5 | 59 | +77.7% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| ILS:constructor=greedy_most_work_remaining_tail_bound | 5.85% | 887.1 | 52 | +77.7% | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| VNS:constructor=greedy_bottleneck_machine_load_priority | 6.42% | 892.2 | 64 | +77.6% | `VNS[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=greedy_bottleneck_machine_load_priority | 6.45% | 892.7 | 63 | +77.6% | `ILS[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| VNS:neighborhood=critical_path_adjacent_swap | 6.48% | 891.7 | 53 | +77.6% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| VNS:constructor=random | 6.56% | 893.2 | 59 | +77.5% | `VNS[constructor=random, neighborhood=critical_operation_reinsertion]` |
| SA:constructor=greedy_earliest_completion_idle_penalty | 6.79% | 895.1 | 56 | +77.5% | `SA[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion]` |
| ILS:perturbation=critical_block_adjacent_swaps | 7.12% | 897.9 | 57 | +77.4% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=critical_block_adjacent_swaps]` |
| SA:constructor=greedy_most_work_remaining_tail_bound | 7.29% | 898.9 | 53 | +77.4% | `SA[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=random | 7.91% | 904.3 | 63 | +77.3% | `ILS[constructor=random, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| SA:constructor=greedy_bottleneck_machine_load_priority | 9.93% | 921.9 | 71 | +76.8% | `SA[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion]` |
| default:ILS | 10.58% | 926.7 | 59 | +76.7% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| default:VNS | 10.86% | 929.1 | 56 | +76.6% | `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
| SA:constructor=random | 11.28% | 932.6 | 67 | +76.5% | `SA[constructor=random, neighborhood=critical_operation_reinsertion]` |
| SA:neighborhood=critical_path_adjacent_swap | 13.55% | 952.0 | 65 | +76.1% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| LNS_MIP:constructor=greedy_earliest_completion_idle_penalty | 14.25% | 958.3 | 73 | +75.9% | `LNS_MIP[constructor=greedy_earliest_completion_idle_penalty, destruction=critical_block_window_destruction]` |
| ILS:perturbation=noisy_start_key_redispatch | 15.61% | 968.9 | 63 | +75.6% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=noisy_start_key_redispatch]` |
| LNS_MIP:constructor=greedy_most_work_remaining_tail_bound | 16.67% | 977.2 | 50 | +75.4% | `LNS_MIP[constructor=greedy_most_work_remaining_tail_bound, destruction=critical_block_window_destruction]` |
| default:SA | 29.04% | 1082.3 | 155 | +72.8% | `SA[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
| LNS_MIP:constructor=greedy_bottleneck_machine_load_priority | 42.83% | 1197.1 | 171 | +69.9% | `LNS_MIP[constructor=greedy_bottleneck_machine_load_priority, destruction=critical_block_window_destruction]` |
| ILS:neighborhood=job_priority_shift_all_machines | 95.22% | 1636.0 | 134 | +58.9% | `ILS[constructor=trivial, neighborhood=job_priority_shift_all_machines, perturbation=acyclic_random_insertions]` |
| LNS_MIP:constructor=random | 100.55% | 1678.3 | 201 | +57.8% | `LNS_MIP[constructor=random, destruction=critical_block_window_destruction]` |
| VNS:neighborhood=job_priority_shift_all_machines | 101.79% | 1688.2 | 217 | +57.5% | `VNS[constructor=trivial, neighborhood=job_priority_shift_all_machines]` |
| LNS_MIP:destruction=time_slice_destruction | 136.37% | 1980.8 | 294 | +50.2% | `LNS_MIP[constructor=trivial, destruction=time_slice_destruction]` |
| SA:neighborhood=job_priority_shift_all_machines | 281.26% | 3193.7 | 273 | +19.7% | `SA[constructor=trivial, neighborhood=job_priority_shift_all_machines]` |
| LNS_MIP:destruction=related_jobs_slot_destruction | 341.42% | 3700.6 | 451 | +6.9% | `LNS_MIP[constructor=trivial, destruction=related_jobs_slot_destruction]` |
| default:LNS_MIP | 364.51% | 3898.7 | 516 | +2.0% | `LNS_MIP[constructor=trivial, destruction=critical_block_window_destruction]` |

Ganancia del afinado sobre el mejor default: **+2.81%**; gana en 9/10 instancias de test. Esqueletos explorados: ILS × 21, SA × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `VNS:constructor=greedy_earliest_completion_idle_penalty` (mejor default por gap): +2.91% de gap a favor del afinado, IC95 [+0.79%, +4.97%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 29 (numéricos por defecto) ✔ | 0.2131 | 0.2130, 0.2137, 0.2127, 0.2127, 0.2134, 0.2128, 0.2131 | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| 34 | 0.2142 | 0.2128, 0.2145, 0.2166, 0.2143, 0.2121, 0.2120, 0.2169 | `ILS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 21 | 0.2148 | 0.2129, 0.2124, 0.2160, 0.2138, 0.2167, 0.2172, 0.2147 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 29 | 0.2166 | 0.2175, 0.2180, 0.2143 | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| 10 | 0.2179 | 0.2197, 0.2175, 0.2165 | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| 9 | 0.2194 | 0.2188, 0.2201, 0.2192 | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| 21 (numéricos por defecto) | 0.2211 | 0.2222, 0.2203, 0.2207 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 34 (numéricos por defecto) | 0.2228 | 0.2216, 0.2231, 0.2235 | `ILS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 2* | 0.2256 | 0.2255, 0.2281, 0.2233 | `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop_sequences 10x10) · 0 configuraciones fallidas · 3628 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_block_window_destruction`, `related_jobs_slot_destruction`, `time_slice_destruction`, `bottleneck_machine_load_priority`, `earliest_completion_idle_penalty`, `most_work_remaining_tail_bound`, `critical_operation_reinsertion`, `critical_path_adjacent_swap`, `job_priority_shift_all_machines`, `acyclic_random_insertions`, `critical_block_adjacent_swaps`, `noisy_start_key_redispatch`

**Mejor en train**: `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` = 0.2140 (mejor default: 0.2276, `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.16%** | **858.7** | 49 | +78.4% | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| VNS:constructor=greedy_earliest_completion_idle_penalty | 4.67% | 879.8 | 53 | +77.9% | `VNS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion]` |
| VNS:constructor=greedy_most_work_remaining_tail_bound | 5.45% | 886.0 | 53 | +77.7% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=greedy_earliest_completion_idle_penalty | 5.58% | 887.4 | 55 | +77.7% | `ILS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| ILS:constructor=greedy_most_work_remaining_tail_bound | 5.95% | 890.4 | 52 | +77.6% | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| ILS:neighborhood=critical_path_adjacent_swap | 6.06% | 891.8 | 61 | +77.6% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| SA:constructor=greedy_earliest_completion_idle_penalty | 6.21% | 893.1 | 62 | +77.5% | `SA[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion]` |
| VNS:constructor=greedy_bottleneck_machine_load_priority | 6.43% | 894.9 | 63 | +77.5% | `VNS[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=greedy_bottleneck_machine_load_priority | 6.90% | 899.1 | 68 | +77.4% | `ILS[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| VNS:constructor=random | 7.03% | 899.7 | 59 | +77.4% | `VNS[constructor=random, neighborhood=critical_operation_reinsertion]` |
| VNS:neighborhood=critical_path_adjacent_swap | 7.21% | 900.0 | 53 | +77.4% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| SA:constructor=greedy_most_work_remaining_tail_bound | 7.30% | 901.6 | 54 | +77.3% | `SA[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion]` |
| ILS:perturbation=critical_block_adjacent_swaps | 7.84% | 906.5 | 58 | +77.2% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=critical_block_adjacent_swaps]` |
| ILS:constructor=random | 8.63% | 913.0 | 66 | +77.0% | `ILS[constructor=random, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| SA:constructor=greedy_bottleneck_machine_load_priority | 8.72% | 914.6 | 72 | +77.0% | `SA[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion]` |
| default:ILS | 10.58% | 929.3 | 60 | +76.6% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| default:VNS | 11.71% | 938.8 | 59 | +76.4% | `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
| SA:constructor=random | 12.55% | 946.2 | 84 | +76.2% | `SA[constructor=random, neighborhood=critical_operation_reinsertion]` |
| LNS_MIP:constructor=greedy_earliest_completion_idle_penalty | 14.67% | 964.7 | 75 | +75.7% | `LNS_MIP[constructor=greedy_earliest_completion_idle_penalty, destruction=critical_block_window_destruction]` |
| ILS:perturbation=noisy_start_key_redispatch | 16.28% | 977.1 | 63 | +75.4% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=noisy_start_key_redispatch]` |
| LNS_MIP:constructor=greedy_most_work_remaining_tail_bound | 16.80% | 980.6 | 45 | +75.3% | `LNS_MIP[constructor=greedy_most_work_remaining_tail_bound, destruction=critical_block_window_destruction]` |
| SA:neighborhood=critical_path_adjacent_swap | 17.00% | 983.2 | 76 | +75.3% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 30.30% | 1095.3 | 124 | +72.5% | `SA[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
| LNS_MIP:constructor=greedy_bottleneck_machine_load_priority | 43.63% | 1207.0 | 171 | +69.6% | `LNS_MIP[constructor=greedy_bottleneck_machine_load_priority, destruction=critical_block_window_destruction]` |
| LNS_MIP:constructor=random | 101.22% | 1688.7 | 214 | +57.5% | `LNS_MIP[constructor=random, destruction=critical_block_window_destruction]` |
| ILS:neighborhood=job_priority_shift_all_machines | 102.16% | 1699.1 | 155 | +57.3% | `ILS[constructor=trivial, neighborhood=job_priority_shift_all_machines, perturbation=acyclic_random_insertions]` |
| VNS:neighborhood=job_priority_shift_all_machines | 113.99% | 1794.8 | 220 | +54.9% | `VNS[constructor=trivial, neighborhood=job_priority_shift_all_machines]` |
| LNS_MIP:destruction=time_slice_destruction | 156.65% | 2156.8 | 404 | +45.8% | `LNS_MIP[constructor=trivial, destruction=time_slice_destruction]` |
| SA:neighborhood=job_priority_shift_all_machines | 280.69% | 3197.4 | 268 | +19.6% | `SA[constructor=trivial, neighborhood=job_priority_shift_all_machines]` |
| LNS_MIP:destruction=related_jobs_slot_destruction | 359.70% | 3869.0 | 484 | +2.7% | `LNS_MIP[constructor=trivial, destruction=related_jobs_slot_destruction]` |
| default:LNS_MIP | 365.93% | 3920.9 | 507 | +1.4% | `LNS_MIP[constructor=trivial, destruction=critical_block_window_destruction]` |

Ganancia del afinado sobre el mejor default: **+2.40%**; gana en 8/10 instancias de test. Esqueletos explorados: ILS × 20, SA × 7, VNS × 7, LNS_MIP × 6.

Afinado vs `VNS:constructor=greedy_earliest_completion_idle_penalty` (mejor default por gap): +2.51% de gap a favor del afinado, IC95 [+1.02%, +4.02%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 34 ✔ | 0.2140 | 0.2137, 0.2128, 0.2134, 0.2148, 0.2156, 0.2138, 0.2139 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 20 (numéricos por defecto) | 0.2145 | 0.2131, 0.2160, 0.2144, 0.2149, 0.2141, 0.2144, 0.2145 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| 38 | 0.2174 | 0.2177, 0.2162, 0.2183 | `ILS[constructor=random, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 20 | 0.2174 | 0.2171, 0.2162, 0.2191 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| 28 | 0.2177 | 0.2159, 0.2178, 0.2194 | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 9 | 0.2198 | 0.2188, 0.2225, 0.2181 | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| 34 (numéricos por defecto) | 0.2217 | 0.2220, 0.2223, 0.2208 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 38 (numéricos por defecto) | 0.2245 | 0.2242, 0.2225, 0.2267 | `ILS[constructor=random, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 28 (numéricos por defecto) | 0.2257 | 0.2264, 0.2240, 0.2267 | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 2* | 0.2293 | 0.2276, 0.2286, 0.2316 | `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop_sequences 10x10) · 0 configuraciones fallidas · 3085 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_block_window_destruction`, `related_jobs_slot_destruction`, `time_slice_destruction`, `bottleneck_machine_load_priority`, `earliest_completion_idle_penalty`, `most_work_remaining_tail_bound`, `critical_operation_reinsertion`, `critical_path_adjacent_swap`, `job_priority_shift_all_machines`, `acyclic_random_insertions`, `critical_block_adjacent_swaps`, `noisy_start_key_redispatch`

**Mejor en train**: `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` = 0.2122 (mejor default: 0.2283, `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.30%** | **858.3** | 44 | +78.4% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| VNS:constructor=greedy_earliest_completion_idle_penalty | 4.82% | 879.8 | 53 | +77.9% | `VNS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion]` |
| VNS:constructor=greedy_most_work_remaining_tail_bound | 5.62% | 886.1 | 53 | +77.7% | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=greedy_earliest_completion_idle_penalty | 5.74% | 887.4 | 55 | +77.7% | `ILS[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| ILS:constructor=greedy_most_work_remaining_tail_bound | 6.12% | 890.5 | 52 | +77.6% | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| ILS:neighborhood=critical_path_adjacent_swap | 6.24% | 892.0 | 61 | +77.6% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| SA:constructor=greedy_earliest_completion_idle_penalty | 6.34% | 892.7 | 58 | +77.6% | `SA[constructor=greedy_earliest_completion_idle_penalty, neighborhood=critical_operation_reinsertion]` |
| VNS:constructor=greedy_bottleneck_machine_load_priority | 6.59% | 894.9 | 63 | +77.5% | `VNS[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion]` |
| ILS:constructor=greedy_bottleneck_machine_load_priority | 7.06% | 899.1 | 68 | +77.4% | `ILS[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| VNS:constructor=random | 7.30% | 900.7 | 60 | +77.4% | `VNS[constructor=random, neighborhood=critical_operation_reinsertion]` |
| VNS:neighborhood=critical_path_adjacent_swap | 7.37% | 900.0 | 53 | +77.4% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| SA:constructor=greedy_most_work_remaining_tail_bound | 7.69% | 903.3 | 50 | +77.3% | `SA[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_operation_reinsertion]` |
| ILS:perturbation=critical_block_adjacent_swaps | 7.97% | 906.3 | 58 | +77.2% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=critical_block_adjacent_swaps]` |
| ILS:constructor=random | 8.80% | 913.0 | 66 | +77.0% | `ILS[constructor=random, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| SA:constructor=greedy_bottleneck_machine_load_priority | 8.82% | 914.0 | 73 | +77.0% | `SA[constructor=greedy_bottleneck_machine_load_priority, neighborhood=critical_operation_reinsertion]` |
| default:ILS | 10.76% | 929.5 | 60 | +76.6% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=acyclic_random_insertions]` |
| default:VNS | 11.79% | 938.1 | 60 | +76.4% | `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
| SA:constructor=random | 12.02% | 940.4 | 82 | +76.4% | `SA[constructor=random, neighborhood=critical_operation_reinsertion]` |
| LNS_MIP:constructor=greedy_earliest_completion_idle_penalty | 14.75% | 963.9 | 76 | +75.8% | `LNS_MIP[constructor=greedy_earliest_completion_idle_penalty, destruction=critical_block_window_destruction]` |
| ILS:perturbation=noisy_start_key_redispatch | 16.45% | 977.1 | 63 | +75.4% | `ILS[constructor=trivial, neighborhood=critical_operation_reinsertion, perturbation=noisy_start_key_redispatch]` |
| LNS_MIP:constructor=greedy_most_work_remaining_tail_bound | 16.97% | 980.6 | 45 | +75.3% | `LNS_MIP[constructor=greedy_most_work_remaining_tail_bound, destruction=critical_block_window_destruction]` |
| SA:neighborhood=critical_path_adjacent_swap | 17.99% | 990.5 | 87 | +75.1% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 29.88% | 1090.7 | 119 | +72.6% | `SA[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
| LNS_MIP:constructor=greedy_bottleneck_machine_load_priority | 43.85% | 1207.0 | 171 | +69.6% | `LNS_MIP[constructor=greedy_bottleneck_machine_load_priority, destruction=critical_block_window_destruction]` |
| LNS_MIP:constructor=random | 101.51% | 1688.7 | 214 | +57.5% | `LNS_MIP[constructor=random, destruction=critical_block_window_destruction]` |
| ILS:neighborhood=job_priority_shift_all_machines | 102.69% | 1701.3 | 157 | +57.2% | `ILS[constructor=trivial, neighborhood=job_priority_shift_all_machines, perturbation=acyclic_random_insertions]` |
| VNS:neighborhood=job_priority_shift_all_machines | 114.25% | 1794.8 | 220 | +54.9% | `VNS[constructor=trivial, neighborhood=job_priority_shift_all_machines]` |
| LNS_MIP:destruction=time_slice_destruction | 154.94% | 2139.4 | 383 | +46.2% | `LNS_MIP[constructor=trivial, destruction=time_slice_destruction]` |
| SA:neighborhood=job_priority_shift_all_machines | 281.19% | 3197.4 | 268 | +19.6% | `SA[constructor=trivial, neighborhood=job_priority_shift_all_machines]` |
| LNS_MIP:destruction=related_jobs_slot_destruction | 353.24% | 3807.7 | 442 | +4.2% | `LNS_MIP[constructor=trivial, destruction=related_jobs_slot_destruction]` |
| default:LNS_MIP | 366.57% | 3920.9 | 507 | +1.4% | `LNS_MIP[constructor=trivial, destruction=critical_block_window_destruction]` |

Ganancia del afinado sobre el mejor default: **+2.44%**; gana en 8/10 instancias de test. Esqueletos explorados: VNS × 19, SA × 7, ILS × 7, LNS_MIP × 7.

Afinado vs `VNS:constructor=greedy_earliest_completion_idle_penalty` (mejor default por gap): +2.52% de gap a favor del afinado, IC95 [+0.16%, +4.57%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 25 (numéricos por defecto) ✔ | 0.2122 | 0.2119, 0.2128, 0.2120 | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| 25 | 0.2144 | 0.2129, 0.2148, 0.2156 | `VNS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap]` |
| 37 | 0.2180 | 0.2176, 0.2182, 0.2182 | `VNS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| 18 | 0.2189 | 0.2189, 0.2200, 0.2178 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 9 | 0.2193 | 0.2187, 0.2219, 0.2175 | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=acyclic_random_insertions]` |
| 37 (numéricos por defecto) | 0.2196 | 0.2197, 0.2204, 0.2187 | `VNS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| 18 (numéricos por defecto) | 0.2221 | 0.2210, 0.2238, 0.2215 | `ILS[constructor=greedy_most_work_remaining_tail_bound, neighborhood=critical_path_adjacent_swap, perturbation=noisy_start_key_redispatch]` |
| 10 | 0.2225 | 0.2183, 0.2270, 0.2222 | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| 2* | 0.2308 | 0.2283, 0.2293, 0.2347 | `VNS[constructor=trivial, neighborhood=critical_operation_reinsertion]` |
