## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.90% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| r1 | 1 | 1.54% | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| r2 | 2 | 0.62% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |

**Afinado entre réplicas**: media 1.02%, desvío 0.38%, rango [0.62%, 1.54%].

**Mejor no afinado** (media entre réplicas): `LNS_MIP:constructor=greedy_immediate_setup_cost_first` = 0.91%. Afinado vs ese: -0.11% de gap a favor del afinado, IC95 [-0.51%, +0.27%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 5 configuraciones fallidas · 4082 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `period_chunk_destruction`, `setup_intensity_destruction`, `uniform_random_destruction`, `capacity_pressure_with_demand_horizon`, `immediate_setup_cost_first`, `inventory_balance_and_setup_sparsity`, `single_setup_flip`, `biased_ruin_and_repair_kick`, `column_shuffle_kick`, `period_block_complement_kick`

**Mejor en train**: `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` = 0.5172 (mejor default: 0.5204, `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.90%** | **86771.1** | 15779 | +46.7% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| LNS_MIP:constructor=greedy_immediate_setup_cost_first | 0.67% | 86516.6 | 15437 | +46.9% | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=period_chunk_destruction]` |
| LNS_MIP:constructor=greedy_inventory_balance_and_setup_sparsity | 1.20% | 87040.2 | 15976 | +46.6% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=period_chunk_destruction]` |
| LNS_MIP:destruction=uniform_random_destruction | 1.50% | 87302.0 | 15982 | +46.4% | `LNS_MIP[constructor=trivial, destruction=uniform_random_destruction]` |
| LNS_MIP:constructor=greedy_capacity_pressure_with_demand_horizon | 2.28% | 87947.7 | 16124 | +46.0% | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| default:LNS_MIP | 2.57% | 88179.5 | 16090 | +45.9% | `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]` |
| SA:constructor=greedy_immediate_setup_cost_first | 9.93% | 94433.7 | 16561 | +42.0% | `SA[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
| SA:constructor=greedy_inventory_balance_and_setup_sparsity | 11.72% | 96086.0 | 17616 | +41.0% | `SA[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_immediate_setup_cost_first | 13.66% | 97649.2 | 17370 | +40.1% | `VNS[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_inventory_balance_and_setup_sparsity | 16.54% | 100413.4 | 19770 | +38.4% | `VNS[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip]` |
| ILS:constructor=greedy_immediate_setup_cost_first | 17.21% | 100514.5 | 16890 | +38.3% | `ILS[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| default:SA | 19.37% | 102478.5 | 17762 | +37.1% | `SA[constructor=trivial, neighborhood=single_setup_flip]` |
| SA:constructor=greedy_capacity_pressure_with_demand_horizon | 19.39% | 102493.2 | 17741 | +37.1% | `SA[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip]` |
| LNS_MIP:destruction=setup_intensity_destruction | 23.73% | 107240.8 | 25284 | +34.2% | `LNS_MIP[constructor=trivial, destruction=setup_intensity_destruction]` |
| default:VNS | 25.69% | 108006.7 | 19634 | +33.7% | `VNS[constructor=trivial, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_capacity_pressure_with_demand_horizon | 25.77% | 107840.2 | 18513 | +33.8% | `VNS[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip]` |
| ILS:constructor=greedy_inventory_balance_and_setup_sparsity | 30.18% | 111760.1 | 19572 | +31.4% | `ILS[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| ILS:perturbation=column_shuffle_kick | 43.88% | 123352.8 | 21039 | +24.3% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=column_shuffle_kick]` |
| ILS:perturbation=period_block_complement_kick | 58.93% | 136208.3 | 22492 | +16.4% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=period_block_complement_kick]` |
| default:ILS | 60.84% | 137566.6 | 20533 | +15.6% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| ILS:constructor=greedy_capacity_pressure_with_demand_horizon | 60.97% | 137671.1 | 20496 | +15.5% | `ILS[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| LNS_MIP:constructor=random | 619402990.14% | 533333372147.4 | 498887610076 | -327322991.9% | `LNS_MIP[constructor=random, destruction=period_chunk_destruction]` |
| SA:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=single_setup_flip]` |
| ILS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| VNS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=single_setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.29%**; gana en 5/10 instancias de test. Esqueletos explorados: LNS_MIP × 22, SA × 6, ILS × 6, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_immediate_setup_cost_first` (mejor default por gap): -0.23% de gap a favor del afinado, IC95 [-0.69%, +0.19%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 18 ✔ | 0.5172 | 0.5159, 0.5178, 0.5159, 0.5172, 0.5181, 0.5184 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| 23 (numéricos por defecto) | 0.5182 | 0.5194, 0.5170, 0.5181 | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=uniform_random_destruction]` |
| 18 (numéricos por defecto) | 0.5192 | 0.5187, 0.5204, 0.5185 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| 23 | 0.5197 | 0.5187, 0.5189, 0.5216 | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=uniform_random_destruction]` |
| 15 | 0.5233 | 0.5204, 0.5368, 0.5170, 0.5213, 0.5184, 0.5262 | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| 3* | 0.5250 | 0.5204, 0.5368, 0.5170, 0.5260 | `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]` |
| 33 | 0.5542 | 0.5546, 0.5554, 0.5526 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=setup_intensity_destruction]` |
| 33 (numéricos por defecto) | 0.5703 | 0.5732, 0.5669, 0.5708 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=setup_intensity_destruction]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 5 configuraciones fallidas · 6854 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `period_chunk_destruction`, `setup_intensity_destruction`, `uniform_random_destruction`, `capacity_pressure_with_demand_horizon`, `immediate_setup_cost_first`, `inventory_balance_and_setup_sparsity`, `single_setup_flip`, `biased_ruin_and_repair_kick`, `column_shuffle_kick`, `period_block_complement_kick`

**Mejor en train**: `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` = 0.5179 (mejor default: 0.5323, `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.54%** | **87325.3** | 15985 | +46.4% | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| LNS_MIP:constructor=greedy_immediate_setup_cost_first | 1.04% | 86906.0 | 16046 | +46.7% | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=period_chunk_destruction]` |
| LNS_MIP:constructor=greedy_inventory_balance_and_setup_sparsity | 1.56% | 87338.6 | 16043 | +46.4% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=period_chunk_destruction]` |
| LNS_MIP:destruction=uniform_random_destruction | 1.96% | 87744.4 | 16384 | +46.1% | `LNS_MIP[constructor=trivial, destruction=uniform_random_destruction]` |
| LNS_MIP:constructor=greedy_capacity_pressure_with_demand_horizon | 3.62% | 89133.3 | 16663 | +45.3% | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| default:LNS_MIP | 3.78% | 89310.0 | 17018 | +45.2% | `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]` |
| SA:constructor=greedy_immediate_setup_cost_first | 11.69% | 95989.8 | 17206 | +41.1% | `SA[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_immediate_setup_cost_first | 13.81% | 97691.3 | 16774 | +40.0% | `VNS[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
| SA:constructor=greedy_inventory_balance_and_setup_sparsity | 15.86% | 99695.4 | 18621 | +38.8% | `SA[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip]` |
| ILS:constructor=greedy_immediate_setup_cost_first | 19.06% | 102001.5 | 16701 | +37.4% | `ILS[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| VNS:constructor=greedy_inventory_balance_and_setup_sparsity | 21.24% | 104365.2 | 20148 | +35.9% | `VNS[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip]` |
| LNS_MIP:destruction=setup_intensity_destruction | 25.92% | 109015.0 | 24861 | +33.1% | `LNS_MIP[constructor=trivial, destruction=setup_intensity_destruction]` |
| default:SA | 27.95% | 109797.0 | 18692 | +32.6% | `SA[constructor=trivial, neighborhood=single_setup_flip]` |
| SA:constructor=greedy_capacity_pressure_with_demand_horizon | 28.04% | 109859.5 | 18597 | +32.6% | `SA[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip]` |
| ILS:constructor=greedy_inventory_balance_and_setup_sparsity | 32.51% | 113729.0 | 19741 | +30.2% | `ILS[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| default:VNS | 32.55% | 114032.4 | 21722 | +30.0% | `VNS[constructor=trivial, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_capacity_pressure_with_demand_horizon | 33.63% | 114460.1 | 18436 | +29.8% | `VNS[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip]` |
| ILS:perturbation=period_block_complement_kick | 49.21% | 128175.5 | 23196 | +21.3% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=period_block_complement_kick]` |
| ILS:perturbation=column_shuffle_kick | 50.33% | 129213.2 | 23850 | +20.7% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=column_shuffle_kick]` |
| ILS:constructor=greedy_capacity_pressure_with_demand_horizon | 69.04% | 144580.7 | 21619 | +11.3% | `ILS[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| default:ILS | 69.11% | 144641.0 | 21654 | +11.2% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| LNS_MIP:constructor=random | 619402990.33% | 533333372365.5 | 498887609843 | -327322992.0% | `LNS_MIP[constructor=random, destruction=period_chunk_destruction]` |
| SA:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=single_setup_flip]` |
| ILS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| VNS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=single_setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.48%**; gana en 2/10 instancias de test. Esqueletos explorados: LNS_MIP × 20, SA × 7, ILS × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_immediate_setup_cost_first` (mejor default por gap): -0.50% de gap a favor del afinado, IC95 [-1.01%, +0.02%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 17 ✔ | 0.5179 | 0.5224, 0.5173, 0.5174, 0.5149, 0.5187, 0.5188, 0.5159 | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| 28 | 0.5193 | 0.5174, 0.5186, 0.5203, 0.5211, 0.5224, 0.5177, 0.5177 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| 39 | 0.5194 | 0.5208, 0.5174, 0.5203, 0.5199, 0.5211, 0.5171, 0.5188 | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=uniform_random_destruction]` |
| 39 (numéricos por defecto) | 0.5202 | 0.5219, 0.5184, 0.5189, 0.5209, 0.5202, 0.5200, 0.5211 | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=uniform_random_destruction]` |
| 23 | 0.5207 | 0.5153, 0.5214, 0.5252, 0.5156, 0.5183, 0.5304, 0.5186 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=period_chunk_destruction]` |
| 28 (numéricos por defecto) | 0.5208 | 0.5214, 0.5212, 0.5173, 0.5202, 0.5224, 0.5220 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| 23 (numéricos por defecto) | 0.5209 | 0.5268, 0.5233, 0.5177, 0.5163, 0.5182, 0.5257, 0.5184 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=period_chunk_destruction]` |
| 17 (numéricos por defecto) | 0.5346 | 0.5323, 0.5457, 0.5256 | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| 3* | 0.5359 | 0.5323, 0.5458, 0.5296 | `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp_setups 10x15) · 5 configuraciones fallidas · 4204 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `period_chunk_destruction`, `setup_intensity_destruction`, `uniform_random_destruction`, `capacity_pressure_with_demand_horizon`, `immediate_setup_cost_first`, `inventory_balance_and_setup_sparsity`, `single_setup_flip`, `biased_ruin_and_repair_kick`, `column_shuffle_kick`, `period_block_complement_kick`

**Mejor en train**: `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` = 0.5157 (mejor default: 0.5342, `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.62%** | **86479.4** | 15398 | +46.9% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| LNS_MIP:constructor=greedy_immediate_setup_cost_first | 1.04% | 86906.0 | 16046 | +46.7% | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=period_chunk_destruction]` |
| LNS_MIP:constructor=greedy_inventory_balance_and_setup_sparsity | 1.55% | 87329.1 | 16034 | +46.4% | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=period_chunk_destruction]` |
| LNS_MIP:destruction=uniform_random_destruction | 1.91% | 87701.2 | 16369 | +46.2% | `LNS_MIP[constructor=trivial, destruction=uniform_random_destruction]` |
| LNS_MIP:constructor=greedy_capacity_pressure_with_demand_horizon | 3.35% | 88890.6 | 16491 | +45.4% | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| default:LNS_MIP | 3.78% | 89310.0 | 17018 | +45.2% | `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]` |
| SA:constructor=greedy_immediate_setup_cost_first | 11.16% | 95537.1 | 17133 | +41.4% | `SA[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
| SA:constructor=greedy_inventory_balance_and_setup_sparsity | 14.22% | 98272.3 | 18240 | +39.7% | `SA[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_immediate_setup_cost_first | 14.91% | 98611.7 | 16671 | +39.5% | `VNS[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
| ILS:constructor=greedy_immediate_setup_cost_first | 18.39% | 101513.5 | 17018 | +37.7% | `ILS[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| VNS:constructor=greedy_inventory_balance_and_setup_sparsity | 21.22% | 104328.7 | 20564 | +36.0% | `VNS[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip]` |
| default:SA | 24.48% | 106905.1 | 18678 | +34.4% | `SA[constructor=trivial, neighborhood=single_setup_flip]` |
| SA:constructor=greedy_capacity_pressure_with_demand_horizon | 24.52% | 106939.4 | 18669 | +34.4% | `SA[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip]` |
| LNS_MIP:destruction=setup_intensity_destruction | 25.75% | 108875.5 | 24912 | +33.2% | `LNS_MIP[constructor=trivial, destruction=setup_intensity_destruction]` |
| default:VNS | 30.85% | 112453.2 | 20812 | +31.0% | `VNS[constructor=trivial, neighborhood=single_setup_flip]` |
| VNS:constructor=greedy_capacity_pressure_with_demand_horizon | 31.61% | 112834.6 | 19186 | +30.7% | `VNS[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip]` |
| ILS:constructor=greedy_inventory_balance_and_setup_sparsity | 32.08% | 113367.0 | 19784 | +30.4% | `ILS[constructor=greedy_inventory_balance_and_setup_sparsity, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| ILS:perturbation=period_block_complement_kick | 51.32% | 129678.3 | 21334 | +20.4% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=period_block_complement_kick]` |
| ILS:perturbation=column_shuffle_kick | 51.44% | 129745.6 | 22081 | +20.4% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=column_shuffle_kick]` |
| ILS:constructor=greedy_capacity_pressure_with_demand_horizon | 66.81% | 142701.0 | 21529 | +12.4% | `ILS[constructor=greedy_capacity_pressure_with_demand_horizon, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| default:ILS | 66.88% | 142732.9 | 21363 | +12.4% | `ILS[constructor=trivial, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| LNS_MIP:constructor=random | 619402990.33% | 533333372365.5 | 498887609843 | -327322992.0% | `LNS_MIP[constructor=random, destruction=period_chunk_destruction]` |
| SA:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `SA[constructor=random, neighborhood=single_setup_flip]` |
| ILS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `ILS[constructor=random, neighborhood=single_setup_flip, perturbation=biased_ruin_and_repair_kick]` |
| VNS:constructor=random | 1195892942.41% | 1000000000000.0 | 0 | -613730652.6% | `VNS[constructor=random, neighborhood=single_setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.49%**; gana en 6/10 instancias de test. Esqueletos explorados: LNS_MIP × 20, SA × 7, ILS × 7, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_immediate_setup_cost_first` (mejor default por gap): +0.42% de gap a favor del afinado, IC95 [-0.14%, +1.07%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 21 ✔ | 0.5157 | 0.5157, 0.5156, 0.5149, 0.5164, 0.5161 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| 25 | 0.5179 | 0.5174, 0.5181, 0.5180 | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=uniform_random_destruction]` |
| 25 (numéricos por defecto) | 0.5197 | 0.5200, 0.5201, 0.5189 | `LNS_MIP[constructor=greedy_immediate_setup_cost_first, destruction=uniform_random_destruction]` |
| 21 (numéricos por defecto) | 0.5206 | 0.5215, 0.5228, 0.5174 | `LNS_MIP[constructor=greedy_inventory_balance_and_setup_sparsity, destruction=uniform_random_destruction]` |
| 17 (numéricos por defecto) | 0.5245 | 0.5342, 0.5257, 0.5188, 0.5148, 0.5291 | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| 3* | 0.5281 | 0.5342, 0.5257, 0.5244 | `LNS_MIP[constructor=trivial, destruction=period_chunk_destruction]` |
| 17 | 0.5290 | 0.5240, 0.5378, 0.5251 | `LNS_MIP[constructor=greedy_capacity_pressure_with_demand_horizon, destruction=period_chunk_destruction]` |
| 12 | 0.5719 | 0.5720, 0.5746, 0.5693 | `SA[constructor=greedy_immediate_setup_cost_first, neighborhood=single_setup_flip]` |
