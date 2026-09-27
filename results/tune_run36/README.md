## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.11% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| r1 | 1 | 1.35% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| r2 | 2 | 1.46% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |

**Afinado entre réplicas**: media 1.31%, desvío 0.14%, rango [1.11%, 1.46%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=two_opt_segment_reversal` = 2.33%. Afinado vs ese: +1.03% de gap a favor del afinado, IC95 [+0.29%, +1.78%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3354 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4720 (mejor default: 0.4872, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.02%** | **676.9** | 155 | +50.1% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.16% | 683.8 | 154 | +49.6% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 2.89% | 689.6 | 159 | +49.1% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 4.09% | 698.0 | 162 | +48.5% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| default:ILS | 4.39% | 698.2 | 155 | +48.5% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 4.84% | 702.4 | 162 | +48.2% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 5.18% | 705.1 | 163 | +48.0% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=random | 5.39% | 705.3 | 159 | +48.0% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.57% | 706.4 | 158 | +47.9% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 5.74% | 708.8 | 165 | +47.7% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:SA | 5.75% | 707.8 | 160 | +47.8% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_geometric_cluster_completion | 5.91% | 709.3 | 164 | +47.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 6.09% | 710.4 | 162 | +47.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 6.19% | 712.1 | 165 | +47.5% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 6.38% | 712.8 | 163 | +47.4% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 6.44% | 713.8 | 166 | +47.4% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| default:VNS | 6.53% | 714.4 | 166 | +47.3% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.56% | 712.4 | 158 | +47.5% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 6.66% | 713.9 | 162 | +47.3% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 6.73% | 715.4 | 165 | +47.2% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:neighborhood=customer_swap_neighborhood | 8.12% | 724.6 | 167 | +46.6% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 8.55% | 728.9 | 174 | +46.2% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 8.62% | 727.9 | 169 | +46.3% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| SA:neighborhood=customer_swap_neighborhood | 9.31% | 734.0 | 176 | +45.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 30.23% | 873.6 | 217 | +35.6% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 31.21% | 876.6 | 204 | +35.3% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 36.65% | 918.5 | 241 | +32.3% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 40.93% | 944.7 | 231 | +30.3% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 40.95% | 939.4 | 270 | +30.7% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 41.71% | 947.7 | 233 | +30.1% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 100.20% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+1.01%**; gana en 7/10 instancias de test. Esqueletos explorados: SA × 13, VNS × 13, ILS × 8, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +1.15% de gap a favor del afinado, IC95 [+0.25%, +2.15%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 34 ✔ | 0.4720 | 0.4721, 0.4728, 0.4721, 0.4711 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 22 | 0.4752 | 0.4732, 0.4769, 0.4762, 0.4744 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 22 (numéricos por defecto) | 0.4752 | 0.4762, 0.4765, 0.4731 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4759 | 0.4771, 0.4759, 0.4746 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4765 | 0.4781, 0.4748, 0.4765 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 25 | 0.4777 | 0.4784, 0.4770, 0.4777 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 36 | 0.4797 | 0.4749, 0.4771, 0.4871 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=intra_route_block_shuffle]` |
| 34 (numéricos por defecto) | 0.4880 | 0.4856, 0.4912, 0.4872 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 1* | 0.4915 | 0.4872, 0.4917, 0.4956 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 36 (numéricos por defecto) | 0.4967 | 0.4962, 0.5008, 0.4931 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=intra_route_block_shuffle]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 4024 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4741 (mejor default: 0.4951, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.24%** | **678.2** | 154 | +50.0% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.31% | 684.8 | 155 | +49.5% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 3.68% | 695.2 | 160 | +48.7% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| default:ILS | 4.86% | 701.1 | 154 | +48.3% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 4.97% | 704.1 | 164 | +48.1% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 5.10% | 704.2 | 163 | +48.1% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 5.57% | 708.0 | 166 | +47.8% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.57% | 706.4 | 158 | +47.9% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| default:SA | 5.74% | 707.8 | 160 | +47.8% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 5.89% | 708.8 | 160 | +47.7% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_geometric_cluster_completion | 5.90% | 709.3 | 164 | +47.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 6.08% | 710.4 | 162 | +47.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 6.55% | 714.7 | 168 | +47.3% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.55% | 712.4 | 158 | +47.5% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 6.76% | 716.0 | 167 | +47.2% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_geometric_cluster_completion | 7.13% | 718.1 | 165 | +47.0% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 7.31% | 719.9 | 168 | +46.9% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 7.50% | 721.4 | 169 | +46.8% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 7.53% | 719.7 | 163 | +46.9% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 7.56% | 721.4 | 168 | +46.8% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 9.13% | 733.2 | 176 | +45.9% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| SA:neighborhood=customer_swap_neighborhood | 9.30% | 734.0 | 176 | +45.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=customer_swap_neighborhood | 9.50% | 733.8 | 169 | +45.9% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=intra_route_block_shuffle | 9.55% | 734.9 | 174 | +45.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 30.20% | 875.2 | 218 | +35.4% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 30.97% | 876.6 | 209 | +35.3% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 38.08% | 926.5 | 238 | +31.7% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 41.67% | 948.3 | 238 | +30.1% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 42.32% | 954.0 | 231 | +29.6% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 42.97% | 947.8 | 262 | +30.1% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 100.19% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.97%**; gana en 9/10 instancias de test. Esqueletos explorados: SA × 16, VNS × 12, ILS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +1.06% de gap a favor del afinado, IC95 [+0.44%, +1.75%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 25 ✔ | 0.4741 | 0.4733, 0.4742, 0.4732, 0.4737, 0.4723, 0.4771, 0.4749 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4745 | 0.4740, 0.4760, 0.4753, 0.4739, 0.4745, 0.4740, 0.4737 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 28 | 0.4746 | 0.4750, 0.4722, 0.4745, 0.4758, 0.4756, 0.4746, 0.4741 | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 19 | 0.4762 | 0.4751, 0.4760, 0.4744, 0.4793 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 17 | 0.4772 | 0.4749, 0.4764, 0.4775, 0.4800 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 19 (numéricos por defecto) | 0.4772 | 0.4756, 0.4837, 0.4723 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 17 (numéricos por defecto) | 0.4773 | 0.4802, 0.4763, 0.4754 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4941 | 0.4910, 0.4960, 0.4952 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 1* | 0.4946 | 0.4951, 0.4916, 0.4972 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 28 (numéricos por defecto) | 0.4969 | 0.4979, 0.4944, 0.4985 | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3750 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` = 0.4731 (mejor default: 0.4844, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.44%** | **679.4** | 156 | +49.9% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.31% | 684.1 | 154 | +49.5% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 2.98% | 689.6 | 159 | +49.1% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 4.30% | 698.7 | 162 | +48.5% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| default:ILS | 4.48% | 698.2 | 155 | +48.5% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 4.94% | 702.5 | 162 | +48.2% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 5.28% | 705.1 | 163 | +48.0% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=random | 5.48% | 705.4 | 159 | +48.0% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.66% | 706.4 | 158 | +47.9% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| default:SA | 5.83% | 707.8 | 160 | +47.8% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 5.89% | 709.4 | 165 | +47.7% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_geometric_cluster_completion | 6.00% | 709.3 | 164 | +47.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 6.17% | 710.4 | 162 | +47.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 6.36% | 712.7 | 166 | +47.4% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 6.54% | 713.3 | 163 | +47.4% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 6.59% | 714.1 | 166 | +47.3% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.65% | 712.4 | 158 | +47.5% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 6.77% | 715.7 | 167 | +47.2% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 6.90% | 714.8 | 162 | +47.3% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 6.91% | 716.1 | 166 | +47.2% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:neighborhood=customer_swap_neighborhood | 8.21% | 724.6 | 167 | +46.6% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=intra_route_block_shuffle | 8.75% | 728.2 | 170 | +46.3% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| ILS:perturbation=multi_reinsert_kick | 8.76% | 729.6 | 174 | +46.2% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| SA:neighborhood=customer_swap_neighborhood | 9.40% | 734.0 | 176 | +45.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 24.30% | 834.7 | 205 | +38.4% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 25.87% | 842.8 | 199 | +37.8% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 28.61% | 864.3 | 228 | +36.3% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 28.89% | 868.6 | 228 | +35.9% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 31.21% | 879.9 | 212 | +35.1% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 31.52% | 880.8 | 229 | +35.0% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 100.36% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.69%**; gana en 7/10 instancias de test. Esqueletos explorados: SA × 16, VNS × 11, ILS × 7, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.86% de gap a favor del afinado, IC95 [+0.07%, +1.62%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 ✔ | 0.4731 | 0.4715, 0.4757, 0.4710, 0.4725, 0.4738, 0.4754, 0.4721 | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 27 (numéricos por defecto) | 0.4741 | 0.4747, 0.4733, 0.4734, 0.4755, 0.4743, 0.4755, 0.4716 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 23 | 0.4754 | 0.4730, 0.4751, 0.4734, 0.4802 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 23 (numéricos por defecto) | 0.4757 | 0.4768, 0.4732, 0.4771 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4773 | 0.4790, 0.4748, 0.4782 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 27 | 0.4777 | 0.4760, 0.4798, 0.4773 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 18 | 0.4787 | 0.4801, 0.4779, 0.4781 | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| 18 (numéricos por defecto) | 0.4811 | 0.4747, 0.4834, 0.4852 | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| 1* | 0.4876 | 0.4844, 0.4945, 0.4839 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 33 (numéricos por defecto) | 0.4900 | 0.4906, 0.4862, 0.4931 | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
