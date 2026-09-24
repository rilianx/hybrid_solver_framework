### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1060 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` = 0.6923 (mejor default: 0.7143, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **8.06%** | **91822.8** | 15101 | +29.0% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| SA:constructor=greedy_unit_marginal_cost | 6.55% | 90799.1 | 16637 | +29.8% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| VNS:constructor=greedy_unit_marginal_cost | 9.43% | 93211.7 | 16630 | +28.0% | `VNS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| ILS:constructor=greedy_unit_marginal_cost | 9.91% | 93582.8 | 16428 | +27.7% | `ILS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:SA | 11.42% | 94827.1 | 16639 | +26.7% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=greedy_latest_source | 11.77% | 95250.1 | 17493 | +26.4% | `SA[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| default:ILS | 39.28% | 118847.0 | 23024 | +8.2% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:constructor=greedy_latest_source | 39.84% | 119252.1 | 22522 | +7.8% | `ILS[constructor=greedy_latest_source, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | 40.54% | 119752.6 | 21906 | +7.5% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| VNS:constructor=greedy_latest_source | 40.81% | 119995.5 | 22021 | +7.3% | `VNS[constructor=greedy_latest_source, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-1.13%**; gana en 1/5 instancias de test. Esqueletos explorados: SA × 22, VNS × 10, ILS × 8.

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1066 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `backward_inventory_constructor`, `forward_urgency_constructor`, `saturation_balancer_constructor`, `high_setup_cost_item_destruction`, `most_congested_period_destruction`, `sparse_run_and_gap_destruction`, `amortized_unit_cost`, `deadline_pressure`, `setup_consolidation_balance`, `merge_with_previous_setup`, `shift_setup_to_adjacent_period`, `swap_setups_across_items`, `congestion_window_shuffle`, `item_break_repair`, `merge_split_consecutive_setups`

**Mejor en train**: `ILS[constructor=greedy_setup_consolidation_balance, neighborhood=merge_with_previous_setup, perturbation=item_break_repair]` = 0.6935 (mejor default: 0.9923, `ILS[constructor=backward_inventory_constructor, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **7.54%** | **91566.8** | 16213 | +29.2% | `ILS[constructor=greedy_setup_consolidation_balance, neighborhood=merge_with_previous_setup, perturbation=item_break_repair]` |
| VNS:constructor=greedy_amortized_unit_cost | 8.29% | 92137.5 | 15712 | +28.8% | `VNS[constructor=greedy_amortized_unit_cost, neighborhood=merge_with_previous_setup]` |
| VNS:constructor=greedy_setup_consolidation_balance | 9.54% | 93154.1 | 15541 | +28.0% | `VNS[constructor=greedy_setup_consolidation_balance, neighborhood=merge_with_previous_setup]` |
| SA:constructor=greedy_amortized_unit_cost | 9.77% | 93295.8 | 15232 | +27.9% | `SA[constructor=greedy_amortized_unit_cost, neighborhood=merge_with_previous_setup]` |
| ILS:constructor=greedy_amortized_unit_cost | 9.77% | 93295.8 | 15232 | +27.9% | `ILS[constructor=greedy_amortized_unit_cost, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]` |
| SA:constructor=greedy_setup_consolidation_balance | 11.55% | 94794.4 | 15286 | +26.7% | `SA[constructor=greedy_setup_consolidation_balance, neighborhood=merge_with_previous_setup]` |
| ILS:constructor=greedy_setup_consolidation_balance | 11.55% | 94794.4 | 15286 | +26.7% | `ILS[constructor=greedy_setup_consolidation_balance, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]` |
| VNS:constructor=greedy_deadline_pressure | 11.88% | 95271.8 | 17096 | +26.4% | `VNS[constructor=greedy_deadline_pressure, neighborhood=merge_with_previous_setup]` |
| ILS:perturbation=item_break_repair | 16.06% | 98952.3 | 18879 | +23.5% | `ILS[constructor=backward_inventory_constructor, neighborhood=merge_with_previous_setup, perturbation=item_break_repair]` |
| SA:constructor=greedy_deadline_pressure | 16.25% | 99147.1 | 18822 | +23.4% | `SA[constructor=greedy_deadline_pressure, neighborhood=merge_with_previous_setup]` |
| ILS:constructor=greedy_deadline_pressure | 16.25% | 99147.1 | 18822 | +23.4% | `ILS[constructor=greedy_deadline_pressure, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]` |
| ILS:perturbation=merge_split_consecutive_setups | 19.42% | 101700.6 | 18650 | +21.4% | `ILS[constructor=backward_inventory_constructor, neighborhood=merge_with_previous_setup, perturbation=merge_split_consecutive_setups]` |
| VNS:constructor=saturation_balancer_constructor | 43.77% | 122299.3 | 21210 | +5.5% | `VNS[constructor=saturation_balancer_constructor, neighborhood=merge_with_previous_setup]` |
| SA:neighborhood=swap_setups_across_items | 45.96% | 124141.2 | 21558 | +4.1% | `SA[constructor=backward_inventory_constructor, neighborhood=swap_setups_across_items]` |
| default:VNS | 47.15% | 125066.4 | 21137 | +3.3% | `VNS[constructor=backward_inventory_constructor, neighborhood=merge_with_previous_setup]` |
| VNS:neighborhood=swap_setups_across_items | 48.53% | 126441.9 | 22290 | +2.3% | `VNS[constructor=backward_inventory_constructor, neighborhood=swap_setups_across_items]` |
| VNS:neighborhood=shift_setup_to_adjacent_period | 50.51% | 128234.3 | 23391 | +0.9% | `VNS[constructor=backward_inventory_constructor, neighborhood=shift_setup_to_adjacent_period]` |
| SA:constructor=saturation_balancer_constructor | 52.10% | 129569.4 | 23512 | -0.1% | `SA[constructor=saturation_balancer_constructor, neighborhood=merge_with_previous_setup]` |
| ILS:constructor=saturation_balancer_constructor | 52.10% | 129569.4 | 23512 | -0.1% | `ILS[constructor=saturation_balancer_constructor, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]` |
| ILS:neighborhood=swap_setups_across_items | 54.02% | 131309.9 | 24502 | -1.5% | `ILS[constructor=backward_inventory_constructor, neighborhood=swap_setups_across_items, perturbation=congestion_window_shuffle]` |
| SA:neighborhood=shift_setup_to_adjacent_period | 55.02% | 131994.5 | 23544 | -2.0% | `SA[constructor=backward_inventory_constructor, neighborhood=shift_setup_to_adjacent_period]` |
| default:SA | 55.11% | 132073.3 | 23602 | -2.1% | `SA[constructor=backward_inventory_constructor, neighborhood=merge_with_previous_setup]` |
| default:ILS | 55.11% | 132073.3 | 23602 | -2.1% | `ILS[constructor=backward_inventory_constructor, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]` |
| ILS:neighborhood=shift_setup_to_adjacent_period | 55.11% | 132073.3 | 23602 | -2.1% | `ILS[constructor=backward_inventory_constructor, neighborhood=shift_setup_to_adjacent_period, perturbation=congestion_window_shuffle]` |
| VNS:constructor=forward_urgency_constructor | 61.30% | 137083.2 | 22855 | -5.9% | `VNS[constructor=forward_urgency_constructor, neighborhood=merge_with_previous_setup]` |
| SA:constructor=forward_urgency_constructor | 71.73% | 146071.8 | 24801 | -12.9% | `SA[constructor=forward_urgency_constructor, neighborhood=merge_with_previous_setup]` |
| ILS:constructor=forward_urgency_constructor | 71.73% | 146071.8 | 24801 | -12.9% | `ILS[constructor=forward_urgency_constructor, neighborhood=merge_with_previous_setup, perturbation=congestion_window_shuffle]` |

Ganancia del afinado sobre el mejor default: **+0.62%**; gana en 2/5 instancias de test. Esqueletos explorados: ILS × 17, SA × 13, VNS × 10.

### Catálogo `all`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1051 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `backward_inventory_constructor`, `forward_urgency_constructor`, `saturation_balancer_constructor`, `high_setup_cost_item_destruction`, `most_congested_period_destruction`, `sparse_run_and_gap_destruction`, `amortized_unit_cost`, `deadline_pressure`, `setup_consolidation_balance`, `merge_with_previous_setup`, `shift_setup_to_adjacent_period`, `swap_setups_across_items`, `congestion_window_shuffle`, `item_break_repair`, `merge_split_consecutive_setups`

**Mejor en train**: `SA[constructor=greedy_unit_marginal_cost, neighborhood=merge_with_previous_setup]` = 0.6904 (mejor default: 0.7143, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **6.86%** | **91046.2** | 16633 | +29.6% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=merge_with_previous_setup]` |
| SA:constructor=greedy_unit_marginal_cost | 6.55% | 90801.1 | 16635 | +29.8% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| SA:constructor=greedy_amortized_unit_cost | 7.05% | 91125.1 | 15949 | +29.6% | `SA[constructor=greedy_amortized_unit_cost, neighborhood=setup_flip]` |
| SA:constructor=greedy_setup_consolidation_balance | 7.50% | 91492.4 | 15839 | +29.3% | `SA[constructor=greedy_setup_consolidation_balance, neighborhood=setup_flip]` |
| SA:constructor=greedy_deadline_pressure | 9.62% | 93411.8 | 17036 | +27.8% | `SA[constructor=greedy_deadline_pressure, neighborhood=setup_flip]` |
| ILS:constructor=greedy_amortized_unit_cost | 9.69% | 93234.9 | 15269 | +27.9% | `ILS[constructor=greedy_amortized_unit_cost, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=greedy_amortized_unit_cost | 9.69% | 93240.6 | 15254 | +27.9% | `VNS[constructor=greedy_amortized_unit_cost, neighborhood=setup_flip]` |
| VNS:constructor=greedy_unit_marginal_cost | 9.87% | 93545.9 | 16425 | +27.7% | `VNS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| ILS:constructor=greedy_unit_marginal_cost | 9.91% | 93582.8 | 16428 | +27.7% | `ILS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:constructor=greedy_setup_consolidation_balance | 11.03% | 94373.2 | 15403 | +27.1% | `ILS[constructor=greedy_setup_consolidation_balance, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=greedy_setup_consolidation_balance | 11.15% | 94483.7 | 15404 | +27.0% | `VNS[constructor=greedy_setup_consolidation_balance, neighborhood=setup_flip]` |
| SA:constructor=saturation_balancer_constructor | 11.27% | 94825.2 | 17439 | +26.7% | `SA[constructor=saturation_balancer_constructor, neighborhood=setup_flip]` |
| default:SA | 11.34% | 94770.7 | 16685 | +26.8% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=greedy_latest_source | 12.27% | 95640.9 | 17398 | +26.1% | `SA[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| SA:constructor=backward_inventory_constructor | 14.63% | 97700.7 | 18046 | +24.5% | `SA[constructor=backward_inventory_constructor, neighborhood=setup_flip]` |
| VNS:constructor=greedy_deadline_pressure | 14.75% | 97810.6 | 18198 | +24.4% | `VNS[constructor=greedy_deadline_pressure, neighborhood=setup_flip]` |
| ILS:constructor=greedy_deadline_pressure | 15.77% | 98659.3 | 18147 | +23.8% | `ILS[constructor=greedy_deadline_pressure, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| SA:constructor=forward_urgency_constructor | 15.94% | 98740.9 | 17535 | +23.7% | `SA[constructor=forward_urgency_constructor, neighborhood=setup_flip]` |
| VNS:neighborhood=merge_with_previous_setup | 19.14% | 101470.9 | 18354 | +21.6% | `VNS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]` |
| ILS:neighborhood=merge_with_previous_setup | 19.63% | 101964.5 | 19408 | +21.2% | `ILS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=item_break_repair | 34.55% | 114847.8 | 22317 | +11.2% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=item_break_repair]` |
| default:ILS | 39.33% | 118888.4 | 23020 | +8.1% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:constructor=greedy_latest_source | 39.78% | 119210.2 | 22546 | +7.9% | `ILS[constructor=greedy_latest_source, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=saturation_balancer_constructor | 39.81% | 119115.1 | 21751 | +7.9% | `VNS[constructor=saturation_balancer_constructor, neighborhood=setup_flip]` |
| default:VNS | 40.06% | 119245.8 | 21007 | +7.8% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| VNS:constructor=greedy_latest_source | 40.18% | 119381.8 | 21193 | +7.7% | `VNS[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| ILS:constructor=saturation_balancer_constructor | 41.08% | 120032.3 | 20901 | +7.2% | `ILS[constructor=saturation_balancer_constructor, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:neighborhood=swap_setups_across_items | 42.53% | 121305.9 | 21187 | +6.3% | `ILS[constructor=lot_for_lot, neighborhood=swap_setups_across_items, perturbation=setup_flip_perturbation]` |
| ILS:neighborhood=shift_setup_to_adjacent_period | 42.92% | 121636.5 | 21311 | +6.0% | `ILS[constructor=lot_for_lot, neighborhood=shift_setup_to_adjacent_period, perturbation=setup_flip_perturbation]` |
| SA:neighborhood=swap_setups_across_items | 42.94% | 121604.1 | 21184 | +6.0% | `SA[constructor=lot_for_lot, neighborhood=swap_setups_across_items]` |
| ILS:constructor=backward_inventory_constructor | 43.40% | 122014.1 | 21293 | +5.7% | `ILS[constructor=backward_inventory_constructor, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=merge_split_consecutive_setups | 44.42% | 123211.4 | 23644 | +4.8% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=merge_split_consecutive_setups]` |
| VNS:constructor=backward_inventory_constructor | 45.25% | 123815.0 | 22983 | +4.3% | `VNS[constructor=backward_inventory_constructor, neighborhood=setup_flip]` |
| VNS:neighborhood=swap_setups_across_items | 45.60% | 123950.9 | 21925 | +4.2% | `VNS[constructor=lot_for_lot, neighborhood=swap_setups_across_items]` |
| VNS:neighborhood=shift_setup_to_adjacent_period | 47.69% | 125851.0 | 23042 | +2.7% | `VNS[constructor=lot_for_lot, neighborhood=shift_setup_to_adjacent_period]` |
| SA:neighborhood=shift_setup_to_adjacent_period | 51.79% | 129310.1 | 23467 | +0.1% | `SA[constructor=lot_for_lot, neighborhood=shift_setup_to_adjacent_period]` |
| SA:neighborhood=merge_with_previous_setup | 51.88% | 129394.4 | 23541 | +0.0% | `SA[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]` |
| ILS:perturbation=congestion_window_shuffle | 51.88% | 129394.4 | 23541 | +0.0% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=congestion_window_shuffle]` |
| ILS:constructor=forward_urgency_constructor | 58.43% | 134857.4 | 23588 | -4.2% | `ILS[constructor=forward_urgency_constructor, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=forward_urgency_constructor | 59.12% | 135211.8 | 22181 | -4.5% | `VNS[constructor=forward_urgency_constructor, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.27%**; gana en 1/5 instancias de test. Esqueletos explorados: SA × 22, ILS × 12, VNS × 6.

### ¿Ayuda o diluye?

Afinado en test — a mano: 91822.8 (`SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]`) · con LLM: 91046.2 (`SA[constructor=greedy_unit_marginal_cost, neighborhood=merge_with_previous_setup]`) → **+0.85%**, el catálogo ampliado **ayuda**. Gap medio vs mejor conocido: a mano 8.06%, con LLM 6.86%.

### Solo generados vs a mano

Afinado en test — a mano: 91822.8, gap 8.06% (`SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]`) · solo LLM: 91566.8, gap 7.54% (`ILS[constructor=greedy_setup_consolidation_balance, neighborhood=merge_with_previous_setup, perturbation=item_break_repair]`) → **+0.28%**, **empate** entre solo generados y a mano.
