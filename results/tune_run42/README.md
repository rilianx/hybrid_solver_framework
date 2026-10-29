## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.51% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| r1 | 1 | 0.47% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| r2 | 2 | 0.27% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |

**Afinado entre réplicas**: media 0.41%, desvío 0.11%, rango [0.27%, 0.51%].

**Mejor no afinado** (media entre réplicas): `SA:neighborhood=giant_tour_2opt_reversal` = 0.83%. Afinado vs ese: +0.42% de gap a favor del afinado, IC95 [+0.18%, +0.71%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 6 configuraciones fallidas · 3572 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `neighbor_routes_subproblem_destruction`, `shaw_relatedness_arc_destruction`, `worst_detour_arc_destruction`, `far_seed_best_fit_fill`, `nearest_neighbor_return_aware`, `polar_sweep_angle_gap`, `decoded_routes_2opt_star_tail_exchange`, `giant_tour_2opt_reversal`, `giant_tour_or_opt_segment_shift`, `multi_double_bridge_tour`, `route_cross_exchange_shuffle`, `spatial_ruin_cheapest_recreate`

**Mejor en train**: `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` = 0.4705 (mejor default: 0.4811, `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.44%** | **671.1** | 152 | +50.5% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| SA:neighborhood=giant_tour_2opt_reversal | 0.82% | 673.7 | 154 | +50.3% | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| SA:neighborhood=giant_tour_or_opt_segment_shift | 1.88% | 681.0 | 156 | +49.8% | `SA[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift]` |
| VNS:neighborhood=giant_tour_2opt_reversal | 2.25% | 683.7 | 158 | +49.6% | `VNS[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| VNS:constructor=greedy_far_seed_best_fit_fill | 3.15% | 689.3 | 157 | +49.2% | `VNS[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=random | 3.17% | 689.0 | 155 | +49.2% | `VNS[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=greedy_nearest_neighbor_return_aware | 3.22% | 690.3 | 159 | +49.1% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| default:VNS | 3.50% | 691.1 | 155 | +49.0% | `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=greedy_polar_sweep_angle_gap | 3.63% | 692.9 | 159 | +48.9% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=greedy_nearest_neighbor_return_aware | 4.39% | 697.8 | 160 | +48.5% | `SA[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:neighborhood=giant_tour_or_opt_segment_shift | 4.42% | 698.3 | 160 | +48.5% | `VNS[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift]` |
| SA:constructor=greedy_polar_sweep_angle_gap | 4.76% | 700.8 | 162 | +48.3% | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=greedy_far_seed_best_fit_fill | 5.04% | 701.3 | 158 | +48.3% | `SA[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=random | 5.16% | 703.6 | 165 | +48.1% | `SA[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| default:SA | 5.25% | 702.8 | 159 | +48.2% | `SA[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| ILS:perturbation=spatial_ruin_cheapest_recreate | 5.46% | 705.7 | 165 | +47.9% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=spatial_ruin_cheapest_recreate]` |
| ILS:perturbation=route_cross_exchange_shuffle | 7.74% | 720.4 | 167 | +46.9% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=route_cross_exchange_shuffle]` |
| ILS:neighborhood=giant_tour_2opt_reversal | 9.00% | 729.2 | 169 | +46.2% | `ILS[constructor=trivial, neighborhood=giant_tour_2opt_reversal, perturbation=multi_double_bridge_tour]` |
| default:ILS | 9.44% | 731.4 | 167 | +46.1% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_far_seed_best_fit_fill | 9.50% | 732.7 | 171 | +46.0% | `ILS[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_polar_sweep_angle_gap | 9.99% | 736.1 | 172 | +45.7% | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_nearest_neighbor_return_aware | 10.00% | 735.8 | 171 | +45.7% | `ILS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=random | 10.19% | 737.8 | 173 | +45.6% | `ILS[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:neighborhood=giant_tour_or_opt_segment_shift | 13.17% | 757.1 | 177 | +44.2% | `ILS[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift, perturbation=multi_double_bridge_tour]` |
| default:LNS_MIP | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=random | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=random, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_far_seed_best_fit_fill | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_far_seed_best_fit_fill, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_nearest_neighbor_return_aware | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_nearest_neighbor_return_aware, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle_gap | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_polar_sweep_angle_gap, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:destruction=shaw_relatedness_arc_destruction | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=shaw_relatedness_arc_destruction]` |
| LNS_MIP:destruction=worst_detour_arc_destruction | 159621966209.02% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=worst_detour_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.39%**; gana en 7/10 instancias de test. Esqueletos explorados: VNS × 15, SA × 12, ILS × 7, LNS_MIP × 6.

Afinado vs `SA:neighborhood=giant_tour_2opt_reversal` (mejor default por gap): +0.39% de gap a favor del afinado, IC95 [+0.15%, +0.64%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 30 ✔ | 0.4705 | 0.4698, 0.4698, 0.4715, 0.4710, 0.4707, 0.4709, 0.4698 | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| 20 (numéricos por defecto) | 0.4712 | 0.4709, 0.4719, 0.4701, 0.4703, 0.4730, 0.4711, 0.4708 | `SA[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| 8 | 0.4715 | 0.4723, 0.4706, 0.4709, 0.4722, 0.4723, 0.4709, 0.4715 | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| 19 (numéricos por defecto) | 0.4719 | 0.4715, 0.4723, 0.4705, 0.4721, 0.4717, 0.4724, 0.4727 | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| 19 | 0.4722 | 0.4725, 0.4733, 0.4708 | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| 20 | 0.4754 | 0.4761, 0.4759, 0.4741 | `SA[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| 10 | 0.4757 | 0.4774, 0.4758, 0.4741 | `VNS[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| 30 (numéricos por defecto) | 0.4766 | 0.4760, 0.4772, 0.4767 | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| 2* | 0.4815 | 0.4811, 0.4815, 0.4819 | `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 6 configuraciones fallidas · 3855 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `neighbor_routes_subproblem_destruction`, `shaw_relatedness_arc_destruction`, `worst_detour_arc_destruction`, `far_seed_best_fit_fill`, `nearest_neighbor_return_aware`, `polar_sweep_angle_gap`, `decoded_routes_2opt_star_tail_exchange`, `giant_tour_2opt_reversal`, `giant_tour_or_opt_segment_shift`, `multi_double_bridge_tour`, `route_cross_exchange_shuffle`, `spatial_ruin_cheapest_recreate`

**Mejor en train**: `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` = 0.4706 (mejor default: 0.4801, `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.39%** | **671.2** | 154 | +50.5% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| SA:neighborhood=giant_tour_2opt_reversal | 0.85% | 674.4 | 156 | +50.3% | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| SA:neighborhood=giant_tour_or_opt_segment_shift | 1.81% | 680.6 | 157 | +49.8% | `SA[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift]` |
| VNS:neighborhood=giant_tour_2opt_reversal | 2.06% | 682.4 | 158 | +49.7% | `VNS[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| VNS:constructor=greedy_far_seed_best_fit_fill | 2.77% | 686.7 | 156 | +49.3% | `VNS[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=greedy_nearest_neighbor_return_aware | 2.78% | 687.2 | 158 | +49.3% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=random | 2.79% | 686.2 | 154 | +49.4% | `VNS[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| default:VNS | 3.06% | 688.2 | 155 | +49.2% | `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=greedy_polar_sweep_angle_gap | 3.06% | 688.7 | 157 | +49.2% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:neighborhood=giant_tour_or_opt_segment_shift | 4.05% | 695.7 | 159 | +48.7% | `VNS[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift]` |
| SA:constructor=greedy_nearest_neighbor_return_aware | 4.11% | 694.9 | 155 | +48.7% | `SA[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=greedy_polar_sweep_angle_gap | 4.17% | 696.4 | 160 | +48.6% | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=greedy_far_seed_best_fit_fill | 4.19% | 696.3 | 159 | +48.6% | `SA[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=random | 4.50% | 699.3 | 163 | +48.4% | `SA[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| default:SA | 4.70% | 700.1 | 161 | +48.4% | `SA[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| ILS:perturbation=spatial_ruin_cheapest_recreate | 4.87% | 701.4 | 162 | +48.3% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=spatial_ruin_cheapest_recreate]` |
| ILS:perturbation=route_cross_exchange_shuffle | 7.43% | 718.4 | 167 | +47.0% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=route_cross_exchange_shuffle]` |
| ILS:neighborhood=giant_tour_2opt_reversal | 8.71% | 727.7 | 170 | +46.3% | `ILS[constructor=trivial, neighborhood=giant_tour_2opt_reversal, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_polar_sweep_angle_gap | 9.14% | 730.2 | 170 | +46.1% | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| default:ILS | 9.27% | 730.2 | 167 | +46.1% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_far_seed_best_fit_fill | 9.36% | 731.6 | 170 | +46.0% | `ILS[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_nearest_neighbor_return_aware | 9.47% | 732.6 | 172 | +46.0% | `ILS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=random | 9.95% | 736.2 | 173 | +45.7% | `ILS[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:neighborhood=giant_tour_or_opt_segment_shift | 12.57% | 753.0 | 175 | +44.5% | `ILS[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift, perturbation=multi_double_bridge_tour]` |
| default:LNS_MIP | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=random | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=random, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_far_seed_best_fit_fill | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_far_seed_best_fit_fill, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_nearest_neighbor_return_aware | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_nearest_neighbor_return_aware, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle_gap | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_polar_sweep_angle_gap, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:destruction=shaw_relatedness_arc_destruction | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=shaw_relatedness_arc_destruction]` |
| LNS_MIP:destruction=worst_detour_arc_destruction | 159642272220.47% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=worst_detour_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.48%**; gana en 8/10 instancias de test. Esqueletos explorados: ILS × 16, SA × 10, VNS × 8, LNS_MIP × 6.

Afinado vs `SA:neighborhood=giant_tour_2opt_reversal` (mejor default por gap): +0.46% de gap a favor del afinado, IC95 [+0.06%, +0.84%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 18 ✔ | 0.4706 | 0.4709, 0.4701, 0.4712, 0.4710, 0.4701, 0.4703, 0.4709 | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| 39 | 0.4708 | 0.4698, 0.4713, 0.4698, 0.4711, 0.4698, 0.4723, 0.4715 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal, perturbation=route_cross_exchange_shuffle]` |
| 30 (numéricos por defecto) | 0.4708 | 0.4719, 0.4697, 0.4691, 0.4720, 0.4708, 0.4714, 0.4710 | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| 8 | 0.4711 | 0.4704, 0.4731, 0.4694, 0.4711, 0.4713, 0.4706, 0.4718 | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| 35 | 0.4714 | 0.4700, 0.4715, 0.4720, 0.4721, 0.4711 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal, perturbation=spatial_ruin_cheapest_recreate]` |
| 30 | 0.4727 | 0.4721, 0.4732, 0.4726 | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| 18 (numéricos por defecto) | 0.4758 | 0.4768, 0.4761, 0.4746 | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal]` |
| 2* | 0.4818 | 0.4801, 0.4820, 0.4833 | `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| 35 (numéricos por defecto) | 0.4889 | 0.4883, 0.4875, 0.4909 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal, perturbation=spatial_ruin_cheapest_recreate]` |
| 39 (numéricos por defecto) | 0.4953 | 0.4924, 0.4972, 0.4962 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal, perturbation=route_cross_exchange_shuffle]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 7 configuraciones fallidas · 3012 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `neighbor_routes_subproblem_destruction`, `shaw_relatedness_arc_destruction`, `worst_detour_arc_destruction`, `far_seed_best_fit_fill`, `nearest_neighbor_return_aware`, `polar_sweep_angle_gap`, `decoded_routes_2opt_star_tail_exchange`, `giant_tour_2opt_reversal`, `giant_tour_or_opt_segment_shift`, `multi_double_bridge_tour`, `route_cross_exchange_shuffle`, `spatial_ruin_cheapest_recreate`

**Mejor en train**: `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` = 0.4691 (mejor default: 0.4783, `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **669.4** | 152 | +50.6% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| SA:neighborhood=giant_tour_2opt_reversal | 0.68% | 672.6 | 155 | +50.4% | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| VNS:neighborhood=giant_tour_2opt_reversal | 1.43% | 677.3 | 154 | +50.0% | `VNS[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| SA:neighborhood=giant_tour_or_opt_segment_shift | 1.83% | 679.7 | 154 | +49.9% | `SA[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift]` |
| VNS:constructor=greedy_nearest_neighbor_return_aware | 2.06% | 682.0 | 157 | +49.7% | `VNS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=random | 2.07% | 681.2 | 154 | +49.8% | `VNS[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=greedy_polar_sweep_angle_gap | 2.22% | 682.4 | 155 | +49.7% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:constructor=greedy_far_seed_best_fit_fill | 2.22% | 682.5 | 155 | +49.7% | `VNS[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| default:VNS | 2.30% | 683.1 | 155 | +49.6% | `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| VNS:neighborhood=giant_tour_or_opt_segment_shift | 2.87% | 687.6 | 159 | +49.3% | `VNS[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift]` |
| SA:constructor=greedy_nearest_neighbor_return_aware | 3.13% | 689.2 | 158 | +49.2% | `SA[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| default:SA | 3.64% | 692.5 | 159 | +48.9% | `SA[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=random | 3.91% | 693.5 | 157 | +48.8% | `SA[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| ILS:perturbation=spatial_ruin_cheapest_recreate | 3.93% | 693.7 | 157 | +48.8% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=spatial_ruin_cheapest_recreate]` |
| SA:constructor=greedy_polar_sweep_angle_gap | 3.97% | 695.0 | 161 | +48.7% | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| SA:constructor=greedy_far_seed_best_fit_fill | 4.30% | 696.8 | 161 | +48.6% | `SA[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| ILS:perturbation=route_cross_exchange_shuffle | 6.50% | 711.9 | 166 | +47.5% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=route_cross_exchange_shuffle]` |
| ILS:neighborhood=giant_tour_2opt_reversal | 7.33% | 717.5 | 167 | +47.1% | `ILS[constructor=trivial, neighborhood=giant_tour_2opt_reversal, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_far_seed_best_fit_fill | 8.74% | 726.5 | 167 | +46.4% | `ILS[constructor=greedy_far_seed_best_fit_fill, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_polar_sweep_angle_gap | 8.76% | 727.0 | 168 | +46.4% | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| default:ILS | 8.77% | 726.1 | 165 | +46.4% | `ILS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=greedy_nearest_neighbor_return_aware | 8.93% | 728.1 | 169 | +46.3% | `ILS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:constructor=random | 9.29% | 731.6 | 174 | +46.0% | `ILS[constructor=random, neighborhood=decoded_routes_2opt_star_tail_exchange, perturbation=multi_double_bridge_tour]` |
| ILS:neighborhood=giant_tour_or_opt_segment_shift | 11.73% | 747.3 | 175 | +44.9% | `ILS[constructor=trivial, neighborhood=giant_tour_or_opt_segment_shift, perturbation=multi_double_bridge_tour]` |
| default:LNS_MIP | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=random | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=random, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_far_seed_best_fit_fill | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_far_seed_best_fit_fill, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_nearest_neighbor_return_aware | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_nearest_neighbor_return_aware, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle_gap | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=greedy_polar_sweep_angle_gap, destruction=neighbor_routes_subproblem_destruction]` |
| LNS_MIP:destruction=shaw_relatedness_arc_destruction | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=shaw_relatedness_arc_destruction]` |
| LNS_MIP:destruction=worst_detour_arc_destruction | 159744569516.13% | 1000000000000.0 | 0 | -73758383647.9% | `LNS_MIP[constructor=trivial, destruction=worst_detour_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.47%**; gana en 6/10 instancias de test. Esqueletos explorados: VNS × 16, SA × 10, ILS × 7, LNS_MIP × 7.

Afinado vs `SA:neighborhood=giant_tour_2opt_reversal` (mejor default por gap): +0.41% de gap a favor del afinado, IC95 [+0.05%, +0.87%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 22 ✔ | 0.4691 | 0.4691, 0.4685, 0.4698 | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| 36 | 0.4702 | 0.4703, 0.4701, 0.4701 | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| 36 (numéricos por defecto) | 0.4707 | 0.4701, 0.4708, 0.4711 | `SA[constructor=trivial, neighborhood=giant_tour_2opt_reversal]` |
| 25 | 0.4715 | 0.4717, 0.4719, 0.4711 | `ILS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal, perturbation=spatial_ruin_cheapest_recreate]` |
| 38 | 0.4717 | 0.4718, 0.4711, 0.4722 | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_or_opt_segment_shift]` |
| 37 | 0.4720 | 0.4712, 0.4721, 0.4726 | `VNS[constructor=random, neighborhood=giant_tour_2opt_reversal]` |
| 37 (numéricos por defecto) | 0.4735 | 0.4730, 0.4737, 0.4737 | `VNS[constructor=random, neighborhood=giant_tour_2opt_reversal]` |
| 22 (numéricos por defecto) | 0.4736 | 0.4751, 0.4716, 0.4740 | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_2opt_reversal]` |
| 2* | 0.4782 | 0.4783, 0.4771, 0.4793 | `VNS[constructor=trivial, neighborhood=decoded_routes_2opt_star_tail_exchange]` |
| 38 (numéricos por defecto) | 0.4822 | 0.4789, 0.4850, 0.4827 | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_or_opt_segment_shift]` |
| 25 (numéricos por defecto) | 0.4840 | 0.4839, 0.4845, 0.4836 | `ILS[constructor=greedy_nearest_neighbor_return_aware, neighborhood=giant_tour_2opt_reversal, perturbation=spatial_ruin_cheapest_recreate]` |
