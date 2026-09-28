## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 6.36% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| r1 | 1 | 5.98% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| r2 | 2 | 2.76% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |

**Afinado entre réplicas**: media 5.03%, desvío 1.62%, rango [2.76%, 6.36%].

**Mejor no afinado** (media entre réplicas): `VNS:constructor=greedy_nearest_next_customer` = 9.94%. Afinado vs ese: +4.91% de gap a favor del afinado, IC95 [+3.76%, +6.00%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3311 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` = 0.3375 (mejor default: 0.3668, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.72%** | **717.8** | 169 | +64.4% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| VNS:constructor=greedy_nearest_next_customer | 7.08% | 733.4 | 171 | +63.6% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 7.24% | 734.9 | 173 | +63.5% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_high_demand_first_fill | 8.19% | 741.7 | 175 | +63.2% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 8.61% | 741.9 | 170 | +63.2% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| SA:constructor=greedy_nearest_next_customer | 9.90% | 749.1 | 163 | +62.8% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 12.17% | 768.9 | 182 | +61.8% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_depot_balance_lookahead | 12.89% | 774.2 | 186 | +61.6% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| default:ILS | 13.17% | 777.0 | 190 | +61.4% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_depot_balance_lookahead | 13.38% | 777.6 | 187 | +61.4% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 13.51% | 781.6 | 202 | +61.2% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 13.61% | 781.0 | 195 | +61.2% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:neighborhood=route_suffix_2opt_star | 14.99% | 788.9 | 190 | +60.8% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_high_demand_first_fill | 20.94% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| LNS_MIP:constructor=random | 33.44% | 912.2 | 244 | +54.7% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| default:LNS_MIP | 34.09% | 914.8 | 274 | +54.6% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 39.42% | 943.5 | 235 | +53.1% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 39.64% | 956.2 | 246 | +52.5% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 44.47% | 987.0 | 256 | +51.0% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 195.34% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 195.34% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 195.34% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 195.34% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 195.34% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 195.34% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 195.34% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16537747121.07% | 133333333966.4 | 339934633991 | -6621579713.7% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21804637151.09% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+2.13%**; gana en 8/10 instancias de test. Esqueletos explorados: VNS × 21, ILS × 7, SA × 6, LNS_MIP × 6.

Afinado vs `VNS:constructor=greedy_nearest_next_customer` (mejor default por gap): +2.36% de gap a favor del afinado, IC95 [+1.16%, +3.41%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 21 ✔ | 0.3375 | 0.3368, 0.3377, 0.3381 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 17 | 0.3384 | 0.3358, 0.3397, 0.3399 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 38 | 0.3407 | 0.3395, 0.3425, 0.3401 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 18 | 0.3417 | 0.3407, 0.3447, 0.3396 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star]` |
| 27 | 0.3421 | 0.3408, 0.3430, 0.3425 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star, perturbation=interroute_customer_swap_kick]` |
| 38 (numéricos por defecto) | 0.3481 | 0.3487, 0.3499, 0.3458 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 21 (numéricos por defecto) | 0.3526 | 0.3527, 0.3539, 0.3514 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 17 (numéricos por defecto) | 0.3576 | 0.3627, 0.3604, 0.3498 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| 18 (numéricos por defecto) | 0.3609 | 0.3582, 0.3631, 0.3615 | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star]` |
| 1* | 0.3685 | 0.3668, 0.3693, 0.3693 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| 27 (numéricos por defecto) | 0.3898 | 0.3874, 0.3918, 0.3901 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star, perturbation=interroute_customer_swap_kick]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3267 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` = 0.3432 (mejor default: 0.3779, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.86%** | **715.5** | 170 | +64.5% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_nearest_next_customer | 7.28% | 745.7 | 175 | +63.0% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 7.55% | 747.8 | 177 | +62.9% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_nearest_next_customer | 8.38% | 749.1 | 163 | +62.8% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_high_demand_first_fill | 9.26% | 762.3 | 190 | +62.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 11.27% | 774.2 | 186 | +61.6% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 11.92% | 778.9 | 188 | +61.3% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| default:ILS | 12.70% | 785.6 | 194 | +61.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 12.99% | 784.3 | 188 | +61.0% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| ILS:constructor=greedy_depot_balance_lookahead | 13.25% | 788.1 | 190 | +60.9% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 13.69% | 792.4 | 195 | +60.6% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 14.21% | 796.7 | 201 | +60.4% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:neighborhood=route_suffix_2opt_star | 16.04% | 808.1 | 196 | +59.9% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_high_demand_first_fill | 19.17% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| default:LNS_MIP | 46.85% | 1015.7 | 315 | +49.6% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 58.16% | 1086.7 | 267 | +46.0% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 59.29% | 1104.3 | 277 | +45.2% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=random | 68.10% | 1176.1 | 358 | +41.6% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 70.25% | 1182.4 | 323 | +41.3% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 190.96% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 190.96% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 190.96% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 190.96% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 190.96% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 190.96% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 190.96% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16214517591.11% | 133333333981.8 | 339934633985 | -6621579714.5% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21481407618.68% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+4.06%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 16, VNS × 13, SA × 6, LNS_MIP × 5.

Afinado vs `VNS:constructor=greedy_nearest_next_customer` (mejor default por gap): +4.42% de gap a favor del afinado, IC95 [+3.05%, +5.67%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 35 ✔ | 0.3432 | 0.3431, 0.3464, 0.3401 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 39 | 0.3462 | 0.3488, 0.3447, 0.3453 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 29 | 0.3484 | 0.3486, 0.3465, 0.3500 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| 23 | 0.3502 | 0.3511, 0.3546, 0.3449 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| 19 | 0.3576 | 0.3514, 0.3610, 0.3604 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| 39 (numéricos por defecto) | 0.3576 | 0.3567, 0.3574, 0.3588 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 35 (numéricos por defecto) | 0.3577 | 0.3500, 0.3582, 0.3648 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| 29 (numéricos por defecto) | 0.3684 | 0.3709, 0.3702, 0.3640 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| 19 (numéricos por defecto) | 0.3732 | 0.3682, 0.3741, 0.3774 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| 1* | 0.3758 | 0.3779, 0.3759, 0.3737 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| 23 (numéricos por defecto) | 0.3774 | 0.3792, 0.3769, 0.3761 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3241 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `geographic_cluster_destruction`, `route_segment_destruction`, `uniform_customer_arc_destruction`, `depot_balance_lookahead`, `high_demand_first_fill`, `nearest_next_customer`, `customer_swap_exchange`, `route_suffix_2opt_star`, `customer_relocation_kick`, `interroute_customer_swap_kick`, `route_segment_reversal_kick`

**Mejor en train**: `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` = 0.3314 (mejor default: 0.3758, `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.76%** | **693.1** | 163 | +65.6% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| VNS:constructor=greedy_nearest_next_customer | 9.50% | 745.9 | 176 | +63.0% | `VNS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_depot_balance_lookahead | 9.78% | 748.0 | 177 | +62.9% | `VNS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_nearest_next_customer | 10.60% | 749.1 | 163 | +62.8% | `SA[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange]` |
| VNS:constructor=greedy_high_demand_first_fill | 11.60% | 763.4 | 191 | +62.1% | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| SA:constructor=greedy_depot_balance_lookahead | 13.53% | 774.2 | 186 | +61.6% | `SA[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange]` |
| ILS:constructor=greedy_nearest_next_customer | 14.19% | 778.9 | 188 | +61.3% | `ILS[constructor=greedy_nearest_next_customer, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| default:ILS | 14.99% | 785.6 | 194 | +61.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| LNS_MIP:constructor=greedy_nearest_next_customer | 15.21% | 783.4 | 186 | +61.1% | `LNS_MIP[constructor=greedy_nearest_next_customer, destruction=geographic_cluster_destruction]` |
| ILS:constructor=greedy_depot_balance_lookahead | 15.57% | 788.1 | 190 | +60.9% | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=random | 16.03% | 792.5 | 194 | +60.6% | `ILS[constructor=random, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:constructor=greedy_high_demand_first_fill | 16.48% | 796.4 | 200 | +60.4% | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
| ILS:neighborhood=route_suffix_2opt_star | 18.40% | 808.1 | 196 | +59.9% | `ILS[constructor=trivial, neighborhood=route_suffix_2opt_star, perturbation=customer_relocation_kick]` |
| SA:constructor=greedy_high_demand_first_fill | 21.58% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_first_fill, neighborhood=customer_swap_exchange]` |
| default:LNS_MIP | 49.32% | 1013.4 | 318 | +49.7% | `LNS_MIP[constructor=trivial, destruction=geographic_cluster_destruction]` |
| LNS_MIP:destruction=uniform_customer_arc_destruction | 60.76% | 1096.1 | 288 | +45.6% | `LNS_MIP[constructor=trivial, destruction=uniform_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_depot_balance_lookahead | 61.07% | 1084.6 | 272 | +46.1% | `LNS_MIP[constructor=greedy_depot_balance_lookahead, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=random | 65.95% | 1134.4 | 329 | +43.7% | `LNS_MIP[constructor=random, destruction=geographic_cluster_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_first_fill | 72.07% | 1172.2 | 326 | +41.8% | `LNS_MIP[constructor=greedy_high_demand_first_fill, destruction=geographic_cluster_destruction]` |
| default:SA | 196.79% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=customer_swap_exchange]` |
| SA:neighborhood=route_suffix_2opt_star | 196.79% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| ILS:perturbation=interroute_customer_swap_kick | 196.79% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=interroute_customer_swap_kick]` |
| ILS:perturbation=route_segment_reversal_kick | 196.79% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=route_segment_reversal_kick]` |
| default:VNS | 196.79% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=customer_swap_exchange]` |
| VNS:neighborhood=route_suffix_2opt_star | 196.79% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=route_suffix_2opt_star]` |
| LNS_MIP:destruction=route_segment_destruction | 196.79% | 2013.6 | 442 | +0.0% | `LNS_MIP[constructor=trivial, destruction=route_segment_destruction]` |
| VNS:constructor=random | 16348572159.33% | 133333333981.8 | 339934633985 | -6621579714.5% | `VNS[constructor=random, neighborhood=customer_swap_exchange]` |
| SA:constructor=random | 21738762571.77% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=customer_swap_exchange]` |

Ganancia del afinado sobre el mejor default: **+7.09%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 19, SA × 7, VNS × 7, LNS_MIP × 7.

Afinado vs `VNS:constructor=greedy_nearest_next_customer` (mejor default por gap): +7.74% de gap a favor del afinado, IC95 [+6.33%, +9.28%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 36 ✔ | 0.3314 | 0.3307, 0.3314, 0.3321 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 25 (numéricos por defecto) | 0.3331 | 0.3335, 0.3296, 0.3362 | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 27 (numéricos por defecto) | 0.3336 | 0.3343, 0.3332, 0.3335 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 36 (numéricos por defecto) | 0.3345 | 0.3344, 0.3324, 0.3366 | `ILS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 27 | 0.3445 | 0.3464, 0.3423, 0.3449 | `ILS[constructor=greedy_depot_balance_lookahead, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 24 | 0.3450 | 0.3459, 0.3469, 0.3420 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 35 | 0.3467 | 0.3544, 0.3414, 0.3443 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 25 | 0.3491 | 0.3496, 0.3506, 0.3469 | `ILS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star, perturbation=route_segment_reversal_kick]` |
| 24 (numéricos por defecto) | 0.3603 | 0.3589, 0.3650, 0.3571 | `VNS[constructor=greedy_nearest_next_customer, neighborhood=route_suffix_2opt_star]` |
| 35 (numéricos por defecto) | 0.3679 | 0.3683, 0.3722, 0.3631 | `VNS[constructor=greedy_high_demand_first_fill, neighborhood=route_suffix_2opt_star]` |
| 1* | 0.3769 | 0.3758, 0.3732, 0.3818 | `ILS[constructor=trivial, neighborhood=customer_swap_exchange, perturbation=customer_relocation_kick]` |
