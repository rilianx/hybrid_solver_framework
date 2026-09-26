## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 8.62% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| r1 | 1 | 4.82% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| r2 | 2 | 5.33% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |

**Afinado entre réplicas**: media 6.26%, desvío 1.68%, rango [4.82%, 8.62%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_forward_cover_cost` = 4.82%. Afinado vs ese: -1.44% de gap a favor del afinado, IC95 [-2.20%, -0.72%] sobre las instancias; el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3010 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` = 0.7061 (mejor default: 0.7632, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **8.62%** | **93607.1** | 16197 | +29.1% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.82% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.78% | 93891.2 | 17338 | +28.9% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.39% | 94518.6 | 18000 | +28.5% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.96% | 94867.1 | 17158 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:SA | 10.22% | 95183.5 | 17951 | +27.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.26% | 95149.1 | 17496 | +28.0% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.69% | 96468.5 | 18252 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.55% | 101359.4 | 18659 | +23.3% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 18.42% | 102540.1 | 21325 | +22.4% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:VNS | 18.59% | 102340.2 | 19165 | +22.5% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| default:ILS | 18.78% | 102771.1 | 21064 | +22.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 18.97% | 102870.1 | 20217 | +22.1% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.70% | 103607.9 | 21074 | +21.6% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.74% | 103351.1 | 19177 | +21.8% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=critical_period_seeding | 20.86% | 104398.0 | 19777 | +21.0% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 22.32% | 105742.8 | 20965 | +20.0% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.61% | 107655.5 | 20879 | +18.5% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.07% | 108043.3 | 20641 | +18.2% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 26.81% | 109327.2 | 19642 | +17.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.42% | 110102.5 | 21678 | +16.7% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.07% | 130562.9 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-3.51%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 26, ILS × 7, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -3.80% de gap a favor del afinado, IC95 [-4.92%, -2.75%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 14 ✔ | 0.7061 | 0.7070, 0.7055, 0.7057 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 26 | 0.7114 | 0.7081, 0.7109, 0.7152 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 32 | 0.7129 | 0.7081, 0.7106, 0.7201 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 36 | 0.7130 | 0.7079, 0.7117, 0.7193 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 33 | 0.7134 | 0.7081, 0.7106, 0.7216 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 14 (numéricos por defecto) | 0.7149 | 0.7123, 0.7146, 0.7178 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 36 (numéricos por defecto) | 0.7152 | 0.7139, 0.7173, 0.7143 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 2* | 0.7607 | 0.7632, 0.7401, 0.7789 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3012 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6853 (mejor default: 0.7957, `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.82%** | **90434.7** | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.82% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.52% | 93703.3 | 17505 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.39% | 94518.6 | 18000 | +28.5% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.98% | 94882.6 | 17154 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:SA | 10.27% | 95235.7 | 18018 | +27.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.41% | 95225.0 | 17199 | +27.9% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.72% | 96499.5 | 18244 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.33% | 101328.7 | 19297 | +23.3% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:VNS | 17.58% | 101413.6 | 18715 | +23.2% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=critical_period_seeding | 18.24% | 102329.3 | 20728 | +22.5% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 18.83% | 102578.1 | 19488 | +22.4% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.31% | 103008.8 | 19356 | +22.0% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:ILS | 19.67% | 103617.4 | 21583 | +21.6% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.67% | 103289.2 | 19143 | +21.8% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=critical_period_seeding | 21.48% | 105036.4 | 20770 | +20.5% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 23.15% | 106510.9 | 21494 | +19.4% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.98% | 107960.9 | 20542 | +18.3% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:neighborhood=swap_capacity_pressure | 25.53% | 108377.2 | 20446 | +18.0% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| ILS:perturbation=merge_adjacent_lots | 25.75% | 108227.8 | 18348 | +18.1% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.74% | 110344.1 | 21492 | +16.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.07% | 130563.3 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 23, ILS × 12, VNS × 5.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 38 (numéricos por defecto) ✔ | 0.6853 | 0.6842, 0.6866, 0.6852 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 38 | 0.6860 | 0.6839, 0.6838, 0.6904 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 34 | 0.7041 | 0.7086, 0.7058, 0.6978 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 35 | 0.7043 | 0.7091, 0.7070, 0.6967 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 30 | 0.7102 | 0.7068, 0.7106, 0.7131 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 30 (numéricos por defecto) | 0.7122 | 0.7122, 0.7129, 0.7115 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 33 | 0.7124 | 0.7088, 0.7130, 0.7152 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 1* | 0.7878 | 0.7957, 0.7780, 0.7896 | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 2849 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6849 (mejor default: 0.7564, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **5.33%** | **90864.1** | 16308 | +31.2% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.82% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.82% | 93926.6 | 17332 | +28.9% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.39% | 94518.6 | 18000 | +28.5% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.95% | 94860.4 | 17159 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:SA | 10.22% | 95183.5 | 17951 | +27.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.34% | 95234.6 | 17545 | +27.9% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.72% | 96499.5 | 18244 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:VNS | 16.71% | 100811.6 | 19210 | +23.7% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.35% | 101276.6 | 18794 | +23.3% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 18.05% | 102232.1 | 21362 | +22.6% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:ILS | 18.38% | 102224.2 | 19388 | +22.6% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 18.58% | 102460.8 | 19623 | +22.4% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.65% | 103267.4 | 19107 | +21.8% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| VNS:constructor=greedy_capacity_pressure_balance | 20.34% | 103900.8 | 19532 | +21.3% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:constructor=critical_period_seeding | 20.48% | 104235.2 | 21141 | +21.1% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 21.83% | 105378.7 | 21392 | +20.2% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.73% | 107733.9 | 20785 | +18.4% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.03% | 107952.6 | 20239 | +18.3% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.25% | 107972.2 | 19627 | +18.3% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.75% | 110356.3 | 21503 | +16.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.07% | 130563.3 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-0.47%**; gana en 5/10 instancias de test. Esqueletos explorados: SA × 24, ILS × 9, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -0.51% de gap a favor del afinado, IC95 [-1.77%, +0.75%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 24 ✔ | 0.6849 | 0.6851, 0.6858, 0.6838 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 36 | 0.6857 | 0.6868, 0.6857, 0.6846 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 31 | 0.6869 | 0.6874, 0.6862, 0.6870 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 33 | 0.6869 | 0.6895, 0.6870, 0.6843 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 21 | 0.6874 | 0.6887, 0.6865, 0.6869 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 24 (numéricos por defecto) | 0.6884 | 0.6866, 0.6921, 0.6867 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 2* | 0.7663 | 0.7564, 0.7712, 0.7714 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
