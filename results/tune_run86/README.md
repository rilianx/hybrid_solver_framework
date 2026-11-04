## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.00% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=group_window]` |

**Afinado entre réplicas**: media 0.00%, desvío 0.00%, rango [0.00%, 0.00%].

**Mejor no afinado** (media entre réplicas): `HYB:neighborhood=granular_swap_star` = 0.00%. Afinado vs ese: +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (cvrp x100) · 0 configuraciones fallidas · 27 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_clarke_wright_savings`, `polar_sweep_2opt`, `sequential_cheapest_insertion`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `radial_ruin_cheapest_blink_insert`, `random_feasible_move_chain_kick`, `route_copy_relink`, `giant_tour_swap_relink`, `route_prefix_growth_relink`, `granular_intra_or_opt`, `granular_swap_star`, `route_dissolve_reinsert`, `geo_ball_arc_release`, `route_centroid_cluster_release`, `detour_weighted_segment_release`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=group_window]` = 1000000000000.0000

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **nan%** | **1000000000000.0** | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=group_window]` |
| default:HYB | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=random | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=randomized_clarke_wright_savings | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=randomized_clarke_wright_savings, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=polar_sweep_2opt | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=polar_sweep_2opt, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:constructor=sequential_cheapest_insertion | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_two_opt_star | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_cross_exchange | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_cross_exchange, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_intra_or_opt | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_intra_or_opt, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=granular_swap_star | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_swap_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=route_dissolve_reinsert | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:neighborhood=composite | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=composite, perturbation=radial_ruin_cheapest_blink_insert, destruction=geo_ball_arc_release]` |
| HYB:perturbation=random_feasible_move_chain_kick | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=geo_ball_arc_release]` |
| HYB:destruction=route_centroid_cluster_release | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=route_centroid_cluster_release]` |
| HYB:destruction=detour_weighted_segment_release | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=detour_weighted_segment_release]` |
| HYB:destruction=group_window | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:destruction=random_variables | nan% | 1000000000000.0 | 0 | -869908037.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): +nan% de gap a favor del afinado, IC95 [+nan%, +nan%] — **no se distingue del ruido** con estas instancias.
