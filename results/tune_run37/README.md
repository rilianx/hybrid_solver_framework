## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.51% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| r1 | 1 | 0.73% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| r2 | 2 | 0.49% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |

**Afinado entre réplicas**: media 0.58%, desvío 0.11%, rango [0.49%, 0.73%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=two_opt_segment_reversal` = 0.87%. Afinado vs ese: +0.29% de gap a favor del afinado, IC95 [+0.09%, +0.49%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 1 configuraciones fallidas · 3308 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4700 (mejor default: 0.4780, `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.45%** | **671.0** | 153 | +50.5% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 0.81% | 672.9 | 152 | +50.4% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 1.99% | 681.5 | 156 | +49.7% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 3.09% | 688.6 | 157 | +49.2% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 3.27% | 690.2 | 159 | +49.1% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 3.40% | 690.4 | 156 | +49.1% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 3.43% | 691.1 | 159 | +49.0% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_geometric_cluster_completion | 3.44% | 691.7 | 161 | +49.0% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| default:SA | 3.52% | 690.9 | 155 | +49.0% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 3.68% | 692.3 | 157 | +48.9% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_capacity_balance_frontier | 3.75% | 693.4 | 161 | +48.9% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_capacity_balance_frontier | 3.84% | 694.4 | 161 | +48.8% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| default:ILS | 3.96% | 693.8 | 156 | +48.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=random | 4.13% | 695.1 | 158 | +48.7% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 4.14% | 696.1 | 160 | +48.7% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:neighborhood=customer_swap_neighborhood | 4.19% | 696.5 | 161 | +48.6% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 4.34% | 696.9 | 159 | +48.6% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 4.48% | 698.6 | 162 | +48.5% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 4.51% | 697.9 | 158 | +48.5% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 4.57% | 699.3 | 163 | +48.4% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 5.16% | 703.2 | 163 | +48.1% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=customer_swap_neighborhood | 6.15% | 709.5 | 164 | +47.7% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 6.86% | 715.2 | 169 | +47.2% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 7.17% | 716.2 | 165 | +47.2% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 31.14% | 875.4 | 208 | +35.4% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 31.22% | 876.8 | 216 | +35.3% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 37.32% | 919.1 | 237 | +32.2% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 41.76% | 945.6 | 234 | +30.3% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 42.01% | 943.4 | 270 | +30.4% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| default:LNS_MIP | 42.35% | 952.6 | 236 | +29.7% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 100.77% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.28%**; gana en 6/10 instancias de test. Esqueletos explorados: VNS × 17, SA × 9, ILS × 8, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.36% de gap a favor del afinado, IC95 [+0.05%, +0.69%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 30 ✔ | 0.4700 | 0.4690, 0.4710, 0.4701, 0.4700 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 39 | 0.4712 | 0.4721, 0.4702, 0.4704, 0.4721 | `VNS[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 26 | 0.4714 | 0.4713, 0.4712, 0.4718 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=multi_reinsert_kick]` |
| 25 | 0.4716 | 0.4710, 0.4720, 0.4718 | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4718 | 0.4716, 0.4722, 0.4717 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 39 (numéricos por defecto) | 0.4799 | 0.4777, 0.4814, 0.4805 | `VNS[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4801 | 0.4803, 0.4803, 0.4798 | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 30 (numéricos por defecto) | 0.4804 | 0.4814, 0.4784, 0.4813 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 0* | 0.4823 | 0.4780, 0.4861, 0.4828 | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| 26 (numéricos por defecto) | 0.4891 | 0.4904, 0.4884, 0.4887 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=multi_reinsert_kick]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 4218 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4706 (mejor default: 0.4809, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.59%** | **672.6** | 154 | +50.4% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 0.57% | 672.5 | 154 | +50.4% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 1.90% | 681.5 | 156 | +49.7% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| SA:constructor=random | 2.98% | 687.1 | 153 | +49.3% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:neighborhood=two_opt_segment_reversal | 3.00% | 688.6 | 157 | +49.2% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 3.27% | 690.9 | 160 | +49.0% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 3.29% | 690.2 | 156 | +49.1% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_geometric_cluster_completion | 3.34% | 691.1 | 158 | +49.0% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 3.34% | 691.1 | 159 | +49.0% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:SA | 3.56% | 692.5 | 158 | +48.9% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_capacity_balance_frontier | 3.69% | 693.6 | 161 | +48.8% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:ILS | 3.88% | 693.9 | 156 | +48.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_capacity_balance_frontier | 4.00% | 695.2 | 159 | +48.7% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 4.06% | 695.2 | 158 | +48.7% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 4.08% | 696.3 | 160 | +48.6% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 4.25% | 696.9 | 159 | +48.6% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 4.39% | 698.6 | 162 | +48.5% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 4.45% | 698.1 | 158 | +48.5% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 4.48% | 699.3 | 163 | +48.4% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:neighborhood=customer_swap_neighborhood | 4.54% | 699.3 | 162 | +48.4% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 5.02% | 702.7 | 163 | +48.2% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=customer_swap_neighborhood | 6.06% | 709.5 | 164 | +47.7% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 6.82% | 715.4 | 168 | +47.2% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 7.08% | 716.2 | 165 | +47.2% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 30.97% | 875.0 | 204 | +35.5% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 32.41% | 887.0 | 217 | +34.6% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 38.05% | 926.8 | 249 | +31.6% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 42.21% | 953.0 | 244 | +29.7% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 42.54% | 954.6 | 238 | +29.6% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 46.02% | 967.8 | 268 | +28.6% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 100.60% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **-0.02%**; gana en 5/10 instancias de test. Esqueletos explorados: SA × 20, VNS × 8, ILS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): -0.01% de gap a favor del afinado, IC95 [-0.37%, +0.32%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 37 ✔ | 0.4706 | 0.4700, 0.4700, 0.4716, 0.4711, 0.4711, 0.4705, 0.4701 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 23 (numéricos por defecto) | 0.4710 | 0.4705, 0.4713, 0.4701, 0.4713, 0.4711, 0.4712, 0.4716 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 20 (numéricos por defecto) | 0.4715 | 0.4722, 0.4705, 0.4707, 0.4715, 0.4716, 0.4713, 0.4728 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 19 (numéricos por defecto) | 0.4717 | 0.4708, 0.4702, 0.4720, 0.4723, 0.4727, 0.4709, 0.4725 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4718 | 0.4711, 0.4727, 0.4709, 0.4719, 0.4716, 0.4725 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 19 | 0.4735 | 0.4755, 0.4723, 0.4726 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 20 | 0.4759 | 0.4775, 0.4733, 0.4770 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 23 | 0.4760 | 0.4745, 0.4780, 0.4755 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 37 (numéricos por defecto) | 0.4798 | 0.4778, 0.4794, 0.4822 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 1* | 0.4812 | 0.4809, 0.4800, 0.4827 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3734 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4695 (mejor default: 0.4780, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.47%** | **671.1** | 153 | +50.5% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 1.00% | 674.6 | 154 | +50.2% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 1.33% | 677.1 | 156 | +50.1% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_geometric_cluster_completion | 2.16% | 682.1 | 155 | +49.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 2.22% | 683.3 | 158 | +49.6% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:neighborhood=two_opt_segment_reversal | 2.23% | 683.0 | 157 | +49.6% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| default:SA | 2.58% | 685.0 | 157 | +49.5% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 2.78% | 686.4 | 157 | +49.4% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 2.81% | 686.8 | 158 | +49.3% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 2.94% | 686.8 | 155 | +49.3% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 2.98% | 687.4 | 156 | +49.3% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 3.02% | 687.7 | 157 | +49.3% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:VNS | 3.03% | 688.3 | 158 | +49.2% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 3.11% | 687.7 | 154 | +49.3% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 3.46% | 691.1 | 159 | +49.0% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| default:ILS | 3.49% | 690.6 | 156 | +49.1% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 3.54% | 691.3 | 157 | +49.0% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 3.71% | 693.2 | 161 | +48.9% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:neighborhood=customer_swap_neighborhood | 3.71% | 692.7 | 160 | +48.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 3.99% | 694.5 | 159 | +48.8% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:neighborhood=customer_swap_neighborhood | 4.22% | 696.9 | 163 | +48.6% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=customer_swap_neighborhood | 4.59% | 699.1 | 163 | +48.4% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 5.41% | 704.8 | 165 | +48.0% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 5.86% | 707.0 | 162 | +47.9% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 22.97% | 819.5 | 189 | +39.6% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 23.05% | 821.8 | 197 | +39.4% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 25.09% | 833.3 | 200 | +38.5% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| default:LNS_MIP | 26.31% | 844.9 | 205 | +37.7% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 26.55% | 851.1 | 235 | +37.2% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 27.91% | 857.3 | 214 | +36.8% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 100.85% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.52%**; gana en 8/10 instancias de test. Esqueletos explorados: VNS × 15, SA × 13, ILS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.52% de gap a favor del afinado, IC95 [+0.17%, +0.87%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 ✔ | 0.4695 | 0.4687, 0.4700, 0.4701, 0.4696, 0.4697, 0.4688 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4704 | 0.4713, 0.4705, 0.4695, 0.4710, 0.4695, 0.4706 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4704 | 0.4707, 0.4715, 0.4694, 0.4703, 0.4699, 0.4707 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 25 | 0.4709 | 0.4707, 0.4710, 0.4710, 0.4711 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 18 (numéricos por defecto) | 0.4710 | 0.4715, 0.4713, 0.4703 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 18 | 0.4731 | 0.4734, 0.4725, 0.4734 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 39 | 0.4741 | 0.4736, 0.4752, 0.4733 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_swap_neighborhood]` |
| 33 (numéricos por defecto) | 0.4778 | 0.4774, 0.4797, 0.4764 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 1* | 0.4790 | 0.4780, 0.4828, 0.4760 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 39 (numéricos por defecto) | 0.4860 | 0.4865, 0.4861, 0.4853 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_swap_neighborhood]` |
