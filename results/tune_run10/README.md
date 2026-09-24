### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 2 configuraciones fallidas · 996 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `destroy_capacity_hotspots`, `destroy_item_block`, `destroy_low_value_setups`, `balance_fifo_multiactivo`, `coste_holding_setup_inmediato`, `urgencia_falta_capacidad`, `capacity_swap_between_items`, `merge_with_previous_setup`, `window_destroy_and_repair`, `item_chain_shift_kick`, `swap_and_rebalance_kick`

**Mejor en train**: `SA[constructor=greedy_coste_holding_setup_inmediato, neighborhood=merge_with_previous_setup]` = 0.6890 (mejor default: 0.7262, `VNS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **7.59%** | **91280.5** | 14360 | +29.5% | `SA[constructor=greedy_coste_holding_setup_inmediato, neighborhood=merge_with_previous_setup]` |
| SA:constructor=greedy_coste_holding_setup_inmediato | 6.92% | 90833.5 | 14896 | +29.8% | `SA[constructor=greedy_coste_holding_setup_inmediato, neighborhood=capacity_swap_between_items]` |
| ILS:constructor=greedy_coste_holding_setup_inmediato | 8.16% | 91823.6 | 14675 | +29.0% | `ILS[constructor=greedy_coste_holding_setup_inmediato, neighborhood=capacity_swap_between_items, perturbation=item_chain_shift_kick]` |
| VNS:constructor=greedy_coste_holding_setup_inmediato | 9.00% | 92496.1 | 14449 | +28.5% | `VNS[constructor=greedy_coste_holding_setup_inmediato, neighborhood=merge_with_previous_setup]` |
| SA:neighborhood=merge_with_previous_setup | 9.20% | 92823.7 | 15761 | +28.3% | `SA[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]` |
| SA:constructor=greedy_urgencia_falta_capacidad | 10.97% | 94202.2 | 14905 | +27.2% | `SA[constructor=greedy_urgencia_falta_capacidad, neighborhood=capacity_swap_between_items]` |
| ILS:constructor=greedy_urgencia_falta_capacidad | 13.13% | 95935.2 | 14632 | +25.9% | `ILS[constructor=greedy_urgencia_falta_capacidad, neighborhood=capacity_swap_between_items, perturbation=item_chain_shift_kick]` |
| SA:neighborhood=window_destroy_and_repair | 13.29% | 96517.3 | 17711 | +25.4% | `SA[constructor=lot_for_lot, neighborhood=window_destroy_and_repair]` |
| VNS:constructor=greedy_urgencia_falta_capacidad | 15.12% | 97584.1 | 14462 | +24.6% | `VNS[constructor=greedy_urgencia_falta_capacidad, neighborhood=merge_with_previous_setup]` |
| default:VNS | 15.13% | 98079.3 | 18327 | +24.2% | `VNS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]` |
| ILS:neighborhood=merge_with_previous_setup | 18.18% | 100597.9 | 18156 | +22.3% | `ILS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup, perturbation=item_chain_shift_kick]` |
| VNS:neighborhood=window_destroy_and_repair | 20.06% | 102268.6 | 18836 | +21.0% | `VNS[constructor=lot_for_lot, neighborhood=window_destroy_and_repair]` |
| ILS:neighborhood=window_destroy_and_repair | 20.89% | 103261.6 | 21240 | +20.2% | `ILS[constructor=lot_for_lot, neighborhood=window_destroy_and_repair, perturbation=item_chain_shift_kick]` |
| VNS:constructor=greedy_balance_fifo_multiactivo | 23.40% | 104921.6 | 18611 | +18.9% | `VNS[constructor=greedy_balance_fifo_multiactivo, neighborhood=merge_with_previous_setup]` |
| ILS:constructor=greedy_balance_fifo_multiactivo | 42.47% | 121329.3 | 22429 | +6.2% | `ILS[constructor=greedy_balance_fifo_multiactivo, neighborhood=capacity_swap_between_items, perturbation=item_chain_shift_kick]` |
| default:ILS | 45.75% | 123972.9 | 21663 | +4.2% | `ILS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items, perturbation=item_chain_shift_kick]` |
| SA:constructor=greedy_balance_fifo_multiactivo | 45.89% | 124479.2 | 24760 | +3.8% | `SA[constructor=greedy_balance_fifo_multiactivo, neighborhood=capacity_swap_between_items]` |
| default:SA | 51.86% | 129303.8 | 23474 | +0.1% | `SA[constructor=lot_for_lot, neighborhood=capacity_swap_between_items]` |
| ILS:perturbation=swap_and_rebalance_kick | 51.89% | 129326.8 | 23470 | +0.1% | `ILS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items, perturbation=swap_and_rebalance_kick]` |

Ganancia del afinado sobre el mejor default: **-0.49%**; gana en 2/5 instancias de test. Esqueletos explorados: SA × 20, VNS × 11, ILS × 9.
