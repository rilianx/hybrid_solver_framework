### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1051 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `destroy_capacity_hotspots`, `destroy_item_block`, `destroy_low_value_setups`, `balance_fifo_multiactivo`, `coste_holding_setup_inmediato`, `urgencia_falta_capacidad`, `capacity_swap_between_items`, `merge_with_previous_setup`, `window_destroy_and_repair`, `capacity_pressure_window_kick`, `item_chain_shift_kick`, `swap_and_rebalance_kick`

**Mejor en train**: `SA[constructor=greedy_coste_holding_setup_inmediato, neighborhood=merge_with_previous_setup]` = 0.6892 (mejor default: 0.9625, `VNS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **7.83%** | **91550.8** | 14914 | +29.2% | `SA[constructor=greedy_coste_holding_setup_inmediato, neighborhood=merge_with_previous_setup]` |
| SA:constructor=greedy_coste_holding_setup_inmediato | 6.94% | 90845.9 | 14891 | +29.8% | `SA[constructor=greedy_coste_holding_setup_inmediato, neighborhood=capacity_swap_between_items]` |
| SA:neighborhood=merge_with_previous_setup | 9.23% | 92858.7 | 15831 | +28.2% | `SA[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]` |
| VNS:constructor=greedy_coste_holding_setup_inmediato | 9.32% | 92757.8 | 14394 | +28.3% | `VNS[constructor=greedy_coste_holding_setup_inmediato, neighborhood=capacity_swap_between_items]` |
| ILS:constructor=greedy_coste_holding_setup_inmediato | 9.41% | 92820.0 | 14342 | +28.3% | `ILS[constructor=greedy_coste_holding_setup_inmediato, neighborhood=capacity_swap_between_items, perturbation=capacity_pressure_window_kick]` |
| SA:constructor=greedy_urgencia_falta_capacidad | 11.08% | 94307.3 | 15031 | +27.1% | `SA[constructor=greedy_urgencia_falta_capacidad, neighborhood=capacity_swap_between_items]` |
| SA:neighborhood=window_destroy_and_repair | 13.33% | 96545.1 | 17703 | +25.4% | `SA[constructor=lot_for_lot, neighborhood=window_destroy_and_repair]` |
| VNS:constructor=greedy_urgencia_falta_capacidad | 15.00% | 97492.9 | 14496 | +24.7% | `VNS[constructor=greedy_urgencia_falta_capacidad, neighborhood=capacity_swap_between_items]` |
| ILS:constructor=greedy_urgencia_falta_capacidad | 15.12% | 97584.1 | 14462 | +24.6% | `ILS[constructor=greedy_urgencia_falta_capacidad, neighborhood=capacity_swap_between_items, perturbation=capacity_pressure_window_kick]` |
| VNS:neighborhood=merge_with_previous_setup | 36.38% | 116281.8 | 22494 | +10.1% | `VNS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup]` |
| VNS:neighborhood=window_destroy_and_repair | 40.68% | 119693.7 | 21033 | +7.5% | `VNS[constructor=lot_for_lot, neighborhood=window_destroy_and_repair]` |
| VNS:constructor=greedy_balance_fifo_multiactivo | 44.05% | 122876.1 | 23996 | +5.0% | `VNS[constructor=greedy_balance_fifo_multiactivo, neighborhood=capacity_swap_between_items]` |
| SA:constructor=greedy_balance_fifo_multiactivo | 45.92% | 124507.6 | 24749 | +3.8% | `SA[constructor=greedy_balance_fifo_multiactivo, neighborhood=capacity_swap_between_items]` |
| ILS:perturbation=item_chain_shift_kick | 46.17% | 124424.5 | 22546 | +3.8% | `ILS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items, perturbation=item_chain_shift_kick]` |
| ILS:constructor=greedy_balance_fifo_multiactivo | 47.02% | 125399.6 | 24341 | +3.1% | `ILS[constructor=greedy_balance_fifo_multiactivo, neighborhood=capacity_swap_between_items, perturbation=capacity_pressure_window_kick]` |
| default:VNS | 47.05% | 125201.7 | 22734 | +3.2% | `VNS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items]` |
| ILS:neighborhood=merge_with_previous_setup | 50.41% | 128171.0 | 23985 | +0.9% | `ILS[constructor=lot_for_lot, neighborhood=merge_with_previous_setup, perturbation=capacity_pressure_window_kick]` |
| default:ILS | 50.78% | 128425.2 | 23432 | +0.7% | `ILS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items, perturbation=capacity_pressure_window_kick]` |
| ILS:neighborhood=window_destroy_and_repair | 50.88% | 128541.1 | 23839 | +0.7% | `ILS[constructor=lot_for_lot, neighborhood=window_destroy_and_repair, perturbation=capacity_pressure_window_kick]` |
| default:SA | 51.86% | 129303.8 | 23474 | +0.1% | `SA[constructor=lot_for_lot, neighborhood=capacity_swap_between_items]` |
| ILS:perturbation=swap_and_rebalance_kick | 51.93% | 129361.8 | 23478 | +0.0% | `ILS[constructor=lot_for_lot, neighborhood=capacity_swap_between_items, perturbation=swap_and_rebalance_kick]` |

Ganancia del afinado sobre el mejor default: **-0.78%**; gana en 2/5 instancias de test. Esqueletos explorados: VNS × 18, SA × 17, ILS × 5.
