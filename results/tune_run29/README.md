## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 6.02% | `VNS[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| r1 | 1 | 5.35% | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| r2 | 2 | 3.20% | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` |

**Afinado entre réplicas**: media 4.86%, desvío 1.21%, rango [3.20%, 6.02%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=two_opt_reversal_neighborhood` = 6.89%. Afinado vs ese: +2.03% de gap a favor del afinado, IC95 [+1.03%, +2.93%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3456 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `related_customer_destruction`, `uniform_arc_destruction`, `cheapest_incremental_distance`, `demand_aware_urgency`, `route_utilization_balance`, `customer_swap_neighborhood`, `relocate_customer_neighborhood`, `two_opt_reversal_neighborhood`, `segment_reversal_kick`

**Mejor en train**: `VNS[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` = 0.4963 (mejor default: 0.5318, `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **3.00%** | **721.6** | 166 | +46.8% | `VNS[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| SA:neighborhood=two_opt_reversal_neighborhood | 3.90% | 726.7 | 164 | +46.4% | `SA[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| ILS:neighborhood=two_opt_reversal_neighborhood | 5.54% | 739.5 | 173 | +45.5% | `ILS[constructor=trivial, neighborhood=two_opt_reversal_neighborhood, perturbation=segment_reversal_kick]` |
| SA:neighborhood=relocate_customer_neighborhood | 6.08% | 742.4 | 171 | +45.2% | `SA[constructor=trivial, neighborhood=relocate_customer_neighborhood]` |
| SA:constructor=greedy_cheapest_incremental_distance | 8.08% | 756.5 | 175 | +44.2% | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=two_opt_reversal_neighborhood | 8.48% | 759.3 | 174 | +44.0% | `VNS[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| ILS:constructor=greedy_demand_aware_urgency | 8.55% | 761.7 | 183 | +43.8% | `ILS[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| SA:constructor=random | 8.63% | 759.4 | 172 | +44.0% | `SA[constructor=random, neighborhood=customer_swap_neighborhood]` |
| ILS:neighborhood=relocate_customer_neighborhood | 8.75% | 762.1 | 178 | +43.8% | `ILS[constructor=trivial, neighborhood=relocate_customer_neighborhood, perturbation=segment_reversal_kick]` |
| SA:constructor=greedy_route_utilization_balance | 9.10% | 763.1 | 173 | +43.7% | `SA[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood]` |
| SA:constructor=greedy_demand_aware_urgency | 9.17% | 764.3 | 176 | +43.6% | `SA[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_cheapest_incremental_distance | 9.17% | 765.9 | 183 | +43.5% | `ILS[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| default:SA | 9.69% | 768.2 | 181 | +43.3% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=relocate_customer_neighborhood | 10.40% | 773.8 | 181 | +42.9% | `VNS[constructor=trivial, neighborhood=relocate_customer_neighborhood]` |
| ILS:constructor=greedy_route_utilization_balance | 10.72% | 777.0 | 186 | +42.7% | `ILS[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| ILS:constructor=random | 11.09% | 779.3 | 184 | +42.5% | `ILS[constructor=random, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| default:ILS | 11.55% | 782.5 | 186 | +42.3% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| default:VNS | 13.14% | 795.2 | 196 | +41.3% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_cheapest_incremental_distance | 13.16% | 793.2 | 186 | +41.5% | `VNS[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_demand_aware_urgency | 13.36% | 796.2 | 193 | +41.3% | `VNS[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_route_utilization_balance | 13.54% | 796.8 | 191 | +41.2% | `VNS[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=random | 14.46% | 807.3 | 207 | +40.5% | `VNS[constructor=random, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:destruction=uniform_arc_destruction | 20.07% | 840.7 | 196 | +38.0% | `LNS_MIP[constructor=trivial, destruction=uniform_arc_destruction]` |
| LNS_MIP:constructor=greedy_demand_aware_urgency | 41.87% | 1018.1 | 352 | +24.9% | `LNS_MIP[constructor=greedy_demand_aware_urgency, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=greedy_cheapest_incremental_distance | 59.18% | 1123.8 | 313 | +17.1% | `LNS_MIP[constructor=greedy_cheapest_incremental_distance, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=random | 67.43% | 1183.2 | 321 | +12.7% | `LNS_MIP[constructor=random, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=greedy_route_utilization_balance | 70.22% | 1197.9 | 333 | +11.6% | `LNS_MIP[constructor=greedy_route_utilization_balance, destruction=related_customer_destruction]` |
| default:LNS_MIP | 91.60% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=related_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.70%**; gana en 6/10 instancias de test. Esqueletos explorados: SA × 20, ILS × 7, VNS × 7, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_reversal_neighborhood` (mejor default por gap): +0.90% de gap a favor del afinado, IC95 [-0.50%, +2.33%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 36 ✔ | 0.4963 | 0.4991, 0.4883, 0.5014 | `VNS[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 17 | 0.4981 | 0.4952, 0.5036, 0.4955 | `SA[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 37 | 0.4986 | 0.5003, 0.4977, 0.4978 | `SA[constructor=random, neighborhood=two_opt_reversal_neighborhood]` |
| 39 | 0.4996 | 0.5044, 0.4982, 0.4963 | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` |
| 24 | 0.5012 | 0.5064, 0.4982, 0.4990 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| 37 (numéricos por defecto) | 0.5051 | 0.4959, 0.5100, 0.5094 | `SA[constructor=random, neighborhood=two_opt_reversal_neighborhood]` |
| 39 (numéricos por defecto) | 0.5071 | 0.5085, 0.5073, 0.5056 | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` |
| 24 (numéricos por defecto) | 0.5083 | 0.5071, 0.5127, 0.5051 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| 17 (numéricos por defecto) | 0.5118 | 0.5155, 0.5020, 0.5177 | `SA[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 36 (numéricos por defecto) | 0.5330 | 0.5219, 0.5348, 0.5422 | `VNS[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 0* | 0.5337 | 0.5318, 0.5387, 0.5305 | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3242 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `related_customer_destruction`, `uniform_arc_destruction`, `cheapest_incremental_distance`, `demand_aware_urgency`, `route_utilization_balance`, `customer_swap_neighborhood`, `relocate_customer_neighborhood`, `two_opt_reversal_neighborhood`, `segment_reversal_kick`

**Mejor en train**: `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` = 0.4933 (mejor default: 0.5212, `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **3.61%** | **718.1** | 171 | +47.0% | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| SA:neighborhood=two_opt_reversal_neighborhood | 5.14% | 726.6 | 164 | +46.4% | `SA[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| SA:neighborhood=relocate_customer_neighborhood | 7.24% | 741.6 | 171 | +45.3% | `SA[constructor=trivial, neighborhood=relocate_customer_neighborhood]` |
| ILS:neighborhood=two_opt_reversal_neighborhood | 7.32% | 743.2 | 176 | +45.2% | `ILS[constructor=trivial, neighborhood=two_opt_reversal_neighborhood, perturbation=segment_reversal_kick]` |
| SA:constructor=greedy_cheapest_incremental_distance | 9.35% | 756.3 | 175 | +44.2% | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood]` |
| SA:constructor=random | 9.77% | 758.3 | 172 | +44.1% | `SA[constructor=random, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_demand_aware_urgency | 9.92% | 762.3 | 184 | +43.8% | `ILS[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| ILS:neighborhood=relocate_customer_neighborhood | 10.21% | 763.4 | 180 | +43.7% | `ILS[constructor=trivial, neighborhood=relocate_customer_neighborhood, perturbation=segment_reversal_kick]` |
| SA:constructor=greedy_route_utilization_balance | 10.34% | 762.6 | 174 | +43.8% | `SA[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=two_opt_reversal_neighborhood | 10.41% | 763.8 | 175 | +43.7% | `VNS[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| SA:constructor=greedy_demand_aware_urgency | 10.52% | 764.7 | 176 | +43.6% | `SA[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood]` |
| default:SA | 10.99% | 768.3 | 182 | +43.3% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_route_utilization_balance | 11.09% | 770.0 | 184 | +43.2% | `ILS[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| ILS:constructor=greedy_cheapest_incremental_distance | 11.39% | 772.5 | 186 | +43.0% | `ILS[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| VNS:neighborhood=relocate_customer_neighborhood | 11.84% | 775.7 | 186 | +42.8% | `VNS[constructor=trivial, neighborhood=relocate_customer_neighborhood]` |
| ILS:constructor=random | 12.75% | 782.8 | 190 | +42.3% | `ILS[constructor=random, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| default:ILS | 12.91% | 782.6 | 186 | +42.3% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| VNS:constructor=greedy_cheapest_incremental_distance | 13.95% | 789.3 | 186 | +41.8% | `VNS[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood]` |
| default:VNS | 14.37% | 793.3 | 192 | +41.5% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_demand_aware_urgency | 14.50% | 793.8 | 190 | +41.4% | `VNS[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_route_utilization_balance | 15.03% | 797.5 | 190 | +41.2% | `VNS[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=random | 15.94% | 807.1 | 204 | +40.5% | `VNS[constructor=random, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:destruction=uniform_arc_destruction | 20.93% | 836.9 | 196 | +38.3% | `LNS_MIP[constructor=trivial, destruction=uniform_arc_destruction]` |
| LNS_MIP:constructor=greedy_demand_aware_urgency | 43.67% | 1018.1 | 352 | +24.9% | `LNS_MIP[constructor=greedy_demand_aware_urgency, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=greedy_cheapest_incremental_distance | 61.02% | 1123.8 | 313 | +17.1% | `LNS_MIP[constructor=greedy_cheapest_incremental_distance, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=random | 69.45% | 1183.2 | 321 | +12.7% | `LNS_MIP[constructor=random, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=greedy_route_utilization_balance | 72.42% | 1197.9 | 333 | +11.6% | `LNS_MIP[constructor=greedy_route_utilization_balance, destruction=related_customer_destruction]` |
| default:LNS_MIP | 93.90% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=related_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+1.17%**; gana en 8/10 instancias de test. Esqueletos explorados: SA × 20, ILS × 7, VNS × 7, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_reversal_neighborhood` (mejor default por gap): +1.53% de gap a favor del afinado, IC95 [-0.05%, +2.85%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 22 ✔ | 0.4933 | 0.4874, 0.4964, 0.4961 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| 35 | 0.4953 | 0.4945, 0.5003, 0.4911 | `SA[constructor=random, neighborhood=two_opt_reversal_neighborhood]` |
| 39 | 0.4975 | 0.4978, 0.4955, 0.4991 | `SA[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 16 | 0.5042 | 0.5107, 0.4948, 0.5071 | `SA[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| 22 (numéricos por defecto) | 0.5059 | 0.5028, 0.5015, 0.5135 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| 39 (numéricos por defecto) | 0.5067 | 0.5081, 0.5084, 0.5036 | `SA[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 23 (numéricos por defecto) | 0.5084 | 0.5118, 0.5119, 0.5014 | `ILS[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood, perturbation=segment_reversal_kick]` |
| 23 | 0.5093 | 0.5140, 0.5052, 0.5088 | `ILS[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood, perturbation=segment_reversal_kick]` |
| 35 (numéricos por defecto) | 0.5098 | 0.5094, 0.5125, 0.5076 | `SA[constructor=random, neighborhood=two_opt_reversal_neighborhood]` |
| 0* | 0.5263 | 0.5212, 0.5312, 0.5264 | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3240 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `related_customer_destruction`, `uniform_arc_destruction`, `cheapest_incremental_distance`, `demand_aware_urgency`, `route_utilization_balance`, `customer_swap_neighborhood`, `relocate_customer_neighborhood`, `two_opt_reversal_neighborhood`, `segment_reversal_kick`

**Mejor en train**: `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` = 0.4912 (mejor default: 0.5303, `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.67%** | **701.7** | 161 | +48.2% | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` |
| SA:neighborhood=two_opt_reversal_neighborhood | 6.30% | 726.2 | 164 | +46.4% | `SA[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| SA:neighborhood=relocate_customer_neighborhood | 8.39% | 740.8 | 170 | +45.4% | `SA[constructor=trivial, neighborhood=relocate_customer_neighborhood]` |
| ILS:neighborhood=two_opt_reversal_neighborhood | 8.61% | 743.0 | 173 | +45.2% | `ILS[constructor=trivial, neighborhood=two_opt_reversal_neighborhood, perturbation=segment_reversal_kick]` |
| SA:constructor=greedy_cheapest_incremental_distance | 10.65% | 756.3 | 175 | +44.2% | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=two_opt_reversal_neighborhood | 10.71% | 756.3 | 171 | +44.2% | `VNS[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| SA:constructor=random | 11.13% | 758.7 | 171 | +44.0% | `SA[constructor=random, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_demand_aware_urgency | 11.15% | 761.7 | 183 | +43.8% | `ILS[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| ILS:neighborhood=relocate_customer_neighborhood | 11.46% | 763.1 | 180 | +43.7% | `ILS[constructor=trivial, neighborhood=relocate_customer_neighborhood, perturbation=segment_reversal_kick]` |
| SA:constructor=greedy_route_utilization_balance | 11.58% | 762.1 | 173 | +43.8% | `SA[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood]` |
| SA:constructor=greedy_demand_aware_urgency | 11.69% | 763.6 | 175 | +43.7% | `SA[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_cheapest_incremental_distance | 12.23% | 768.7 | 182 | +43.3% | `ILS[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| default:SA | 12.29% | 767.9 | 181 | +43.4% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_route_utilization_balance | 12.57% | 771.6 | 186 | +43.1% | `ILS[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| VNS:neighborhood=relocate_customer_neighborhood | 12.95% | 773.8 | 184 | +42.9% | `VNS[constructor=trivial, neighborhood=relocate_customer_neighborhood]` |
| ILS:constructor=random | 13.82% | 780.6 | 188 | +42.4% | `ILS[constructor=random, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| default:ILS | 14.23% | 782.9 | 186 | +42.3% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=segment_reversal_kick]` |
| VNS:constructor=greedy_cheapest_incremental_distance | 15.19% | 789.0 | 187 | +41.8% | `VNS[constructor=greedy_cheapest_incremental_distance, neighborhood=customer_swap_neighborhood]` |
| default:VNS | 15.49% | 790.9 | 188 | +41.7% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_demand_aware_urgency | 15.78% | 793.7 | 190 | +41.5% | `VNS[constructor=greedy_demand_aware_urgency, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_route_utilization_balance | 16.14% | 796.2 | 191 | +41.3% | `VNS[constructor=greedy_route_utilization_balance, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=random | 17.27% | 807.1 | 204 | +40.5% | `VNS[constructor=random, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:destruction=uniform_arc_destruction | 23.13% | 842.1 | 196 | +37.9% | `LNS_MIP[constructor=trivial, destruction=uniform_arc_destruction]` |
| LNS_MIP:constructor=greedy_demand_aware_urgency | 45.12% | 1018.1 | 352 | +24.9% | `LNS_MIP[constructor=greedy_demand_aware_urgency, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=greedy_cheapest_incremental_distance | 62.84% | 1123.8 | 313 | +17.1% | `LNS_MIP[constructor=greedy_cheapest_incremental_distance, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=random | 71.44% | 1183.2 | 321 | +12.7% | `LNS_MIP[constructor=random, destruction=related_customer_destruction]` |
| LNS_MIP:constructor=greedy_route_utilization_balance | 74.31% | 1197.9 | 333 | +11.6% | `LNS_MIP[constructor=greedy_route_utilization_balance, destruction=related_customer_destruction]` |
| default:LNS_MIP | 96.08% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=related_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+3.38%**; gana en 10/10 instancias de test. Esqueletos explorados: SA × 22, ILS × 6, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_reversal_neighborhood` (mejor default por gap): +3.63% de gap a favor del afinado, IC95 [+2.70%, +4.59%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 17 ✔ | 0.4912 | 0.4896, 0.4923, 0.4917 | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` |
| 39 | 0.4939 | 0.4897, 0.4960, 0.4960 | `SA[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 20 | 0.4939 | 0.4952, 0.4974, 0.4892 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| 16 | 0.5033 | 0.5047, 0.5010, 0.5042 | `SA[constructor=trivial, neighborhood=two_opt_reversal_neighborhood]` |
| 39 (numéricos por defecto) | 0.5035 | 0.5013, 0.5023, 0.5068 | `SA[constructor=greedy_route_utilization_balance, neighborhood=two_opt_reversal_neighborhood]` |
| 17 (numéricos por defecto) | 0.5038 | 0.5105, 0.4953, 0.5056 | `SA[constructor=greedy_cheapest_incremental_distance, neighborhood=two_opt_reversal_neighborhood]` |
| 20 (numéricos por defecto) | 0.5058 | 0.5102, 0.5007, 0.5065 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=two_opt_reversal_neighborhood]` |
| 38 | 0.5072 | 0.5135, 0.4999, 0.5083 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=relocate_customer_neighborhood]` |
| 38 (numéricos por defecto) | 0.5226 | 0.5250, 0.5247, 0.5181 | `SA[constructor=greedy_demand_aware_urgency, neighborhood=relocate_customer_neighborhood]` |
| 0* | 0.5289 | 0.5303, 0.5288, 0.5275 | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
