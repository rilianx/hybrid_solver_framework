## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 5 train / 5 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 11.10% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| r1 | 1 | 5.68% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| r2 | 2 | 6.85% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |

**Afinado entre réplicas**: media 7.88%, desvío 2.33%, rango [5.68%, 11.10%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_forward_cover_cost` = 4.31%. Afinado vs ese: -3.57% de gap a favor del afinado, IC95 [-4.44%, -2.24%] sobre las instancias; el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (clsp 10x15) · 0 configuraciones fallidas · 1441 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` = 0.7017 (mejor default: 0.7772, `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **10.97%** | **94684.7** | 17646 | +26.8% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.18% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 7.53% | 91446.5 | 15028 | +29.3% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_forward_cover_cost | 8.72% | 92473.9 | 15397 | +28.5% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.33% | 93137.3 | 16406 | +28.0% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.76% | 93501.2 | 16340 | +27.7% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.99% | 94695.4 | 17813 | +26.8% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:SA | 11.16% | 94836.6 | 17688 | +26.7% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| default:VNS | 15.27% | 97892.9 | 15828 | +24.3% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=critical_period_seeding | 17.05% | 99895.4 | 19277 | +22.8% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 17.32% | 100049.2 | 18861 | +22.7% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.64% | 100673.9 | 21116 | +22.2% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 17.77% | 100239.3 | 17427 | +22.5% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.73% | 101938.3 | 17791 | +21.2% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=critical_period_seeding | 21.01% | 103290.7 | 19800 | +20.2% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:ILS | 22.59% | 104431.8 | 18687 | +19.3% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 23.08% | 104623.8 | 17336 | +19.1% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.41% | 105857.7 | 18426 | +18.2% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.72% | 106186.5 | 18583 | +17.9% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.41% | 106780.9 | 18550 | +17.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 26.97% | 108215.4 | 19407 | +16.4% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| VNS:neighborhood=shift_setup_in_time | 43.77% | 122698.0 | 23206 | +5.2% | `VNS[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |
| SA:neighborhood=shift_setup_in_time | 49.15% | 127104.6 | 22699 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-6.72%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 26, ILS × 7, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -6.79% de gap a favor del afinado, IC95 [-8.18%, -4.80%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 35 ✔ | 0.7017 | 0.6925, 0.7104, 0.7022 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 33 | 0.7026 | 0.6925, 0.7103, 0.7050 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 32 | 0.7027 | 0.6925, 0.7099, 0.7058 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 18 | 0.7033 | 0.6932, 0.7104, 0.7062 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 21 | 0.7033 | 0.6932, 0.7104, 0.7062 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 32 (numéricos por defecto) | 0.7068 | 0.6974, 0.7159, 0.7070 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 1* | 0.7778 | 0.7772, 0.7735, 0.7828 | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (clsp 10x15) · 0 configuraciones fallidas · 1359 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6672 (mejor default: 0.7545, `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **5.68%** | **89949.9** | 15897 | +30.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.31% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 7.79% | 91551.1 | 15104 | +29.2% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=critical_period_seeding | 9.30% | 92999.5 | 16363 | +28.1% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.89% | 93500.6 | 16340 | +27.7% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.05% | 93521.9 | 15819 | +27.7% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.96% | 94563.6 | 17702 | +26.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.98% | 94542.2 | 17591 | +26.9% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:VNS | 17.48% | 99927.3 | 17613 | +22.8% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 18.24% | 100788.9 | 19241 | +22.1% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:ILS | 18.41% | 101221.0 | 21224 | +21.8% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 18.87% | 101345.1 | 19735 | +21.7% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.43% | 101441.3 | 16846 | +21.6% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 19.59% | 101895.6 | 19098 | +21.3% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.73% | 101794.5 | 17648 | +21.3% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=greedy_capacity_pressure_balance | 20.67% | 102668.2 | 18878 | +20.7% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 21.68% | 103870.5 | 20796 | +19.7% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.78% | 106150.5 | 18744 | +18.0% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:neighborhood=swap_capacity_pressure | 25.58% | 106824.2 | 18904 | +17.4% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| ILS:perturbation=merge_adjacent_lots | 26.40% | 107227.2 | 17399 | +17.1% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 26.74% | 108157.8 | 20859 | +16.4% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 49.33% | 127102.6 | 22700 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-1.38%**; gana en 1/5 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -1.37% de gap a favor del afinado, IC95 [-2.38%, -0.07%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 17 ✔ | 0.6672 | 0.6702, 0.6619, 0.6696 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 15 | 0.6689 | 0.6686, 0.6680, 0.6702 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 22 | 0.6720 | 0.6658, 0.6799, 0.6703 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 32 | 0.6745 | 0.6729, 0.6761, 0.6745 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 26 | 0.6760 | 0.6733, 0.6764, 0.6784 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 1* | 0.7596 | 0.7545, 0.7456, 0.7788 | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 5 train / 5 test (clsp 10x15) · 0 configuraciones fallidas · 1360 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6632 (mejor default: 0.7308, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **6.73%** | **90880.7** | 15683 | +29.8% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.18% | 88725.9 | 15463 | +31.4% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 7.88% | 91719.1 | 14888 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=critical_period_seeding | 8.98% | 92839.8 | 16402 | +28.3% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.67% | 93432.6 | 16344 | +27.8% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 9.93% | 93563.4 | 15979 | +27.7% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.58% | 94340.7 | 17546 | +27.1% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 10.78% | 94494.0 | 17617 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:VNS | 18.53% | 100876.5 | 17537 | +22.0% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 18.59% | 100946.6 | 17485 | +22.0% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 19.08% | 101506.1 | 18421 | +21.6% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.26% | 101499.1 | 17456 | +21.6% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| VNS:constructor=critical_period_seeding | 20.20% | 102490.3 | 18791 | +20.8% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_capacity_pressure_balance | 20.69% | 102900.6 | 19081 | +20.5% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:ILS | 20.77% | 102868.2 | 18503 | +20.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 20.96% | 103425.3 | 21023 | +20.1% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_capacity_pressure_balance | 21.25% | 103370.5 | 19306 | +20.1% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:neighborhood=swap_capacity_pressure | 23.25% | 104939.4 | 18545 | +18.9% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.76% | 106319.5 | 19077 | +17.8% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.70% | 106973.2 | 18367 | +17.3% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 26.65% | 108058.6 | 20154 | +16.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 49.15% | 127101.6 | 22700 | +1.8% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-2.43%**; gana en 0/5 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -2.54% de gap a favor del afinado, IC95 [-3.35%, -1.73%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 39 ✔ | 0.6632 | 0.6641, 0.6635, 0.6619 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 29 | 0.6675 | 0.6646, 0.6684, 0.6694 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 15 | 0.6719 | 0.6706, 0.6771, 0.6680 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 33 | 0.6761 | 0.6763, 0.6754, 0.6768 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 28 | 0.6781 | 0.6766, 0.6796, 0.6781 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 2* | 0.7477 | 0.7308, 0.7644, 0.7480 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
