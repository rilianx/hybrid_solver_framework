## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.78% | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` |
| r1 | 1 | 0.66% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| r2 | 2 | 0.66% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |

**Afinado entre réplicas**: media 0.70%, desvío 0.06%, rango [0.66%, 0.78%].

**Mejor no afinado** (media entre réplicas): `LNS_MIP:constructor=greedy_part_period_balancing_score` = 2.28%. Afinado vs ese: +1.58% de gap a favor del afinado, IC95 [+0.84%, +2.35%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 5 configuraciones fallidas · 4015 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `capacity_bottleneck_destruction`, `costly_item_rows_destruction`, `time_window_destruction`, `capacity_tightness_marginal_score`, `part_period_balancing_score`, `silver_meal_period_average_score`, `item_window_lot_consolidation`, `setup_shift_or_merge`, `single_setup_toggle`, `adjacent_setup_shift`, `item_row_periodic_rebuild`, `random_setup_flip_k`

**Mejor en train**: `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` = 0.5145 (mejor default: 0.5411, `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.78%** | **86675.0** | 15890 | +46.8% | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` |
| LNS_MIP:constructor=greedy_part_period_balancing_score | 2.30% | 87848.1 | 15227 | +46.1% | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:constructor=greedy_capacity_tightness_marginal_score | 2.79% | 88299.7 | 15461 | +45.8% | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:constructor=greedy_silver_meal_period_average_score | 3.26% | 88762.0 | 15910 | +45.5% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=greedy_silver_meal_period_average_score | 4.33% | 89799.2 | 16871 | +44.9% | `SA[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation]` |
| SA:constructor=greedy_capacity_tightness_marginal_score | 4.62% | 90017.9 | 16690 | +44.8% | `SA[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| default:LNS_MIP | 4.72% | 90001.0 | 16110 | +44.8% | `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=greedy_part_period_balancing_score | 4.75% | 90130.7 | 16779 | +44.7% | `SA[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation]` |
| LNS_MIP:destruction=time_window_destruction | 5.05% | 90500.5 | 19297 | +44.5% | `LNS_MIP[constructor=trivial, destruction=time_window_destruction]` |
| ILS:constructor=greedy_silver_meal_period_average_score | 7.25% | 92320.2 | 17413 | +43.3% | `ILS[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_silver_meal_period_average_score | 7.32% | 92399.9 | 17567 | +43.3% | `VNS[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation]` |
| ILS:constructor=greedy_capacity_tightness_marginal_score | 7.32% | 92360.9 | 17287 | +43.3% | `ILS[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:constructor=greedy_part_period_balancing_score | 7.55% | 92539.1 | 17200 | +43.2% | `ILS[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_capacity_tightness_marginal_score | 7.56% | 92620.6 | 17633 | +43.2% | `VNS[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| VNS:constructor=greedy_part_period_balancing_score | 7.68% | 92665.6 | 17354 | +43.1% | `VNS[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation]` |
| LNS_MIP:destruction=costly_item_rows_destruction | 9.38% | 94113.1 | 17461 | +42.2% | `LNS_MIP[constructor=trivial, destruction=costly_item_rows_destruction]` |
| SA:neighborhood=single_setup_toggle | 11.88% | 96217.0 | 17648 | +40.9% | `SA[constructor=trivial, neighborhood=single_setup_toggle]` |
| VNS:neighborhood=single_setup_toggle | 14.81% | 98805.0 | 18794 | +39.4% | `VNS[constructor=trivial, neighborhood=single_setup_toggle]` |
| default:SA | 16.67% | 100294.5 | 18350 | +38.4% | `SA[constructor=trivial, neighborhood=item_window_lot_consolidation]` |
| ILS:perturbation=item_row_periodic_rebuild | 20.05% | 103406.7 | 19986 | +36.5% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=item_row_periodic_rebuild]` |
| ILS:neighborhood=single_setup_toggle | 21.14% | 104043.7 | 18839 | +36.1% | `ILS[constructor=trivial, neighborhood=single_setup_toggle, perturbation=adjacent_setup_shift]` |
| default:VNS | 24.99% | 107906.4 | 22761 | +33.8% | `VNS[constructor=trivial, neighborhood=item_window_lot_consolidation]` |
| default:ILS | 27.55% | 109654.3 | 20819 | +32.7% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=random_setup_flip_k | 31.35% | 112931.3 | 21756 | +30.7% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=random_setup_flip_k]` |
| ILS:neighborhood=setup_shift_or_merge | 60.84% | 137804.6 | 22061 | +15.4% | `ILS[constructor=trivial, neighborhood=setup_shift_or_merge, perturbation=adjacent_setup_shift]` |
| VNS:neighborhood=setup_shift_or_merge | 71.53% | 147029.3 | 24116 | +9.8% | `VNS[constructor=trivial, neighborhood=setup_shift_or_merge]` |
| SA:neighborhood=setup_shift_or_merge | 87.62% | 160483.4 | 24208 | +1.5% | `SA[constructor=trivial, neighborhood=setup_shift_or_merge]` |
| LNS_MIP:constructor=random | 1074577244.95% | 900000009394.8 | 299999971816 | -552357583.1% | `LNS_MIP[constructor=random, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=item_window_lot_consolidation]` |
| ILS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=item_window_lot_consolidation]` |

Ganancia del afinado sobre el mejor default: **+1.34%**; gana en 9/10 instancias de test. Esqueletos explorados: LNS_MIP × 21, SA × 7, ILS × 6, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_part_period_balancing_score` (mejor default por gap): +1.52% de gap a favor del afinado, IC95 [+0.79%, +2.27%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 21 (numéricos por defecto) ✔ | 0.5145 | 0.5146, 0.5140, 0.5151, 0.5157, 0.5137, 0.5151, 0.5135 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` |
| 28 (numéricos por defecto) | 0.5152 | 0.5143, 0.5142, 0.5164, 0.5162, 0.5144, 0.5145, 0.5166 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| 21 | 0.5157 | 0.5149, 0.5164, 0.5157 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` |
| 28 | 0.5157 | 0.5149, 0.5162, 0.5154, 0.5172, 0.5146, 0.5154, 0.5166 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| 39 (numéricos por defecto) | 0.5164 | 0.5152, 0.5143, 0.5176, 0.5184 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=time_window_destruction]` |
| 39 | 0.5192 | 0.5182, 0.5214, 0.5181 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=time_window_destruction]` |
| 15 | 0.5239 | 0.5243, 0.5239, 0.5236 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=capacity_bottleneck_destruction]` |
| 35 | 0.5240 | 0.5236, 0.5249, 0.5235 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=costly_item_rows_destruction]` |
| 35 (numéricos por defecto) | 0.5345 | 0.5351, 0.5338, 0.5345 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=costly_item_rows_destruction]` |
| 3* | 0.5387 | 0.5411, 0.5406, 0.5342 | `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 4 configuraciones fallidas · 3995 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `capacity_bottleneck_destruction`, `costly_item_rows_destruction`, `time_window_destruction`, `capacity_tightness_marginal_score`, `part_period_balancing_score`, `silver_meal_period_average_score`, `item_window_lot_consolidation`, `setup_shift_or_merge`, `single_setup_toggle`, `adjacent_setup_shift`, `item_row_periodic_rebuild`, `random_setup_flip_k`

**Mejor en train**: `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` = 0.5153 (mejor default: 0.5336, `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.66%** | **86581.0** | 15956 | +46.9% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| LNS_MIP:constructor=greedy_part_period_balancing_score | 2.25% | 87810.9 | 15215 | +46.1% | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:constructor=greedy_capacity_tightness_marginal_score | 2.74% | 88265.5 | 15479 | +45.8% | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:constructor=greedy_silver_meal_period_average_score | 3.23% | 88724.4 | 15860 | +45.5% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=greedy_silver_meal_period_average_score | 4.40% | 89863.3 | 16906 | +44.8% | `SA[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation]` |
| LNS_MIP:destruction=time_window_destruction | 4.45% | 89819.8 | 17698 | +44.9% | `LNS_MIP[constructor=trivial, destruction=time_window_destruction]` |
| default:LNS_MIP | 4.54% | 89840.8 | 16039 | +44.9% | `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=greedy_capacity_tightness_marginal_score | 4.83% | 90201.5 | 16741 | +44.6% | `SA[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| SA:constructor=greedy_part_period_balancing_score | 4.89% | 90257.2 | 16795 | +44.6% | `SA[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation]` |
| VNS:constructor=greedy_silver_meal_period_average_score | 7.21% | 92379.2 | 18114 | +43.3% | `VNS[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation]` |
| ILS:constructor=greedy_silver_meal_period_average_score | 7.44% | 92452.1 | 17245 | +43.3% | `ILS[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:constructor=greedy_capacity_tightness_marginal_score | 7.44% | 92467.9 | 17302 | +43.2% | `ILS[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:constructor=greedy_part_period_balancing_score | 7.48% | 92491.7 | 17255 | +43.2% | `ILS[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_capacity_tightness_marginal_score | 7.61% | 92648.3 | 17571 | +43.1% | `VNS[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| VNS:constructor=greedy_part_period_balancing_score | 8.12% | 93028.2 | 17311 | +42.9% | `VNS[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation]` |
| LNS_MIP:destruction=costly_item_rows_destruction | 9.38% | 94113.1 | 17461 | +42.2% | `LNS_MIP[constructor=trivial, destruction=costly_item_rows_destruction]` |
| SA:neighborhood=single_setup_toggle | 12.31% | 96563.1 | 17585 | +40.7% | `SA[constructor=trivial, neighborhood=single_setup_toggle]` |
| VNS:neighborhood=single_setup_toggle | 14.93% | 98877.4 | 18503 | +39.3% | `VNS[constructor=trivial, neighborhood=single_setup_toggle]` |
| default:SA | 17.56% | 101059.7 | 18484 | +38.0% | `SA[constructor=trivial, neighborhood=item_window_lot_consolidation]` |
| ILS:perturbation=item_row_periodic_rebuild | 21.80% | 104839.3 | 19865 | +35.7% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=item_row_periodic_rebuild]` |
| ILS:neighborhood=single_setup_toggle | 22.97% | 105808.9 | 20724 | +35.1% | `ILS[constructor=trivial, neighborhood=single_setup_toggle, perturbation=adjacent_setup_shift]` |
| default:VNS | 25.63% | 108462.1 | 23246 | +33.4% | `VNS[constructor=trivial, neighborhood=item_window_lot_consolidation]` |
| default:ILS | 31.11% | 112898.1 | 22655 | +30.7% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=random_setup_flip_k | 35.20% | 116735.7 | 25166 | +28.4% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=random_setup_flip_k]` |
| ILS:neighborhood=setup_shift_or_merge | 61.01% | 137867.1 | 21721 | +15.4% | `ILS[constructor=trivial, neighborhood=setup_shift_or_merge, perturbation=adjacent_setup_shift]` |
| VNS:neighborhood=setup_shift_or_merge | 72.38% | 147693.8 | 24078 | +9.4% | `VNS[constructor=trivial, neighborhood=setup_shift_or_merge]` |
| SA:neighborhood=setup_shift_or_merge | 87.63% | 160484.1 | 24208 | +1.5% | `SA[constructor=trivial, neighborhood=setup_shift_or_merge]` |
| LNS_MIP:constructor=random | 1074577244.95% | 900000009394.8 | 299999971816 | -552357583.1% | `LNS_MIP[constructor=random, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=item_window_lot_consolidation]` |
| ILS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=item_window_lot_consolidation]` |

Ganancia del afinado sobre el mejor default: **+1.40%**; gana en 9/10 instancias de test. Esqueletos explorados: LNS_MIP × 21, ILS × 7, SA × 6, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_part_period_balancing_score` (mejor default por gap): +1.60% de gap a favor del afinado, IC95 [+0.86%, +2.37%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 24 | 0.5147 | 0.5142, 0.5144, 0.5148, 0.5147, 0.5146, 0.5152, 0.5147 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| 18 (numéricos por defecto) | 0.5149 | 0.5151, 0.5140, 0.5147, 0.5146, 0.5178, 0.5142, 0.5137 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` |
| 24 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.5153 | 0.5143, 0.5137, 0.5142, 0.5173, 0.5202, 0.5145, 0.5133 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| 22 (numéricos por defecto) | 0.5157 | 0.5158, 0.5143, 0.5144, 0.5174, 0.5185, 0.5154, 0.5139 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=time_window_destruction]` |
| 22 | 0.5165 | 0.5168, 0.5155, 0.5172 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=time_window_destruction]` |
| 18 | 0.5183 | 0.5184, 0.5186, 0.5179 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=time_window_destruction]` |
| 15 | 0.5230 | 0.5228, 0.5230, 0.5233 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=capacity_bottleneck_destruction]` |
| 12 | 0.5340 | 0.5318, 0.5360, 0.5341 | `SA[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| 3* | 0.5361 | 0.5336, 0.5363, 0.5382 | `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 4 configuraciones fallidas · 3699 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `capacity_bottleneck_destruction`, `costly_item_rows_destruction`, `time_window_destruction`, `capacity_tightness_marginal_score`, `part_period_balancing_score`, `silver_meal_period_average_score`, `item_window_lot_consolidation`, `setup_shift_or_merge`, `single_setup_toggle`, `adjacent_setup_shift`, `item_row_periodic_rebuild`, `random_setup_flip_k`

**Mejor en train**: `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` = 0.5148 (mejor default: 0.5345, `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.66%** | **86581.0** | 15956 | +46.9% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| LNS_MIP:constructor=greedy_part_period_balancing_score | 2.29% | 87843.7 | 15230 | +46.1% | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:constructor=greedy_capacity_tightness_marginal_score | 2.77% | 88284.9 | 15472 | +45.8% | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:constructor=greedy_silver_meal_period_average_score | 3.26% | 88755.3 | 15908 | +45.5% | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=capacity_bottleneck_destruction]` |
| LNS_MIP:destruction=time_window_destruction | 4.46% | 89836.0 | 17716 | +44.9% | `LNS_MIP[constructor=trivial, destruction=time_window_destruction]` |
| SA:constructor=greedy_silver_meal_period_average_score | 4.58% | 90022.8 | 16979 | +44.8% | `SA[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation]` |
| default:LNS_MIP | 4.98% | 90181.7 | 15954 | +44.7% | `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=greedy_part_period_balancing_score | 5.12% | 90445.3 | 16808 | +44.5% | `SA[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation]` |
| SA:constructor=greedy_capacity_tightness_marginal_score | 5.14% | 90470.1 | 16811 | +44.5% | `SA[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| VNS:constructor=greedy_silver_meal_period_average_score | 7.43% | 92493.9 | 17511 | +43.2% | `VNS[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation]` |
| ILS:constructor=greedy_capacity_tightness_marginal_score | 7.60% | 92570.5 | 17110 | +43.2% | `ILS[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:constructor=greedy_silver_meal_period_average_score | 7.63% | 92599.3 | 17127 | +43.2% | `ILS[constructor=greedy_silver_meal_period_average_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:constructor=greedy_part_period_balancing_score | 7.67% | 92612.8 | 17041 | +43.2% | `ILS[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=greedy_part_period_balancing_score | 8.04% | 92970.0 | 17423 | +42.9% | `VNS[constructor=greedy_part_period_balancing_score, neighborhood=item_window_lot_consolidation]` |
| VNS:constructor=greedy_capacity_tightness_marginal_score | 8.28% | 93179.0 | 17390 | +42.8% | `VNS[constructor=greedy_capacity_tightness_marginal_score, neighborhood=item_window_lot_consolidation]` |
| LNS_MIP:destruction=costly_item_rows_destruction | 9.38% | 94113.1 | 17461 | +42.2% | `LNS_MIP[constructor=trivial, destruction=costly_item_rows_destruction]` |
| SA:neighborhood=single_setup_toggle | 13.64% | 97731.6 | 18019 | +40.0% | `SA[constructor=trivial, neighborhood=single_setup_toggle]` |
| VNS:neighborhood=single_setup_toggle | 19.49% | 102953.1 | 20373 | +36.8% | `VNS[constructor=trivial, neighborhood=single_setup_toggle]` |
| default:SA | 20.02% | 103172.5 | 18801 | +36.7% | `SA[constructor=trivial, neighborhood=item_window_lot_consolidation]` |
| ILS:neighborhood=single_setup_toggle | 24.25% | 107025.0 | 21292 | +34.3% | `ILS[constructor=trivial, neighborhood=single_setup_toggle, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=item_row_periodic_rebuild | 25.09% | 107820.1 | 21483 | +33.8% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=item_row_periodic_rebuild]` |
| default:VNS | 27.59% | 110065.5 | 23117 | +32.4% | `VNS[constructor=trivial, neighborhood=item_window_lot_consolidation]` |
| default:ILS | 34.43% | 115828.8 | 23770 | +28.9% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| ILS:perturbation=random_setup_flip_k | 37.92% | 118808.6 | 24271 | +27.1% | `ILS[constructor=trivial, neighborhood=item_window_lot_consolidation, perturbation=random_setup_flip_k]` |
| ILS:neighborhood=setup_shift_or_merge | 62.46% | 138986.3 | 21220 | +14.7% | `ILS[constructor=trivial, neighborhood=setup_shift_or_merge, perturbation=adjacent_setup_shift]` |
| VNS:neighborhood=setup_shift_or_merge | 74.68% | 149474.2 | 22986 | +8.3% | `VNS[constructor=trivial, neighborhood=setup_shift_or_merge]` |
| SA:neighborhood=setup_shift_or_merge | 87.63% | 160484.1 | 24208 | +1.5% | `SA[constructor=trivial, neighborhood=setup_shift_or_merge]` |
| LNS_MIP:constructor=random | 1074577245.02% | 900000009453.5 | 299999971640 | -552357583.2% | `LNS_MIP[constructor=random, destruction=capacity_bottleneck_destruction]` |
| SA:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=item_window_lot_consolidation]` |
| ILS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=item_window_lot_consolidation, perturbation=adjacent_setup_shift]` |
| VNS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=item_window_lot_consolidation]` |

Ganancia del afinado sobre el mejor default: **+1.44%**; gana en 9/10 instancias de test. Esqueletos explorados: LNS_MIP × 20, SA × 7, ILS × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_part_period_balancing_score` (mejor default por gap): +1.63% de gap a favor del afinado, IC95 [+0.88%, +2.41%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 (numéricos por defecto) ✔ | 0.5148 | 0.5152, 0.5136, 0.5150, 0.5158, 0.5153, 0.5145, 0.5142 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| 22 (numéricos por defecto) | 0.5154 | 0.5163, 0.5144, 0.5140, 0.5172, 0.5173, 0.5142, 0.5141 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=time_window_destruction]` |
| 33 | 0.5159 | 0.5145, 0.5166, 0.5150, 0.5159, 0.5160, 0.5166, 0.5164 | `LNS_MIP[constructor=greedy_silver_meal_period_average_score, destruction=time_window_destruction]` |
| 22 | 0.5164 | 0.5144, 0.5175, 0.5172 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=time_window_destruction]` |
| 15 | 0.5237 | 0.5248, 0.5225, 0.5237 | `LNS_MIP[constructor=greedy_capacity_tightness_marginal_score, destruction=capacity_bottleneck_destruction]` |
| 38 | 0.5320 | 0.5304, 0.5337, 0.5320 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=costly_item_rows_destruction]` |
| 38 (numéricos por defecto) | 0.5324 | 0.5318, 0.5324, 0.5330 | `LNS_MIP[constructor=greedy_part_period_balancing_score, destruction=costly_item_rows_destruction]` |
| 3* | 0.5361 | 0.5345, 0.5338, 0.5399 | `LNS_MIP[constructor=trivial, destruction=capacity_bottleneck_destruction]` |
