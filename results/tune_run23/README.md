## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 5 train / 5 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 10.35% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| r1 | 1 | 11.30% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| r2 | 2 | 4.34% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |

**Afinado entre réplicas**: media 8.66%, desvío 3.08%, rango [4.34%, 11.30%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_forward_cover_cost` = 4.34%. Afinado vs ese: -4.32% de gap a favor del afinado, IC95 [-5.15%, -3.52%] sobre las instancias; el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (clsp 10x15) · 0 configuraciones fallidas · 1421 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` = 0.6977 (mejor default: 0.7172, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **10.35%** | **94020.9** | 17632 | +27.3% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.34% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 6.45% | 90389.6 | 14792 | +30.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_forward_cover_cost | 8.79% | 92471.3 | 15978 | +28.5% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 8.91% | 92636.9 | 16322 | +28.4% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.84% | 93431.7 | 16343 | +27.8% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:SA | 10.45% | 94087.7 | 17512 | +27.3% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.64% | 94222.4 | 17530 | +27.2% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 15.29% | 98153.2 | 18003 | +24.1% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 15.92% | 98849.7 | 19650 | +23.6% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 16.02% | 98925.5 | 19116 | +23.5% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:VNS | 16.07% | 98601.4 | 16662 | +23.8% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 16.45% | 99049.4 | 17736 | +23.5% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 17.41% | 99873.4 | 17687 | +22.8% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| default:ILS | 17.42% | 99843.2 | 17845 | +22.8% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 17.56% | 100253.3 | 19389 | +22.5% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 18.42% | 100814.9 | 18760 | +22.1% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 19.10% | 101672.6 | 20290 | +21.4% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| ILS:neighborhood=swap_capacity_pressure | 21.20% | 103365.3 | 20368 | +20.1% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 21.56% | 103494.3 | 19294 | +20.0% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| SA:neighborhood=shift_setup_in_time | 49.37% | 127099.6 | 22702 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-5.97%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 24, VNS × 9, ILS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -6.01% de gap a favor del afinado, IC95 [-7.46%, -4.44%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 ✔ | 0.6977 | 0.6913, 0.7031, 0.6987 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 35 | 0.6977 | 0.6913, 0.7031, 0.6987 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 30 | 0.6984 | 0.6913, 0.7031, 0.7009 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 32 | 0.6984 | 0.6913, 0.7031, 0.7009 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 30 (numéricos por defecto) | 0.7000 | 0.6938, 0.7078, 0.6983 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 31 | 0.7003 | 0.6913, 0.7031, 0.7065 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 2* | 0.7322 | 0.7172, 0.7456, 0.7337 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (clsp 10x15) · 0 configuraciones fallidas · 1497 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` = 0.7060 (mejor default: 0.7841, `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **11.27%** | **94794.3** | 17700 | +26.7% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.31% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.02% | 91720.0 | 14890 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=critical_period_seeding | 9.11% | 92839.8 | 16402 | +28.3% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.81% | 93432.6 | 16344 | +27.8% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.11% | 93593.7 | 15948 | +27.7% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.76% | 94379.2 | 17535 | +27.1% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.91% | 94494.0 | 17617 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 18.72% | 101090.9 | 18487 | +21.9% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 18.98% | 101362.1 | 18974 | +21.7% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.56% | 101617.6 | 17396 | +21.5% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| default:VNS | 19.64% | 101575.2 | 16903 | +21.5% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| default:ILS | 19.65% | 101625.8 | 17128 | +21.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 20.01% | 102282.6 | 19415 | +21.0% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| ILS:constructor=critical_period_seeding | 21.03% | 103389.3 | 21144 | +20.1% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_capacity_pressure_balance | 21.34% | 103562.4 | 20654 | +20.0% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_capacity_pressure_balance | 22.28% | 103785.8 | 17462 | +19.8% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.11% | 105696.3 | 19825 | +18.3% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.00% | 106277.6 | 18258 | +17.9% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.10% | 106459.5 | 18888 | +17.7% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 26.54% | 107893.9 | 20443 | +16.6% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 49.33% | 127101.6 | 22700 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-6.84%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 29, VNS × 6, ILS × 5.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -6.96% de gap a favor del afinado, IC95 [-8.25%, -5.70%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 25 ✔ | 0.7060 | 0.7040, 0.7022, 0.7118 | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| 38 | 0.7068 | 0.6988, 0.7110, 0.7106 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 34 | 0.7069 | 0.6988, 0.7111, 0.7106 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 35 | 0.7069 | 0.6988, 0.7113, 0.7106 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 33 | 0.7078 | 0.7008, 0.7109, 0.7118 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 25 (numéricos por defecto) | 0.7136 | 0.7135, 0.7178, 0.7094 | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| 34 (numéricos por defecto) | 0.7144 | 0.7190, 0.7188, 0.7055 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 1* | 0.7663 | 0.7841, 0.7572, 0.7575 | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (clsp 10x15) · 0 configuraciones fallidas · 1426 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6720 (mejor default: 0.7600, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.31%** | **88725.9** | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.31% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.08% | 91794.5 | 15044 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=critical_period_seeding | 9.25% | 92961.7 | 16378 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.81% | 93432.6 | 16344 | +27.8% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.43% | 93839.3 | 15799 | +27.5% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.76% | 94379.2 | 17535 | +27.1% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.91% | 94494.0 | 17617 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:VNS | 16.74% | 99306.5 | 17590 | +23.3% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.86% | 100568.1 | 19629 | +22.3% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=critical_period_seeding | 17.87% | 100317.0 | 18270 | +22.5% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:ILS | 19.25% | 101547.5 | 18759 | +21.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.76% | 101820.8 | 17633 | +21.3% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=critical_period_seeding | 20.40% | 102795.5 | 20922 | +20.6% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 20.58% | 102488.6 | 17526 | +20.8% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 22.52% | 104211.0 | 18479 | +19.5% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_capacity_pressure_balance | 23.50% | 105122.2 | 19534 | +18.8% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:neighborhood=swap_capacity_pressure | 24.63% | 105978.9 | 18681 | +18.1% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.08% | 106395.2 | 18723 | +17.8% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.45% | 106467.5 | 17189 | +17.7% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 25.68% | 107348.5 | 21331 | +17.0% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 49.33% | 127102.6 | 22700 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 38 (numéricos por defecto) ✔ | 0.6720 | 0.6709, 0.6771, 0.6680 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 39 | 0.6751 | 0.6734, 0.6787, 0.6732 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 24 | 0.6753 | 0.6741, 0.6748, 0.6771 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 31 | 0.6754 | 0.6760, 0.6690, 0.6813 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 38 | 0.6754 | 0.6732, 0.6799, 0.6732 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 23 | 0.6770 | 0.6752, 0.6791, 0.6767 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 2* | 0.7567 | 0.7600, 0.7577, 0.7523 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
