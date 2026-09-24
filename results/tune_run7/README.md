### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1143 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `rcl_capacity_balancer`, `rolling_urgency_constructor`, `congested_period_destruction`, `critical_item_chain_destruction`, `low_utility_setup_destruction`, `capacity_balancing_pressure`, `earliest_deadline_setup_aware`, `setup_amortization_by_quantity`, `capacity_based_setup_toggle`, `merge_adjacent_setups`, `single_item_two_period_swap`, `adjacent_setup_relocation`, `congestion_based_setup_swap`, `item_window_compaction`

**Mejor en train**: `SA[constructor=greedy_setup_amortization_by_quantity, neighborhood=merge_adjacent_setups]` = 0.7115 (mejor default: 0.7264, `SA[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **11.90%** | **95125.6** | 16094 | +26.5% | `SA[constructor=greedy_setup_amortization_by_quantity, neighborhood=merge_adjacent_setups]` |
| SA:constructor=greedy_setup_amortization_by_quantity | 9.09% | 92741.4 | 15758 | +28.3% | `SA[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle]` |
| VNS:constructor=greedy_setup_amortization_by_quantity | 10.84% | 94129.2 | 15404 | +27.3% | `VNS[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle]` |
| SA:constructor=greedy_earliest_deadline_setup_aware | 11.37% | 94656.5 | 16045 | +26.8% | `SA[constructor=greedy_earliest_deadline_setup_aware, neighborhood=capacity_based_setup_toggle]` |
| SA:constructor=greedy_capacity_balancing_pressure | 13.28% | 96388.9 | 17104 | +25.5% | `SA[constructor=greedy_capacity_balancing_pressure, neighborhood=capacity_based_setup_toggle]` |
| default:SA | 14.05% | 97170.7 | 18172 | +24.9% | `SA[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle]` |
| ILS:constructor=greedy_setup_amortization_by_quantity | 14.09% | 96776.2 | 15089 | +25.2% | `ILS[constructor=greedy_setup_amortization_by_quantity, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| SA:constructor=rolling_urgency_constructor | 20.64% | 102661.2 | 18460 | +20.7% | `SA[constructor=rolling_urgency_constructor, neighborhood=capacity_based_setup_toggle]` |
| ILS:constructor=greedy_capacity_balancing_pressure | 34.94% | 114920.5 | 21555 | +11.2% | `ILS[constructor=greedy_capacity_balancing_pressure, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| ILS:constructor=greedy_earliest_deadline_setup_aware | 35.70% | 115228.4 | 18974 | +10.9% | `ILS[constructor=greedy_earliest_deadline_setup_aware, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| VNS:constructor=greedy_capacity_balancing_pressure | 36.28% | 116049.5 | 21622 | +10.3% | `VNS[constructor=greedy_capacity_balancing_pressure, neighborhood=capacity_based_setup_toggle]` |
| VNS:constructor=greedy_earliest_deadline_setup_aware | 38.56% | 118018.3 | 21744 | +8.8% | `VNS[constructor=greedy_earliest_deadline_setup_aware, neighborhood=capacity_based_setup_toggle]` |
| ILS:neighborhood=merge_adjacent_setups | 40.32% | 119455.5 | 22596 | +7.7% | `ILS[constructor=rcl_capacity_balancer, neighborhood=merge_adjacent_setups, perturbation=adjacent_setup_relocation]` |
| default:VNS | 40.50% | 119736.8 | 23224 | +7.5% | `VNS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle]` |
| default:ILS | 42.98% | 122319.3 | 26906 | +5.5% | `ILS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| ILS:neighborhood=single_item_two_period_swap | 43.95% | 122659.4 | 23823 | +5.2% | `ILS[constructor=rcl_capacity_balancer, neighborhood=single_item_two_period_swap, perturbation=adjacent_setup_relocation]` |
| ILS:perturbation=congestion_based_setup_swap | 45.33% | 123796.8 | 23615 | +4.3% | `ILS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle, perturbation=congestion_based_setup_swap]` |
| ILS:perturbation=item_window_compaction | 46.11% | 124926.9 | 27336 | +3.5% | `ILS[constructor=rcl_capacity_balancer, neighborhood=capacity_based_setup_toggle, perturbation=item_window_compaction]` |
| SA:neighborhood=single_item_two_period_swap | 46.54% | 125125.7 | 26230 | +3.3% | `SA[constructor=rcl_capacity_balancer, neighborhood=single_item_two_period_swap]` |
| VNS:neighborhood=single_item_two_period_swap | 48.78% | 127040.7 | 26562 | +1.8% | `VNS[constructor=rcl_capacity_balancer, neighborhood=single_item_two_period_swap]` |
| VNS:neighborhood=merge_adjacent_setups | 48.98% | 127130.9 | 26235 | +1.7% | `VNS[constructor=rcl_capacity_balancer, neighborhood=merge_adjacent_setups]` |
| SA:neighborhood=merge_adjacent_setups | 51.22% | 129112.1 | 27253 | +0.2% | `SA[constructor=rcl_capacity_balancer, neighborhood=merge_adjacent_setups]` |
| ILS:constructor=rolling_urgency_constructor | 58.98% | 134693.3 | 20072 | -4.1% | `ILS[constructor=rolling_urgency_constructor, neighborhood=capacity_based_setup_toggle, perturbation=adjacent_setup_relocation]` |
| VNS:constructor=rolling_urgency_constructor | 61.21% | 136623.5 | 20585 | -5.6% | `VNS[constructor=rolling_urgency_constructor, neighborhood=capacity_based_setup_toggle]` |

Ganancia del afinado sobre el mejor default: **-2.57%**; gana en 1/5 instancias de test. Esqueletos explorados: ILS × 18, SA × 12, VNS × 10.
