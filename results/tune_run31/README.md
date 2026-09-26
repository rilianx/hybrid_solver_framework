## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 3.46% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| r1 | 1 | 3.60% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| r2 | 2 | 3.02% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |

**Afinado entre réplicas**: media 3.36%, desvío 0.25%, rango [3.02%, 3.60%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_nearest_next_customer` = 9.95%. Afinado vs ese: +6.59% de gap a favor del afinado, IC95 [+4.36%, +9.12%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 2 configuraciones fallidas · 3337 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` = 0.3319 (mejor default: 0.3920, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **3.26%** | **708.2** | 164 | +64.8% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| SA:constructor=greedy_nearest_next_customer | 9.73% | 749.1 | 163 | +62.8% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 12.67% | 774.2 | 186 | +61.6% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 12.96% | 776.8 | 190 | +61.4% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 14.13% | 782.2 | 186 | +61.2% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| VNS:constructor=greedy_depot_balance_lookahead | 15.39% | 791.4 | 185 | +60.7% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 18.71% | 817.2 | 201 | +59.4% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| VNS:constructor=greedy_high_demand_first_fill | 19.41% | 823.8 | 210 | +59.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:neighborhood=route_suffix_2opt_star | 19.64% | 822.7 | 200 | +59.1% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_high_demand_first_fill | 20.71% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| default:ILS | 20.92% | 833.4 | 210 | +58.6% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_depot_balance_lookahead | 20.95% | 830.6 | 198 | +58.8% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 21.51% | 835.1 | 201 | +58.5% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 23.07% | 847.6 | 215 | +57.9% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| default:LNS_MIP | 47.06% | 1005.5 | 318 | +50.1% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 57.97% | 1071.0 | 269 | +46.8% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 59.45% | 1097.7 | 295 | +45.5% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=random | 62.95% | 1121.5 | 329 | +44.3% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 69.74% | 1168.6 | 333 | +42.0% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 194.68% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 194.68% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 194.68% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 194.68% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 194.68% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 194.68% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 194.68% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16278116251.86% | 133333334030.4 | 339934633966 | -6621579716.9% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21545006272.36% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+5.46%**; gana en 10/10 instancias de test. Esqueletos explorados: VNS × 16, ILS × 11, SA × 7, LNS_MIP × 6.

Afinado vs `SA:constructor=greedy_nearest_next_customer` (mejor default por gap): +6.47% de gap a favor del afinado, IC95 [+4.32%, +8.74%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 39 ✔ | 0.3319 | 0.3312, 0.3313, 0.3331 | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 39 (numéricos por defecto) | 0.3386 | 0.3398, 0.3351, 0.3408 | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 25 (numéricos por defecto) | 0.3389 | 0.3389, 0.3406, 0.3371 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 32 | 0.3467 | 0.3451, 0.3472, 0.3479 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 25 | 0.3507 | 0.3516, 0.3451, 0.3555 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 29 (numéricos por defecto) | 0.3562 | 0.3546, 0.3594, 0.3546 | `SA[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 17 | 0.3570 | 0.3553, 0.3585, 0.3572 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 29 | 0.3615 | 0.3505, 0.3643, 0.3697 | `SA[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 32 (numéricos por defecto) | 0.3715 | 0.3690, 0.3732, 0.3723 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 17 (numéricos por defecto) | 0.3864 | 0.3851, 0.3906, 0.3835 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 1* | 0.3940 | 0.3920, 0.3944, 0.3956 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 2 configuraciones fallidas · 3324 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` = 0.3363 (mejor default: 0.4059, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.63%** | **709.7** | 167 | +64.8% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| SA:constructor=greedy_nearest_next_customer | 8.93% | 749.1 | 163 | +62.8% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 11.83% | 774.2 | 186 | +61.6% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 11.95% | 775.9 | 190 | +61.5% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 13.67% | 784.8 | 187 | +61.0% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| VNS:constructor=greedy_depot_balance_lookahead | 14.57% | 791.4 | 185 | +60.7% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 17.84% | 817.2 | 201 | +59.4% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| VNS:constructor=greedy_high_demand_first_fill | 18.53% | 823.8 | 210 | +59.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:neighborhood=route_suffix_2opt_star | 18.76% | 822.7 | 200 | +59.1% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_high_demand_first_fill | 19.78% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| default:ILS | 19.82% | 831.8 | 208 | +58.7% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_depot_balance_lookahead | 19.83% | 829.3 | 198 | +58.8% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 20.61% | 835.1 | 201 | +58.5% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 22.12% | 847.6 | 215 | +57.9% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| default:LNS_MIP | 46.92% | 1012.2 | 317 | +49.7% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 58.17% | 1080.7 | 270 | +46.3% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 60.49% | 1107.4 | 276 | +45.0% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=random | 66.94% | 1159.2 | 345 | +42.4% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 68.64% | 1168.8 | 333 | +42.0% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 192.39% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 192.39% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 192.39% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 192.39% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 192.39% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 192.39% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 192.39% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16201282891.16% | 133333334029.1 | 339934633967 | -6621579716.8% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21500174545.18% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+5.26%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 17, VNS × 11, SA × 6, LNS_MIP × 6.

Afinado vs `SA:constructor=greedy_nearest_next_customer` (mejor default por gap): +6.30% de gap a favor del afinado, IC95 [+3.91%, +9.03%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 38 | 0.3342 | 0.3344, 0.3319, 0.3364 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 38 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.3363 | 0.3349, 0.3372, 0.3368 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 31 (numéricos por defecto) | 0.3382 | 0.3380, 0.3389, 0.3377 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 29 (numéricos por defecto) | 0.3433 | 0.3469, 0.3399, 0.3430 | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 29 | 0.3433 | 0.3408, 0.3487, 0.3402 | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 31 | 0.3482 | 0.3438, 0.3510, 0.3497 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 39 | 0.3531 | 0.3544, 0.3505, 0.3545 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=interroute_customer_swap_kick]` |
| 23 | 0.3578 | 0.3539, 0.3650, 0.3546 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 23 (numéricos por defecto) | 0.3815 | 0.3796, 0.3874, 0.3776 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 39 (numéricos por defecto) | 0.3948 | 0.3954, 0.3918, 0.3972 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=interroute_customer_swap_kick]` |
| 1* | 0.4013 | 0.4059, 0.4038, 0.3942 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 2 configuraciones fallidas · 3427 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` = 0.3332 (mejor default: 0.4008, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.78%** | **705.4** | 164 | +65.0% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| SA:constructor=greedy_nearest_next_customer | 8.63% | 749.1 | 163 | +62.8% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 11.51% | 774.2 | 186 | +61.6% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 11.60% | 775.7 | 190 | +61.5% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 14.14% | 790.8 | 185 | +60.7% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 14.69% | 795.0 | 192 | +60.5% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| ILS:constructor=greedy_nearest_next_customer | 17.50% | 817.1 | 201 | +59.4% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| VNS:constructor=greedy_high_demand_first_fill | 18.19% | 823.8 | 210 | +59.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:neighborhood=route_suffix_2opt_star | 18.42% | 822.7 | 200 | +59.1% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| default:ILS | 19.35% | 831.0 | 209 | +58.7% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_high_demand_first_fill | 19.43% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_depot_balance_lookahead | 19.44% | 829.2 | 199 | +58.8% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 20.27% | 835.1 | 201 | +58.5% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 21.77% | 847.5 | 215 | +57.9% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| default:LNS_MIP | 47.75% | 1019.2 | 320 | +49.4% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 58.76% | 1101.9 | 286 | +45.3% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 60.60% | 1102.2 | 271 | +45.3% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=random | 68.20% | 1175.1 | 361 | +41.6% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 70.68% | 1183.1 | 323 | +41.2% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 191.57% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 191.57% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 191.57% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 191.57% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 191.57% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 191.57% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 191.57% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16188830011.97% | 133333334028.0 | 339934633967 | -6621579716.8% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21443022530.09% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+5.84%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 19, VNS × 8, SA × 7, LNS_MIP × 6.

Afinado vs `SA:constructor=greedy_nearest_next_customer` (mejor default por gap): +6.86% de gap a favor del afinado, IC95 [+4.50%, +9.54%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 37 ✔ | 0.3332 | 0.3326, 0.3336, 0.3334 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 37 (numéricos por defecto) | 0.3402 | 0.3379, 0.3414, 0.3413 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 38 | 0.3590 | 0.3571, 0.3608, 0.3592 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 31 | 0.3694 | 0.3703, 0.3749, 0.3629 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 31 (numéricos por defecto) | 0.3701 | 0.3671, 0.3722, 0.3710 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 23 (numéricos por defecto) | 0.3750 | 0.3815, 0.3731, 0.3704 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| 23 | 0.3767 | 0.3701, 0.3840, 0.3761 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| 28 | 0.3768 | 0.3720, 0.3838, 0.3746 | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=uniform_customer_arc_destruction]` |
| 28 (numéricos por defecto) | 0.3779 | 0.3755, 0.3690, 0.3893 | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=uniform_customer_arc_destruction]` |
| 38 (numéricos por defecto) | 0.3833 | 0.3850, 0.3837, 0.3813 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 1* | 0.4019 | 0.4008, 0.4040, 0.4008 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
