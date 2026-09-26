## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 4.84% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| r1 | 1 | 6.10% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| r2 | 2 | 4.84% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |

**Afinado entre réplicas**: media 5.26%, desvío 0.59%, rango [4.84%, 6.10%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_forward_cover_cost` = 4.84%. Afinado vs ese: -0.42% de gap a favor del afinado, IC95 [-0.75%, -0.09%] sobre las instancias; el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3179 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6859 (mejor default: 0.7635, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.84%** | **90434.7** | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.84% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.61% | 93648.6 | 16807 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.21% | 94300.2 | 17674 | +28.6% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.83% | 94727.6 | 17139 | +28.3% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:SA | 9.89% | 94863.3 | 17792 | +28.2% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.38% | 95147.7 | 17159 | +28.0% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.50% | 96288.9 | 18238 | +27.1% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 15.07% | 99500.1 | 19854 | +24.7% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 16.77% | 100787.5 | 19089 | +23.7% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 17.07% | 101190.9 | 20071 | +23.4% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:ILS | 18.37% | 102255.2 | 19800 | +22.6% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:VNS | 18.48% | 102418.8 | 20488 | +22.5% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| ILS:constructor=critical_period_seeding | 18.73% | 102493.1 | 19300 | +22.4% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 18.83% | 102534.0 | 19007 | +22.4% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.43% | 103081.0 | 19647 | +22.0% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_capacity_pressure_balance | 22.17% | 105653.7 | 21482 | +20.0% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 22.78% | 106019.7 | 20087 | +19.7% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 23.30% | 106431.9 | 20033 | +19.4% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 23.65% | 107051.1 | 22190 | +19.0% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.10% | 130561.9 | 25145 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 15 ✔ | 0.6859 | 0.6860, 0.6884, 0.6833 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 30 | 0.7084 | 0.7085, 0.7064, 0.7104 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 38 | 0.7090 | 0.7076, 0.7156, 0.7039 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 34 | 0.7099 | 0.7091, 0.7078, 0.7127 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| 34 (numéricos por defecto) | 0.7115 | 0.7086, 0.7131, 0.7127 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| 12 | 0.7130 | 0.7133, 0.7143, 0.7114 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 30 (numéricos por defecto) | 0.7147 | 0.7117, 0.7145, 0.7178 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 38 (numéricos por defecto) | 0.7170 | 0.7231, 0.7107, 0.7172 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 2* | 0.7645 | 0.7635, 0.7536, 0.7764 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3346 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6845 (mejor default: 0.7848, `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **6.08%** | **91631.8** | 17323 | +30.6% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.82% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.88% | 93983.1 | 17427 | +28.9% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.39% | 94518.6 | 18000 | +28.5% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.98% | 94882.6 | 17154 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:SA | 10.22% | 95183.5 | 17951 | +27.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.41% | 95231.2 | 17241 | +27.9% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.72% | 96499.5 | 18244 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.90% | 101679.8 | 18666 | +23.0% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:VNS | 18.65% | 102605.0 | 20636 | +22.3% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 19.13% | 103052.1 | 20855 | +22.0% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 19.43% | 103242.5 | 20581 | +21.8% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.50% | 103248.8 | 19779 | +21.8% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.65% | 103267.4 | 19107 | +21.8% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| default:ILS | 20.24% | 104210.4 | 22643 | +21.1% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 21.32% | 105052.8 | 21907 | +20.5% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 22.51% | 105813.2 | 20324 | +19.9% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.09% | 107034.6 | 19597 | +19.0% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.31% | 108203.8 | 20320 | +18.1% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.81% | 108294.2 | 18527 | +18.0% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.61% | 110251.6 | 21669 | +16.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.07% | 130562.9 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-1.32%**; gana en 4/10 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -1.26% de gap a favor del afinado, IC95 [-2.26%, -0.26%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 32 ✔ | 0.6845 | 0.6803, 0.6863, 0.6870 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 32 (numéricos por defecto) | 0.6853 | 0.6842, 0.6865, 0.6852 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 34 | 0.7073 | 0.7033, 0.7105, 0.7081 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| 18 | 0.7077 | 0.7058, 0.7085, 0.7089 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 33 | 0.7088 | 0.7093, 0.7067, 0.7103 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 18 (numéricos por defecto) | 0.7122 | 0.7122, 0.7128, 0.7115 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 34 (numéricos por defecto) | 0.7126 | 0.7115, 0.7156, 0.7106 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| 12 | 0.7143 | 0.7155, 0.7138, 0.7137 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 33 (numéricos por defecto) | 0.7161 | 0.7206, 0.7183, 0.7093 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 1* | 0.7771 | 0.7848, 0.7743, 0.7722 | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3060 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6884 (mejor default: 0.7648, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.73%** | **90434.7** | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.73% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 9.15% | 94316.2 | 17663 | +28.6% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.31% | 94518.6 | 18000 | +28.5% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.81% | 94815.8 | 17173 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 9.96% | 95009.0 | 17699 | +28.1% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.10% | 95157.6 | 17945 | +28.0% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.60% | 96468.5 | 18252 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 16.93% | 101010.3 | 19283 | +23.5% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:ILS | 18.08% | 102346.9 | 21804 | +22.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:VNS | 19.12% | 102962.6 | 19797 | +22.1% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 19.15% | 103311.0 | 21840 | +21.8% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 19.36% | 103188.2 | 19806 | +21.9% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.46% | 103184.8 | 19097 | +21.9% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=greedy_capacity_pressure_balance | 20.31% | 103914.0 | 19306 | +21.3% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 20.35% | 104296.9 | 21496 | +21.0% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_capacity_pressure_balance | 20.80% | 104585.6 | 21033 | +20.8% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:neighborhood=swap_capacity_pressure | 24.18% | 107249.4 | 19875 | +18.8% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.52% | 107609.5 | 20296 | +18.5% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.26% | 108018.0 | 18919 | +18.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.51% | 110176.4 | 21203 | +16.6% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 50.95% | 130562.4 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 24, ILS × 8, VNS × 8.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 15 ✔ | 0.6884 | 0.6866, 0.6921, 0.6867 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 22 | 0.7061 | 0.7042, 0.7063, 0.7079 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 39 | 0.7074 | 0.7036, 0.7099, 0.7088 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=swap_capacity_pressure, perturbation=remove_low_value_setup_and_recover]` |
| 22 (numéricos por defecto) | 0.7112 | 0.7095, 0.7123, 0.7118 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 6 | 0.7137 | 0.7147, 0.7167, 0.7099 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 14 | 0.7175 | 0.7132, 0.7195, 0.7198 | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 39 (numéricos por defecto) | 0.7367 | 0.7368, 0.7386, 0.7348 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=swap_capacity_pressure, perturbation=remove_low_value_setup_and_recover]` |
| 2* | 0.7746 | 0.7648, 0.7738, 0.7851 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
