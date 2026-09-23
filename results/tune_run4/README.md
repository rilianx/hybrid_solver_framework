### Catálogo `handwritten`

30 trials · 20.0 s/corrida · 5 train / 5 test (20×20) · 0 configuraciones fallidas · 3122 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 120 s

**Mejor en train**: `SA[constructor=lot_for_lot, neighborhood=setup_flip]` = 0.7633 (mejor default: 0.7636, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **13.06%** | **265004.6** | 36423 | +24.3% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:SA | 13.21% | 265361.8 | 36691 | +24.2% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 42.16% | 333039.3 | 45584 | +4.9% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | 42.88% | 334856.3 | 46276 | +4.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.13%**; gana en 2/5 instancias de test. Esqueletos explorados: SA × 20, ILS × 5, VNS × 5.

### Catálogo `all`

30 trials · 20.0 s/corrida · 5 train / 5 test (20×20) · 0 configuraciones fallidas · 3123 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 120 s

Componentes LLM en el catálogo: `backward_capacity_packing`, `earliest_slack_repair`, `adjacent_pair_merge_destruction`, `capacity_critical_period_destruction`, `whole_item_destruction`, `drop_single_setup`, `left_shift_setup_chain`, `merge_consecutive_setups`, `congested_period_relocation_perturbation`, `item_block_compaction_perturbation`, `period_swap_relink_perturbation`

**Mejor en train**: `SA[constructor=earliest_slack_repair, neighborhood=setup_flip]` = 0.7596 (mejor default: 0.7651, `SA[constructor=lot_for_lot, neighborhood=setup_flip]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **13.43%** | **265900.7** | 36807 | +24.1% | `SA[constructor=earliest_slack_repair, neighborhood=setup_flip]` |
| default:SA | 13.22% | 265402.4 | 36696 | +24.2% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=earliest_slack_repair | 13.30% | 265558.6 | 36450 | +24.2% | `SA[constructor=earliest_slack_repair, neighborhood=setup_flip]` |
| SA:neighborhood=merge_consecutive_setups | 16.41% | 273024.7 | 39504 | +22.0% | `SA[constructor=lot_for_lot, neighborhood=merge_consecutive_setups]` |
| SA:constructor=backward_capacity_packing | 24.06% | 290229.6 | 35991 | +17.1% | `SA[constructor=backward_capacity_packing, neighborhood=setup_flip]` |
| ILS:neighborhood=merge_consecutive_setups | 40.56% | 329916.4 | 48832 | +5.8% | `ILS[constructor=lot_for_lot, neighborhood=merge_consecutive_setups, perturbation=setup_flip_perturbation]` |
| VNS:neighborhood=merge_consecutive_setups | 41.78% | 332747.6 | 48937 | +5.0% | `VNS[constructor=lot_for_lot, neighborhood=merge_consecutive_setups]` |
| default:ILS | 42.16% | 333039.3 | 45584 | +4.9% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:constructor=earliest_slack_repair | 42.21% | 333170.2 | 45592 | +4.8% | `ILS[constructor=earliest_slack_repair, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=item_block_compaction_perturbation | 43.02% | 335068.0 | 45591 | +4.3% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=item_block_compaction_perturbation]` |
| VNS:constructor=earliest_slack_repair | 43.23% | 335757.9 | 46953 | +4.1% | `VNS[constructor=earliest_slack_repair, neighborhood=setup_flip]` |
| default:VNS | 43.61% | 336530.2 | 46260 | +3.9% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| ILS:neighborhood=left_shift_setup_chain | 45.41% | 340310.7 | 44278 | +2.8% | `ILS[constructor=lot_for_lot, neighborhood=left_shift_setup_chain, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=congested_period_relocation_perturbation | 45.48% | 341911.9 | 53016 | +2.4% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=congested_period_relocation_perturbation]` |
| ILS:neighborhood=drop_single_setup | 45.70% | 340966.9 | 44096 | +2.6% | `ILS[constructor=lot_for_lot, neighborhood=drop_single_setup, perturbation=setup_flip_perturbation]` |
| ILS:perturbation=period_swap_relink_perturbation | 46.29% | 343050.6 | 48326 | +2.0% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=period_swap_relink_perturbation]` |
| VNS:neighborhood=left_shift_setup_chain | 47.96% | 346263.1 | 44568 | +1.1% | `VNS[constructor=lot_for_lot, neighborhood=left_shift_setup_chain]` |
| VNS:neighborhood=drop_single_setup | 48.00% | 346397.9 | 44904 | +1.1% | `VNS[constructor=lot_for_lot, neighborhood=drop_single_setup]` |
| SA:neighborhood=drop_single_setup | 49.57% | 350110.8 | 45610 | +0.0% | `SA[constructor=lot_for_lot, neighborhood=drop_single_setup]` |
| SA:neighborhood=left_shift_setup_chain | 49.58% | 350133.1 | 45624 | +0.0% | `SA[constructor=lot_for_lot, neighborhood=left_shift_setup_chain]` |
| ILS:constructor=backward_capacity_packing | 67.46% | 391627.5 | 48440 | -11.8% | `ILS[constructor=backward_capacity_packing, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| VNS:constructor=backward_capacity_packing | 70.07% | 397912.7 | 50278 | -13.6% | `VNS[constructor=backward_capacity_packing, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.19%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 19, ILS × 6, VNS × 5.

### ¿Ayuda o diluye?

Afinado en test — a mano: 265004.6 (`SA[constructor=lot_for_lot, neighborhood=setup_flip]`) · con LLM: 265900.7 (`SA[constructor=earliest_slack_repair, neighborhood=setup_flip]`) → **-0.34%**, **empate**: el tuner eligió lo mismo o equivalente. Gap medio vs mejor conocido: a mano 13.06%, con LLM 13.43%.
