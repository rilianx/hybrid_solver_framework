## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 5.49% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| r1 | 1 | 4.73% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| r2 | 2 | 4.23% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |

**Afinado entre réplicas**: media 4.82%, desvío 0.52%, rango [4.23%, 5.49%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_nearest_next_customer` = 6.10%. Afinado vs ese: +1.28% de gap a favor del afinado, IC95 [+0.50%, +2.06%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3837 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` = 0.3424 (mejor default: 0.3715, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.13%** | **717.4** | 168 | +64.4% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_nearest_next_customer | 4.72% | 720.7 | 165 | +64.2% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 5.16% | 724.3 | 169 | +64.0% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 8.23% | 745.7 | 175 | +63.0% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 8.39% | 746.9 | 176 | +62.9% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_high_demand_first_fill | 10.20% | 762.2 | 190 | +62.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_high_demand_first_fill | 11.34% | 768.8 | 191 | +61.8% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 12.86% | 778.6 | 188 | +61.3% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| default:ILS | 13.69% | 785.6 | 194 | +61.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 13.89% | 783.4 | 187 | +61.1% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| ILS:constructor=greedy_depot_balance_lookahead | 14.22% | 787.8 | 190 | +60.9% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 14.51% | 790.9 | 194 | +60.7% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 15.13% | 796.2 | 201 | +60.5% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:neighborhood=route_suffix_2opt_star | 16.94% | 807.2 | 195 | +59.9% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| default:LNS_MIP | 46.98% | 1009.6 | 319 | +49.9% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 58.87% | 1095.1 | 285 | +45.6% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 59.32% | 1085.3 | 272 | +46.1% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=random | 63.17% | 1129.4 | 331 | +43.9% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 69.25% | 1168.6 | 333 | +42.0% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 193.42% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 193.42% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 193.42% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 193.42% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 193.42% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 193.42% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 193.42% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16260193267.57% | 133333333980.7 | 339934633986 | -6621579714.4% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21527083284.48% | 166666667267.9 | 372677995981 | -8276974657.7% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+0.45%**; gana en 7/10 instancias de test. Esqueletos explorados: VNS × 20, SA × 7, ILS × 7, LNS_MIP × 6.

Afinado vs `SA:constructor=greedy_nearest_next_customer` (mejor default por gap): +0.59% de gap a favor del afinado, IC95 [-0.34%, +1.51%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 31 ✔ | 0.3424 | 0.3389, 0.3394, 0.3412, 0.3467, 0.3404, 0.3433, 0.3472 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 20 | 0.3428 | 0.3381, 0.3443, 0.3460, 0.3430, 0.3439, 0.3425, 0.3416 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 22 | 0.3438 | 0.3383, 0.3454, 0.3438, 0.3468, 0.3444, 0.3419, 0.3458 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| 12 | 0.3479 | 0.3484, 0.3457, 0.3497 | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 20 (numéricos por defecto) | 0.3529 | 0.3521, 0.3567, 0.3500 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 25 (numéricos por defecto) | 0.3594 | 0.3566, 0.3641, 0.3576 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| 22 (numéricos por defecto) | 0.3616 | 0.3544, 0.3627, 0.3676 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| 31 (numéricos por defecto) | 0.3635 | 0.3675, 0.3649, 0.3581 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 25 | 0.3706 | 0.3644, 0.3719, 0.3753 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| 1* | 0.3762 | 0.3715, 0.3780, 0.3791 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3230 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` = 0.3392 (mejor default: 0.3779, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **3.44%** | **711.1** | 162 | +64.7% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_nearest_next_customer | 4.76% | 720.9 | 167 | +64.2% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 5.12% | 723.8 | 169 | +64.1% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 8.31% | 745.7 | 175 | +63.0% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 8.48% | 746.9 | 176 | +62.9% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_high_demand_first_fill | 10.32% | 762.4 | 190 | +62.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_high_demand_first_fill | 11.88% | 773.3 | 197 | +61.6% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 12.95% | 778.6 | 188 | +61.3% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 13.30% | 779.6 | 188 | +61.3% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| default:ILS | 13.79% | 785.6 | 194 | +61.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_depot_balance_lookahead | 14.33% | 788.0 | 189 | +60.9% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 14.59% | 790.9 | 194 | +60.7% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 15.25% | 796.4 | 201 | +60.4% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:neighborhood=route_suffix_2opt_star | 17.04% | 807.2 | 195 | +59.9% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| default:LNS_MIP | 46.58% | 1005.5 | 318 | +50.1% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 57.82% | 1071.8 | 267 | +46.8% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 58.98% | 1095.9 | 289 | +45.6% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=random | 62.35% | 1123.5 | 336 | +44.2% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 69.49% | 1168.6 | 333 | +42.0% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 193.75% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 193.75% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 193.75% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 193.75% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 193.75% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 193.75% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 193.75% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16275695658.33% | 133333333981.0 | 339934633985 | -6621579714.4% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21650586530.91% | 166666667278.6 | 372677995976 | -8276974658.2% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+1.36%**; gana en 7/10 instancias de test. Esqueletos explorados: VNS × 20, SA × 7, ILS × 7, LNS_MIP × 6.

Afinado vs `SA:constructor=greedy_nearest_next_customer` (mejor default por gap): +1.32% de gap a favor del afinado, IC95 [+0.42%, +2.23%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 23 ✔ | 0.3392 | 0.3394, 0.3396, 0.3384 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 26 | 0.3462 | 0.3485, 0.3454, 0.3446 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| 27 | 0.3486 | 0.3490, 0.3468, 0.3500 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 12 | 0.3504 | 0.3502, 0.3519, 0.3492 | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 39 | 0.3554 | 0.3580, 0.3538, 0.3545 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| 23 (numéricos por defecto) | 0.3578 | 0.3500, 0.3585, 0.3648 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 39 (numéricos por defecto) | 0.3648 | 0.3667, 0.3609, 0.3669 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| 27 (numéricos por defecto) | 0.3654 | 0.3616, 0.3684, 0.3663 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 26 (numéricos por defecto) | 0.3685 | 0.3707, 0.3708, 0.3640 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| 1* | 0.3758 | 0.3779, 0.3759, 0.3737 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3074 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` = 0.3366 (mejor default: 0.3758, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **3.45%** | **708.6** | 165 | +64.8% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 4.95% | 720.1 | 173 | +64.2% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_nearest_next_customer | 5.34% | 721.4 | 167 | +64.2% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 8.28% | 742.1 | 175 | +63.1% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 8.67% | 745.0 | 176 | +63.0% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_high_demand_first_fill | 10.05% | 756.3 | 185 | +62.4% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_high_demand_first_fill | 10.50% | 759.4 | 193 | +62.3% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 13.27% | 777.0 | 187 | +61.4% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 13.51% | 777.0 | 186 | +61.4% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| default:ILS | 13.97% | 783.2 | 193 | +61.1% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_depot_balance_lookahead | 14.20% | 783.0 | 187 | +61.1% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 14.62% | 787.0 | 192 | +60.9% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 14.80% | 789.9 | 201 | +60.8% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:neighborhood=route_suffix_2opt_star | 17.12% | 804.2 | 195 | +60.1% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| default:LNS_MIP | 46.83% | 1002.0 | 320 | +50.2% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 57.13% | 1079.5 | 295 | +46.4% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 57.62% | 1066.2 | 267 | +47.0% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=random | 60.43% | 1096.1 | 304 | +45.6% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 69.23% | 1163.4 | 339 | +42.2% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 195.38% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 195.38% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 195.38% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 195.38% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 195.38% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 195.38% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 195.38% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16237776384.90% | 133333333977.8 | 339934633987 | -6621579714.3% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21565981045.88% | 166666667270.8 | 372677995980 | -8276974657.9% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+1.60%**; gana en 8/10 instancias de test. Esqueletos explorados: VNS × 19, SA × 7, ILS × 7, LNS_MIP × 7.

Afinado vs `SA:constructor=greedy_depot_balance_lookahead` (mejor default por gap): +1.50% de gap a favor del afinado, IC95 [+0.51%, +2.57%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 28 ✔ | 0.3366 | 0.3341, 0.3366, 0.3392 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 27 | 0.3511 | 0.3527, 0.3488, 0.3518 | `SA[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 12 | 0.3526 | 0.3544, 0.3528, 0.3505 | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 26 | 0.3526 | 0.3529, 0.3543, 0.3508 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| 27 (numéricos por defecto) | 0.3537 | 0.3515, 0.3576, 0.3519 | `SA[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 14 | 0.3560 | 0.3526, 0.3537, 0.3616 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 28 (numéricos por defecto) | 0.3573 | 0.3580, 0.3552, 0.3586 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 26 (numéricos por defecto) | 0.3578 | 0.3604, 0.3600, 0.3531 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| 1* | 0.3753 | 0.3758, 0.3695, 0.3805 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
