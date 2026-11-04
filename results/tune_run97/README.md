## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.26% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.26%, desvío 0.00%, rango [0.26%, 0.26%].

**Mejor no afinado** (media entre réplicas): `HYB:neighborhood=route_dissolve_reinsert` = 0.35%. Afinado vs ese: +0.10% de gap a favor del afinado, IC95 [-0.15%, +0.35%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (cvrp x100) · 0 configuraciones fallidas · 2241 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_clarke_wright_savings`, `polar_sweep_2opt`, `sequential_cheapest_insertion`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `radial_ruin_cheapest_blink_insert`, `random_feasible_move_chain_kick`, `route_copy_relink`, `giant_tour_swap_relink`, `route_prefix_growth_relink`, `granular_intra_or_opt`, `granular_swap_star`, `route_dissolve_reinsert`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` = 0.1379

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **13528.8** | 3938 | +88.2% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:neighborhood=route_dissolve_reinsert | 0.35% | 13540.2 | 3933 | +88.2% | `HYB[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_swap_star | 0.56% | 13560.1 | 3920 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_swap_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_two_opt_star | 0.81% | 13602.2 | 3943 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=composite | 0.90% | 13616.9 | 3958 | +88.2% | `HYB[constructor=trivial, neighborhood=composite, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_cross_exchange | 0.94% | 13619.2 | 3940 | +88.2% | `HYB[constructor=trivial, neighborhood=granular_cross_exchange, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:destruction=random_variables | 1.11% | 13643.8 | 3944 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=random_variables]` |
| HYB:constructor=sequential_cheapest_insertion | 1.11% | 13639.6 | 3942 | +88.1% | `HYB[constructor=sequential_cheapest_insertion, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=polar_sweep_2opt | 1.13% | 13647.0 | 3946 | +88.1% | `HYB[constructor=polar_sweep_2opt, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:neighborhood=granular_intra_or_opt | 1.34% | 13670.1 | 3934 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_intra_or_opt, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=randomized_clarke_wright_savings | 1.37% | 13675.4 | 3939 | +88.1% | `HYB[constructor=randomized_clarke_wright_savings, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| default:HYB | 1.50% | 13692.3 | 3950 | +88.1% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:constructor=random | 1.89% | 13742.8 | 3938 | +88.0% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert, destruction=group_window]` |
| HYB:perturbation=random_feasible_move_chain_kick | 8.21% | 14593.7 | 4179 | +87.3% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_feasible_move_chain_kick, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **+0.08%**; gana en 4/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `HYB:neighborhood=route_dissolve_reinsert` (mejor default por gap): +0.10% de gap a favor del afinado, IC95 [-0.15%, +0.35%] — **no se distingue del ruido** con estas instancias.
