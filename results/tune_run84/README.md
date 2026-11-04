## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.00% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=clsp_related_items_horizon]` |

**Afinado entre réplicas**: media 0.00%, desvío 0.00%, rango [0.00%, 0.00%].

**Mejor no afinado** (media entre réplicas): `HYB:neighborhood=composite` = 0.00%. Afinado vs ese: +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 38 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_toggle_flip`, `lot_consolidation_window`, `random_setup_flips_flow_repair`, `lot_shift_merge_swap_repair`, `window_wagner_whitin_rebuild`, `hamming_single_setup_flip`, `differing_run_segment_copy`, `period_column_transplant`, `clsp_time_window_block`, `clsp_related_items_horizon`, `clsp_bottleneck_weighted_sampling`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=clsp_related_items_horizon]` = 1000000000000.0000

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **nan%** | **1000000000000.0** | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=clsp_related_items_horizon]` |
| default:HYB | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:constructor=random | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:neighborhood=lot_consolidation_window | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=lot_consolidation_window, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:neighborhood=composite | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=composite, perturbation=random_setup_flips_flow_repair, destruction=clsp_time_window_block]` |
| HYB:perturbation=lot_shift_merge_swap_repair | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=clsp_time_window_block]` |
| HYB:perturbation=window_wagner_whitin_rebuild | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=clsp_time_window_block]` |
| HYB:destruction=clsp_related_items_horizon | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_related_items_horizon]` |
| HYB:destruction=clsp_bottleneck_weighted_sampling | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=clsp_bottleneck_weighted_sampling]` |
| HYB:destruction=group_window | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:destruction=random_variables | nan% | 1000000000000.0 | 0 | -227043519.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=random_variables]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/6 instancias de test. Esqueletos explorados: HYB × 6.

Afinado vs `default:HYB` (mejor default por gap): +nan% de gap a favor del afinado, IC95 [+nan%, +nan%] — **no se distingue del ruido** con estas instancias.
