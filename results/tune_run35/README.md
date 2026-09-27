## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.61% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| r1 | 1 | 2.14% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| r2 | 2 | 1.75% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |

**Afinado entre réplicas**: media 1.83%, desvío 0.22%, rango [1.61%, 2.14%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=two_opt_segment_reversal` = 2.24%. Afinado vs ese: +0.41% de gap a favor del afinado, IC95 [-0.06%, +0.88%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 1 configuraciones fallidas · 3212 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4734 (mejor default: 0.4914, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.49%** | **680.9** | 155 | +49.8% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.17% | 684.8 | 155 | +49.5% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 3.55% | 695.2 | 160 | +48.7% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| default:ILS | 4.72% | 701.1 | 154 | +48.3% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 4.83% | 704.1 | 164 | +48.1% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 4.96% | 704.2 | 163 | +48.1% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.43% | 706.4 | 158 | +47.9% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_capacity_balance_frontier | 5.43% | 708.1 | 166 | +47.8% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:SA | 5.60% | 707.8 | 160 | +47.8% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_geometric_cluster_completion | 5.77% | 709.3 | 164 | +47.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 5.80% | 709.0 | 160 | +47.7% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=random | 5.94% | 710.4 | 162 | +47.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.41% | 712.4 | 158 | +47.5% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 6.42% | 714.9 | 169 | +47.3% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:neighborhood=customer_swap_neighborhood | 6.74% | 716.9 | 168 | +47.1% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_geometric_cluster_completion | 7.04% | 718.5 | 166 | +47.0% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 7.23% | 720.4 | 168 | +46.9% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 7.37% | 721.4 | 169 | +46.8% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 7.42% | 721.4 | 168 | +46.8% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 7.44% | 720.0 | 163 | +46.9% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 8.99% | 733.2 | 176 | +45.9% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| SA:neighborhood=customer_swap_neighborhood | 9.16% | 734.0 | 176 | +45.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=customer_swap_neighborhood | 9.35% | 733.8 | 169 | +45.9% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=intra_route_block_shuffle | 9.46% | 735.2 | 174 | +45.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 30.25% | 875.2 | 219 | +35.4% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 30.51% | 876.0 | 209 | +35.4% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 37.31% | 922.6 | 237 | +31.9% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 41.31% | 946.5 | 234 | +30.2% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 42.12% | 954.0 | 231 | +29.6% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 43.31% | 951.1 | 259 | +29.8% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 99.94% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.57%**; gana en 6/10 instancias de test. Esqueletos explorados: SA × 13, VNS × 13, ILS × 8, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.68% de gap a favor del afinado, IC95 [-0.13%, +1.48%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 34 ✔ | 0.4734 | 0.4737, 0.4736, 0.4730 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 22 (numéricos por defecto) | 0.4757 | 0.4765, 0.4776, 0.4731 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 22 | 0.4762 | 0.4738, 0.4778, 0.4770 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4766 | 0.4772, 0.4780, 0.4746 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4771 | 0.4788, 0.4761, 0.4765 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 25 | 0.4786 | 0.4791, 0.4776, 0.4791 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 36 | 0.4819 | 0.4766, 0.4797, 0.4894 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=intra_route_block_shuffle]` |
| 34 (numéricos por defecto) | 0.4916 | 0.4876, 0.4949, 0.4922 | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 1* | 0.4952 | 0.4914, 0.4969, 0.4972 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 36 (numéricos por defecto) | 0.5007 | 0.5026, 0.5055, 0.4940 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=intra_route_block_shuffle]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3372 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` = 0.4740 (mejor default: 0.4898, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.04%** | **683.8** | 154 | +49.6% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.04% | 683.8 | 154 | +49.6% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 2.57% | 688.3 | 158 | +49.2% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 3.72% | 696.5 | 162 | +48.6% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| default:ILS | 4.10% | 696.9 | 154 | +48.6% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 4.46% | 700.8 | 162 | +48.3% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=random | 4.84% | 702.6 | 159 | +48.2% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 4.89% | 703.8 | 163 | +48.1% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_geometric_cluster_completion | 5.02% | 705.0 | 164 | +48.0% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.45% | 706.4 | 158 | +47.9% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| default:SA | 5.62% | 707.8 | 160 | +47.8% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 5.73% | 708.8 | 160 | +47.7% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 5.74% | 709.9 | 165 | +47.6% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_geometric_cluster_completion | 5.79% | 709.3 | 164 | +47.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 5.90% | 710.9 | 164 | +47.6% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 5.96% | 710.4 | 162 | +47.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 6.02% | 710.8 | 162 | +47.6% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 6.11% | 712.2 | 165 | +47.5% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=random | 6.16% | 711.8 | 163 | +47.5% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.43% | 712.4 | 158 | +47.5% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:neighborhood=customer_swap_neighborhood | 7.65% | 722.5 | 168 | +46.7% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 8.19% | 727.3 | 174 | +46.4% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 8.25% | 726.8 | 170 | +46.4% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| SA:neighborhood=customer_swap_neighborhood | 9.19% | 734.0 | 176 | +45.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 24.01% | 834.1 | 205 | +38.5% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 25.59% | 841.9 | 196 | +37.9% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 28.60% | 868.8 | 231 | +35.9% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 29.27% | 870.5 | 232 | +35.8% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 31.36% | 885.3 | 226 | +34.7% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 32.17% | 886.6 | 227 | +34.6% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 99.99% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 1/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.01%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 34 | 0.4731 | 0.4733, 0.4751, 0.4708 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 30 | 0.4735 | 0.4712, 0.4731, 0.4761 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 34 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.4740 | 0.4740, 0.4726, 0.4753 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 20 | 0.4758 | 0.4768, 0.4762, 0.4744 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 30 (numéricos por defecto) | 0.4763 | 0.4773, 0.4779, 0.4737 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 20 (numéricos por defecto) | 0.4766 | 0.4756, 0.4820, 0.4722 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 33 | 0.4793 | 0.4795, 0.4796, 0.4787 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=intra_route_block_shuffle]` |
| 17 | 0.4821 | 0.4833, 0.4816, 0.4815 | `ILS[constructor=random, neighborhood=two_opt_segment_reversal, perturbation=multi_reinsert_kick]` |
| 1* | 0.4900 | 0.4898, 0.4874, 0.4929 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 17 (numéricos por defecto) | 0.4964 | 0.4965, 0.4975, 0.4953 | `ILS[constructor=random, neighborhood=two_opt_segment_reversal, perturbation=multi_reinsert_kick]` |
| 33 (numéricos por defecto) | 0.4966 | 0.4994, 0.4940, 0.4965 | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal, perturbation=intra_route_block_shuffle]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 1 configuraciones fallidas · 3179 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` = 0.4764 (mejor default: 0.4861, `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.63%** | **681.1** | 153 | +49.8% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.17% | 684.8 | 155 | +49.5% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:neighborhood=two_opt_segment_reversal | 3.63% | 695.5 | 160 | +48.7% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| default:ILS | 4.72% | 701.1 | 154 | +48.3% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 4.85% | 704.2 | 164 | +48.1% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 4.97% | 704.3 | 163 | +48.1% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.43% | 706.4 | 158 | +47.9% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_capacity_balance_frontier | 5.44% | 708.1 | 166 | +47.8% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:SA | 5.60% | 707.8 | 160 | +47.8% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_geometric_cluster_completion | 5.77% | 709.3 | 164 | +47.7% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 5.85% | 709.4 | 160 | +47.7% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:constructor=random | 5.94% | 710.4 | 162 | +47.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.41% | 712.4 | 158 | +47.5% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 6.42% | 714.9 | 169 | +47.3% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:neighborhood=customer_swap_neighborhood | 6.74% | 716.9 | 168 | +47.1% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_geometric_cluster_completion | 7.09% | 718.8 | 166 | +47.0% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 7.32% | 720.9 | 168 | +46.8% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 7.40% | 721.7 | 170 | +46.8% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 7.42% | 721.4 | 168 | +46.8% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 7.44% | 720.0 | 163 | +46.9% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 9.01% | 733.3 | 176 | +45.9% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| SA:neighborhood=customer_swap_neighborhood | 9.16% | 734.0 | 176 | +45.9% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=customer_swap_neighborhood | 9.35% | 733.8 | 169 | +45.9% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:perturbation=intra_route_block_shuffle | 9.46% | 735.2 | 174 | +45.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 29.15% | 865.2 | 204 | +36.2% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 29.49% | 870.9 | 217 | +35.8% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 37.18% | 921.9 | 238 | +32.0% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 41.17% | 948.1 | 234 | +30.1% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 41.17% | 941.8 | 270 | +30.5% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 41.66% | 949.7 | 238 | +30.0% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 99.94% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.54%**; gana en 7/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.54% de gap a favor del afinado, IC95 [-0.17%, +1.22%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 28 | 0.4742 | 0.4740, 0.4729, 0.4759 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 23 (numéricos por defecto) | 0.4743 | 0.4761, 0.4733, 0.4734 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 23 | 0.4744 | 0.4743, 0.4738, 0.4750 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 28 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.4764 | 0.4770, 0.4739, 0.4783 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 37 | 0.4766 | 0.4755, 0.4798, 0.4744 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 37 (numéricos por defecto) | 0.4774 | 0.4788, 0.4801, 0.4734 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4776 | 0.4790, 0.4751, 0.4788 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 36 | 0.4886 | 0.4854, 0.4939, 0.4866 | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal, perturbation=multi_reinsert_kick]` |
| 1* | 0.4896 | 0.4861, 0.4957, 0.4869 | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| 36 (numéricos por defecto) | 0.5063 | 0.5037, 0.5079, 0.5072 | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal, perturbation=multi_reinsert_kick]` |
