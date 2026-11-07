## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.00% | `TS[constructor=random, neighborhood=composite]` |
| r1 | 1 | 0.01% | `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` |

**Afinado entre réplicas**: media 0.01%, desvío 0.00%, rango [0.00%, 0.01%].

**Mejor no afinado** (media entre réplicas): `default:VNS` = 0.11%. Afinado vs ese: +0.11% de gap a favor del afinado, IC95 [+0.04%, +0.18%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (mkp 100x5,250x5,250x10) · 0 configuraciones fallidas · 15203 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_topk_jittered_ratio`, `lagrangian_dual_ratio_greedy`, `random_overfill_drop_add_congestion`, `swap_1_1_ratio_candidates`, `drop_k_greedy_refill`, `forced_insert_ejection_repair`, `random_drop_noisy_greedy_refill`, `forced_insertion_excess_repair`, `surrogate_weighted_ruin_repair`

**Mejor en train**: `TS[constructor=random, neighborhood=composite]` = -1.0283

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **-67679.7** | 31959 | -3.2% | `TS[constructor=random, neighborhood=composite]` |
| default:VNS | 0.11% | -67587.1 | 31893 | -3.1% | `VNS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:HYB | 0.20% | -67525.7 | 31872 | -3.0% | `HYB[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill, destruction=group_window]` |
| default:TS | 0.43% | -67366.7 | 31767 | -2.7% | `TS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:ILS | 0.61% | -67251.4 | 31750 | -2.6% | `ILS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |
| default:SA | 0.75% | -67169.3 | 31799 | -2.4% | `SA[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:GRASP | 0.83% | -67067.7 | 31652 | -2.3% | `GRASP[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |

Ganancia del afinado sobre el mejor default: **+0.14%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 4, GRASP × 3, ILS × 1.

Afinado vs `default:VNS` (mejor default por gap): +0.11% de gap a favor del afinado, IC95 [+0.04%, +0.18%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (mkp 100x5,250x5,250x10) · 0 configuraciones fallidas · 15061 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_topk_jittered_ratio`, `lagrangian_dual_ratio_greedy`, `random_overfill_drop_add_congestion`, `swap_1_1_ratio_candidates`, `drop_k_greedy_refill`, `forced_insert_ejection_repair`, `random_drop_noisy_greedy_refill`, `forced_insertion_excess_repair`, `surrogate_weighted_ruin_repair`

**Mejor en train**: `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` = -1.0284

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **-67674.5** | 31952 | -3.2% | `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` |
| default:VNS | 0.11% | -67587.1 | 31893 | -3.1% | `VNS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:HYB | 0.18% | -67531.1 | 31865 | -3.0% | `HYB[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill, destruction=group_window]` |
| default:TS | 0.42% | -67370.9 | 31769 | -2.7% | `TS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:ILS | 0.56% | -67282.1 | 31752 | -2.6% | `ILS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |
| default:SA | 0.71% | -67198.0 | 31813 | -2.5% | `SA[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:GRASP | 0.80% | -67083.9 | 31651 | -2.3% | `GRASP[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |

Ganancia del afinado sobre el mejor default: **+0.13%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 7, HYB × 1.

Afinado vs `default:VNS` (mejor default por gap): +0.11% de gap a favor del afinado, IC95 [+0.04%, +0.17%].
