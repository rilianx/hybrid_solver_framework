### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1044 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=lot_for_lot, neighborhood=setup_flip]` = 0.7096 (mejor default: 0.7142, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **11.29%** | **94703.2** | 16790 | +26.8% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:SA | 11.19% | 94606.5 | 16766 | +26.9% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 39.02% | 118571.5 | 23021 | +8.4% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | 40.62% | 119756.4 | 21862 | +7.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.10%**; gana en 2/5 instancias de test. Esqueletos explorados: SA × 27, ILS × 7, VNS × 6.

### Catálogo `all`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1051 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `backward_capacity_packing`, `earliest_slack_repair`, `adjacent_pair_merge_destruction`, `capacity_critical_period_destruction`, `whole_item_destruction`, `drop_single_setup`, `left_shift_setup_chain`, `merge_consecutive_setups`, `congested_period_relocation_perturbation`, `item_block_compaction_perturbation`, `period_swap_relink_perturbation`

**Mejor en train**: `SA[constructor=lot_for_lot, neighborhood=setup_flip]` = 0.7093 (mejor default: 0.7142, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **11.62%** | **95064.3** | 17395 | +26.5% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:SA | 11.19% | 94606.7 | 16766 | +26.9% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=earliest_slack_repair | 12.10% | 95409.9 | 17165 | +26.3% | `SA[constructor=earliest_slack_repair, neighborhood=setup_flip]` |
| SA:constructor=backward_capacity_packing | 17.15% | 99536.2 | 16625 | +23.1% | `SA[constructor=backward_capacity_packing, neighborhood=setup_flip]` |
| SA:neighborhood=merge_consecutive_setups | 17.45% | 100125.9 | 19091 | +22.6% | `SA[constructor=lot_for_lot, neighborhood=merge_consecutive_setups]` |
| default:ILS | 39.09% | 118624.8 | 22966 | +8.3% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:neighborhood=merge_consecutive_setups | 39.23% | 118620.0 | 22143 | +8.3% | `ILS[constructor=lot_for_lot, neighborhood=merge_consecutive_setups, perturbation=setup_flip_perturbation]` |
| ILS:constructor=earliest_slack_repair | 39.73% | 119049.6 | 22126 | +8.0% | `ILS[constructor=earliest_slack_repair, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:neighborhood=left_shift_setup_chain | 40.79% | 119768.4 | 20895 | +7.4% | `ILS[constructor=lot_for_lot, neighborhood=left_shift_setup_chain, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=item_block_compaction_perturbation | 40.95% | 119977.3 | 21473 | +7.3% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=item_block_compaction_perturbation]` |
| ILS:neighborhood=drop_single_setup | 42.08% | 120837.4 | 21097 | +6.6% | `ILS[constructor=lot_for_lot, neighborhood=drop_single_setup, perturbation=setup_flip_perturbation]` |
| VNS:neighborhood=merge_consecutive_setups | 42.59% | 121389.4 | 22272 | +6.2% | `VNS[constructor=lot_for_lot, neighborhood=merge_consecutive_setups]` |
| VNS:constructor=earliest_slack_repair | 42.68% | 121356.5 | 21132 | +6.2% | `VNS[constructor=earliest_slack_repair, neighborhood=setup_flip]` |
| default:VNS | 42.91% | 121711.8 | 22299 | +5.9% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| ILS:perturbation=period_swap_relink_perturbation | 44.39% | 123160.0 | 23579 | +4.8% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=period_swap_relink_perturbation]` |
| ILS:perturbation=congested_period_relocation_perturbation | 44.45% | 122979.3 | 22052 | +5.0% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=congested_period_relocation_perturbation]` |
| VNS:neighborhood=left_shift_setup_chain | 47.38% | 125538.4 | 23103 | +3.0% | `VNS[constructor=lot_for_lot, neighborhood=left_shift_setup_chain]` |
| VNS:neighborhood=drop_single_setup | 48.74% | 126652.0 | 22953 | +2.1% | `VNS[constructor=lot_for_lot, neighborhood=drop_single_setup]` |
| SA:neighborhood=drop_single_setup | 51.86% | 129308.9 | 23481 | +0.1% | `SA[constructor=lot_for_lot, neighborhood=drop_single_setup]` |
| SA:neighborhood=left_shift_setup_chain | 51.89% | 129326.8 | 23473 | +0.1% | `SA[constructor=lot_for_lot, neighborhood=left_shift_setup_chain]` |
| ILS:constructor=backward_capacity_packing | 61.03% | 136513.7 | 20576 | -5.5% | `ILS[constructor=backward_capacity_packing, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=backward_capacity_packing | 63.12% | 138360.0 | 21211 | -6.9% | `VNS[constructor=backward_capacity_packing, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.48%**; gana en 1/5 instancias de test. Esqueletos explorados: SA × 22, ILS × 9, VNS × 9.

### ¿Ayuda o diluye?

Afinado en test — a mano: 94703.2 (`SA[constructor=lot_for_lot, neighborhood=setup_flip]`) · con LLM: 95064.3 (`SA[constructor=lot_for_lot, neighborhood=setup_flip]`) → **-0.38%**, **empate**: el tuner eligió lo mismo o equivalente. Gap medio vs mejor conocido: a mano 11.29%, con LLM 11.62%.
