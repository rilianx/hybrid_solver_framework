## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.31% | `VNS[constructor=trivial, neighborhood=facility_close_open_greedy_redistribution]` |
| r1 | 1 | 0.13% | `VNS[constructor=grasp_amortized_fixed_regret_order, neighborhood=facility_close_open_greedy_redistribution]` |

**Afinado entre réplicas**: media 0.22%, desvío 0.09%, rango [0.13%, 0.31%].

**Mejor no afinado** (media entre réplicas): `default:VNS` = 1.74%. Afinado vs ese: +1.53% de gap a favor del afinado, IC95 [+0.97%, +2.07%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (sscflp 20x100,30x200,60x200) · 0 configuraciones fallidas · 9573 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_amortized_fixed_regret_order`, `randomized_add_open_then_regret_assign`, `facility_star_packing_greedy`, `shift_customer_near_or_open`, `swap_customers_between_near_facilities`, `facility_close_open_greedy_redistribution`, `random_shift_swap_walk`, `cluster_ruin_regret_recreate`, `facility_close_greedy_repair`

**Mejor en train**: `VNS[constructor=trivial, neighborhood=facility_close_open_greedy_redistribution]` = 0.5698

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.13%** | **25666.3** | 6436 | +45.1% | `VNS[constructor=trivial, neighborhood=facility_close_open_greedy_redistribution]` |
| default:VNS | 1.59% | 26055.7 | 6608 | +44.3% | `VNS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:HYB | 19.67% | 31001.8 | 8848 | +33.7% | `HYB[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk, destruction=group_window]` |
| default:TS | 20.65% | 30993.8 | 7922 | +33.7% | `TS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:SA | 31.80% | 33850.9 | 8748 | +27.6% | `SA[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:ILS | 55.18% | 40524.3 | 12822 | +13.3% | `ILS[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+1.49%**; gana en 6/6 instancias de test. Esqueletos explorados: VNS × 8.

Afinado vs `default:VNS` (mejor default por gap): +1.46% de gap a favor del afinado, IC95 [+0.87%, +2.03%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (sscflp 20x100,30x200,60x200) · 0 configuraciones fallidas · 9909 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_amortized_fixed_regret_order`, `randomized_add_open_then_regret_assign`, `facility_star_packing_greedy`, `shift_customer_near_or_open`, `swap_customers_between_near_facilities`, `facility_close_open_greedy_redistribution`, `random_shift_swap_walk`, `cluster_ruin_regret_recreate`, `facility_close_greedy_repair`

**Mejor en train**: `VNS[constructor=grasp_amortized_fixed_regret_order, neighborhood=facility_close_open_greedy_redistribution]` = 0.5692

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.11%** | **25625.9** | 6449 | +45.2% | `VNS[constructor=grasp_amortized_fixed_regret_order, neighborhood=facility_close_open_greedy_redistribution]` |
| default:VNS | 1.70% | 26037.0 | 6589 | +44.3% | `VNS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:HYB | 18.57% | 30580.9 | 8390 | +34.6% | `HYB[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk, destruction=group_window]` |
| default:TS | 20.55% | 30929.0 | 7942 | +33.8% | `TS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:SA | 31.57% | 33706.3 | 8550 | +27.9% | `SA[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:ILS | 54.84% | 40354.3 | 12714 | +13.7% | `ILS[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+1.58%**; gana en 6/6 instancias de test. Esqueletos explorados: VNS × 8.

Afinado vs `default:VNS` (mejor default por gap): +1.59% de gap a favor del afinado, IC95 [+1.10%, +2.10%].
