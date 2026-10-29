## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.44% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| r1 | 1 | 0.76% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| r2 | 2 | 0.71% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |

**Afinado entre réplicas**: media 0.97%, desvío 0.33%, rango [0.71%, 1.44%].

**Mejor no afinado** (media entre réplicas): `ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert` = 0.87%. Afinado vs ese: -0.10% de gap a favor del afinado, IC95 [-0.78%, +0.59%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 0 configuraciones fallidas · 4140 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_arc_destruction`, `route_cluster_arc_destruction`, `shaw_relatedness_arc_destruction`, `insertion_cost_per_demand`, `polar_sweep_angle_gap`, `savings_isolation_seed_far`, `giant_tour_depot_2opt`, `or_opt_segment_relocation`, `two_opt_star_tail_exchange`, `giant_tour_double_bridge_resplit`, `random_relocate_k_capacity_aware`, `spatial_ruin_noisy_cheapest_reinsert`

**Mejor en train**: `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` = 0.3207 (mejor default: 0.3221, `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.44%** | **678.4** | 159 | +66.3% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert | 0.90% | 673.7 | 153 | +66.5% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| SA:constructor=greedy_insertion_cost_per_demand | 1.72% | 679.7 | 159 | +66.2% | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=random | 1.74% | 679.9 | 156 | +66.2% | `SA[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_polar_sweep_angle_gap | 1.78% | 679.8 | 155 | +66.2% | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt]` |
| default:SA | 2.00% | 682.5 | 161 | +66.1% | `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_savings_isolation_seed_far | 2.07% | 681.3 | 155 | +66.2% | `SA[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt]` |
| SA:neighborhood=or_opt_segment_relocation | 3.17% | 688.8 | 157 | +65.8% | `SA[constructor=trivial, neighborhood=or_opt_segment_relocation]` |
| VNS:constructor=greedy_savings_isolation_seed_far | 5.31% | 703.1 | 163 | +65.1% | `VNS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=greedy_polar_sweep_angle_gap | 6.53% | 712.0 | 167 | +64.6% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=greedy_insertion_cost_per_demand | 6.83% | 714.2 | 165 | +64.5% | `VNS[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=random | 6.84% | 714.9 | 169 | +64.5% | `VNS[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| default:VNS | 6.86% | 714.6 | 167 | +64.5% | `VNS[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| VNS:neighborhood=or_opt_segment_relocation | 7.46% | 718.8 | 170 | +64.3% | `VNS[constructor=trivial, neighborhood=or_opt_segment_relocation]` |
| VNS:neighborhood=two_opt_star_tail_exchange | 9.64% | 733.9 | 176 | +63.6% | `VNS[constructor=trivial, neighborhood=two_opt_star_tail_exchange]` |
| ILS:constructor=greedy_savings_isolation_seed_far | 10.51% | 739.9 | 180 | +63.3% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| SA:neighborhood=two_opt_star_tail_exchange | 11.04% | 738.7 | 172 | +63.3% | `SA[constructor=trivial, neighborhood=two_opt_star_tail_exchange]` |
| ILS:constructor=greedy_insertion_cost_per_demand | 11.62% | 746.4 | 175 | +62.9% | `ILS[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| default:ILS | 12.00% | 748.9 | 176 | +62.8% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=greedy_polar_sweep_angle_gap | 12.04% | 749.0 | 175 | +62.8% | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=random | 12.24% | 750.7 | 176 | +62.7% | `ILS[constructor=random, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:perturbation=random_relocate_k_capacity_aware | 13.20% | 757.3 | 181 | +62.4% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| ILS:neighborhood=or_opt_segment_relocation | 13.53% | 758.5 | 176 | +62.3% | `ILS[constructor=trivial, neighborhood=or_opt_segment_relocation, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:neighborhood=two_opt_star_tail_exchange | 15.66% | 772.5 | 178 | +61.6% | `ILS[constructor=trivial, neighborhood=two_opt_star_tail_exchange, perturbation=giant_tour_double_bridge_resplit]` |
| LNS_MIP:constructor=greedy_savings_isolation_seed_far | 17.22% | 788.2 | 211 | +60.9% | `LNS_MIP[constructor=greedy_savings_isolation_seed_far, destruction=random_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_insertion_cost_per_demand | 23.37% | 823.1 | 196 | +59.1% | `LNS_MIP[constructor=greedy_insertion_cost_per_demand, destruction=random_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle_gap | 27.22% | 850.4 | 208 | +57.8% | `LNS_MIP[constructor=greedy_polar_sweep_angle_gap, destruction=random_customer_arc_destruction]` |
| LNS_MIP:destruction=route_cluster_arc_destruction | 28.10% | 857.6 | 242 | +57.4% | `LNS_MIP[constructor=trivial, destruction=route_cluster_arc_destruction]` |
| LNS_MIP:constructor=random | 62.62% | 1080.8 | 335 | +46.3% | `LNS_MIP[constructor=random, destruction=random_customer_arc_destruction]` |
| LNS_MIP:destruction=shaw_relatedness_arc_destruction | 68.29% | 1117.5 | 263 | +44.5% | `LNS_MIP[constructor=trivial, destruction=shaw_relatedness_arc_destruction]` |
| default:LNS_MIP | 83.74% | 1232.5 | 335 | +38.8% | `LNS_MIP[constructor=trivial, destruction=random_customer_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **-0.70%**; gana en 4/10 instancias de test. Esqueletos explorados: ILS × 17, SA × 11, VNS × 6, LNS_MIP × 6.

Afinado vs `ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert` (mejor default por gap): -0.53% de gap a favor del afinado, IC95 [-1.73%, +0.45%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 28 ✔ | 0.3207 | 0.3205, 0.3216, 0.3202, 0.3199, 0.3211, 0.3206, 0.3209 | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| 25 | 0.3214 | 0.3207, 0.3217, 0.3209, 0.3207, 0.3211, 0.3221, 0.3223 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 32 | 0.3214 | 0.3209, 0.3199, 0.3220, 0.3217, 0.3217, 0.3207, 0.3226 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| 25 (numéricos por defecto) | 0.3214 | 0.3189, 0.3199, 0.3261, 0.3248, 0.3196, 0.3197, 0.3207 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 22 | 0.3220 | 0.3215, 0.3212, 0.3213, 0.3253, 0.3218, 0.3211, 0.3221 | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| 0* | 0.3232 | 0.3221, 0.3233, 0.3244 | `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| 22 (numéricos por defecto) | 0.3255 | 0.3244, 0.3258, 0.3264 | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| 28 (numéricos por defecto) | 0.3545 | 0.3504, 0.3558, 0.3574 | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| 32 (numéricos por defecto) | 0.3614 | 0.3588, 0.3663, 0.3593 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 0 configuraciones fallidas · 3872 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_arc_destruction`, `route_cluster_arc_destruction`, `shaw_relatedness_arc_destruction`, `insertion_cost_per_demand`, `polar_sweep_angle_gap`, `savings_isolation_seed_far`, `giant_tour_depot_2opt`, `or_opt_segment_relocation`, `two_opt_star_tail_exchange`, `giant_tour_double_bridge_resplit`, `random_relocate_k_capacity_aware`, `spatial_ruin_noisy_cheapest_reinsert`

**Mejor en train**: `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` = 0.3204 (mejor default: 0.3226, `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.76%** | **673.1** | 154 | +66.6% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert | 0.89% | 673.6 | 153 | +66.5% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| SA:constructor=greedy_polar_sweep_angle_gap | 1.52% | 678.2 | 156 | +66.3% | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_insertion_cost_per_demand | 1.64% | 678.0 | 152 | +66.3% | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=random | 1.84% | 680.2 | 156 | +66.2% | `SA[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_savings_isolation_seed_far | 2.17% | 681.4 | 154 | +66.2% | `SA[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt]` |
| default:SA | 2.30% | 683.8 | 159 | +66.0% | `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| SA:neighborhood=or_opt_segment_relocation | 4.13% | 695.3 | 158 | +65.5% | `SA[constructor=trivial, neighborhood=or_opt_segment_relocation]` |
| VNS:constructor=greedy_savings_isolation_seed_far | 5.11% | 702.0 | 163 | +65.1% | `VNS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=greedy_polar_sweep_angle_gap | 6.25% | 710.1 | 166 | +64.7% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=random | 6.51% | 712.7 | 168 | +64.6% | `VNS[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=greedy_insertion_cost_per_demand | 6.56% | 712.5 | 166 | +64.6% | `VNS[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| default:VNS | 6.64% | 713.3 | 167 | +64.6% | `VNS[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| VNS:neighborhood=or_opt_segment_relocation | 7.20% | 716.8 | 169 | +64.4% | `VNS[constructor=trivial, neighborhood=or_opt_segment_relocation]` |
| VNS:neighborhood=two_opt_star_tail_exchange | 9.03% | 729.5 | 174 | +63.8% | `VNS[constructor=trivial, neighborhood=two_opt_star_tail_exchange]` |
| SA:neighborhood=two_opt_star_tail_exchange | 9.21% | 725.6 | 167 | +64.0% | `SA[constructor=trivial, neighborhood=two_opt_star_tail_exchange]` |
| ILS:constructor=greedy_savings_isolation_seed_far | 10.35% | 739.1 | 180 | +63.3% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=greedy_insertion_cost_per_demand | 11.46% | 745.5 | 175 | +63.0% | `ILS[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| default:ILS | 11.82% | 747.8 | 176 | +62.9% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=random | 11.90% | 748.1 | 175 | +62.8% | `ILS[constructor=random, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=greedy_polar_sweep_angle_gap | 11.96% | 748.3 | 174 | +62.8% | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:perturbation=random_relocate_k_capacity_aware | 13.00% | 756.3 | 182 | +62.4% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| ILS:neighborhood=or_opt_segment_relocation | 13.31% | 757.2 | 176 | +62.4% | `ILS[constructor=trivial, neighborhood=or_opt_segment_relocation, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:neighborhood=two_opt_star_tail_exchange | 15.39% | 771.1 | 179 | +61.7% | `ILS[constructor=trivial, neighborhood=two_opt_star_tail_exchange, perturbation=giant_tour_double_bridge_resplit]` |
| LNS_MIP:constructor=greedy_savings_isolation_seed_far | 16.55% | 782.9 | 205 | +61.1% | `LNS_MIP[constructor=greedy_savings_isolation_seed_far, destruction=random_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_insertion_cost_per_demand | 23.16% | 821.8 | 196 | +59.2% | `LNS_MIP[constructor=greedy_insertion_cost_per_demand, destruction=random_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle_gap | 26.65% | 846.4 | 207 | +58.0% | `LNS_MIP[constructor=greedy_polar_sweep_angle_gap, destruction=random_customer_arc_destruction]` |
| LNS_MIP:destruction=route_cluster_arc_destruction | 28.56% | 860.4 | 241 | +57.3% | `LNS_MIP[constructor=trivial, destruction=route_cluster_arc_destruction]` |
| LNS_MIP:constructor=random | 57.41% | 1041.9 | 304 | +48.3% | `LNS_MIP[constructor=random, destruction=random_customer_arc_destruction]` |
| LNS_MIP:destruction=shaw_relatedness_arc_destruction | 68.71% | 1120.8 | 264 | +44.3% | `LNS_MIP[constructor=trivial, destruction=shaw_relatedness_arc_destruction]` |
| default:LNS_MIP | 83.10% | 1227.1 | 335 | +39.1% | `LNS_MIP[constructor=trivial, destruction=random_customer_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.07%**; gana en 5/10 instancias de test. Esqueletos explorados: ILS × 17, SA × 11, VNS × 6, LNS_MIP × 6.

Afinado vs `ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert` (mejor default por gap): +0.13% de gap a favor del afinado, IC95 [-0.34%, +0.69%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 38 | 0.3201 | 0.3192, 0.3201, 0.3201, 0.3202, 0.3203, 0.3207, 0.3201 | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 38 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.3204 | 0.3206, 0.3198, 0.3210, 0.3204, 0.3200, 0.3199, 0.3210 | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 37 (numéricos por defecto) | 0.3204 | 0.3218, 0.3199, 0.3190, 0.3204, 0.3211, 0.3208, 0.3200 | `ILS[constructor=greedy_insertion_cost_per_demand, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 37 | 0.3205 | 0.3216, 0.3216, 0.3203, 0.3200, 0.3201, 0.3207, 0.3194 | `ILS[constructor=greedy_insertion_cost_per_demand, neighborhood=two_opt_star_tail_exchange, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 25 (numéricos por defecto) | 0.3222 | 0.3225, 0.3231, 0.3205, 0.3227 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 0* | 0.3230 | 0.3226, 0.3216, 0.3247 | `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| 25 | 0.3232 | 0.3227, 0.3251, 0.3216 | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 4 | 0.3246 | 0.3234, 0.3247, 0.3256 | `SA[constructor=random, neighborhood=giant_tour_depot_2opt]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_routes 30) · 0 configuraciones fallidas · 3608 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `random_customer_arc_destruction`, `route_cluster_arc_destruction`, `shaw_relatedness_arc_destruction`, `insertion_cost_per_demand`, `polar_sweep_angle_gap`, `savings_isolation_seed_far`, `giant_tour_depot_2opt`, `or_opt_segment_relocation`, `two_opt_star_tail_exchange`, `giant_tour_double_bridge_resplit`, `random_relocate_k_capacity_aware`, `spatial_ruin_noisy_cheapest_reinsert`

**Mejor en train**: `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` = 0.3198 (mejor default: 0.3214, `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.71%** | **672.8** | 154 | +66.6% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert | 0.82% | 673.1 | 152 | +66.6% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| default:SA | 1.32% | 676.7 | 155 | +66.4% | `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_insertion_cost_per_demand | 1.61% | 677.2 | 149 | +66.4% | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_polar_sweep_angle_gap | 1.79% | 679.8 | 156 | +66.2% | `SA[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=random | 2.02% | 682.0 | 159 | +66.1% | `SA[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| SA:constructor=greedy_savings_isolation_seed_far | 2.78% | 684.8 | 152 | +66.0% | `SA[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt]` |
| SA:neighborhood=or_opt_segment_relocation | 3.32% | 689.0 | 153 | +65.8% | `SA[constructor=trivial, neighborhood=or_opt_segment_relocation]` |
| VNS:constructor=greedy_savings_isolation_seed_far | 4.61% | 698.4 | 162 | +65.3% | `VNS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=random | 5.97% | 709.1 | 167 | +64.8% | `VNS[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=greedy_insertion_cost_per_demand | 5.98% | 708.6 | 165 | +64.8% | `VNS[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| VNS:constructor=greedy_polar_sweep_angle_gap | 5.99% | 708.1 | 165 | +64.8% | `VNS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt]` |
| default:VNS | 6.49% | 712.5 | 167 | +64.6% | `VNS[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| VNS:neighborhood=or_opt_segment_relocation | 6.66% | 713.2 | 168 | +64.6% | `VNS[constructor=trivial, neighborhood=or_opt_segment_relocation]` |
| SA:neighborhood=two_opt_star_tail_exchange | 8.15% | 724.4 | 182 | +64.0% | `SA[constructor=trivial, neighborhood=two_opt_star_tail_exchange]` |
| VNS:neighborhood=two_opt_star_tail_exchange | 8.39% | 725.1 | 172 | +64.0% | `VNS[constructor=trivial, neighborhood=two_opt_star_tail_exchange]` |
| ILS:constructor=greedy_savings_isolation_seed_far | 9.74% | 734.4 | 177 | +63.5% | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=greedy_insertion_cost_per_demand | 10.95% | 742.0 | 174 | +63.2% | `ILS[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=greedy_polar_sweep_angle_gap | 11.05% | 742.5 | 173 | +63.1% | `ILS[constructor=greedy_polar_sweep_angle_gap, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| default:ILS | 11.54% | 745.8 | 175 | +63.0% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:constructor=random | 11.68% | 746.6 | 174 | +62.9% | `ILS[constructor=random, neighborhood=giant_tour_depot_2opt, perturbation=giant_tour_double_bridge_resplit]` |
| ILS:perturbation=random_relocate_k_capacity_aware | 12.43% | 753.0 | 181 | +62.6% | `ILS[constructor=trivial, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| ILS:neighborhood=or_opt_segment_relocation | 12.85% | 754.3 | 177 | +62.5% | `ILS[constructor=trivial, neighborhood=or_opt_segment_relocation, perturbation=giant_tour_double_bridge_resplit]` |
| LNS_MIP:constructor=greedy_savings_isolation_seed_far | 14.34% | 767.5 | 196 | +61.9% | `LNS_MIP[constructor=greedy_savings_isolation_seed_far, destruction=random_customer_arc_destruction]` |
| ILS:neighborhood=two_opt_star_tail_exchange | 14.78% | 766.6 | 176 | +61.9% | `ILS[constructor=trivial, neighborhood=two_opt_star_tail_exchange, perturbation=giant_tour_double_bridge_resplit]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle_gap | 21.84% | 814.4 | 198 | +59.6% | `LNS_MIP[constructor=greedy_polar_sweep_angle_gap, destruction=random_customer_arc_destruction]` |
| LNS_MIP:constructor=greedy_insertion_cost_per_demand | 21.88% | 814.5 | 200 | +59.5% | `LNS_MIP[constructor=greedy_insertion_cost_per_demand, destruction=random_customer_arc_destruction]` |
| LNS_MIP:destruction=route_cluster_arc_destruction | 29.65% | 875.7 | 269 | +56.5% | `LNS_MIP[constructor=trivial, destruction=route_cluster_arc_destruction]` |
| LNS_MIP:constructor=random | 46.53% | 980.6 | 297 | +51.3% | `LNS_MIP[constructor=random, destruction=random_customer_arc_destruction]` |
| LNS_MIP:destruction=shaw_relatedness_arc_destruction | 65.42% | 1100.8 | 270 | +45.3% | `LNS_MIP[constructor=trivial, destruction=shaw_relatedness_arc_destruction]` |
| default:LNS_MIP | 76.52% | 1170.2 | 290 | +41.9% | `LNS_MIP[constructor=trivial, destruction=random_customer_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.05%**; gana en 5/10 instancias de test. Esqueletos explorados: ILS × 15, SA × 14, LNS_MIP × 6, VNS × 5.

Afinado vs `ILS:perturbation=spatial_ruin_noisy_cheapest_reinsert` (mejor default por gap): +0.11% de gap a favor del afinado, IC95 [-0.49%, +0.76%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 38 | 0.3197 | 0.3196, 0.3202, 0.3199, 0.3202, 0.3194, 0.3197, 0.3192 | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 38 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.3198 | 0.3205, 0.3192, 0.3195, 0.3207, 0.3199, 0.3197, 0.3193 | `ILS[constructor=greedy_savings_isolation_seed_far, neighborhood=giant_tour_depot_2opt, perturbation=spatial_ruin_noisy_cheapest_reinsert]` |
| 21 | 0.3208 | 0.3208, 0.3206, 0.3206, 0.3200, 0.3207, 0.3200, 0.3230 | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| 39 | 0.3212 | 0.3214, 0.3213, 0.3210 | `ILS[constructor=random, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
| 0* | 0.3225 | 0.3214, 0.3227, 0.3235 | `SA[constructor=trivial, neighborhood=giant_tour_depot_2opt]` |
| 4 | 0.3250 | 0.3241, 0.3267, 0.3242 | `SA[constructor=random, neighborhood=giant_tour_depot_2opt]` |
| 21 (numéricos por defecto) | 0.3267 | 0.3255, 0.3247, 0.3298 | `SA[constructor=greedy_insertion_cost_per_demand, neighborhood=giant_tour_depot_2opt]` |
| 39 (numéricos por defecto) | 0.3550 | 0.3530, 0.3590, 0.3529 | `ILS[constructor=random, neighborhood=giant_tour_depot_2opt, perturbation=random_relocate_k_capacity_aware]` |
