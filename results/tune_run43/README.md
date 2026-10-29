## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.52% | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| r1 | 1 | 0.67% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| r2 | 2 | 0.39% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |

**Afinado entre réplicas**: media 0.53%, desvío 0.11%, rango [0.39%, 0.67%].

**Mejor no afinado** (media entre réplicas): `LNS_MIP:constructor=greedy_capacity_pressure_priced` = 0.67%. Afinado vs ese: +0.14% de gap a favor del afinado, IC95 [-0.04%, +0.32%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 4 configuraciones fallidas · 4990 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `period_window_destruction`, `related_items_row_destruction`, `wasteful_cell_destruction`, `capacity_pressure_priced`, `eoq_lot_target_deviation`, `part_period_setup_vs_holding`, `block_lot_consolidation`, `same_period_item_pair_toggle`, `wagner_whitin_row_reopt`, `adjacent_setup_shift`, `item_cycle_rebuild`, `period_window_reshuffle`

**Mejor en train**: `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` = 0.5166 (mejor default: 0.5556, `LNS_MIP[constructor=trivial, destruction=period_window_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.52%** | **86404.5** | 15408 | +47.0% | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| LNS_MIP:constructor=greedy_capacity_pressure_priced | 0.53% | 86417.5 | 15432 | +47.0% | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| LNS_MIP:constructor=greedy_part_period_setup_vs_holding | 0.68% | 86570.9 | 15632 | +46.9% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| LNS_MIP:destruction=wasteful_cell_destruction | 1.26% | 87029.2 | 15430 | +46.6% | `LNS_MIP[constructor=trivial, destruction=wasteful_cell_destruction]` |
| LNS_MIP:constructor=greedy_eoq_lot_target_deviation | 1.29% | 87156.7 | 16149 | +46.5% | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=period_window_destruction]` |
| LNS_MIP:destruction=related_items_row_destruction | 1.52% | 87361.3 | 16280 | +46.4% | `LNS_MIP[constructor=trivial, destruction=related_items_row_destruction]` |
| default:LNS_MIP | 4.12% | 89637.3 | 17131 | +45.0% | `LNS_MIP[constructor=trivial, destruction=period_window_destruction]` |
| SA:constructor=greedy_capacity_pressure_priced | 4.42% | 89800.3 | 16320 | +44.9% | `SA[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_capacity_pressure_priced | 6.47% | 91520.7 | 16299 | +43.8% | `ILS[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_capacity_pressure_priced | 7.06% | 92078.8 | 16829 | +43.5% | `VNS[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation]` |
| SA:constructor=greedy_eoq_lot_target_deviation | 9.81% | 94297.5 | 16293 | +42.1% | `SA[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation]` |
| SA:constructor=greedy_part_period_setup_vs_holding | 10.36% | 94931.5 | 17599 | +41.7% | `SA[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_eoq_lot_target_deviation | 11.90% | 96063.9 | 16467 | +41.0% | `ILS[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_eoq_lot_target_deviation | 12.06% | 96248.7 | 16714 | +40.9% | `VNS[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_part_period_setup_vs_holding | 14.31% | 98278.1 | 17902 | +39.7% | `ILS[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_part_period_setup_vs_holding | 14.84% | 98698.9 | 17875 | +39.4% | `VNS[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation]` |
| SA:neighborhood=same_period_item_pair_toggle | 24.36% | 106784.8 | 18595 | +34.5% | `SA[constructor=trivial, neighborhood=same_period_item_pair_toggle]` |
| default:SA | 28.59% | 110422.0 | 19322 | +32.2% | `SA[constructor=trivial, neighborhood=block_lot_consolidation]` |
| VNS:neighborhood=same_period_item_pair_toggle | 31.37% | 112851.8 | 21567 | +30.7% | `VNS[constructor=trivial, neighborhood=same_period_item_pair_toggle]` |
| ILS:neighborhood=same_period_item_pair_toggle | 34.07% | 115183.1 | 20723 | +29.3% | `ILS[constructor=trivial, neighborhood=same_period_item_pair_toggle, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=period_window_reshuffle | 37.21% | 118372.4 | 24329 | +27.4% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=period_window_reshuffle]` |
| default:ILS | 39.82% | 120300.0 | 23504 | +26.2% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| default:VNS | 39.97% | 120632.1 | 25225 | +26.0% | `VNS[constructor=trivial, neighborhood=block_lot_consolidation]` |
| VNS:neighborhood=wagner_whitin_row_reopt | 42.07% | 122699.7 | 29169 | +24.7% | `VNS[constructor=trivial, neighborhood=wagner_whitin_row_reopt]` |
| ILS:neighborhood=wagner_whitin_row_reopt | 42.50% | 122819.2 | 28160 | +24.6% | `ILS[constructor=trivial, neighborhood=wagner_whitin_row_reopt, perturbation=adjacent_setup_shift]` |
| SA:neighborhood=wagner_whitin_row_reopt | 48.72% | 127982.5 | 28220 | +21.5% | `SA[constructor=trivial, neighborhood=wagner_whitin_row_reopt]` |
| ILS:perturbation=item_cycle_rebuild | 59.99% | 137117.0 | 22383 | +15.8% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=item_cycle_rebuild]` |
| LNS_MIP:constructor=random | 869771086.78% | 733333357688.4 | 442216598326 | -450069133.5% | `LNS_MIP[constructor=random, destruction=period_window_destruction]` |
| SA:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=block_lot_consolidation]` |
| ILS:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=block_lot_consolidation]` |

Ganancia del afinado sobre el mejor default: **+0.02%**; gana en 2/10 instancias de test. Esqueletos explorados: LNS_MIP × 20, SA × 7, ILS × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_capacity_pressure_priced` (mejor default por gap): +0.01% de gap a favor del afinado, IC95 [+0.00%, +0.03%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 37 | 0.5146 | 0.5141, 0.5142, 0.5162, 0.5141 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| 27 | 0.5160 | 0.5161, 0.5161, 0.5161, 0.5156 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=wasteful_cell_destruction]` |
| 37 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.5166 | 0.5156, 0.5181, 0.5145, 0.5184 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| 32 | 0.5167 | 0.5163, 0.5170, 0.5169 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| 34 | 0.5176 | 0.5179, 0.5174, 0.5175 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=related_items_row_destruction]` |
| 18 | 0.5182 | 0.5193, 0.5178, 0.5175 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=wasteful_cell_destruction]` |
| 32 (numéricos por defecto) | 0.5183 | 0.5194, 0.5182, 0.5172 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| 18 (numéricos por defecto) | 0.5184 | 0.5184, 0.5187, 0.5181 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=wasteful_cell_destruction]` |
| 27 (numéricos por defecto) | 0.5195 | 0.5198, 0.5197, 0.5189 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=wasteful_cell_destruction]` |
| 34 (numéricos por defecto) | 0.5251 | 0.5278, 0.5225, 0.5251 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=related_items_row_destruction]` |
| 3* | 0.5477 | 0.5556, 0.5398, 0.5476 | `LNS_MIP[constructor=trivial, destruction=period_window_destruction]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 5 configuraciones fallidas · 5257 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `period_window_destruction`, `related_items_row_destruction`, `wasteful_cell_destruction`, `capacity_pressure_priced`, `eoq_lot_target_deviation`, `part_period_setup_vs_holding`, `block_lot_consolidation`, `same_period_item_pair_toggle`, `wagner_whitin_row_reopt`, `adjacent_setup_shift`, `item_cycle_rebuild`, `period_window_reshuffle`

**Mejor en train**: `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` = 0.5179 (mejor default: 0.5354, `LNS_MIP[constructor=trivial, destruction=period_window_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.67%** | **86559.6** | 15609 | +46.9% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| LNS_MIP:constructor=greedy_capacity_pressure_priced | 0.54% | 86425.9 | 15426 | +47.0% | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| LNS_MIP:constructor=greedy_part_period_setup_vs_holding | 0.67% | 86559.6 | 15609 | +46.9% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| LNS_MIP:destruction=wasteful_cell_destruction | 1.27% | 87037.2 | 15429 | +46.6% | `LNS_MIP[constructor=trivial, destruction=wasteful_cell_destruction]` |
| LNS_MIP:constructor=greedy_eoq_lot_target_deviation | 1.34% | 87202.9 | 16210 | +46.5% | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=period_window_destruction]` |
| LNS_MIP:destruction=related_items_row_destruction | 1.54% | 87370.1 | 16273 | +46.4% | `LNS_MIP[constructor=trivial, destruction=related_items_row_destruction]` |
| default:LNS_MIP | 4.29% | 89763.1 | 17049 | +44.9% | `LNS_MIP[constructor=trivial, destruction=period_window_destruction]` |
| SA:constructor=greedy_capacity_pressure_priced | 4.50% | 89863.9 | 16324 | +44.8% | `SA[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_capacity_pressure_priced | 6.50% | 91544.9 | 16275 | +43.8% | `ILS[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_capacity_pressure_priced | 7.18% | 92178.9 | 16782 | +43.4% | `VNS[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation]` |
| SA:constructor=greedy_eoq_lot_target_deviation | 9.79% | 94279.0 | 16280 | +42.1% | `SA[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation]` |
| SA:constructor=greedy_part_period_setup_vs_holding | 10.49% | 95031.0 | 17562 | +41.7% | `SA[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_eoq_lot_target_deviation | 11.92% | 96096.6 | 16552 | +41.0% | `ILS[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_eoq_lot_target_deviation | 12.44% | 96567.7 | 16723 | +40.7% | `VNS[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation]` |
| VNS:constructor=greedy_part_period_setup_vs_holding | 14.79% | 98698.9 | 18117 | +39.4% | `VNS[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_part_period_setup_vs_holding | 14.90% | 98797.2 | 18139 | +39.4% | `ILS[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| SA:neighborhood=same_period_item_pair_toggle | 24.67% | 107025.7 | 18441 | +34.3% | `SA[constructor=trivial, neighborhood=same_period_item_pair_toggle]` |
| default:SA | 28.91% | 110658.2 | 19108 | +32.1% | `SA[constructor=trivial, neighborhood=block_lot_consolidation]` |
| ILS:neighborhood=same_period_item_pair_toggle | 34.95% | 115679.3 | 19077 | +29.0% | `ILS[constructor=trivial, neighborhood=same_period_item_pair_toggle, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=period_window_reshuffle | 35.10% | 116081.6 | 21308 | +28.8% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=period_window_reshuffle]` |
| VNS:neighborhood=same_period_item_pair_toggle | 35.58% | 116473.7 | 22082 | +28.5% | `VNS[constructor=trivial, neighborhood=same_period_item_pair_toggle]` |
| default:VNS | 39.23% | 119761.2 | 23199 | +26.5% | `VNS[constructor=trivial, neighborhood=block_lot_consolidation]` |
| default:ILS | 40.91% | 121283.6 | 23796 | +25.6% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:neighborhood=wagner_whitin_row_reopt | 42.81% | 123128.5 | 28522 | +24.4% | `ILS[constructor=trivial, neighborhood=wagner_whitin_row_reopt, perturbation=adjacent_setup_shift]` |
| VNS:neighborhood=wagner_whitin_row_reopt | 43.81% | 123817.2 | 27315 | +24.0% | `VNS[constructor=trivial, neighborhood=wagner_whitin_row_reopt]` |
| SA:neighborhood=wagner_whitin_row_reopt | 48.72% | 127982.5 | 28220 | +21.5% | `SA[constructor=trivial, neighborhood=wagner_whitin_row_reopt]` |
| ILS:perturbation=item_cycle_rebuild | 59.34% | 136486.8 | 22459 | +16.2% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=item_cycle_rebuild]` |
| LNS_MIP:constructor=random | 869771086.84% | 733333357729.1 | 442216598258 | -450069133.6% | `LNS_MIP[constructor=random, destruction=period_window_destruction]` |
| SA:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=block_lot_consolidation]` |
| ILS:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=block_lot_consolidation]` |

Ganancia del afinado sobre el mejor default: **-0.15%**; gana en 6/10 instancias de test. Esqueletos explorados: LNS_MIP × 20, SA × 7, ILS × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_capacity_pressure_priced` (mejor default por gap): -0.13% de gap a favor del afinado, IC95 [-0.38%, +0.07%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 32 | 0.5156 | 0.5142, 0.5175, 0.5158, 0.5158, 0.5149, 0.5148, 0.5159 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| 15 | 0.5165 | 0.5158, 0.5174, 0.5166, 0.5169, 0.5162, 0.5156, 0.5167 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| 33 | 0.5170 | 0.5161, 0.5168, 0.5168, 0.5172, 0.5180 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| 32 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.5179 | 0.5163, 0.5176, 0.5184, 0.5192 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| 33 (numéricos por defecto) | 0.5185 | 0.5192, 0.5182, 0.5181 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| 28 (numéricos por defecto) | 0.5200 | 0.5223, 0.5185, 0.5192 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=related_items_row_destruction]` |
| 19 (numéricos por defecto) | 0.5202 | 0.5201, 0.5205, 0.5202 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=wasteful_cell_destruction]` |
| 28 | 0.5246 | 0.5272, 0.5238, 0.5227 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=related_items_row_destruction]` |
| 19 | 0.5266 | 0.5256, 0.5270, 0.5272 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=wasteful_cell_destruction]` |
| 3* | 0.5400 | 0.5354, 0.5418, 0.5430 | `LNS_MIP[constructor=trivial, destruction=period_window_destruction]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 4 configuraciones fallidas · 5175 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `period_window_destruction`, `related_items_row_destruction`, `wasteful_cell_destruction`, `capacity_pressure_priced`, `eoq_lot_target_deviation`, `part_period_setup_vs_holding`, `block_lot_consolidation`, `same_period_item_pair_toggle`, `wagner_whitin_row_reopt`, `adjacent_setup_shift`, `item_cycle_rebuild`, `period_window_reshuffle`

**Mejor en train**: `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` = 0.5155 (mejor default: 0.5513, `LNS_MIP[constructor=trivial, destruction=period_window_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.39%** | **86268.8** | 15242 | +47.1% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| LNS_MIP:constructor=greedy_capacity_pressure_priced | 0.92% | 86771.8 | 15623 | +46.7% | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| LNS_MIP:constructor=greedy_part_period_setup_vs_holding | 1.05% | 86894.1 | 15715 | +46.7% | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=period_window_destruction]` |
| LNS_MIP:destruction=wasteful_cell_destruction | 1.62% | 87386.2 | 15815 | +46.4% | `LNS_MIP[constructor=trivial, destruction=wasteful_cell_destruction]` |
| LNS_MIP:constructor=greedy_eoq_lot_target_deviation | 1.91% | 87684.6 | 16242 | +46.2% | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=period_window_destruction]` |
| LNS_MIP:destruction=related_items_row_destruction | 1.96% | 87740.3 | 16421 | +46.2% | `LNS_MIP[constructor=trivial, destruction=related_items_row_destruction]` |
| SA:constructor=greedy_capacity_pressure_priced | 4.73% | 90078.3 | 16458 | +44.7% | `SA[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation]` |
| default:LNS_MIP | 5.86% | 91142.3 | 17277 | +44.1% | `LNS_MIP[constructor=trivial, destruction=period_window_destruction]` |
| ILS:constructor=greedy_capacity_pressure_priced | 6.58% | 91610.8 | 16283 | +43.8% | `ILS[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_capacity_pressure_priced | 7.16% | 92150.4 | 16718 | +43.4% | `VNS[constructor=greedy_capacity_pressure_priced, neighborhood=block_lot_consolidation]` |
| SA:constructor=greedy_eoq_lot_target_deviation | 10.20% | 94599.5 | 16137 | +41.9% | `SA[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation]` |
| SA:constructor=greedy_part_period_setup_vs_holding | 11.49% | 95891.5 | 17791 | +41.1% | `SA[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_eoq_lot_target_deviation | 12.14% | 96310.7 | 16714 | +40.9% | `ILS[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_eoq_lot_target_deviation | 12.45% | 96591.9 | 16890 | +40.7% | `VNS[constructor=greedy_eoq_lot_target_deviation, neighborhood=block_lot_consolidation]` |
| ILS:constructor=greedy_part_period_setup_vs_holding | 15.24% | 99083.4 | 18276 | +39.2% | `ILS[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_part_period_setup_vs_holding | 15.47% | 99311.3 | 18493 | +39.0% | `VNS[constructor=greedy_part_period_setup_vs_holding, neighborhood=block_lot_consolidation]` |
| SA:neighborhood=same_period_item_pair_toggle | 28.57% | 110331.2 | 18754 | +32.3% | `SA[constructor=trivial, neighborhood=same_period_item_pair_toggle]` |
| default:SA | 31.04% | 112515.0 | 19529 | +30.9% | `SA[constructor=trivial, neighborhood=block_lot_consolidation]` |
| VNS:neighborhood=same_period_item_pair_toggle | 37.02% | 118021.0 | 23837 | +27.6% | `VNS[constructor=trivial, neighborhood=same_period_item_pair_toggle]` |
| ILS:neighborhood=same_period_item_pair_toggle | 37.29% | 117610.7 | 19024 | +27.8% | `ILS[constructor=trivial, neighborhood=same_period_item_pair_toggle, perturbation=adjacent_setup_shift]` |
| default:ILS | 40.45% | 120661.5 | 22677 | +25.9% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=period_window_reshuffle | 40.53% | 120994.7 | 23318 | +25.7% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=period_window_reshuffle]` |
| default:VNS | 41.01% | 121549.4 | 25334 | +25.4% | `VNS[constructor=trivial, neighborhood=block_lot_consolidation]` |
| VNS:neighborhood=wagner_whitin_row_reopt | 42.99% | 123071.4 | 26518 | +24.5% | `VNS[constructor=trivial, neighborhood=wagner_whitin_row_reopt]` |
| ILS:neighborhood=wagner_whitin_row_reopt | 43.38% | 123638.5 | 29397 | +24.1% | `ILS[constructor=trivial, neighborhood=wagner_whitin_row_reopt, perturbation=adjacent_setup_shift]` |
| SA:neighborhood=wagner_whitin_row_reopt | 48.72% | 127986.7 | 28229 | +21.5% | `SA[constructor=trivial, neighborhood=wagner_whitin_row_reopt]` |
| ILS:perturbation=item_cycle_rebuild | 65.36% | 141708.7 | 22996 | +13.0% | `ILS[constructor=trivial, neighborhood=block_lot_consolidation, perturbation=item_cycle_rebuild]` |
| LNS_MIP:constructor=random | 917616782.51% | 766666688438.8 | 422952545216 | -470526823.7% | `LNS_MIP[constructor=random, destruction=period_window_destruction]` |
| SA:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=block_lot_consolidation]` |
| ILS:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=block_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=random | 1195834542.75% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=block_lot_consolidation]` |

Ganancia del afinado sobre el mejor default: **+0.58%**; gana en 9/10 instancias de test. Esqueletos explorados: LNS_MIP × 20, SA × 7, ILS × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_capacity_pressure_priced` (mejor default por gap): +0.53% de gap a favor del afinado, IC95 [+0.13%, +0.97%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 35 ✔ | 0.5155 | 0.5143, 0.5157, 0.5155, 0.5158, 0.5155, 0.5155, 0.5159 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| 20 | 0.5158 | 0.5156, 0.5157, 0.5158, 0.5155, 0.5156, 0.5161, 0.5161 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=wasteful_cell_destruction]` |
| 17 (numéricos por defecto) | 0.5185 | 0.5185, 0.5184, 0.5184 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=related_items_row_destruction]` |
| 15 | 0.5186 | 0.5173, 0.5203, 0.5181 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=period_window_destruction]` |
| 35 (numéricos por defecto) | 0.5188 | 0.5183, 0.5189, 0.5191 | `LNS_MIP[constructor=greedy_part_period_setup_vs_holding, destruction=wasteful_cell_destruction]` |
| 20 (numéricos por defecto) | 0.5210 | 0.5220, 0.5208, 0.5201 | `LNS_MIP[constructor=greedy_eoq_lot_target_deviation, destruction=wasteful_cell_destruction]` |
| 17 | 0.5242 | 0.5250, 0.5235, 0.5240 | `LNS_MIP[constructor=greedy_capacity_pressure_priced, destruction=related_items_row_destruction]` |
| 11 | 0.5301 | 0.5254, 0.5294, 0.5354 | `LNS_MIP[constructor=trivial, destruction=related_items_row_destruction]` |
| 3* | 0.5567 | 0.5513, 0.5643, 0.5544 | `LNS_MIP[constructor=trivial, destruction=period_window_destruction]` |
