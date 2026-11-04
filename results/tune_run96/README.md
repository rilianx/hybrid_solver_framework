## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.20% | `HYB[constructor=random, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.20%, desvío 0.00%, rango [0.20%, 0.20%].

**Mejor no afinado** (media entre réplicas): `HYB:neighborhood=route_dissolve_reinsert` = 0.50%. Afinado vs ese: +0.30% de gap a favor del afinado, IC95 [-0.03%, +0.66%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (cvrp x100) · 0 configuraciones fallidas · 2402 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_clarke_wright_savings`, `polar_sweep_2opt`, `sequential_cheapest_insertion`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `radial_ruin_cheapest_blink_insert`, `random_feasible_move_chain_kick`, `route_copy_relink`, `giant_tour_swap_relink`, `route_prefix_growth_relink`, `granular_intra_or_opt`, `granular_swap_star`, `route_dissolve_reinsert`

**Mejor en train**: `HYB[constructor=random, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` = 0.1385

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.20%** | **13511.8** | 3935 | +88.2% | `HYB[constructor=random, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:neighborhood=route_dissolve_reinsert | 0.50% | 13549.0 | 3928 | +88.2% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_two_opt_star | 0.85% | 13602.8 | 3952 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=composite | 0.88% | 13601.7 | 3949 | +88.2% | `HYB[constructor=trivial, neighborhood=composite, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_swap_star | 1.09% | 13624.0 | 3922 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_swap_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_cross_exchange | 1.12% | 13634.5 | 3946 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_cross_exchange, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=sequential_cheapest_insertion | 1.21% | 13641.2 | 3932 | +88.1% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_intra_or_opt | 1.32% | 13658.2 | 3932 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_intra_or_opt, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=randomized_clarke_wright_savings | 1.53% | 13691.5 | 3950 | +88.1% | `HYB[constructor=randomized_clarke_wright_savings, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:destruction=random_variables | 1.57% | 13697.4 | 3953 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:constructor=polar_sweep_2opt | 1.60% | 13699.4 | 3948 | +88.1% | `HYB[constructor=polar_sweep_2opt, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| default:HYB | 1.68% | 13707.6 | 3945 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=random | 1.92% | 13736.3 | 3937 | +88.1% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:perturbation=random_feasible_move_chain_kick | 8.02% | 14544.6 | 4103 | +87.3% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **+0.27%**; gana en 4/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `HYB:neighborhood=route_dissolve_reinsert` (mejor default por gap): +0.30% de gap a favor del afinado, IC95 [-0.03%, +0.66%] — **no se distingue del ruido** con estas instancias.
