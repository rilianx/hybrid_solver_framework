## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.11% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |

**Afinado entre réplicas**: media 0.11%, desvío 0.00%, rango [0.11%, 0.11%].

**Mejor no afinado** (media entre réplicas): `HYB:neighborhood=route_dissolve_reinsert` = 0.28%. Afinado vs ese: +0.18% de gap a favor del afinado, IC95 [-0.06%, +0.47%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (cvrp x100) · 0 configuraciones fallidas · 2222 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_clarke_wright_savings`, `polar_sweep_2opt`, `sequential_cheapest_insertion`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `radial_ruin_cheapest_blink_insert`, `random_feasible_move_chain_kick`, `route_copy_relink`, `giant_tour_swap_relink`, `route_prefix_growth_relink`, `granular_intra_or_opt`, `granular_swap_star`, `route_dissolve_reinsert`, `geo_ball_arc_release`, `route_centroid_cluster_release`, `detour_weighted_segment_release`

**Mejor en train**: `HYB[constructor=sequential_cheapest_insertion, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` = 0.1380

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.11%** | **13498.3** | 3926 | +88.3% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |
| HYB:neighborhood=route_dissolve_reinsert | 0.28% | 13524.8 | 3932 | +88.2% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=sequential_cheapest_insertion | 0.77% | 13583.8 | 3925 | +88.2% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_two_opt_star | 0.78% | 13592.3 | 3949 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:destruction=random_variables | 1.05% | 13629.2 | 3940 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:neighborhood=granular_cross_exchange | 1.12% | 13634.6 | 3935 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_cross_exchange, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_swap_star | 1.17% | 13636.1 | 3921 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_swap_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=composite | 1.21% | 13638.2 | 3919 | +88.1% | `HYB[constructor=trivial, neighborhood=composite, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_intra_or_opt | 1.26% | 13653.1 | 3936 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_intra_or_opt, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:destruction=route_centroid_cluster_release | 1.31% | 13666.5 | 3953 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=route_centroid_cluster_release]` |
| HYB:destruction=group_window | 1.31% | 13664.8 | 3950 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=polar_sweep_2opt | 1.37% | 13668.2 | 3943 | +88.1% | `HYB[constructor=polar_sweep_2opt, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:destruction=detour_weighted_segment_release | 1.55% | 13690.0 | 3935 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |
| HYB:constructor=randomized_clarke_wright_savings | 1.56% | 13695.2 | 3945 | +88.1% | `HYB[constructor=randomized_clarke_wright_savings, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| default:HYB | 1.60% | 13700.2 | 3946 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=random | 2.05% | 13750.3 | 3929 | +88.0% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:perturbation=random_feasible_move_chain_kick | 9.55% | 14710.1 | 4111 | +87.2% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=geo_ball_arc_release]` |

Ganancia del afinado sobre el mejor default: **+0.20%**; gana en 3/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `HYB:neighborhood=route_dissolve_reinsert` (mejor default por gap): +0.18% de gap a favor del afinado, IC95 [-0.06%, +0.47%] — **no se distingue del ruido** con estas instancias.
