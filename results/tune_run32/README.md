## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 2.67% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| r1 | 1 | 3.44% | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| r2 | 2 | 4.08% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |

**Afinado entre réplicas**: media 3.40%, desvío 0.57%, rango [2.67%, 4.08%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=two_opt_segment_reversal` = 4.66%. Afinado vs ese: +1.27% de gap a favor del afinado, IC95 [+0.38%, +2.05%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3234 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` = 0.4847 (mejor default: 0.5053, `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.62%** | **692.4** | 156 | +48.9% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 3.05% | 695.7 | 157 | +48.7% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| SA:constructor=greedy_geometric_cluster_completion | 6.03% | 716.1 | 165 | +47.2% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 6.18% | 716.6 | 161 | +47.1% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| default:SA | 6.24% | 717.2 | 162 | +47.1% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=two_opt_segment_reversal | 6.31% | 718.2 | 163 | +47.0% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| SA:constructor=random | 6.62% | 720.2 | 164 | +46.9% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 7.28% | 723.0 | 159 | +46.7% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 8.94% | 736.7 | 173 | +45.7% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:ILS | 8.96% | 735.4 | 167 | +45.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:neighborhood=customer_swap_neighborhood | 8.97% | 737.3 | 176 | +45.6% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:neighborhood=two_opt_segment_reversal | 9.19% | 739.7 | 177 | +45.4% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:constructor=greedy_capacity_balance_frontier | 9.21% | 738.0 | 171 | +45.6% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 9.22% | 738.0 | 170 | +45.6% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=random | 9.48% | 738.8 | 167 | +45.5% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:VNS | 10.65% | 748.4 | 174 | +44.8% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 10.90% | 750.9 | 178 | +44.6% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=random | 11.23% | 750.4 | 168 | +44.7% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 11.81% | 754.6 | 170 | +44.3% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 11.82% | 757.8 | 184 | +44.1% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 12.09% | 759.7 | 184 | +44.0% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 12.73% | 762.9 | 183 | +43.7% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 13.16% | 766.7 | 186 | +43.4% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| VNS:neighborhood=customer_swap_neighborhood | 13.44% | 768.5 | 184 | +43.3% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 20.07% | 811.7 | 194 | +40.1% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 20.25% | 812.5 | 191 | +40.1% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 20.31% | 813.6 | 193 | +40.0% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| default:LNS_MIP | 22.29% | 826.2 | 192 | +39.1% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 23.51% | 841.5 | 224 | +37.9% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 24.51% | 845.9 | 221 | +37.6% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 98.55% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.47%**; gana en 5/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +0.43% de gap a favor del afinado, IC95 [-0.87%, +1.74%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 35 | 0.4793 | 0.4770, 0.4779, 0.4829 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4830 | 0.4820, 0.4836, 0.4834 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 21 (numéricos por defecto) | 0.4842 | 0.4828, 0.4848, 0.4850 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 25 | 0.4847 | 0.4851, 0.4843, 0.4846 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 35 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.4847 | 0.4872, 0.4864, 0.4805 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 37 (numéricos por defecto) | 0.4852 | 0.4805, 0.4899, 0.4851 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.4858 | 0.4905, 0.4855, 0.4815 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 21 | 0.4869 | 0.4890, 0.4855, 0.4863 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 37 | 0.5014 | 0.4965, 0.5037, 0.5038 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 0* | 0.5034 | 0.5053, 0.4994, 0.5054 | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3242 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `SA[constructor=random, neighborhood=two_opt_segment_reversal]` = 0.4831 (mejor default: 0.5063, `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.89%** | **698.5** | 161 | +48.5% | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 2.68% | 696.6 | 157 | +48.6% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| SA:constructor=greedy_geometric_cluster_completion | 5.59% | 716.6 | 166 | +47.1% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 5.69% | 716.8 | 161 | +47.1% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=two_opt_segment_reversal | 5.70% | 717.5 | 164 | +47.1% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| default:SA | 5.73% | 717.2 | 162 | +47.1% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 6.12% | 720.4 | 164 | +46.9% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_capacity_balance_frontier | 6.77% | 723.0 | 159 | +46.7% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=greedy_geometric_cluster_completion | 8.21% | 735.1 | 172 | +45.8% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 8.26% | 735.6 | 172 | +45.7% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 8.30% | 735.3 | 169 | +45.8% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 8.37% | 737.7 | 177 | +45.6% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| default:ILS | 8.48% | 735.8 | 167 | +45.7% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:neighborhood=customer_swap_neighborhood | 8.60% | 738.5 | 177 | +45.5% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| ILS:constructor=random | 8.70% | 736.8 | 166 | +45.7% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:VNS | 9.83% | 746.3 | 173 | +45.0% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 10.16% | 749.5 | 178 | +44.7% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=random | 10.45% | 749.3 | 169 | +44.7% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 10.88% | 752.2 | 170 | +44.5% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_capacity_balance_frontier | 11.16% | 757.1 | 184 | +44.2% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 11.51% | 759.4 | 184 | +44.0% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:perturbation=multi_reinsert_kick | 12.07% | 762.1 | 184 | +43.8% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| ILS:perturbation=intra_route_block_shuffle | 12.62% | 766.7 | 186 | +43.4% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| VNS:neighborhood=customer_swap_neighborhood | 12.81% | 767.6 | 183 | +43.4% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 20.46% | 818.9 | 200 | +39.6% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 21.25% | 821.7 | 192 | +39.4% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 23.56% | 842.8 | 221 | +37.8% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 23.57% | 839.1 | 199 | +38.1% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 25.14% | 848.1 | 204 | +37.4% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:constructor=random | 26.40% | 861.4 | 211 | +36.5% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 97.59% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **-0.28%**; gana en 6/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): -0.21% de gap a favor del afinado, IC95 [-1.40%, +0.84%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 17 ✔ | 0.4831 | 0.4800, 0.4828, 0.4864 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 19 (numéricos por defecto) | 0.4851 | 0.4813, 0.4908, 0.4832 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 36 (numéricos por defecto) | 0.4852 | 0.4869, 0.4803, 0.4882 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 25 | 0.4861 | 0.4865, 0.4856, 0.4862 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 17 (numéricos por defecto) | 0.4864 | 0.4857, 0.4863, 0.4871 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.4874 | 0.4861, 0.4863, 0.4896 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 36 | 0.4878 | 0.4828, 0.4903, 0.4902 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 19 | 0.4947 | 0.4895, 0.5001, 0.4945 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 4 | 0.5004 | 0.4968, 0.4994, 0.5050 | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| 0* | 0.5017 | 0.5063, 0.5007, 0.4982 | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 1 configuraciones fallidas · 3234 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_relink_destruction`, `route_block_destruction`, `worst_position_customer_destruction`, `capacity_balance_frontier`, `geometric_cluster_completion`, `nearest_insert_with_return_bias`, `customer_relocate_neighborhood`, `customer_swap_neighborhood`, `two_opt_segment_reversal`, `double_bridge_tour_break`, `intra_route_block_shuffle`, `multi_reinsert_kick`

**Mejor en train**: `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` = 0.4956 (mejor default: 0.5232, `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.85%** | **702.1** | 158 | +48.2% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| SA:neighborhood=two_opt_segment_reversal | 5.35% | 726.4 | 164 | +46.4% | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| default:SA | 7.44% | 741.1 | 170 | +45.3% | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_nearest_insert_with_return_bias | 7.56% | 741.6 | 168 | +45.3% | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=two_opt_segment_reversal | 8.25% | 749.4 | 181 | +44.7% | `ILS[constructor=trivial, neighborhood=two_opt_segment_reversal, perturbation=double_bridge_tour_break]` |
| SA:constructor=greedy_capacity_balance_frontier | 8.80% | 749.3 | 168 | +44.7% | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=greedy_geometric_cluster_completion | 8.93% | 751.8 | 175 | +44.5% | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| SA:constructor=random | 9.03% | 751.1 | 168 | +44.6% | `SA[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:constructor=random | 9.21% | 754.1 | 177 | +44.4% | `ILS[constructor=random, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:neighborhood=two_opt_segment_reversal | 9.50% | 757.3 | 181 | +44.1% | `VNS[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| ILS:constructor=greedy_nearest_insert_with_return_bias | 9.85% | 758.4 | 178 | +44.1% | `ILS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_capacity_balance_frontier | 10.15% | 761.0 | 181 | +43.9% | `ILS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| ILS:constructor=greedy_geometric_cluster_completion | 10.27% | 762.1 | 182 | +43.8% | `ILS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| default:ILS | 10.83% | 765.5 | 180 | +43.5% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=double_bridge_tour_break]` |
| SA:neighborhood=customer_swap_neighborhood | 11.25% | 767.9 | 181 | +43.4% | `SA[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| VNS:constructor=greedy_geometric_cluster_completion | 11.54% | 770.6 | 180 | +43.2% | `VNS[constructor=greedy_geometric_cluster_completion, neighborhood=customer_relocate_neighborhood]` |
| default:VNS | 11.77% | 772.8 | 183 | +43.0% | `VNS[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
| ILS:neighborhood=customer_swap_neighborhood | 12.11% | 775.5 | 186 | +42.8% | `ILS[constructor=trivial, neighborhood=customer_swap_neighborhood, perturbation=double_bridge_tour_break]` |
| VNS:constructor=greedy_capacity_balance_frontier | 12.15% | 774.7 | 182 | +42.9% | `VNS[constructor=greedy_capacity_balance_frontier, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=greedy_nearest_insert_with_return_bias | 12.55% | 779.1 | 188 | +42.5% | `VNS[constructor=greedy_nearest_insert_with_return_bias, neighborhood=customer_relocate_neighborhood]` |
| VNS:constructor=random | 12.58% | 777.1 | 179 | +42.7% | `VNS[constructor=random, neighborhood=customer_relocate_neighborhood]` |
| ILS:perturbation=intra_route_block_shuffle | 12.85% | 781.2 | 190 | +42.4% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=intra_route_block_shuffle]` |
| ILS:perturbation=multi_reinsert_kick | 13.69% | 784.3 | 181 | +42.1% | `ILS[constructor=trivial, neighborhood=customer_relocate_neighborhood, perturbation=multi_reinsert_kick]` |
| VNS:neighborhood=customer_swap_neighborhood | 14.61% | 792.8 | 191 | +41.5% | `VNS[constructor=trivial, neighborhood=customer_swap_neighborhood]` |
| LNS_MIP:constructor=greedy_capacity_balance_frontier | 26.57% | 873.8 | 209 | +35.6% | `LNS_MIP[constructor=greedy_capacity_balance_frontier, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_nearest_insert_with_return_bias | 28.41% | 887.0 | 214 | +34.6% | `LNS_MIP[constructor=greedy_nearest_insert_with_return_bias, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=random | 35.16% | 933.1 | 236 | +31.2% | `LNS_MIP[constructor=random, destruction=random_customer_relink_destruction]` |
| default:LNS_MIP | 37.58% | 950.2 | 235 | +29.9% | `LNS_MIP[constructor=trivial, destruction=random_customer_relink_destruction]` |
| LNS_MIP:constructor=greedy_geometric_cluster_completion | 39.49% | 963.7 | 243 | +28.9% | `LNS_MIP[constructor=greedy_geometric_cluster_completion, destruction=random_customer_relink_destruction]` |
| LNS_MIP:destruction=route_block_destruction | 41.06% | 964.0 | 267 | +28.9% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=worst_position_customer_destruction | 94.36% | 1355.8 | 374 | +0.0% | `LNS_MIP[constructor=trivial, destruction=worst_position_customer_destruction]` |

Ganancia del afinado sobre el mejor default: **+3.36%**; gana en 9/10 instancias de test. Esqueletos explorados: SA × 22, ILS × 7, LNS_MIP × 6, VNS × 5.

Afinado vs `SA:neighborhood=two_opt_segment_reversal` (mejor default por gap): +3.50% de gap a favor del afinado, IC95 [+2.20%, +4.62%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 25 ✔ | 0.4956 | 0.4950, 0.4922, 0.4997 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 22 | 0.4970 | 0.4993, 0.4908, 0.5009 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 23 | 0.5014 | 0.4910, 0.5078, 0.5053 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 16 | 0.5032 | 0.5045, 0.5010, 0.5043 | `SA[constructor=trivial, neighborhood=two_opt_segment_reversal]` |
| 23 (numéricos por defecto) | 0.5050 | 0.5021, 0.5070, 0.5060 | `SA[constructor=greedy_nearest_insert_with_return_bias, neighborhood=two_opt_segment_reversal]` |
| 22 (numéricos por defecto) | 0.5060 | 0.5113, 0.5016, 0.5051 | `SA[constructor=greedy_geometric_cluster_completion, neighborhood=two_opt_segment_reversal]` |
| 36 (numéricos por defecto) | 0.5060 | 0.5107, 0.5060, 0.5014 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 36 | 0.5063 | 0.5074, 0.5045, 0.5072 | `SA[constructor=random, neighborhood=two_opt_segment_reversal]` |
| 25 (numéricos por defecto) | 0.5071 | 0.5063, 0.5076, 0.5073 | `SA[constructor=greedy_capacity_balance_frontier, neighborhood=two_opt_segment_reversal]` |
| 0* | 0.5199 | 0.5232, 0.5109, 0.5255 | `SA[constructor=trivial, neighborhood=customer_relocate_neighborhood]` |
