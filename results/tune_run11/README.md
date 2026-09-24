### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 5 configuraciones fallidas · 1010 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `reverse_greedy_all_setups_pruning`, `congested_period_destruction`, `item_chain_destruction`, `low_utility_setup_destruction`, `capacity_slack_preserver`, `setup_consolidation_bias`, `urgent_cost_per_unit`, `backward_merge_shift`, `double_retiming_block_move`, `same_period_setup_swap`, `backward_setup_shift_kick`, `capacity_swap_kick`, `period_block_destroy_repair`

**Mejor en train**: `SA[constructor=greedy_urgent_cost_per_unit, neighborhood=same_period_setup_swap]` = 0.6929 (mejor default: 0.7349, `SA[constructor=reverse_greedy_all_setups_pruning, neighborhood=double_retiming_block_move]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **6.41%** | **90336.9** | 14536 | +30.2% | `SA[constructor=greedy_urgent_cost_per_unit, neighborhood=same_period_setup_swap]` |
| SA:constructor=greedy_urgent_cost_per_unit | 6.33% | 90538.0 | 16377 | +30.0% | `SA[constructor=greedy_urgent_cost_per_unit, neighborhood=double_retiming_block_move]` |
| VNS:constructor=greedy_urgent_cost_per_unit | 8.33% | 92163.3 | 16024 | +28.8% | `VNS[constructor=greedy_urgent_cost_per_unit, neighborhood=double_retiming_block_move]` |
| ILS:constructor=greedy_urgent_cost_per_unit | 8.87% | 92633.3 | 16142 | +28.4% | `ILS[constructor=greedy_urgent_cost_per_unit, neighborhood=backward_merge_shift, perturbation=backward_setup_shift_kick]` |
| SA:constructor=greedy_setup_consolidation_bias | 9.41% | 93204.0 | 17286 | +28.0% | `SA[constructor=greedy_setup_consolidation_bias, neighborhood=double_retiming_block_move]` |
| SA:constructor=greedy_capacity_slack_preserver | 9.65% | 93335.0 | 16775 | +27.9% | `SA[constructor=greedy_capacity_slack_preserver, neighborhood=double_retiming_block_move]` |
| default:SA | 9.73% | 93102.5 | 14656 | +28.0% | `SA[constructor=reverse_greedy_all_setups_pruning, neighborhood=double_retiming_block_move]` |
| VNS:constructor=greedy_capacity_slack_preserver | 13.52% | 96490.7 | 16295 | +25.4% | `VNS[constructor=greedy_capacity_slack_preserver, neighborhood=double_retiming_block_move]` |
| VNS:constructor=greedy_setup_consolidation_bias | 13.63% | 96805.6 | 17842 | +25.2% | `VNS[constructor=greedy_setup_consolidation_bias, neighborhood=double_retiming_block_move]` |
| ILS:neighborhood=double_retiming_block_move | 14.72% | 97215.9 | 14745 | +24.9% | `ILS[constructor=reverse_greedy_all_setups_pruning, neighborhood=double_retiming_block_move, perturbation=backward_setup_shift_kick]` |
| ILS:constructor=greedy_setup_consolidation_bias | 15.28% | 98174.3 | 17809 | +24.1% | `ILS[constructor=greedy_setup_consolidation_bias, neighborhood=backward_merge_shift, perturbation=backward_setup_shift_kick]` |
| default:VNS | 15.48% | 97884.7 | 14788 | +24.4% | `VNS[constructor=reverse_greedy_all_setups_pruning, neighborhood=double_retiming_block_move]` |
| SA:neighborhood=same_period_setup_swap | 18.58% | 100292.8 | 13495 | +22.5% | `SA[constructor=reverse_greedy_all_setups_pruning, neighborhood=same_period_setup_swap]` |
| VNS:neighborhood=same_period_setup_swap | 20.55% | 101852.5 | 13190 | +21.3% | `VNS[constructor=reverse_greedy_all_setups_pruning, neighborhood=same_period_setup_swap]` |
| ILS:neighborhood=same_period_setup_swap | 22.59% | 103532.1 | 12956 | +20.0% | `ILS[constructor=reverse_greedy_all_setups_pruning, neighborhood=same_period_setup_swap, perturbation=backward_setup_shift_kick]` |
| default:ILS | 25.02% | 105480.5 | 12423 | +18.5% | `ILS[constructor=reverse_greedy_all_setups_pruning, neighborhood=backward_merge_shift, perturbation=backward_setup_shift_kick]` |
| ILS:perturbation=capacity_swap_kick | 25.14% | 105578.2 | 12430 | +18.4% | `ILS[constructor=reverse_greedy_all_setups_pruning, neighborhood=backward_merge_shift, perturbation=capacity_swap_kick]` |
| ILS:perturbation=period_block_destroy_repair | 25.14% | 105578.2 | 12430 | +18.4% | `ILS[constructor=reverse_greedy_all_setups_pruning, neighborhood=backward_merge_shift, perturbation=period_block_destroy_repair]` |
| ILS:constructor=greedy_capacity_slack_preserver | 35.70% | 115563.0 | 21186 | +10.7% | `ILS[constructor=greedy_capacity_slack_preserver, neighborhood=backward_merge_shift, perturbation=backward_setup_shift_kick]` |

Ganancia del afinado sobre el mejor default: **+0.22%**; gana en 2/5 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.
