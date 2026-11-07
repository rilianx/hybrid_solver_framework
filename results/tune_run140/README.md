## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.42% | `GRASP[constructor=randomized_add_open_then_regret_assign, neighborhood=composite, perturbation=random_shift_swap_walk]` |
| r1 | 1 | 0.30% | `VNS[constructor=randomized_add_open_then_regret_assign, neighborhood=facility_close_open_greedy_redistribution]` |

**Afinado entre réplicas**: media 0.36%, desvío 0.06%, rango [0.30%, 0.42%].

**Mejor no afinado** (media entre réplicas): `default:VNS` = 1.82%. Afinado vs ese: +1.46% de gap a favor del afinado, IC95 [+0.89%, +2.05%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (sscflp 20x100,30x200,60x200) · 0 configuraciones fallidas · 9738 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_amortized_fixed_regret_order`, `randomized_add_open_then_regret_assign`, `facility_star_packing_greedy`, `shift_customer_near_or_open`, `swap_customers_between_near_facilities`, `facility_close_open_greedy_redistribution`, `random_shift_swap_walk`, `cluster_ruin_regret_recreate`, `facility_close_greedy_repair`

**Mejor en train**: `GRASP[constructor=randomized_add_open_then_regret_assign, neighborhood=composite, perturbation=random_shift_swap_walk]` = 0.5695

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.39%** | **25688.4** | 6475 | +45.1% | `GRASP[constructor=randomized_add_open_then_regret_assign, neighborhood=composite, perturbation=random_shift_swap_walk]` |
| default:VNS | 1.75% | 26037.0 | 6589 | +44.3% | `VNS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:HYB | 18.90% | 30647.4 | 8387 | +34.4% | `HYB[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk, destruction=group_window]` |
| default:TS | 20.62% | 30929.0 | 7942 | +33.8% | `TS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:SA | 31.37% | 33646.3 | 8566 | +28.0% | `SA[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:ILS | 55.07% | 40401.0 | 12723 | +13.6% | `ILS[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk]` |
| default:GRASP | 64.59% | 42374.6 | 11678 | +9.4% | `GRASP[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+1.34%**; gana en 6/6 instancias de test. Esqueletos explorados: GRASP × 7, ILS × 1.

Afinado vs `default:VNS` (mejor default por gap): +1.37% de gap a favor del afinado, IC95 [+0.82%, +1.99%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (sscflp 20x100,30x200,60x200) · 0 configuraciones fallidas · 8519 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `grasp_amortized_fixed_regret_order`, `randomized_add_open_then_regret_assign`, `facility_star_packing_greedy`, `shift_customer_near_or_open`, `swap_customers_between_near_facilities`, `facility_close_open_greedy_redistribution`, `random_shift_swap_walk`, `cluster_ruin_regret_recreate`, `facility_close_greedy_repair`

**Mejor en train**: `VNS[constructor=randomized_add_open_then_regret_assign, neighborhood=facility_close_open_greedy_redistribution]` = 0.5684

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.11%** | **25644.9** | 6434 | +45.1% | `VNS[constructor=randomized_add_open_then_regret_assign, neighborhood=facility_close_open_greedy_redistribution]` |
| default:VNS | 1.66% | 26055.6 | 6608 | +44.3% | `VNS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:HYB | 19.36% | 30897.6 | 8817 | +33.9% | `HYB[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk, destruction=group_window]` |
| default:TS | 20.73% | 30993.8 | 7922 | +33.7% | `TS[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:SA | 30.93% | 33572.4 | 8568 | +28.2% | `SA[constructor=trivial, neighborhood=shift_customer_near_or_open]` |
| default:ILS | 55.21% | 40494.1 | 12781 | +13.4% | `ILS[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk]` |
| default:GRASP | 64.43% | 42390.5 | 11693 | +9.3% | `GRASP[constructor=trivial, neighborhood=shift_customer_near_or_open, perturbation=random_shift_swap_walk]` |

Ganancia del afinado sobre el mejor default: **+1.58%**; gana en 6/6 instancias de test. Esqueletos explorados: VNS × 2.

Afinado vs `default:VNS` (mejor default por gap): +1.55% de gap a favor del afinado, IC95 [+0.87%, +2.15%].
