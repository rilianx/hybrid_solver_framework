## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.53% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| r1 | 1 | 0.34% | `ILS[constructor=random, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` |
| r2 | 2 | 0.53% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |

**Afinado entre réplicas**: media 0.47%, desvío 0.09%, rango [0.34%, 0.53%].

**Mejor no afinado** (media entre réplicas): `ILS:perturbation=related_removal_noisy_reinsertion` = 1.36%. Afinado vs ese: +0.89% de gap a favor del afinado, IC95 [+0.39%, +1.39%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 4090 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `route_cluster_destruction`, `shaw_related_arc_destruction`, `worst_detour_destruction`, `farthest_seed_nearest_extend`, `insertion_delta_route_penalty`, `polar_sweep_angle`, `decoded_route_two_opt`, `granular_segment_relocate`, `inter_route_tail_exchange`, `giant_tour_double_bridge`, `related_removal_noisy_reinsertion`

**Mejor en train**: `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` = 0.4701 (mejor default: 0.4828, `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.53%** | **671.6** | 154 | +50.5% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| ILS:perturbation=related_removal_noisy_reinsertion | 1.44% | 677.1 | 154 | +50.1% | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=related_removal_noisy_reinsertion]` |
| VNS:neighborhood=inter_route_tail_exchange | 1.57% | 677.7 | 153 | +50.0% | `VNS[constructor=trivial, neighborhood=inter_route_tail_exchange]` |
| SA:neighborhood=granular_segment_relocate | 1.67% | 679.0 | 155 | +49.9% | `SA[constructor=trivial, neighborhood=granular_segment_relocate]` |
| VNS:neighborhood=granular_segment_relocate | 2.05% | 681.9 | 157 | +49.7% | `VNS[constructor=trivial, neighborhood=granular_segment_relocate]` |
| VNS:constructor=greedy_farthest_seed_nearest_extend | 2.30% | 683.0 | 156 | +49.6% | `VNS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=random | 2.86% | 686.4 | 155 | +49.4% | `VNS[constructor=random, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=greedy_polar_sweep_angle | 3.07% | 688.8 | 159 | +49.2% | `VNS[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt]` |
| default:VNS | 3.49% | 690.8 | 156 | +49.0% | `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]` |
| SA:neighborhood=inter_route_tail_exchange | 3.58% | 691.9 | 159 | +49.0% | `SA[constructor=trivial, neighborhood=inter_route_tail_exchange]` |
| VNS:constructor=greedy_insertion_delta_route_penalty | 3.81% | 692.4 | 156 | +48.9% | `VNS[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt]` |
| ILS:neighborhood=granular_segment_relocate | 5.74% | 706.8 | 165 | +47.9% | `ILS[constructor=trivial, neighborhood=granular_segment_relocate, perturbation=giant_tour_double_bridge]` |
| ILS:neighborhood=inter_route_tail_exchange | 5.75% | 706.4 | 162 | +47.9% | `ILS[constructor=trivial, neighborhood=inter_route_tail_exchange, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=greedy_farthest_seed_nearest_extend | 8.37% | 723.6 | 169 | +46.6% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=greedy_polar_sweep_angle | 9.21% | 730.4 | 170 | +46.1% | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| SA:constructor=greedy_farthest_seed_nearest_extend | 10.13% | 738.1 | 187 | +45.6% | `SA[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt]` |
| ILS:constructor=random | 10.17% | 736.5 | 172 | +45.7% | `ILS[constructor=random, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| default:ILS | 10.42% | 738.9 | 176 | +45.5% | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| LNS_MIP:constructor=greedy_farthest_seed_nearest_extend | 11.00% | 742.5 | 186 | +45.2% | `LNS_MIP[constructor=greedy_farthest_seed_nearest_extend, destruction=route_cluster_destruction]` |
| ILS:constructor=greedy_insertion_delta_route_penalty | 11.04% | 742.9 | 176 | +45.2% | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle | 13.91% | 759.4 | 173 | +44.0% | `LNS_MIP[constructor=greedy_polar_sweep_angle, destruction=route_cluster_destruction]` |
| SA:constructor=greedy_polar_sweep_angle | 15.29% | 771.2 | 184 | +43.1% | `SA[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt]` |
| SA:constructor=greedy_insertion_delta_route_penalty | 16.30% | 781.6 | 204 | +42.4% | `SA[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt]` |
| LNS_MIP:constructor=greedy_insertion_delta_route_penalty | 19.86% | 806.0 | 211 | +40.6% | `LNS_MIP[constructor=greedy_insertion_delta_route_penalty, destruction=route_cluster_destruction]` |
| default:SA | 21.40% | 816.3 | 208 | +39.8% | `SA[constructor=trivial, neighborhood=decoded_route_two_opt]` |
| SA:constructor=random | 22.57% | 823.2 | 208 | +39.3% | `SA[constructor=random, neighborhood=decoded_route_two_opt]` |
| LNS_MIP:destruction=worst_detour_destruction | 30.83% | 864.8 | 252 | +36.2% | `LNS_MIP[constructor=trivial, destruction=worst_detour_destruction]` |
| LNS_MIP:constructor=random | 33.00% | 890.7 | 233 | +34.3% | `LNS_MIP[constructor=random, destruction=route_cluster_destruction]` |
| default:LNS_MIP | 39.57% | 915.0 | 182 | +32.5% | `LNS_MIP[constructor=trivial, destruction=route_cluster_destruction]` |
| LNS_MIP:destruction=shaw_related_arc_destruction | 42.11% | 937.5 | 225 | +30.9% | `LNS_MIP[constructor=trivial, destruction=shaw_related_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.80%**; gana en 8/10 instancias de test. Esqueletos explorados: ILS × 22, SA × 6, VNS × 6, LNS_MIP × 6.

Afinado vs `ILS:perturbation=related_removal_noisy_reinsertion` (mejor default por gap): +0.90% de gap a favor del afinado, IC95 [+0.32%, +1.50%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 28 | 0.4701 | 0.4694, 0.4701, 0.4697, 0.4704, 0.4699, 0.4711, 0.4699 | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 37 | 0.4701 | 0.4699, 0.4699, 0.4709, 0.4698, 0.4699, 0.4695, 0.4705 | `ILS[constructor=random, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 28 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.4701 | 0.4700, 0.4706, 0.4689, 0.4701, 0.4701, 0.4712, 0.4700 | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 21 (numéricos por defecto) | 0.4703 | 0.4704, 0.4699, 0.4695, 0.4706, 0.4716, 0.4701, 0.4700 | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 37 (numéricos por defecto) | 0.4703 | 0.4691, 0.4700, 0.4711, 0.4705, 0.4713, 0.4711, 0.4693 | `ILS[constructor=random, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 21 | 0.4713 | 0.4704, 0.4715, 0.4721 | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 13 | 0.4745 | 0.4743, 0.4740, 0.4753 | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=related_removal_noisy_reinsertion]` |
| 10 | 0.4749 | 0.4728, 0.4764, 0.4756 | `VNS[constructor=trivial, neighborhood=granular_segment_relocate]` |
| 2* | 0.4844 | 0.4828, 0.4817, 0.4887 | `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 3812 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `route_cluster_destruction`, `shaw_related_arc_destruction`, `worst_detour_destruction`, `farthest_seed_nearest_extend`, `insertion_delta_route_penalty`, `polar_sweep_angle`, `decoded_route_two_opt`, `granular_segment_relocate`, `inter_route_tail_exchange`, `giant_tour_double_bridge`, `related_removal_noisy_reinsertion`

**Mejor en train**: `ILS[constructor=random, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` = 0.4693 (mejor default: 0.4826, `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.34%** | **669.7** | 151 | +50.6% | `ILS[constructor=random, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` |
| VNS:neighborhood=inter_route_tail_exchange | 1.10% | 674.9 | 153 | +50.2% | `VNS[constructor=trivial, neighborhood=inter_route_tail_exchange]` |
| ILS:perturbation=related_removal_noisy_reinsertion | 1.21% | 675.5 | 153 | +50.2% | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=related_removal_noisy_reinsertion]` |
| VNS:constructor=greedy_farthest_seed_nearest_extend | 1.42% | 677.2 | 155 | +50.0% | `VNS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt]` |
| SA:neighborhood=granular_segment_relocate | 1.46% | 677.7 | 155 | +50.0% | `SA[constructor=trivial, neighborhood=granular_segment_relocate]` |
| VNS:neighborhood=granular_segment_relocate | 1.55% | 678.9 | 158 | +49.9% | `VNS[constructor=trivial, neighborhood=granular_segment_relocate]` |
| VNS:constructor=greedy_polar_sweep_angle | 1.98% | 681.5 | 157 | +49.7% | `VNS[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=random | 2.07% | 681.1 | 154 | +49.8% | `VNS[constructor=random, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=greedy_insertion_delta_route_penalty | 2.18% | 682.8 | 158 | +49.6% | `VNS[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt]` |
| default:VNS | 2.24% | 682.6 | 155 | +49.6% | `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]` |
| SA:neighborhood=inter_route_tail_exchange | 3.50% | 691.0 | 157 | +49.0% | `SA[constructor=trivial, neighborhood=inter_route_tail_exchange]` |
| ILS:neighborhood=granular_segment_relocate | 4.48% | 698.2 | 161 | +48.5% | `ILS[constructor=trivial, neighborhood=granular_segment_relocate, perturbation=giant_tour_double_bridge]` |
| ILS:neighborhood=inter_route_tail_exchange | 4.70% | 699.5 | 161 | +48.4% | `ILS[constructor=trivial, neighborhood=inter_route_tail_exchange, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=greedy_farthest_seed_nearest_extend | 7.21% | 715.4 | 165 | +47.2% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=greedy_polar_sweep_angle | 7.85% | 721.0 | 167 | +46.8% | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| LNS_MIP:constructor=greedy_farthest_seed_nearest_extend | 7.97% | 718.5 | 160 | +47.0% | `LNS_MIP[constructor=greedy_farthest_seed_nearest_extend, destruction=route_cluster_destruction]` |
| default:ILS | 8.85% | 728.1 | 171 | +46.3% | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=random | 9.02% | 729.4 | 172 | +46.2% | `ILS[constructor=random, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| SA:constructor=greedy_farthest_seed_nearest_extend | 9.57% | 732.7 | 177 | +46.0% | `SA[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt]` |
| ILS:constructor=greedy_insertion_delta_route_penalty | 9.82% | 734.6 | 173 | +45.8% | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle | 11.41% | 743.9 | 173 | +45.1% | `LNS_MIP[constructor=greedy_polar_sweep_angle, destruction=route_cluster_destruction]` |
| LNS_MIP:destruction=worst_detour_destruction | 12.19% | 749.2 | 177 | +44.7% | `LNS_MIP[constructor=trivial, destruction=worst_detour_destruction]` |
| LNS_MIP:constructor=greedy_insertion_delta_route_penalty | 12.84% | 755.8 | 190 | +44.3% | `LNS_MIP[constructor=greedy_insertion_delta_route_penalty, destruction=route_cluster_destruction]` |
| SA:constructor=greedy_insertion_delta_route_penalty | 14.86% | 771.1 | 196 | +43.1% | `SA[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt]` |
| SA:constructor=greedy_polar_sweep_angle | 14.90% | 765.9 | 171 | +43.5% | `SA[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt]` |
| default:SA | 18.39% | 794.0 | 195 | +41.4% | `SA[constructor=trivial, neighborhood=decoded_route_two_opt]` |
| SA:constructor=random | 20.02% | 805.9 | 202 | +40.6% | `SA[constructor=random, neighborhood=decoded_route_two_opt]` |
| LNS_MIP:destruction=shaw_related_arc_destruction | 21.22% | 804.0 | 170 | +40.7% | `LNS_MIP[constructor=trivial, destruction=shaw_related_arc_destruction]` |
| default:LNS_MIP | 21.25% | 800.1 | 171 | +41.0% | `LNS_MIP[constructor=trivial, destruction=route_cluster_destruction]` |
| LNS_MIP:constructor=random | 22.94% | 823.7 | 229 | +39.2% | `LNS_MIP[constructor=random, destruction=route_cluster_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.77%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 21, SA × 7, VNS × 6, LNS_MIP × 6.

Afinado vs `VNS:neighborhood=inter_route_tail_exchange` (mejor default por gap): +0.77% de gap a favor del afinado, IC95 [+0.42%, +1.12%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 37 | 0.4685 | 0.4686, 0.4685, 0.4682, 0.4691, 0.4686, 0.4682, 0.4683 | `ILS[constructor=random, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` |
| 20 | 0.4685 | 0.4682, 0.4686, 0.4686, 0.4683, 0.4688, 0.4685, 0.4687 | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` |
| 30 | 0.4692 | 0.4692, 0.4693, 0.4692 | `VNS[constructor=greedy_polar_sweep_angle, neighborhood=granular_segment_relocate]` |
| 37 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.4693 | 0.4688, 0.4698, 0.4695 | `ILS[constructor=random, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` |
| 20 (numéricos por defecto) | 0.4693 | 0.4696, 0.4695, 0.4689 | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=granular_segment_relocate, perturbation=related_removal_noisy_reinsertion]` |
| 29 | 0.4696 | 0.4689, 0.4702, 0.4696 | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 38 | 0.4696 | 0.4694, 0.4698, 0.4696 | `ILS[constructor=random, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 38 (numéricos por defecto) | 0.4697 | 0.4697, 0.4696, 0.4699 | `ILS[constructor=random, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 29 (numéricos por defecto) | 0.4706 | 0.4712, 0.4700, 0.4707 | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 30 (numéricos por defecto) | 0.4721 | 0.4728, 0.4717, 0.4719 | `VNS[constructor=greedy_polar_sweep_angle, neighborhood=granular_segment_relocate]` |
| 2* | 0.4806 | 0.4826, 0.4798, 0.4793 | `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp_tour 30) · 0 configuraciones fallidas · 4267 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `route_cluster_destruction`, `shaw_related_arc_destruction`, `worst_detour_destruction`, `farthest_seed_nearest_extend`, `insertion_delta_route_penalty`, `polar_sweep_angle`, `decoded_route_two_opt`, `granular_segment_relocate`, `inter_route_tail_exchange`, `giant_tour_double_bridge`, `related_removal_noisy_reinsertion`

**Mejor en train**: `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` = 0.4702 (mejor default: 0.4808, `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.53%** | **671.6** | 154 | +50.5% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| ILS:perturbation=related_removal_noisy_reinsertion | 1.44% | 677.1 | 154 | +50.1% | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=related_removal_noisy_reinsertion]` |
| VNS:neighborhood=inter_route_tail_exchange | 1.58% | 677.7 | 153 | +50.0% | `VNS[constructor=trivial, neighborhood=inter_route_tail_exchange]` |
| SA:neighborhood=granular_segment_relocate | 1.80% | 679.3 | 152 | +49.9% | `SA[constructor=trivial, neighborhood=granular_segment_relocate]` |
| VNS:neighborhood=granular_segment_relocate | 2.09% | 682.1 | 157 | +49.7% | `VNS[constructor=trivial, neighborhood=granular_segment_relocate]` |
| VNS:constructor=greedy_farthest_seed_nearest_extend | 2.29% | 683.0 | 156 | +49.6% | `VNS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=random | 2.86% | 686.4 | 155 | +49.4% | `VNS[constructor=random, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=greedy_polar_sweep_angle | 3.09% | 689.0 | 159 | +49.2% | `VNS[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt]` |
| default:VNS | 3.34% | 689.6 | 155 | +49.1% | `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]` |
| VNS:constructor=greedy_insertion_delta_route_penalty | 3.81% | 692.4 | 156 | +48.9% | `VNS[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt]` |
| SA:neighborhood=inter_route_tail_exchange | 3.82% | 693.8 | 160 | +48.8% | `SA[constructor=trivial, neighborhood=inter_route_tail_exchange]` |
| ILS:neighborhood=granular_segment_relocate | 5.74% | 706.8 | 165 | +47.9% | `ILS[constructor=trivial, neighborhood=granular_segment_relocate, perturbation=giant_tour_double_bridge]` |
| ILS:neighborhood=inter_route_tail_exchange | 5.75% | 706.4 | 162 | +47.9% | `ILS[constructor=trivial, neighborhood=inter_route_tail_exchange, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=greedy_farthest_seed_nearest_extend | 8.37% | 723.6 | 169 | +46.6% | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=greedy_polar_sweep_angle | 9.10% | 729.5 | 169 | +46.2% | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| ILS:constructor=random | 10.17% | 736.5 | 172 | +45.7% | `ILS[constructor=random, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| default:ILS | 10.42% | 738.9 | 176 | +45.5% | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| SA:constructor=greedy_farthest_seed_nearest_extend | 10.53% | 739.2 | 181 | +45.5% | `SA[constructor=greedy_farthest_seed_nearest_extend, neighborhood=decoded_route_two_opt]` |
| LNS_MIP:constructor=greedy_farthest_seed_nearest_extend | 10.87% | 742.0 | 187 | +45.3% | `LNS_MIP[constructor=greedy_farthest_seed_nearest_extend, destruction=route_cluster_destruction]` |
| ILS:constructor=greedy_insertion_delta_route_penalty | 11.04% | 742.9 | 176 | +45.2% | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt, perturbation=giant_tour_double_bridge]` |
| LNS_MIP:constructor=greedy_polar_sweep_angle | 14.09% | 760.9 | 178 | +43.9% | `LNS_MIP[constructor=greedy_polar_sweep_angle, destruction=route_cluster_destruction]` |
| SA:constructor=greedy_insertion_delta_route_penalty | 15.42% | 775.8 | 200 | +42.8% | `SA[constructor=greedy_insertion_delta_route_penalty, neighborhood=decoded_route_two_opt]` |
| SA:constructor=greedy_polar_sweep_angle | 15.71% | 774.2 | 184 | +42.9% | `SA[constructor=greedy_polar_sweep_angle, neighborhood=decoded_route_two_opt]` |
| LNS_MIP:constructor=greedy_insertion_delta_route_penalty | 19.13% | 802.1 | 216 | +40.8% | `LNS_MIP[constructor=greedy_insertion_delta_route_penalty, destruction=route_cluster_destruction]` |
| default:SA | 21.30% | 815.5 | 207 | +39.8% | `SA[constructor=trivial, neighborhood=decoded_route_two_opt]` |
| SA:constructor=random | 22.95% | 824.9 | 202 | +39.2% | `SA[constructor=random, neighborhood=decoded_route_two_opt]` |
| LNS_MIP:destruction=worst_detour_destruction | 31.09% | 865.9 | 250 | +36.1% | `LNS_MIP[constructor=trivial, destruction=worst_detour_destruction]` |
| LNS_MIP:constructor=random | 33.00% | 890.7 | 233 | +34.3% | `LNS_MIP[constructor=random, destruction=route_cluster_destruction]` |
| default:LNS_MIP | 40.34% | 921.4 | 189 | +32.0% | `LNS_MIP[constructor=trivial, destruction=route_cluster_destruction]` |
| LNS_MIP:destruction=shaw_related_arc_destruction | 41.95% | 936.2 | 224 | +30.9% | `LNS_MIP[constructor=trivial, destruction=shaw_related_arc_destruction]` |

Ganancia del afinado sobre el mejor default: **+0.80%**; gana en 8/10 instancias de test. Esqueletos explorados: ILS × 22, SA × 6, VNS × 6, LNS_MIP × 6.

Afinado vs `ILS:perturbation=related_removal_noisy_reinsertion` (mejor default por gap): +0.90% de gap a favor del afinado, IC95 [+0.32%, +1.50%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 | 0.4698 | 0.4689, 0.4701, 0.4699, 0.4698, 0.4692, 0.4707, 0.4699 | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 39 | 0.4700 | 0.4698, 0.4700, 0.4703, 0.4696, 0.4693, 0.4706, 0.4703 | `ILS[constructor=random, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 22 (numéricos por defecto) | 0.4700 | 0.4702, 0.4691, 0.4707, 0.4704, 0.4693, 0.4699, 0.4705 | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 33 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.4702 | 0.4703, 0.4697, 0.4714, 0.4702, 0.4700, 0.4700, 0.4701 | `ILS[constructor=greedy_farthest_seed_nearest_extend, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 39 (numéricos por defecto) | 0.4704 | 0.4712, 0.4704, 0.4701, 0.4697, 0.4702, 0.4694, 0.4721 | `ILS[constructor=random, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 19 (numéricos por defecto) | 0.4709 | 0.4703, 0.4715, 0.4710 | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 22 | 0.4714 | 0.4706, 0.4720, 0.4716 | `ILS[constructor=greedy_insertion_delta_route_penalty, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 13 | 0.4723 | 0.4717, 0.4738, 0.4714 | `ILS[constructor=trivial, neighborhood=decoded_route_two_opt, perturbation=related_removal_noisy_reinsertion]` |
| 19 | 0.4726 | 0.4726, 0.4731, 0.4720 | `ILS[constructor=greedy_polar_sweep_angle, neighborhood=inter_route_tail_exchange, perturbation=related_removal_noisy_reinsertion]` |
| 2* | 0.4817 | 0.4808, 0.4838, 0.4804 | `VNS[constructor=trivial, neighborhood=decoded_route_two_opt]` |
