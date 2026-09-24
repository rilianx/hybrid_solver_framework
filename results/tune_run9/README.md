### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 3 configuraciones fallidas · 1051 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `rcl_capacity_balancer`, `rolling_urgency_constructor`, `congested_period_destruction`, `critical_item_chain_destruction`, `low_utility_setup_destruction`, `capacity_balancing_pressure`, `earliest_deadline_setup_aware`, `setup_amortization_by_quantity`, `capacity_based_setup_toggle`, `merge_adjacent_setups`, `single_item_two_period_swap`, `adjacent_setup_relocation`, `congestion_based_setup_swap`, `item_window_compaction`

**Mejor en train**: `VNS[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle]` = 0.6935 (mejor default: 0.7235, `SA[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **9.25%** | **92594.9** | 13977 | +28.4% | `VNS[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle]` |
| SA:constructor=greedy_setup_amortization_by_quantity | 9.17% | 92808.6 | 15755 | +28.3% | `SA[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle]` |
| SA:constructor=greedy_earliest_deadline_setup_aware | 11.35% | 94653.4 | 16186 | +26.8% | `SA[constructor=greedy_earliest_deadline_setup_aware, neighborhood=capacity_based_setup_toggle]` |
| VNS:constructor=greedy_setup_amortization_by_quantity | 11.39% | 94666.6 | 15833 | +26.8% | `VNS[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle]` |
| ILS:constructor=greedy_setup_amortization_by_quantity | 12.29% | 95331.6 | 15296 | +26.3% | `ILS[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| SA:constructor=greedy_capacity_balancing_pressure | 12.83% | 96031.3 | 17244 | +25.8% | `SA[constructor=greedy_capacity_balancing_pressure, neighborhood=capacity_based_setup_toggle]` |
| default:SA | 13.64% | 96835.9 | 18192 | +25.2% | `SA[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle]` |
| VNS:constructor=greedy_capacity_balancing_pressure | 15.99% | 98651.2 | 16978 | +23.8% | `VNS[constructor=greedy_capacity_balancing_pressure, neighborhood=capacity_based_setup_toggle]` |
| VNS:constructor=greedy_earliest_deadline_setup_aware | 17.45% | 99984.0 | 17963 | +22.7% | `VNS[constructor=greedy_earliest_deadline_setup_aware, neighborhood=capacity_based_setup_toggle]` |
| default:VNS | 18.57% | 100866.3 | 18396 | +22.0% | `VNS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle]` |
| SA:constructor=rolling_urgency_constructor | 20.04% | 102174.2 | 18523 | +21.0% | `SA[constructor=rolling_urgency_constructor, neighborhood=capacity_based_setup_toggle]` |
| ILS:constructor=greedy_capacity_balancing_pressure | 22.24% | 104278.8 | 20230 | +19.4% | `ILS[constructor=greedy_capacity_balancing_pressure, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| ILS:constructor=greedy_earliest_deadline_setup_aware | 22.25% | 104285.0 | 20567 | +19.4% | `ILS[constructor=greedy_earliest_deadline_setup_aware, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| default:ILS | 23.57% | 105450.4 | 20928 | +18.5% | `ILS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| ILS:perturbation=congestion_based_setup_swap | 27.07% | 108090.9 | 19511 | +16.5% | `ILS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle, perturbation=congestion_based_setup_swap]` |
| ILS:perturbation=item_window_compaction | 31.37% | 112412.7 | 25309 | +13.1% | `ILS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle, perturbation=item_window_compaction]` |
| VNS:constructor=rolling_urgency_constructor | 31.69% | 112061.8 | 21312 | +13.4% | `VNS[constructor=rolling_urgency_constructor, neighborhood=capacity_based_setup_toggle]` |
| ILS:constructor=rolling_urgency_constructor | 33.12% | 112884.5 | 17899 | +12.8% | `ILS[constructor=rolling_urgency_constructor, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| ILS:neighborhood=single_item_two_period_swap | 37.98% | 117590.2 | 22769 | +9.1% | `ILS[constructor=rcl_capacity_balancer, neighborhood=single_item_two_period_swap, perturbation=adjacent_setup_relocation]` |
| SA:neighborhood=single_item_two_period_swap | 46.48% | 125069.0 | 26180 | +3.3% | `SA[constructor=rcl_capacity_balancer, neighborhood=single_item_two_period_swap]` |

Ganancia del afinado sobre el mejor default: **+0.23%**; gana en 3/5 instancias de test. Esqueletos explorados: ILS × 17, SA × 12, VNS × 11.
