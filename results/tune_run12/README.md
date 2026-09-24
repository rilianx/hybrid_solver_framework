### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1052 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `critical_period_repair_constructor`, `greedy_capacity_shifting`, `windowed_lookahead_balancing`, `capacidad_concentrada`, `items_cronicos`, `setup_poco_efectivo`, `capacity_balance_pressure`, `earliness_holding_tradeoff`, `marginal_setup_savings`, `left_shift_merge`, `period_capacity_swap`, `window_block_removal`, `bottleneck_period_repair`, `window_merge_and_shift`

**Mejor en train**: `SA[constructor=windowed_lookahead_balancing, neighborhood=left_shift_merge]` = 0.6741 (mejor default: 0.6868, `SA[constructor=critical_period_repair_constructor, neighborhood=left_shift_merge]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **6.42%** | **90690.8** | 16071 | +29.9% | `SA[constructor=windowed_lookahead_balancing, neighborhood=left_shift_merge]` |
| SA:constructor=windowed_lookahead_balancing | 7.28% | 91494.3 | 16768 | +29.3% | `SA[constructor=windowed_lookahead_balancing, neighborhood=left_shift_merge]` |
| default:SA | 8.11% | 92280.8 | 17580 | +28.7% | `SA[constructor=critical_period_repair_constructor, neighborhood=left_shift_merge]` |
| SA:constructor=greedy_earliness_holding_tradeoff | 8.34% | 92322.0 | 16538 | +28.7% | `SA[constructor=greedy_earliness_holding_tradeoff, neighborhood=left_shift_merge]` |
| SA:constructor=greedy_capacity_balance_pressure | 8.51% | 92494.7 | 16834 | +28.5% | `SA[constructor=greedy_capacity_balance_pressure, neighborhood=left_shift_merge]` |
| SA:constructor=greedy_capacity_shifting | 8.82% | 92856.9 | 17449 | +28.2% | `SA[constructor=greedy_capacity_shifting, neighborhood=left_shift_merge]` |
| SA:constructor=greedy_marginal_setup_savings | 9.48% | 93298.0 | 16609 | +27.9% | `SA[constructor=greedy_marginal_setup_savings, neighborhood=left_shift_merge]` |
| ILS:constructor=greedy_capacity_balance_pressure | 9.60% | 93421.2 | 16871 | +27.8% | `ILS[constructor=greedy_capacity_balance_pressure, neighborhood=left_shift_merge, perturbation=bottleneck_period_repair]` |
| ILS:constructor=greedy_marginal_setup_savings | 10.71% | 94299.7 | 16496 | +27.1% | `ILS[constructor=greedy_marginal_setup_savings, neighborhood=left_shift_merge, perturbation=bottleneck_period_repair]` |
| VNS:constructor=greedy_capacity_balance_pressure | 10.84% | 94478.0 | 16953 | +27.0% | `VNS[constructor=greedy_capacity_balance_pressure, neighborhood=left_shift_merge]` |
| VNS:constructor=greedy_marginal_setup_savings | 11.76% | 95173.1 | 16532 | +26.4% | `VNS[constructor=greedy_marginal_setup_savings, neighborhood=left_shift_merge]` |
| VNS:constructor=windowed_lookahead_balancing | 13.97% | 97115.5 | 17364 | +24.9% | `VNS[constructor=windowed_lookahead_balancing, neighborhood=left_shift_merge]` |
| default:VNS | 15.49% | 98653.1 | 19264 | +23.8% | `VNS[constructor=critical_period_repair_constructor, neighborhood=left_shift_merge]` |
| ILS:perturbation=window_merge_and_shift | 15.73% | 98700.1 | 18751 | +23.7% | `ILS[constructor=critical_period_repair_constructor, neighborhood=left_shift_merge, perturbation=window_merge_and_shift]` |
| VNS:constructor=greedy_earliness_holding_tradeoff | 16.92% | 99879.6 | 19965 | +22.8% | `VNS[constructor=greedy_earliness_holding_tradeoff, neighborhood=left_shift_merge]` |
| VNS:constructor=greedy_capacity_shifting | 17.98% | 100608.5 | 18800 | +22.2% | `VNS[constructor=greedy_capacity_shifting, neighborhood=left_shift_merge]` |
| ILS:constructor=windowed_lookahead_balancing | 21.81% | 103514.7 | 16644 | +20.0% | `ILS[constructor=windowed_lookahead_balancing, neighborhood=left_shift_merge, perturbation=bottleneck_period_repair]` |
| default:ILS | 25.72% | 107346.1 | 20654 | +17.0% | `ILS[constructor=critical_period_repair_constructor, neighborhood=left_shift_merge, perturbation=bottleneck_period_repair]` |
| ILS:constructor=greedy_capacity_shifting | 26.40% | 108042.0 | 21633 | +16.5% | `ILS[constructor=greedy_capacity_shifting, neighborhood=left_shift_merge, perturbation=bottleneck_period_repair]` |
| ILS:constructor=greedy_earliness_holding_tradeoff | 29.01% | 110052.1 | 20849 | +14.9% | `ILS[constructor=greedy_earliness_holding_tradeoff, neighborhood=left_shift_merge, perturbation=bottleneck_period_repair]` |
| SA:neighborhood=window_block_removal | 32.23% | 112989.4 | 22120 | +12.7% | `SA[constructor=critical_period_repair_constructor, neighborhood=window_block_removal]` |
| VNS:neighborhood=window_block_removal | 32.43% | 112987.1 | 20997 | +12.7% | `VNS[constructor=critical_period_repair_constructor, neighborhood=window_block_removal]` |
| ILS:neighborhood=period_capacity_swap | 35.13% | 114976.7 | 20183 | +11.1% | `ILS[constructor=critical_period_repair_constructor, neighborhood=period_capacity_swap, perturbation=bottleneck_period_repair]` |
| ILS:neighborhood=window_block_removal | 36.92% | 117053.9 | 23382 | +9.5% | `ILS[constructor=critical_period_repair_constructor, neighborhood=window_block_removal, perturbation=bottleneck_period_repair]` |
| VNS:neighborhood=period_capacity_swap | 40.58% | 119604.2 | 20253 | +7.6% | `VNS[constructor=critical_period_repair_constructor, neighborhood=period_capacity_swap]` |
| SA:neighborhood=period_capacity_swap | 40.98% | 120096.6 | 21481 | +7.2% | `SA[constructor=critical_period_repair_constructor, neighborhood=period_capacity_swap]` |

Ganancia del afinado sobre el mejor default: **+0.88%**; gana en 4/5 instancias de test. Esqueletos explorados: SA × 24, ILS × 10, VNS × 6.
