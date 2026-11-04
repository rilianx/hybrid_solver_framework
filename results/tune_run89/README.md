## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.09% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |

**Afinado entre réplicas**: media 0.09%, desvío 0.00%, rango [0.09%, 0.09%].

**Mejor no afinado** (media entre réplicas): `HYB:destruction=route_centroid_cluster_release` = 1.38%. Afinado vs ese: +1.29% de gap a favor del afinado, IC95 [+0.43%, +2.71%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (cvrp x100) · 0 configuraciones fallidas · 2065 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_clarke_wright_savings`, `polar_sweep_2opt`, `sequential_cheapest_insertion`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `radial_ruin_cheapest_blink_insert`, `random_feasible_move_chain_kick`, `route_copy_relink`, `giant_tour_swap_relink`, `route_prefix_growth_relink`, `granular_intra_or_opt`, `granular_swap_star`, `route_dissolve_reinsert`, `geo_ball_arc_release`, `route_centroid_cluster_release`, `detour_weighted_segment_release`

**Mejor en train**: `HYB[constructor=sequential_cheapest_insertion, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` = 0.1379

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.09%** | **13501.6** | 3929 | +88.3% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |
| HYB:destruction=route_centroid_cluster_release | 1.38% | 13673.9 | 3945 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=route_centroid_cluster_release]` |
| HYB:destruction=random_variables | 1.42% | 13680.2 | 3945 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:destruction=detour_weighted_segment_release | 1932451665.88% | 250000010359.9 | 433012695911 | -217476943.4% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |
| HYB:destruction=group_window | 2130046690.52% | 250000010148.9 | 433012696033 | -217476943.3% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| default:HYB | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=random | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=randomized_clarke_wright_savings | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=randomized_clarke_wright_savings, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=polar_sweep_2opt | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=polar_sweep_2opt, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=sequential_cheapest_insertion | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_two_opt_star | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_cross_exchange | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_cross_exchange, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_intra_or_opt | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_intra_or_opt, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_swap_star | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_swap_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=route_dissolve_reinsert | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=composite | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=composite, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:perturbation=random_feasible_move_chain_kick | 8124996708.70% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=geo_ball_arc_release]` |

Ganancia del afinado sobre el mejor default: **+1.26%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `HYB:destruction=route_centroid_cluster_release` (mejor default por gap): +1.29% de gap a favor del afinado, IC95 [+0.43%, +2.71%].
