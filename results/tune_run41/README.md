## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.42% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| r1 | 1 | 0.68% | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| r2 | 2 | 1.12% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |

**Afinado entre réplicas**: media 0.74%, desvío 0.29%, rango [0.42%, 1.12%].

**Mejor no afinado** (media entre réplicas): `ILS:perturbation=ruin_recreate_radial_blink` = 1.76%. Afinado vs ese: +1.02% de gap a favor del afinado, IC95 [+0.16%, +2.06%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 0 configuraciones fallidas · 3431 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `route_block_destruction`, `spatial_cluster_arc_destruction`, `worst_detour_arc_destruction`, `best_fit_load_distance_blend`, `generalized_savings_far_seed`, `nearest_neighbor_closure_penalty`, `route_merge_split`, `segment_relocation_oropt`, `two_opt_intra_and_star`, `giant_tour_double_bridge_split`, `random_interroute_relocate_swap`, `ruin_recreate_radial_blink`

**Mejor en train**: `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` = 0.3198 (mejor default: 0.3904, `VNS[constructor=trivial, neighborhood=route_merge_split]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.41%** | **671.0** | 154 | +66.7% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| ILS:perturbation=ruin_recreate_radial_blink | 1.78% | 679.3 | 152 | +66.3% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=ruin_recreate_radial_blink]` |
| SA:neighborhood=two_opt_intra_and_star | 2.85% | 687.1 | 158 | +65.9% | `SA[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| SA:neighborhood=segment_relocation_oropt | 4.75% | 698.5 | 154 | +65.3% | `SA[constructor=trivial, neighborhood=segment_relocation_oropt]` |
| VNS:neighborhood=two_opt_intra_and_star | 4.78% | 702.0 | 167 | +65.1% | `VNS[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| LNS_MIP:destruction=worst_detour_arc_destruction | 5.58% | 705.2 | 161 | +65.0% | `LNS_MIP[constructor=trivial, destruction=worst_detour_arc_destruction]` |
| VNS:neighborhood=segment_relocation_oropt | 7.87% | 719.8 | 163 | +64.3% | `VNS[constructor=trivial, neighborhood=segment_relocation_oropt]` |
| LNS_MIP:constructor=greedy_generalized_savings_far_seed | 9.98% | 736.8 | 182 | +63.4% | `LNS_MIP[constructor=greedy_generalized_savings_far_seed, destruction=route_block_destruction]` |
| ILS:neighborhood=two_opt_intra_and_star | 10.28% | 737.2 | 171 | +63.4% | `ILS[constructor=trivial, neighborhood=two_opt_intra_and_star, perturbation=giant_tour_double_bridge_split]` |
| VNS:constructor=greedy_generalized_savings_far_seed | 11.14% | 745.1 | 184 | +63.0% | `VNS[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split]` |
| VNS:constructor=greedy_nearest_neighbor_closure_penalty | 13.61% | 757.8 | 174 | +62.4% | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split]` |
| VNS:constructor=greedy_best_fit_load_distance_blend | 14.98% | 767.9 | 181 | +61.9% | `VNS[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split]` |
| ILS:constructor=greedy_generalized_savings_far_seed | 16.83% | 784.9 | 201 | +61.0% | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:neighborhood=segment_relocation_oropt | 16.96% | 783.6 | 188 | +61.1% | `ILS[constructor=trivial, neighborhood=segment_relocation_oropt, perturbation=giant_tour_double_bridge_split]` |
| LNS_MIP:constructor=greedy_best_fit_load_distance_blend | 18.43% | 793.1 | 199 | +60.6% | `LNS_MIP[constructor=greedy_best_fit_load_distance_blend, destruction=route_block_destruction]` |
| SA:constructor=greedy_generalized_savings_far_seed | 20.13% | 809.0 | 216 | +59.8% | `SA[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split]` |
| default:VNS | 20.92% | 810.1 | 198 | +59.8% | `VNS[constructor=trivial, neighborhood=route_merge_split]` |
| VNS:constructor=random | 21.01% | 809.4 | 192 | +59.8% | `VNS[constructor=random, neighborhood=route_merge_split]` |
| ILS:constructor=greedy_best_fit_load_distance_blend | 21.76% | 815.2 | 198 | +59.5% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:constructor=greedy_nearest_neighbor_closure_penalty | 22.83% | 822.2 | 197 | +59.2% | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| LNS_MIP:constructor=greedy_nearest_neighbor_closure_penalty | 23.67% | 828.3 | 209 | +58.9% | `LNS_MIP[constructor=greedy_nearest_neighbor_closure_penalty, destruction=route_block_destruction]` |
| ILS:constructor=random | 24.09% | 831.7 | 202 | +58.7% | `ILS[constructor=random, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| default:ILS | 24.56% | 834.3 | 200 | +58.6% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:perturbation=random_interroute_relocate_swap | 24.62% | 835.7 | 206 | +58.5% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=random_interroute_relocate_swap]` |
| SA:constructor=greedy_best_fit_load_distance_blend | 28.95% | 864.7 | 220 | +57.1% | `SA[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split]` |
| SA:constructor=greedy_nearest_neighbor_closure_penalty | 32.60% | 885.5 | 212 | +56.0% | `SA[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split]` |
| default:LNS_MIP | 45.99% | 965.8 | 244 | +52.0% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=spatial_cluster_arc_destruction | 67.26% | 1102.3 | 259 | +45.3% | `LNS_MIP[constructor=trivial, destruction=spatial_cluster_arc_destruction]` |
| default:SA | 115.22% | 1446.3 | 367 | +28.2% | `SA[constructor=trivial, neighborhood=route_merge_split]` |
| SA:constructor=random | 117.98% | 1457.1 | 339 | +27.6% | `SA[constructor=random, neighborhood=route_merge_split]` |
| LNS_MIP:constructor=random | 15537306422.27% | 100000000872.5 | 299999999709 | -4966184780.0% | `LNS_MIP[constructor=random, destruction=route_block_destruction]` |

Ganancia del afinado sobre el mejor default: **+1.22%**; gana en 9/10 instancias de test. Esqueletos explorados: ILS × 20, SA × 8, VNS × 6, LNS_MIP × 6.

Afinado vs `ILS:perturbation=ruin_recreate_radial_blink` (mejor default por gap): +1.36% de gap a favor del afinado, IC95 [+0.27%, +2.56%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 34 ✔ | 0.3198 | 0.3192, 0.3191, 0.3202, 0.3204, 0.3200 | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 23 | 0.3210 | 0.3203, 0.3223, 0.3210, 0.3202, 0.3212 | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 25 | 0.3218 | 0.3226, 0.3215, 0.3213 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 34 (numéricos por defecto) | 0.3238 | 0.3238, 0.3237, 0.3239 | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 25 (numéricos por defecto) | 0.3241 | 0.3238, 0.3248, 0.3237 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 23 (numéricos por defecto) | 0.3244 | 0.3244, 0.3239, 0.3250 | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 16 | 0.3247 | 0.3224, 0.3232, 0.3283 | `SA[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| 30 | 0.3250 | 0.3255, 0.3257, 0.3237 | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star]` |
| 30 (numéricos por defecto) | 0.3350 | 0.3298, 0.3421, 0.3332 | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star]` |
| 2* | 0.3864 | 0.3904, 0.3819, 0.3870 | `VNS[constructor=trivial, neighborhood=route_merge_split]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 1 configuraciones fallidas · 3954 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `route_block_destruction`, `spatial_cluster_arc_destruction`, `worst_detour_arc_destruction`, `best_fit_load_distance_blend`, `generalized_savings_far_seed`, `nearest_neighbor_closure_penalty`, `route_merge_split`, `segment_relocation_oropt`, `two_opt_intra_and_star`, `giant_tour_double_bridge_split`, `random_interroute_relocate_swap`, `ruin_recreate_radial_blink`

**Mejor en train**: `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` = 0.3196 (mejor default: 0.3785, `VNS[constructor=trivial, neighborhood=route_merge_split]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.66%** | **672.7** | 155 | +66.6% | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| ILS:perturbation=ruin_recreate_radial_blink | 1.83% | 679.7 | 152 | +66.2% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=ruin_recreate_radial_blink]` |
| SA:neighborhood=two_opt_intra_and_star | 3.43% | 690.4 | 156 | +65.7% | `SA[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| SA:neighborhood=segment_relocation_oropt | 4.50% | 695.8 | 151 | +65.4% | `SA[constructor=trivial, neighborhood=segment_relocation_oropt]` |
| VNS:neighborhood=two_opt_intra_and_star | 4.77% | 702.0 | 167 | +65.1% | `VNS[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| LNS_MIP:destruction=worst_detour_arc_destruction | 5.64% | 705.8 | 161 | +65.0% | `LNS_MIP[constructor=trivial, destruction=worst_detour_arc_destruction]` |
| VNS:neighborhood=segment_relocation_oropt | 7.85% | 719.8 | 163 | +64.3% | `VNS[constructor=trivial, neighborhood=segment_relocation_oropt]` |
| LNS_MIP:constructor=greedy_generalized_savings_far_seed | 9.31% | 731.7 | 177 | +63.7% | `LNS_MIP[constructor=greedy_generalized_savings_far_seed, destruction=route_block_destruction]` |
| ILS:neighborhood=two_opt_intra_and_star | 10.26% | 737.2 | 171 | +63.4% | `ILS[constructor=trivial, neighborhood=two_opt_intra_and_star, perturbation=giant_tour_double_bridge_split]` |
| VNS:constructor=greedy_generalized_savings_far_seed | 11.09% | 744.8 | 184 | +63.0% | `VNS[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split]` |
| VNS:constructor=greedy_nearest_neighbor_closure_penalty | 13.60% | 757.8 | 174 | +62.4% | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split]` |
| VNS:constructor=greedy_best_fit_load_distance_blend | 14.98% | 768.0 | 181 | +61.9% | `VNS[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split]` |
| ILS:constructor=greedy_generalized_savings_far_seed | 16.81% | 784.9 | 201 | +61.0% | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:neighborhood=segment_relocation_oropt | 16.95% | 783.6 | 188 | +61.1% | `ILS[constructor=trivial, neighborhood=segment_relocation_oropt, perturbation=giant_tour_double_bridge_split]` |
| LNS_MIP:constructor=greedy_best_fit_load_distance_blend | 17.71% | 787.8 | 194 | +60.9% | `LNS_MIP[constructor=greedy_best_fit_load_distance_blend, destruction=route_block_destruction]` |
| SA:constructor=greedy_generalized_savings_far_seed | 20.11% | 809.0 | 216 | +59.8% | `SA[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split]` |
| VNS:constructor=random | 20.91% | 809.1 | 192 | +59.8% | `VNS[constructor=random, neighborhood=route_merge_split]` |
| default:VNS | 21.02% | 810.9 | 198 | +59.7% | `VNS[constructor=trivial, neighborhood=route_merge_split]` |
| ILS:constructor=greedy_best_fit_load_distance_blend | 21.76% | 815.3 | 199 | +59.5% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:constructor=greedy_nearest_neighbor_closure_penalty | 22.81% | 822.2 | 197 | +59.2% | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| LNS_MIP:constructor=greedy_nearest_neighbor_closure_penalty | 23.52% | 827.5 | 209 | +58.9% | `LNS_MIP[constructor=greedy_nearest_neighbor_closure_penalty, destruction=route_block_destruction]` |
| ILS:constructor=random | 24.07% | 831.7 | 202 | +58.7% | `ILS[constructor=random, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| default:ILS | 24.55% | 834.3 | 200 | +58.6% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:perturbation=random_interroute_relocate_swap | 24.60% | 835.7 | 206 | +58.5% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=random_interroute_relocate_swap]` |
| SA:constructor=greedy_best_fit_load_distance_blend | 28.93% | 864.7 | 220 | +57.1% | `SA[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split]` |
| SA:constructor=greedy_nearest_neighbor_closure_penalty | 32.58% | 885.5 | 212 | +56.0% | `SA[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split]` |
| default:LNS_MIP | 48.95% | 983.8 | 234 | +51.1% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=spatial_cluster_arc_destruction | 65.00% | 1093.0 | 275 | +45.7% | `LNS_MIP[constructor=trivial, destruction=spatial_cluster_arc_destruction]` |
| default:SA | 115.19% | 1446.3 | 367 | +28.2% | `SA[constructor=trivial, neighborhood=route_merge_split]` |
| SA:constructor=random | 117.96% | 1457.1 | 339 | +27.6% | `SA[constructor=random, neighborhood=route_merge_split]` |
| LNS_MIP:constructor=random | 15528751136.80% | 100000000866.1 | 299999999711 | -4966184779.7% | `LNS_MIP[constructor=random, destruction=route_block_destruction]` |

Ganancia del afinado sobre el mejor default: **+1.02%**; gana en 8/10 instancias de test. Esqueletos explorados: ILS × 19, SA × 8, VNS × 7, LNS_MIP × 6.

Afinado vs `ILS:perturbation=ruin_recreate_radial_blink` (mejor default por gap): +1.17% de gap a favor del afinado, IC95 [+0.19%, +2.39%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 31 ✔ | 0.3196 | 0.3203, 0.3198, 0.3199, 0.3191, 0.3193, 0.3195, 0.3190 | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 34 | 0.3197 | 0.3192, 0.3204, 0.3200, 0.3193, 0.3199, 0.3198, 0.3188 | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 24 | 0.3215 | 0.3193, 0.3199, 0.3207, 0.3220, 0.3216, 0.3256 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 39 | 0.3227 | 0.3238, 0.3227, 0.3217 | `ILS[constructor=random, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 31 (numéricos por defecto) | 0.3235 | 0.3236, 0.3234, 0.3235 | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 24 (numéricos por defecto) | 0.3240 | 0.3238, 0.3249, 0.3232 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 38 | 0.3242 | 0.3240, 0.3242, 0.3245 | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=segment_relocation_oropt]` |
| 34 (numéricos por defecto) | 0.3248 | 0.3247, 0.3258, 0.3238 | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 39 (numéricos por defecto) | 0.3254 | 0.3256, 0.3274, 0.3233 | `ILS[constructor=random, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 38 (numéricos por defecto) | 0.3361 | 0.3351, 0.3386, 0.3344 | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=segment_relocation_oropt]` |
| 2* | 0.3844 | 0.3785, 0.3875, 0.3874 | `VNS[constructor=trivial, neighborhood=route_merge_split]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 1 configuraciones fallidas · 3623 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `route_block_destruction`, `spatial_cluster_arc_destruction`, `worst_detour_arc_destruction`, `best_fit_load_distance_blend`, `generalized_savings_far_seed`, `nearest_neighbor_closure_penalty`, `route_merge_split`, `segment_relocation_oropt`, `two_opt_intra_and_star`, `giant_tour_double_bridge_split`, `random_interroute_relocate_swap`, `ruin_recreate_radial_blink`

**Mejor en train**: `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` = 0.3198 (mejor default: 0.3747, `VNS[constructor=trivial, neighborhood=route_merge_split]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.10%** | **675.5** | 154 | +66.5% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| ILS:perturbation=ruin_recreate_radial_blink | 1.61% | 678.3 | 152 | +66.3% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=ruin_recreate_radial_blink]` |
| SA:neighborhood=two_opt_intra_and_star | 2.10% | 681.4 | 152 | +66.2% | `SA[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| SA:neighborhood=segment_relocation_oropt | 3.91% | 692.3 | 152 | +65.6% | `SA[constructor=trivial, neighborhood=segment_relocation_oropt]` |
| VNS:neighborhood=two_opt_intra_and_star | 4.30% | 699.0 | 167 | +65.3% | `VNS[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| LNS_MIP:destruction=worst_detour_arc_destruction | 4.83% | 699.8 | 157 | +65.2% | `LNS_MIP[constructor=trivial, destruction=worst_detour_arc_destruction]` |
| LNS_MIP:constructor=greedy_generalized_savings_far_seed | 6.86% | 717.0 | 180 | +64.4% | `LNS_MIP[constructor=greedy_generalized_savings_far_seed, destruction=route_block_destruction]` |
| VNS:neighborhood=segment_relocation_oropt | 7.10% | 714.5 | 160 | +64.5% | `VNS[constructor=trivial, neighborhood=segment_relocation_oropt]` |
| VNS:constructor=greedy_generalized_savings_far_seed | 8.44% | 726.6 | 176 | +63.9% | `VNS[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split]` |
| ILS:neighborhood=two_opt_intra_and_star | 9.10% | 729.8 | 170 | +63.8% | `ILS[constructor=trivial, neighborhood=two_opt_intra_and_star, perturbation=giant_tour_double_bridge_split]` |
| VNS:constructor=greedy_nearest_neighbor_closure_penalty | 11.01% | 739.5 | 164 | +63.3% | `VNS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split]` |
| VNS:constructor=greedy_best_fit_load_distance_blend | 12.40% | 750.3 | 173 | +62.7% | `VNS[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split]` |
| LNS_MIP:constructor=greedy_best_fit_load_distance_blend | 14.22% | 763.9 | 188 | +62.1% | `LNS_MIP[constructor=greedy_best_fit_load_distance_blend, destruction=route_block_destruction]` |
| ILS:neighborhood=segment_relocation_oropt | 15.19% | 770.8 | 181 | +61.7% | `ILS[constructor=trivial, neighborhood=segment_relocation_oropt, perturbation=giant_tour_double_bridge_split]` |
| default:VNS | 16.03% | 776.2 | 185 | +61.5% | `VNS[constructor=trivial, neighborhood=route_merge_split]` |
| ILS:constructor=greedy_generalized_savings_far_seed | 16.29% | 781.0 | 198 | +61.2% | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| VNS:constructor=random | 16.89% | 781.8 | 186 | +61.2% | `VNS[constructor=random, neighborhood=route_merge_split]` |
| LNS_MIP:constructor=greedy_nearest_neighbor_closure_penalty | 17.51% | 783.4 | 180 | +61.1% | `LNS_MIP[constructor=greedy_nearest_neighbor_closure_penalty, destruction=route_block_destruction]` |
| ILS:constructor=greedy_best_fit_load_distance_blend | 19.95% | 803.4 | 194 | +60.1% | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| SA:constructor=greedy_generalized_savings_far_seed | 20.11% | 809.0 | 216 | +59.8% | `SA[constructor=greedy_generalized_savings_far_seed, neighborhood=route_merge_split]` |
| ILS:constructor=greedy_nearest_neighbor_closure_penalty | 21.02% | 809.3 | 189 | +59.8% | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| ILS:perturbation=random_interroute_relocate_swap | 22.03% | 818.4 | 201 | +59.4% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=random_interroute_relocate_swap]` |
| ILS:constructor=random | 22.09% | 818.3 | 198 | +59.4% | `ILS[constructor=random, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| default:ILS | 22.63% | 820.9 | 195 | +59.2% | `ILS[constructor=trivial, neighborhood=route_merge_split, perturbation=giant_tour_double_bridge_split]` |
| SA:constructor=greedy_best_fit_load_distance_blend | 28.93% | 864.7 | 220 | +57.1% | `SA[constructor=greedy_best_fit_load_distance_blend, neighborhood=route_merge_split]` |
| SA:constructor=greedy_nearest_neighbor_closure_penalty | 32.58% | 885.5 | 212 | +56.0% | `SA[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=route_merge_split]` |
| default:LNS_MIP | 50.54% | 1004.3 | 293 | +50.1% | `LNS_MIP[constructor=trivial, destruction=route_block_destruction]` |
| LNS_MIP:destruction=spatial_cluster_arc_destruction | 52.12% | 998.0 | 253 | +50.4% | `LNS_MIP[constructor=trivial, destruction=spatial_cluster_arc_destruction]` |
| default:SA | 115.19% | 1446.3 | 367 | +28.2% | `SA[constructor=trivial, neighborhood=route_merge_split]` |
| SA:constructor=random | 117.96% | 1457.1 | 339 | +27.6% | `SA[constructor=random, neighborhood=route_merge_split]` |
| LNS_MIP:constructor=random | 5727414286.86% | 33333334223.9 | 179505493406 | -1655394889.8% | `LNS_MIP[constructor=random, destruction=route_block_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.42%**; gana en 6/10 instancias de test. Esqueletos explorados: ILS × 17, SA × 11, VNS × 6, LNS_MIP × 6.

Afinado vs `ILS:perturbation=ruin_recreate_radial_blink` (mejor default por gap): +0.51% de gap a favor del afinado, IC95 [-0.20%, +1.34%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 ✔ | 0.3198 | 0.3200, 0.3197, 0.3197, 0.3196, 0.3196, 0.3197, 0.3202 | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 37 | 0.3198 | 0.3193, 0.3191, 0.3197, 0.3202, 0.3198, 0.3204, 0.3202 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 25 | 0.3212 | 0.3215, 0.3208, 0.3212 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=segment_relocation_oropt, perturbation=ruin_recreate_radial_blink]` |
| 30 | 0.3215 | 0.3220, 0.3213, 0.3211 | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 16 | 0.3218 | 0.3218, 0.3214, 0.3223 | `SA[constructor=trivial, neighborhood=two_opt_intra_and_star]` |
| 37 (numéricos por defecto) | 0.3223 | 0.3221, 0.3225, 0.3225 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 33 (numéricos por defecto) | 0.3224 | 0.3233, 0.3228, 0.3211 | `ILS[constructor=greedy_best_fit_load_distance_blend, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 30 (numéricos por defecto) | 0.3228 | 0.3226, 0.3220, 0.3239 | `ILS[constructor=greedy_nearest_neighbor_closure_penalty, neighborhood=two_opt_intra_and_star, perturbation=ruin_recreate_radial_blink]` |
| 25 (numéricos por defecto) | 0.3235 | 0.3245, 0.3219, 0.3240 | `ILS[constructor=greedy_generalized_savings_far_seed, neighborhood=segment_relocation_oropt, perturbation=ruin_recreate_radial_blink]` |
| 2* | 0.3723 | 0.3747, 0.3697, 0.3724 | `VNS[constructor=trivial, neighborhood=route_merge_split]` |
