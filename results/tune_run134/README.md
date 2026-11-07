## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.00% | `ILS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite, perturbation=random_drop_noisy_greedy_refill]` |
| r1 | 1 | 0.00% | `HYB[constructor=grasp_topk_jittered_ratio, neighborhood=composite, perturbation=surrogate_weighted_ruin_repair, destruction=group_window]` |

**Afinado entre réplicas**: media 0.00%, desvío 0.00%, rango [0.00%, 0.00%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.01%. Afinado vs ese: +0.01% de gap a favor del afinado, IC95 [+0.00%, +0.03%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (mkp n100x5,n200x5,n500x5) · 0 configuraciones fallidas · 14679 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_topk_jittered_ratio`, `lagrangian_dual_ratio_greedy`, `random_overfill_drop_add_congestion`, `swap_1_1_ratio_candidates`, `drop_k_greedy_refill`, `forced_insert_ejection_repair`, `random_drop_noisy_greedy_refill`, `forced_insertion_excess_repair`, `surrogate_weighted_ruin_repair`

**Mejor en train**: `ILS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite, perturbation=random_drop_noisy_greedy_refill]` = -1.0658

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **-70.1** | 44 | -7.9% | `ILS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite, perturbation=random_drop_noisy_greedy_refill]` |
| default:HYB | 0.01% | -70.1 | 44 | -7.9% | `HYB[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill, destruction=group_window]` |
| default:VNS | 0.04% | -70.1 | 44 | -7.8% | `VNS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:ILS | 0.26% | -69.9 | 44 | -7.5% | `ILS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |
| default:TS | 0.28% | -69.9 | 44 | -7.6% | `TS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:SA | 4.87% | -67.1 | 43 | -3.3% | `SA[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |

Ganancia del afinado sobre el mejor default: **+0.02%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 4, HYB × 4.

Afinado vs `default:HYB` (mejor default por gap): +0.01% de gap a favor del afinado, IC95 [+0.00%, +0.03%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (mkp n100x5,n200x5,n500x5) · 0 configuraciones fallidas · 13970 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_topk_jittered_ratio`, `lagrangian_dual_ratio_greedy`, `random_overfill_drop_add_congestion`, `swap_1_1_ratio_candidates`, `drop_k_greedy_refill`, `forced_insert_ejection_repair`, `random_drop_noisy_greedy_refill`, `forced_insertion_excess_repair`, `surrogate_weighted_ruin_repair`

**Mejor en train**: `HYB[constructor=grasp_topk_jittered_ratio, neighborhood=composite, perturbation=surrogate_weighted_ruin_repair, destruction=group_window]` = -1.0658

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **-70.1** | 44 | -7.9% | `HYB[constructor=grasp_topk_jittered_ratio, neighborhood=composite, perturbation=surrogate_weighted_ruin_repair, destruction=group_window]` |
| default:HYB | 0.01% | -70.1 | 44 | -7.9% | `HYB[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill, destruction=group_window]` |
| default:VNS | 0.03% | -70.1 | 44 | -7.8% | `VNS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:ILS | 0.25% | -69.9 | 44 | -7.5% | `ILS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |
| default:TS | 0.28% | -69.9 | 44 | -7.6% | `TS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:SA | 4.96% | -67.0 | 43 | -3.1% | `SA[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |

Ganancia del afinado sobre el mejor default: **+0.02%**; gana en 2/6 instancias de test. Esqueletos explorados: HYB × 3, VNS × 3, ILS × 2.

Afinado vs `default:HYB` (mejor default por gap): +0.01% de gap a favor del afinado, IC95 [+0.00%, +0.03%] — **no se distingue del ruido** con estas instancias.
