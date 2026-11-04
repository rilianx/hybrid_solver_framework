## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.49% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=group_window]` |

**Afinado entre réplicas**: media 0.49%, desvío 0.00%, rango [0.49%, 0.49%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.88%. Afinado vs ese: +0.39% de gap a favor del afinado, IC95 [+0.23%, +0.53%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 1425 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_toggle_flip`, `lot_consolidation_window`, `random_setup_flips_flow_repair`, `lot_shift_merge_swap_repair`, `window_wagner_whitin_rebuild`, `hamming_single_setup_flip`, `differing_run_segment_copy`, `period_column_transplant`

**Mejor en train**: `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=group_window]` = 0.5209

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.49%** | **231803.2** | 30039 | +47.4% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=group_window]` |
| default:HYB | 0.88% | 232706.8 | 30108 | +47.2% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:perturbation=lot_shift_merge_swap_repair | 0.92% | 232697.5 | 29584 | +47.2% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=group_window]` |
| HYB:perturbation=window_wagner_whitin_rebuild | 0.94% | 232817.1 | 30035 | +47.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=group_window]` |
| HYB:neighborhood=composite | 1.73% | 234517.5 | 29549 | +46.8% | `HYB[constructor=trivial, neighborhood=composite, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:destruction=random_variables | 2.54% | 236457.8 | 30179 | +46.3% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=random_variables]` |
| HYB:neighborhood=lot_consolidation_window | 2.67% | 236778.5 | 30652 | +46.2% | `HYB[constructor=trivial, neighborhood=lot_consolidation_window, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:constructor=random | 3.25% | 238008.2 | 29831 | +46.0% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **+0.38%**; gana en 4/6 instancias de test. Esqueletos explorados: HYB × 3.

Afinado vs `default:HYB` (mejor default por gap): +0.39% de gap a favor del afinado, IC95 [+0.23%, +0.53%].
