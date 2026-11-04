## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.18% | `HYB[constructor=random, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |

**Afinado entre réplicas**: media 0.18%, desvío 0.00%, rango [0.18%, 0.18%].

**Mejor no afinado** (media entre réplicas): `HYB:neighborhood=route_dissolve_reinsert` = 0.52%. Afinado vs ese: +0.34% de gap a favor del afinado, IC95 [+0.05%, +0.66%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (cvrp x100) · 0 configuraciones fallidas · 2357 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_clarke_wright_savings`, `polar_sweep_2opt`, `sequential_cheapest_insertion`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `radial_ruin_cheapest_blink_insert`, `random_feasible_move_chain_kick`, `route_copy_relink`, `giant_tour_swap_relink`, `route_prefix_growth_relink`, `granular_intra_or_opt`, `granular_swap_star`, `route_dissolve_reinsert`, `geo_ball_arc_release`, `route_centroid_cluster_release`, `detour_weighted_segment_release`

**Mejor en train**: `HYB[constructor=random, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` = 0.1378

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.18%** | **13510.2** | 3929 | +88.2% | `HYB[constructor=random, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=route_dissolve_reinsert | 0.52% | 13554.3 | 3928 | +88.2% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_two_opt_star | 0.61% | 13569.1 | 3942 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:destruction=random_variables | 0.77% | 13591.8 | 3939 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:neighborhood=granular_swap_star | 0.84% | 13600.9 | 3938 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_swap_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=composite | 0.92% | 13606.3 | 3930 | +88.2% | `HYB[constructor=trivial, neighborhood=composite, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=sequential_cheapest_insertion | 0.93% | 13607.9 | 3932 | +88.2% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:destruction=detour_weighted_segment_release | 0.96% | 13608.5 | 3917 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |
| HYB:neighborhood=granular_cross_exchange | 1.09% | 13634.3 | 3943 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_cross_exchange, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:destruction=group_window | 1.12% | 13639.5 | 3948 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:destruction=route_centroid_cluster_release | 1.13% | 13636.1 | 3932 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=route_centroid_cluster_release]` |
| HYB:neighborhood=granular_intra_or_opt | 1.21% | 13651.6 | 3945 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_intra_or_opt, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=polar_sweep_2opt | 1.28% | 13660.2 | 3945 | +88.1% | `HYB[constructor=polar_sweep_2opt, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=random | 1.31% | 13656.6 | 3926 | +88.1% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| default:HYB | 1.38% | 13666.8 | 3928 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=randomized_clarke_wright_savings | 1.67% | 13708.6 | 3947 | +88.1% | `HYB[constructor=randomized_clarke_wright_savings, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:perturbation=random_feasible_move_chain_kick | 7.39% | 14447.8 | 4020 | +87.4% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=geo_ball_arc_release]` |

Ganancia del afinado sobre el mejor default: **+0.33%**; gana en 4/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `HYB:neighborhood=route_dissolve_reinsert` (mejor default por gap): +0.34% de gap a favor del afinado, IC95 [+0.05%, +0.66%].
