## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.01% | `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` |
| r1 | 1 | 0.00% | `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` |

**Afinado entre réplicas**: media 0.00%, desvío 0.00%, rango [0.00%, 0.01%].

**Mejor no afinado** (media entre réplicas): `default:VNS` = 0.12%. Afinado vs ese: +0.11% de gap a favor del afinado, IC95 [+0.04%, +0.18%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (mkp 100x5,250x5,250x10) · 0 configuraciones fallidas · 14840 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_topk_jittered_ratio`, `lagrangian_dual_ratio_greedy`, `random_overfill_drop_add_congestion`, `swap_1_1_ratio_candidates`, `drop_k_greedy_refill`, `forced_insert_ejection_repair`, `random_drop_noisy_greedy_refill`, `forced_insertion_excess_repair`, `surrogate_weighted_ruin_repair`

**Mejor en train**: `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` = -1.0282

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **-67677.8** | 31956 | -3.2% | `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` |
| default:VNS | 0.11% | -67587.1 | 31893 | -3.1% | `VNS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:HYB | 0.19% | -67526.9 | 31866 | -3.0% | `HYB[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill, destruction=group_window]` |
| default:TS | 0.43% | -67366.7 | 31767 | -2.7% | `TS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:ILS | 0.61% | -67251.4 | 31750 | -2.6% | `ILS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |
| default:SA | 0.76% | -67167.3 | 31801 | -2.4% | `SA[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |

Ganancia del afinado sobre el mejor default: **+0.13%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 6, VNS × 1, HYB × 1.

Afinado vs `default:VNS` (mejor default por gap): +0.11% de gap a favor del afinado, IC95 [+0.04%, +0.18%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (mkp 100x5,250x5,250x10) · 0 configuraciones fallidas · 15188 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_topk_jittered_ratio`, `lagrangian_dual_ratio_greedy`, `random_overfill_drop_add_congestion`, `swap_1_1_ratio_candidates`, `drop_k_greedy_refill`, `forced_insert_ejection_repair`, `random_drop_noisy_greedy_refill`, `forced_insertion_excess_repair`, `surrogate_weighted_ruin_repair`

**Mejor en train**: `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` = -1.0281

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **-67684.4** | 31965 | -3.2% | `TS[constructor=lagrangian_dual_ratio_greedy, neighborhood=composite]` |
| default:VNS | 0.12% | -67586.7 | 31893 | -3.1% | `VNS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:HYB | 0.22% | -67517.5 | 31873 | -3.0% | `HYB[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill, destruction=group_window]` |
| default:TS | 0.43% | -67366.7 | 31767 | -2.7% | `TS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |
| default:ILS | 0.62% | -67243.5 | 31741 | -2.5% | `ILS[constructor=trivial, neighborhood=swap_1_1_ratio_candidates, perturbation=random_drop_noisy_greedy_refill]` |
| default:SA | 0.79% | -67134.1 | 31742 | -2.4% | `SA[constructor=trivial, neighborhood=swap_1_1_ratio_candidates]` |

Ganancia del afinado sobre el mejor default: **+0.14%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 7, HYB × 1.

Afinado vs `default:VNS` (mejor default por gap): +0.12% de gap a favor del afinado, IC95 [+0.04%, +0.19%].
