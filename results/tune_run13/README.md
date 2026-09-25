### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1070 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `backward_capacity_balancer`, `period_first_slack_packer`, `randomized_rcl_repair_constructor`, `congested_period_destruction`, `item_chain_destruction`, `low_utility_setup_destruction`, `capacity_congestion_aware`, `setup_and_holding_tradeoff`, `urgency_first_lookahead`, `compress_setup_pair`, `compress_setup_triple`, `drop_redundant_late_setup`, `bottleneck_swap_perturbation`, `destroy_repair_window_perturbation`, `forward_shift_setup_perturbation`

**Mejor en train**: `SA[constructor=greedy_urgency_first_lookahead, neighborhood=compress_setup_triple]` = 0.6690 (mejor default: 0.7256, `SA[constructor=backward_capacity_balancer, neighborhood=compress_setup_pair]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.44%** | **88746.4** | 14882 | +31.4% | `SA[constructor=greedy_urgency_first_lookahead, neighborhood=compress_setup_triple]` |
| SA:constructor=greedy_capacity_congestion_aware | 9.01% | 92758.6 | 16679 | +28.3% | `SA[constructor=greedy_capacity_congestion_aware, neighborhood=compress_setup_pair]` |
| default:SA | 9.91% | 93657.2 | 17413 | +27.6% | `SA[constructor=backward_capacity_balancer, neighborhood=compress_setup_pair]` |
| SA:neighborhood=drop_redundant_late_setup | 9.93% | 93506.9 | 16516 | +27.7% | `SA[constructor=backward_capacity_balancer, neighborhood=drop_redundant_late_setup]` |
| SA:constructor=greedy_setup_and_holding_tradeoff | 10.54% | 93849.0 | 14945 | +27.5% | `SA[constructor=greedy_setup_and_holding_tradeoff, neighborhood=compress_setup_pair]` |
| SA:neighborhood=compress_setup_triple | 11.24% | 94534.2 | 15998 | +26.9% | `SA[constructor=backward_capacity_balancer, neighborhood=compress_setup_triple]` |
| ILS:constructor=greedy_setup_and_holding_tradeoff | 11.49% | 94630.0 | 14972 | +26.9% | `ILS[constructor=greedy_setup_and_holding_tradeoff, neighborhood=compress_setup_pair, perturbation=bottleneck_swap_perturbation]` |
| VNS:constructor=greedy_setup_and_holding_tradeoff | 12.07% | 95113.9 | 15053 | +26.5% | `VNS[constructor=greedy_setup_and_holding_tradeoff, neighborhood=compress_setup_pair]` |
| SA:constructor=greedy_urgency_first_lookahead | 13.28% | 96195.2 | 15445 | +25.7% | `SA[constructor=greedy_urgency_first_lookahead, neighborhood=compress_setup_pair]` |
| ILS:constructor=greedy_urgency_first_lookahead | 13.98% | 96741.6 | 15220 | +25.2% | `ILS[constructor=greedy_urgency_first_lookahead, neighborhood=compress_setup_pair, perturbation=bottleneck_swap_perturbation]` |
| VNS:constructor=greedy_urgency_first_lookahead | 14.05% | 96816.6 | 15345 | +25.2% | `VNS[constructor=greedy_urgency_first_lookahead, neighborhood=compress_setup_pair]` |
| SA:constructor=period_first_slack_packer | 14.28% | 97003.5 | 16109 | +25.0% | `SA[constructor=period_first_slack_packer, neighborhood=compress_setup_pair]` |
| default:VNS | 14.30% | 97260.0 | 17144 | +24.8% | `VNS[constructor=backward_capacity_balancer, neighborhood=compress_setup_pair]` |
| VNS:constructor=greedy_capacity_congestion_aware | 14.71% | 97685.5 | 18061 | +24.5% | `VNS[constructor=greedy_capacity_congestion_aware, neighborhood=compress_setup_pair]` |
| VNS:neighborhood=drop_redundant_late_setup | 15.34% | 98167.9 | 17861 | +24.1% | `VNS[constructor=backward_capacity_balancer, neighborhood=drop_redundant_late_setup]` |
| ILS:perturbation=destroy_repair_window_perturbation | 16.79% | 99556.3 | 18979 | +23.1% | `ILS[constructor=backward_capacity_balancer, neighborhood=compress_setup_pair, perturbation=destroy_repair_window_perturbation]` |
| VNS:neighborhood=compress_setup_triple | 17.91% | 100367.9 | 18442 | +22.4% | `VNS[constructor=backward_capacity_balancer, neighborhood=compress_setup_triple]` |
| SA:constructor=randomized_rcl_repair_constructor | 20.38% | 102111.3 | 15885 | +21.1% | `SA[constructor=randomized_rcl_repair_constructor, neighborhood=compress_setup_pair]` |
| ILS:constructor=greedy_capacity_congestion_aware | 21.27% | 103438.3 | 20119 | +20.1% | `ILS[constructor=greedy_capacity_congestion_aware, neighborhood=compress_setup_pair, perturbation=bottleneck_swap_perturbation]` |
| VNS:constructor=period_first_slack_packer | 24.82% | 106179.1 | 19540 | +17.9% | `VNS[constructor=period_first_slack_packer, neighborhood=compress_setup_pair]` |
| VNS:constructor=randomized_rcl_repair_constructor | 25.28% | 106139.1 | 15981 | +18.0% | `VNS[constructor=randomized_rcl_repair_constructor, neighborhood=compress_setup_pair]` |
| ILS:neighborhood=drop_redundant_late_setup | 27.21% | 108685.6 | 21856 | +16.0% | `ILS[constructor=backward_capacity_balancer, neighborhood=drop_redundant_late_setup, perturbation=bottleneck_swap_perturbation]` |
| default:ILS | 27.43% | 108749.8 | 21040 | +16.0% | `ILS[constructor=backward_capacity_balancer, neighborhood=compress_setup_pair, perturbation=bottleneck_swap_perturbation]` |
| ILS:perturbation=forward_shift_setup_perturbation | 29.32% | 110061.3 | 19579 | +14.9% | `ILS[constructor=backward_capacity_balancer, neighborhood=compress_setup_pair, perturbation=forward_shift_setup_perturbation]` |
| ILS:neighborhood=compress_setup_triple | 30.07% | 110502.7 | 18267 | +14.6% | `ILS[constructor=backward_capacity_balancer, neighborhood=compress_setup_triple, perturbation=bottleneck_swap_perturbation]` |
| ILS:constructor=randomized_rcl_repair_constructor | 33.91% | 113366.1 | 16554 | +12.4% | `ILS[constructor=randomized_rcl_repair_constructor, neighborhood=compress_setup_pair, perturbation=bottleneck_swap_perturbation]` |
| ILS:constructor=period_first_slack_packer | 35.41% | 115098.3 | 20912 | +11.0% | `ILS[constructor=period_first_slack_packer, neighborhood=compress_setup_pair, perturbation=bottleneck_swap_perturbation]` |

Ganancia del afinado sobre el mejor default: **+4.33%**; gana en 5/5 instancias de test. Esqueletos explorados: SA × 21, VNS × 11, ILS × 8.
