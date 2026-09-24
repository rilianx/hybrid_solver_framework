### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 2 configuraciones fallidas · 984 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` = 0.6943 (mejor default: 0.6943, `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **10.66%** | **94291.2** | 17513 | +27.1% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.31% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 7.61% | 91406.5 | 15015 | +29.4% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_forward_cover_cost | 7.65% | 91568.0 | 15951 | +29.2% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.11% | 92839.8 | 16402 | +28.3% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.81% | 93432.5 | 16344 | +27.8% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:SA | 10.68% | 94315.8 | 17560 | +27.1% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.70% | 94327.3 | 17713 | +27.1% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:VNS | 15.37% | 98285.6 | 18570 | +24.0% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=critical_period_seeding | 18.06% | 100469.6 | 18143 | +22.4% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 18.33% | 100582.9 | 17161 | +22.3% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 19.11% | 101630.9 | 20704 | +21.5% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.21% | 101350.3 | 17531 | +21.7% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=greedy_capacity_pressure_balance | 19.68% | 101738.3 | 17381 | +21.4% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:ILS | 19.76% | 101978.3 | 19152 | +21.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 20.02% | 102528.3 | 21004 | +20.8% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 20.10% | 102421.9 | 19739 | +20.8% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:perturbation=merge_adjacent_lots | 22.60% | 104322.3 | 18549 | +19.4% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:neighborhood=swap_capacity_pressure | 23.92% | 105430.9 | 18957 | +18.5% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.64% | 106116.6 | 19747 | +18.0% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 25.70% | 107173.0 | 20115 | +17.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| VNS:neighborhood=shift_setup_in_time | 45.64% | 123999.5 | 22530 | +4.2% | `VNS[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |
| SA:neighborhood=shift_setup_in_time | 49.32% | 127099.6 | 22702 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-6.27%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 22, ILS × 9, VNS × 9.
