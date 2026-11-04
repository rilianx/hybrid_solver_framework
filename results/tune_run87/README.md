## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.83% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=clsp_time_window_block]` |

**Afinado entre réplicas**: media 0.83%, desvío 0.00%, rango [0.83%, 0.83%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.69%. Afinado vs ese: -0.14% de gap a favor del afinado, IC95 [-0.46%, +0.25%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 1537 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_toggle_flip`, `lot_consolidation_window`, `random_setup_flips_flow_repair`, `lot_shift_merge_swap_repair`, `window_wagner_whitin_rebuild`, `hamming_single_setup_flip`, `differing_run_segment_copy`, `period_column_transplant`, `clsp_time_window_block`, `clsp_related_items_horizon`, `clsp_bottleneck_weighted_sampling`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=clsp_time_window_block]` = 0.5207

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.83%** | **233040.1** | 30362 | +47.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=clsp_time_window_block]` |
| default:HYB | 0.69% | 232648.1 | 29711 | +47.2% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:perturbation=lot_shift_merge_swap_repair | 0.79% | 232931.4 | 30145 | +47.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=clsp_time_window_block]` |
| HYB:destruction=group_window | 0.83% | 232978.7 | 29886 | +47.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:perturbation=window_wagner_whitin_rebuild | 0.99% | 233280.1 | 29543 | +47.0% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=clsp_time_window_block]` |
| HYB:destruction=clsp_related_items_horizon | 1.47% | 234355.4 | 29362 | +46.8% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_related_items_horizon]` |
| HYB:neighborhood=composite | 1.61% | 234789.7 | 30185 | +46.7% | `HYB[constructor=trivial, neighborhood=composite, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:neighborhood=lot_consolidation_window | 2.22% | 236307.5 | 31259 | +46.3% | `HYB[constructor=trivial, neighborhood=lot_consolidation_window, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:destruction=clsp_bottleneck_weighted_sampling | 2.77% | 237432.2 | 30363 | +46.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_bottleneck_weighted_sampling]` |
| HYB:destruction=random_variables | 2.90% | 237601.7 | 29361 | +46.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=random_variables]` |
| HYB:constructor=random | 3.53% | 239130.5 | 30278 | +45.7% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |

Ganancia del afinado sobre el mejor default: **-0.17%**; gana en 1/6 instancias de test. Esqueletos explorados: HYB × 6.

Afinado vs `default:HYB` (mejor default por gap): -0.14% de gap a favor del afinado, IC95 [-0.46%, +0.25%] — **no se distingue del ruido** con estas instancias.
