## Réplicas del tuning (1)

### Catálogo `generated`

60 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.35% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=random_variables]` |

**Afinado entre réplicas**: media 1.35%, desvío 0.00%, rango [1.35%, 1.35%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.61%. Afinado vs ese: -0.74% de gap a favor del afinado, IC95 [-1.25%, -0.25%] sobre las instancias; el afinado queda por delante en 0 de 1 réplicas.


## Réplica r0

### Catálogo `generated`

60 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 1456 s de tuning

esqueletos: `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_toggle_flip`, `lot_consolidation_window`, `random_setup_flips_flow_repair`, `lot_shift_merge_swap_repair`, `window_wagner_whitin_rebuild`, `hamming_single_setup_flip`, `differing_run_segment_copy`, `period_column_transplant`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=random_variables]` = 0.5239

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.35%** | **234295.2** | 30185 | +46.8% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=random_variables]` |
| default:HYB | 0.61% | 232576.9 | 29801 | +47.2% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:perturbation=window_wagner_whitin_rebuild | 0.73% | 232912.7 | 30355 | +47.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=group_window]` |
| HYB:perturbation=lot_shift_merge_swap_repair | 0.78% | 232911.1 | 29499 | +47.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=group_window]` |
| HYB:neighborhood=composite | 1.49% | 234489.3 | 29387 | +46.8% | `HYB[constructor=trivial, neighborhood=composite, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:neighborhood=lot_consolidation_window | 2.22% | 236248.8 | 30398 | +46.4% | `HYB[constructor=trivial, neighborhood=lot_consolidation_window, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| HYB:destruction=random_variables | 2.82% | 237570.4 | 29854 | +46.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=random_variables]` |
| HYB:constructor=random | 2.89% | 237724.1 | 29723 | +46.0% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |

Ganancia del afinado sobre el mejor default: **-0.74%**; gana en 1/6 instancias de test. Esqueletos explorados: HYB × 5.

Afinado vs `default:HYB` (mejor default por gap): -0.74% de gap a favor del afinado, IC95 [-1.25%, -0.25%].
