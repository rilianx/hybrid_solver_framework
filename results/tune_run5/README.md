### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1044 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=lot_for_lot, neighborhood=setup_flip]` = 0.7123 (mejor default: 0.7152, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **11.08%** | **94532.0** | 16808 | +26.9% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:SA | 11.28% | 94674.9 | 16743 | +26.8% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 39.09% | 118624.8 | 22966 | +8.3% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | 40.83% | 119904.3 | 21729 | +7.3% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.15%**; gana en 3/5 instancias de test. Esqueletos explorados: SA × 27, ILS × 7, VNS × 6.

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 12 configuraciones fallidas · 798 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `batch_covering_merge`, `prefix_capacity_earliest_feasible`, `bottleneck_period_destruction`, `global_utility_destruction`, `low_value_item_chain_destruction`, `backward_merge_setup`, `bridge_setup_removal`, `cross_item_period_exchange`, `critical_period_block_shift`, `same_period_setup_swap`, `window_reseed_by_item`

**Mejor en train**: `SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]` = 0.6851 (mejor default: 1000000000000.0000, `SA[constructor=batch_covering_merge, neighborhood=backward_merge_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **8.39%** | **92335.0** | 17105 | +28.6% | `SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]` |
| SA:constructor=prefix_capacity_earliest_feasible | 8.47% | 92465.1 | 17536 | +28.5% | `SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]` |
| ILS:constructor=prefix_capacity_earliest_feasible | 32.87% | 113222.4 | 21763 | +12.5% | `ILS[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup, perturbation=critical_period_block_shift]` |
| VNS:constructor=prefix_capacity_earliest_feasible | 35.21% | 115391.3 | 23451 | +10.8% | `VNS[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]` |
| SA:neighborhood=bridge_setup_removal | 1120447137.04% | 933333340506.1 | 249443798947 | -721308590.3% | `SA[constructor=batch_covering_merge, neighborhood=bridge_setup_removal]` |
| default:SA | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `SA[constructor=batch_covering_merge, neighborhood=backward_merge_setup]` |
| SA:neighborhood=cross_item_period_exchange | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `SA[constructor=batch_covering_merge, neighborhood=cross_item_period_exchange]` |
| default:ILS | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `ILS[constructor=batch_covering_merge, neighborhood=backward_merge_setup, perturbation=critical_period_block_shift]` |
| ILS:neighborhood=bridge_setup_removal | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `ILS[constructor=batch_covering_merge, neighborhood=bridge_setup_removal, perturbation=critical_period_block_shift]` |
| ILS:neighborhood=cross_item_period_exchange | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `ILS[constructor=batch_covering_merge, neighborhood=cross_item_period_exchange, perturbation=critical_period_block_shift]` |
| ILS:perturbation=same_period_setup_swap | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `ILS[constructor=batch_covering_merge, neighborhood=backward_merge_setup, perturbation=same_period_setup_swap]` |
| ILS:perturbation=window_reseed_by_item | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `ILS[constructor=batch_covering_merge, neighborhood=backward_merge_setup, perturbation=window_reseed_by_item]` |
| default:VNS | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `VNS[constructor=batch_covering_merge, neighborhood=backward_merge_setup]` |
| VNS:neighborhood=bridge_setup_removal | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `VNS[constructor=batch_covering_merge, neighborhood=bridge_setup_removal]` |
| VNS:neighborhood=cross_item_period_exchange | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `VNS[constructor=batch_covering_merge, neighborhood=cross_item_period_exchange]` |

Ganancia del afinado sobre el mejor default: **+0.14%**; gana en 3/5 instancias de test. Esqueletos explorados: SA × 24, ILS × 9, VNS × 7.

### Catálogo `all`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 8 configuraciones fallidas · 885 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `batch_covering_merge`, `prefix_capacity_earliest_feasible`, `bottleneck_period_destruction`, `global_utility_destruction`, `low_value_item_chain_destruction`, `backward_merge_setup`, `bridge_setup_removal`, `cross_item_period_exchange`, `critical_period_block_shift`, `same_period_setup_swap`, `window_reseed_by_item`

**Mejor en train**: `SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]` = 0.6848 (mejor default: 0.7142, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **8.57%** | **92537.6** | 17566 | +28.5% | `SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]` |
| SA:neighborhood=backward_merge_setup | 8.47% | 92465.0 | 17528 | +28.5% | `SA[constructor=lot_for_lot, neighborhood=backward_merge_setup]` |
| default:SA | 11.19% | 94606.7 | 16766 | +26.9% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=prefix_capacity_earliest_feasible | 11.19% | 94606.7 | 16766 | +26.9% | `SA[constructor=prefix_capacity_earliest_feasible, neighborhood=setup_flip]` |
| SA:neighborhood=cross_item_period_exchange | 13.27% | 96310.0 | 16389 | +25.6% | `SA[constructor=lot_for_lot, neighborhood=cross_item_period_exchange]` |
| VNS:neighborhood=backward_merge_setup | 35.65% | 115875.9 | 23875 | +10.4% | `VNS[constructor=lot_for_lot, neighborhood=backward_merge_setup]` |
| ILS:neighborhood=backward_merge_setup | 37.12% | 116561.6 | 19825 | +9.9% | `ILS[constructor=lot_for_lot, neighborhood=backward_merge_setup, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=critical_period_block_shift | 37.46% | 117349.1 | 23522 | +9.3% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=critical_period_block_shift]` |
| ILS:constructor=prefix_capacity_earliest_feasible | 39.09% | 118624.8 | 22966 | +8.3% | `ILS[constructor=prefix_capacity_earliest_feasible, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:ILS | 39.13% | 118654.9 | 22958 | +8.3% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=prefix_capacity_earliest_feasible | 40.02% | 119171.6 | 21199 | +7.9% | `VNS[constructor=prefix_capacity_earliest_feasible, neighborhood=setup_flip]` |
| default:VNS | 40.33% | 119422.1 | 21176 | +7.7% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| ILS:neighborhood=cross_item_period_exchange | 41.61% | 120648.1 | 22278 | +6.8% | `ILS[constructor=lot_for_lot, neighborhood=cross_item_period_exchange, perturbation=setup_flip_perturbation]` |
| ILS:neighborhood=bridge_setup_removal | 42.00% | 120779.0 | 21156 | +6.7% | `ILS[constructor=lot_for_lot, neighborhood=bridge_setup_removal, perturbation=setup_flip_perturbation]` |
| VNS:neighborhood=cross_item_period_exchange | 43.41% | 122201.8 | 22706 | +5.6% | `VNS[constructor=lot_for_lot, neighborhood=cross_item_period_exchange]` |
| ILS:perturbation=same_period_setup_swap | 47.16% | 125428.8 | 23698 | +3.1% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=same_period_setup_swap]` |
| VNS:neighborhood=bridge_setup_removal | 47.21% | 125363.0 | 22929 | +3.1% | `VNS[constructor=lot_for_lot, neighborhood=bridge_setup_removal]` |
| SA:neighborhood=bridge_setup_removal | 51.86% | 129308.9 | 23481 | +0.1% | `SA[constructor=lot_for_lot, neighborhood=bridge_setup_removal]` |
| ILS:perturbation=window_reseed_by_item | 51.96% | 129394.4 | 23541 | +0.0% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=window_reseed_by_item]` |
| SA:constructor=batch_covering_merge | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `SA[constructor=batch_covering_merge, neighborhood=setup_flip]` |
| ILS:constructor=batch_covering_merge | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `ILS[constructor=batch_covering_merge, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=batch_covering_merge | 1206100379.48% | 1000000000000.0 | 0 | -772830633.7% | `VNS[constructor=batch_covering_merge, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.08%**; gana en 2/5 instancias de test. Esqueletos explorados: SA × 23, ILS × 9, VNS × 8.

### ¿Ayuda o diluye?

Afinado en test — a mano: 94532.0 (`SA[constructor=lot_for_lot, neighborhood=setup_flip]`) · con LLM: 92537.6 (`SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]`) → **+2.11%**, el catálogo ampliado **ayuda**. Gap medio vs mejor conocido: a mano 11.08%, con LLM 8.57%.

### Solo generados vs a mano

Afinado en test — a mano: 94532.0, gap 11.08% (`SA[constructor=lot_for_lot, neighborhood=setup_flip]`) · solo LLM: 92335.0, gap 8.39% (`SA[constructor=prefix_capacity_earliest_feasible, neighborhood=backward_merge_setup]`) → **+2.32%**, solo generados **supera** a lo de mano.
