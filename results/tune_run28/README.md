## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 6.21% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| r1 | 1 | 5.59% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| r2 | 2 | 6.26% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |

**Afinado entre réplicas**: media 6.02%, desvío 0.30%, rango [5.59%, 6.26%].

**Mejor no afinado** (media entre réplicas): `LNS_MIP:constructor=greedy_route_save_ratio_score` = 5.48%. Afinado vs ese: -0.54% de gap a favor del afinado, IC95 [-2.29%, +1.29%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3198 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `customer_star_destruction`, `expensive_edge_destruction`, `route_removal_destruction`, `high_demand_urgent_score`, `nearest_extension_score`, `route_save_ratio_score`, `swap_customers_across_routes`, `customer_relocation_perturbation`, `route_split_merge_perturbation`, `segment_reversal_perturbation`

**Mejor en train**: `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` = 0.3489 (mejor default: 0.4720, `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **5.26%** | **735.2** | 169 | +63.5% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| LNS_MIP:constructor=greedy_route_save_ratio_score | 4.88% | 732.4 | 167 | +63.6% | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=customer_star_destruction]` |
| SA:constructor=greedy_route_save_ratio_score | 7.83% | 752.0 | 168 | +62.7% | `SA[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=greedy_route_save_ratio_score | 8.32% | 756.6 | 175 | +62.4% | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| LNS_MIP:constructor=greedy_nearest_extension_score | 9.30% | 762.1 | 176 | +62.2% | `LNS_MIP[constructor=greedy_nearest_extension_score, destruction=customer_star_destruction]` |
| VNS:constructor=greedy_nearest_extension_score | 9.59% | 767.7 | 188 | +61.9% | `VNS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| SA:constructor=greedy_nearest_extension_score | 9.64% | 768.7 | 192 | +61.8% | `SA[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| ILS:constructor=greedy_route_save_ratio_score | 10.96% | 773.7 | 172 | +61.6% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| ILS:constructor=greedy_nearest_extension_score | 15.99% | 811.8 | 201 | +59.7% | `ILS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| SA:constructor=greedy_high_demand_urgent_score | 18.43% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=greedy_high_demand_urgent_score | 19.84% | 840.7 | 217 | +58.2% | `VNS[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes]` |
| ILS:constructor=greedy_high_demand_urgent_score | 27.08% | 891.6 | 222 | +55.7% | `ILS[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| ILS:constructor=random | 27.51% | 893.4 | 218 | +55.6% | `ILS[constructor=random, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| default:ILS | 38.49% | 972.5 | 244 | +51.7% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| default:LNS_MIP | 47.53% | 1021.0 | 290 | +49.3% | `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]` |
| LNS_MIP:destruction=route_removal_destruction | 73.36% | 1137.5 | 412 | +43.5% | `LNS_MIP[constructor=trivial, destruction=route_removal_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_urgent_score | 74.17% | 1217.7 | 336 | +39.5% | `LNS_MIP[constructor=greedy_high_demand_urgent_score, destruction=customer_star_destruction]` |
| LNS_MIP:constructor=random | 74.95% | 1223.2 | 330 | +39.3% | `LNS_MIP[constructor=random, destruction=customer_star_destruction]` |
| LNS_MIP:destruction=expensive_edge_destruction | 83.67% | 1243.4 | 417 | +38.3% | `LNS_MIP[constructor=trivial, destruction=expensive_edge_destruction]` |
| ILS:perturbation=segment_reversal_perturbation | 176.95% | 1930.9 | 429 | +4.1% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| default:SA | 188.99% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=swap_customers_across_routes]` |
| ILS:perturbation=route_split_merge_perturbation | 188.99% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| default:VNS | 188.99% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=random | 21236659118.06% | 166666667336.0 | 372677995951 | -8276974661.1% | `VNS[constructor=random, neighborhood=swap_customers_across_routes]` |
| SA:constructor=random | 21236659119.55% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=swap_customers_across_routes]` |

Ganancia del afinado sobre el mejor default: **-0.38%**; gana en 4/10 instancias de test. Esqueletos explorados: ILS × 19, SA × 8, LNS_MIP × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_route_save_ratio_score` (mejor default por gap): -0.39% de gap a favor del afinado, IC95 [-2.07%, +1.37%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 29 (numéricos por defecto) ✔ | 0.3489 | 0.3484, 0.3478, 0.3503 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 29 | 0.3502 | 0.3496, 0.3509, 0.3501 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 16 | 0.3536 | 0.3555, 0.3497, 0.3555 | `SA[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 19 | 0.3581 | 0.3534, 0.3601, 0.3608 | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 21 | 0.3585 | 0.3589, 0.3601, 0.3567 | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=route_removal_destruction]` |
| 19 (numéricos por defecto) | 0.3605 | 0.3595, 0.3616, 0.3604 | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 14 | 0.3668 | 0.3640, 0.3665, 0.3697 | `VNS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| 21 (numéricos por defecto) | 0.3669 | 0.3667, 0.3685, 0.3655 | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=route_removal_destruction]` |
| 3* | 0.4666 | 0.4720, 0.4378, 0.4899 | `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 2962 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `customer_star_destruction`, `expensive_edge_destruction`, `route_removal_destruction`, `high_demand_urgent_score`, `nearest_extension_score`, `route_save_ratio_score`, `swap_customers_across_routes`, `customer_relocation_perturbation`, `route_split_merge_perturbation`, `segment_reversal_perturbation`

**Mejor en train**: `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` = 0.3494 (mejor default: 0.4264, `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **5.59%** | **730.8** | 167 | +63.7% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| LNS_MIP:constructor=greedy_route_save_ratio_score | 4.81% | 725.2 | 164 | +64.0% | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=customer_star_destruction]` |
| VNS:constructor=greedy_route_save_ratio_score | 8.44% | 750.5 | 172 | +62.7% | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| SA:constructor=greedy_route_save_ratio_score | 8.80% | 752.0 | 168 | +62.7% | `SA[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| LNS_MIP:constructor=greedy_nearest_extension_score | 8.86% | 753.4 | 179 | +62.6% | `LNS_MIP[constructor=greedy_nearest_extension_score, destruction=customer_star_destruction]` |
| VNS:constructor=greedy_nearest_extension_score | 9.56% | 760.3 | 185 | +62.2% | `VNS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| SA:constructor=greedy_nearest_extension_score | 10.62% | 768.7 | 192 | +61.8% | `SA[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| ILS:constructor=greedy_route_save_ratio_score | 11.73% | 772.3 | 172 | +61.6% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| ILS:constructor=greedy_nearest_extension_score | 16.71% | 809.6 | 200 | +59.8% | `ILS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| VNS:constructor=greedy_high_demand_urgent_score | 18.62% | 825.2 | 214 | +59.0% | `VNS[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes]` |
| SA:constructor=greedy_high_demand_urgent_score | 19.47% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes]` |
| ILS:constructor=greedy_high_demand_urgent_score | 26.65% | 880.5 | 217 | +56.3% | `ILS[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| ILS:constructor=random | 27.31% | 884.6 | 219 | +56.1% | `ILS[constructor=random, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| default:ILS | 34.47% | 935.5 | 235 | +53.5% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| default:LNS_MIP | 44.30% | 992.7 | 288 | +50.7% | `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]` |
| LNS_MIP:destruction=expensive_edge_destruction | 46.63% | 1010.2 | 296 | +49.8% | `LNS_MIP[constructor=trivial, destruction=expensive_edge_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_urgent_score | 58.49% | 1092.6 | 300 | +45.7% | `LNS_MIP[constructor=greedy_high_demand_urgent_score, destruction=customer_star_destruction]` |
| LNS_MIP:destruction=route_removal_destruction | 69.48% | 1142.3 | 487 | +43.3% | `LNS_MIP[constructor=trivial, destruction=route_removal_destruction]` |
| LNS_MIP:constructor=random | 70.09% | 1171.8 | 320 | +41.8% | `LNS_MIP[constructor=random, destruction=customer_star_destruction]` |
| ILS:perturbation=segment_reversal_perturbation | 179.42% | 1930.9 | 429 | +4.1% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| default:SA | 191.56% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=swap_customers_across_routes]` |
| ILS:perturbation=route_split_merge_perturbation | 191.56% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| default:VNS | 191.56% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=random | 21445704374.52% | 166666667325.6 | 372677995955 | -8276974660.6% | `VNS[constructor=random, neighborhood=swap_customers_across_routes]` |
| SA:constructor=random | 21445704377.49% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=swap_customers_across_routes]` |

Ganancia del afinado sobre el mejor default: **-0.77%**; gana en 4/10 instancias de test. Esqueletos explorados: ILS × 20, SA × 7, LNS_MIP × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_route_save_ratio_score` (mejor default por gap): -0.79% de gap a favor del afinado, IC95 [-2.59%, +1.16%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 28 (numéricos por defecto) ✔ | 0.3494 | 0.3503, 0.3499, 0.3479 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 28 | 0.3502 | 0.3492, 0.3548, 0.3467 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 34 | 0.3515 | 0.3514, 0.3536, 0.3495 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| 16 | 0.3558 | 0.3537, 0.3573, 0.3565 | `SA[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 27 (numéricos por defecto) | 0.3581 | 0.3581, 0.3599, 0.3563 | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 27 | 0.3592 | 0.3611, 0.3590, 0.3575 | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 14 | 0.3667 | 0.3674, 0.3692, 0.3634 | `VNS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| 34 (numéricos por defecto) | 0.3690 | 0.3644, 0.3701, 0.3725 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| 3* | 0.4396 | 0.4264, 0.4567, 0.4358 | `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 3 configuraciones fallidas · 3241 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `customer_star_destruction`, `expensive_edge_destruction`, `route_removal_destruction`, `high_demand_urgent_score`, `nearest_extension_score`, `route_save_ratio_score`, `swap_customers_across_routes`, `customer_relocation_perturbation`, `route_split_merge_perturbation`, `segment_reversal_perturbation`

**Mejor en train**: `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` = 0.3486 (mejor default: 0.4745, `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **5.22%** | **735.6** | 170 | +63.5% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| LNS_MIP:constructor=greedy_route_save_ratio_score | 4.77% | 732.3 | 167 | +63.6% | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=customer_star_destruction]` |
| SA:constructor=greedy_route_save_ratio_score | 7.74% | 752.0 | 168 | +62.7% | `SA[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=greedy_route_save_ratio_score | 8.22% | 756.6 | 175 | +62.4% | `VNS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| LNS_MIP:constructor=greedy_nearest_extension_score | 9.11% | 761.5 | 176 | +62.2% | `LNS_MIP[constructor=greedy_nearest_extension_score, destruction=customer_star_destruction]` |
| VNS:constructor=greedy_nearest_extension_score | 9.50% | 767.7 | 188 | +61.9% | `VNS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| SA:constructor=greedy_nearest_extension_score | 9.55% | 768.7 | 192 | +61.8% | `SA[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes]` |
| ILS:constructor=greedy_route_save_ratio_score | 10.86% | 773.7 | 172 | +61.6% | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| ILS:constructor=greedy_nearest_extension_score | 15.90% | 811.8 | 201 | +59.7% | `ILS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| SA:constructor=greedy_high_demand_urgent_score | 18.33% | 832.6 | 218 | +58.7% | `SA[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=greedy_high_demand_urgent_score | 19.67% | 840.4 | 217 | +58.3% | `VNS[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes]` |
| ILS:constructor=greedy_high_demand_urgent_score | 26.87% | 891.3 | 223 | +55.7% | `ILS[constructor=greedy_high_demand_urgent_score, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| ILS:constructor=random | 27.40% | 893.4 | 218 | +55.6% | `ILS[constructor=random, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| default:ILS | 38.19% | 971.4 | 244 | +51.8% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
| default:LNS_MIP | 47.30% | 1020.9 | 293 | +49.3% | `LNS_MIP[constructor=trivial, destruction=customer_star_destruction]` |
| LNS_MIP:destruction=expensive_edge_destruction | 71.12% | 1174.2 | 430 | +41.7% | `LNS_MIP[constructor=trivial, destruction=expensive_edge_destruction]` |
| LNS_MIP:constructor=greedy_high_demand_urgent_score | 71.69% | 1197.7 | 329 | +40.5% | `LNS_MIP[constructor=greedy_high_demand_urgent_score, destruction=customer_star_destruction]` |
| LNS_MIP:constructor=random | 74.85% | 1223.8 | 330 | +39.2% | `LNS_MIP[constructor=random, destruction=customer_star_destruction]` |
| LNS_MIP:destruction=route_removal_destruction | 81.90% | 1215.8 | 510 | +39.6% | `LNS_MIP[constructor=trivial, destruction=route_removal_destruction]` |
| ILS:perturbation=segment_reversal_perturbation | 176.67% | 1930.9 | 429 | +4.1% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| default:SA | 188.69% | 2013.6 | 442 | +0.0% | `SA[constructor=trivial, neighborhood=swap_customers_across_routes]` |
| ILS:perturbation=route_split_merge_perturbation | 188.69% | 2013.6 | 442 | +0.0% | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| default:VNS | 188.69% | 2013.6 | 442 | +0.0% | `VNS[constructor=trivial, neighborhood=swap_customers_across_routes]` |
| VNS:constructor=random | 21191313712.02% | 166666667336.0 | 372677995951 | -8276974661.1% | `VNS[constructor=random, neighborhood=swap_customers_across_routes]` |
| SA:constructor=random | 21191313713.51% | 166666667343.6 | 372677995947 | -8276974661.5% | `SA[constructor=random, neighborhood=swap_customers_across_routes]` |

Ganancia del afinado sobre el mejor default: **-0.45%**; gana en 4/10 instancias de test. Esqueletos explorados: ILS × 19, SA × 8, LNS_MIP × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_route_save_ratio_score` (mejor default por gap): -0.45% de gap a favor del afinado, IC95 [-2.13%, +1.31%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 24 | 0.3454 | 0.3472, 0.3485, 0.3406 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 24 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.3486 | 0.3490, 0.3490, 0.3478 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 16 | 0.3563 | 0.3582, 0.3548, 0.3559 | `SA[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes]` |
| 34 | 0.3571 | 0.3618, 0.3524, 0.3572 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| 37 (numéricos por defecto) | 0.3603 | 0.3593, 0.3622, 0.3595 | `ILS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 37 | 0.3621 | 0.3599, 0.3627, 0.3636 | `ILS[constructor=greedy_nearest_extension_score, neighborhood=swap_customers_across_routes, perturbation=segment_reversal_perturbation]` |
| 39 | 0.3635 | 0.3640, 0.3642, 0.3625 | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=route_removal_destruction]` |
| 39 (numéricos por defecto) | 0.3685 | 0.3675, 0.3700, 0.3679 | `LNS_MIP[constructor=greedy_route_save_ratio_score, destruction=route_removal_destruction]` |
| 34 (numéricos por defecto) | 0.3716 | 0.3700, 0.3726, 0.3723 | `ILS[constructor=greedy_route_save_ratio_score, neighborhood=swap_customers_across_routes, perturbation=route_split_merge_perturbation]` |
| 1* | 0.4755 | 0.4745, 0.4691, 0.4829 | `ILS[constructor=trivial, neighborhood=swap_customers_across_routes, perturbation=customer_relocation_perturbation]` |
