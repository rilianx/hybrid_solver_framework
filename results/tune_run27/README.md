## Réplicas del tuning (3)

### Catálogo `generated`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 3 | 4.82% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| r1 | 4 | 4.85% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| r2 | 5 | 4.84% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |

**Afinado entre réplicas**: media 4.84%, desvío 0.01%, rango [4.82%, 4.85%].

**Mejor no afinado** (media entre réplicas): `SA:constructor=greedy_forward_cover_cost` = 4.84%. Afinado vs ese: -0.00% de gap a favor del afinado, IC95 [-0.01%, +0.00%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3024 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6859 (mejor default: 0.7705, `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.82%** | **90434.7** | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.82% | 90434.7 | 16382 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.72% | 93857.6 | 17424 | +29.0% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.39% | 94519.5 | 17999 | +28.5% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.98% | 94882.6 | 17154 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:SA | 10.25% | 95222.8 | 18021 | +27.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.53% | 95320.0 | 17166 | +27.8% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.72% | 96499.5 | 18244 | +27.0% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 17.15% | 101240.4 | 19574 | +23.4% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=critical_period_seeding | 17.53% | 101651.5 | 20517 | +23.1% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:ILS | 18.59% | 102378.9 | 19154 | +22.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 18.76% | 102665.5 | 20442 | +22.3% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| default:VNS | 19.13% | 102958.4 | 20236 | +22.1% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.59% | 103439.0 | 20651 | +21.7% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| SA:neighborhood=swap_capacity_pressure | 19.67% | 103291.2 | 19140 | +21.8% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=critical_period_seeding | 20.92% | 104689.7 | 21806 | +20.8% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 22.24% | 105633.6 | 20750 | +20.0% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 25.20% | 108107.5 | 20563 | +18.2% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.49% | 108352.7 | 20282 | +18.0% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 25.58% | 108155.6 | 18851 | +18.1% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.73% | 110324.7 | 21419 | +16.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.07% | 130563.3 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 15 ✔ | 0.6859 | 0.6844, 0.6886, 0.6848 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 30 (numéricos por defecto) | 0.7124 | 0.7056, 0.7199, 0.7117 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 30 | 0.7138 | 0.7141, 0.7159, 0.7116 | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| 12 | 0.7159 | 0.7145, 0.7148, 0.7184 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 9 | 0.7205 | 0.7191, 0.7218, 0.7208 | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| 38 (numéricos por defecto) | 0.7206 | 0.7184, 0.7203, 0.7232 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 38 | 0.7221 | 0.7246, 0.7248, 0.7169 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 2* | 0.7868 | 0.7705, 0.7866, 0.8034 | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |

## Réplica r1

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3035 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6847 (mejor default: 0.7860, `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.85%** | **90458.6** | 16365 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.84% | 90454.4 | 16368 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.46% | 93624.8 | 17388 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.49% | 94619.3 | 18130 | +28.4% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 10.09% | 94987.6 | 17268 | +28.1% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 10.46% | 95307.1 | 17403 | +27.9% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.62% | 95537.5 | 18091 | +27.7% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.81% | 96564.6 | 18191 | +26.9% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 16.43% | 100698.7 | 20126 | +23.8% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| VNS:constructor=critical_period_seeding | 17.72% | 101786.3 | 20008 | +23.0% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| default:VNS | 17.99% | 101821.2 | 19165 | +22.9% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_capacity_pressure_balance | 19.04% | 102942.1 | 20565 | +22.1% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| default:ILS | 19.60% | 103400.6 | 20556 | +21.7% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.77% | 103385.4 | 19210 | +21.7% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 20.22% | 103966.6 | 20906 | +21.3% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=critical_period_seeding | 20.45% | 104232.6 | 21251 | +21.1% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:constructor=greedy_capacity_pressure_balance | 23.21% | 106560.5 | 21417 | +19.3% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.40% | 107368.7 | 20151 | +18.7% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 25.09% | 107983.2 | 20168 | +18.3% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 26.11% | 108558.7 | 18510 | +17.8% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 28.09% | 110668.4 | 21595 | +16.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.07% | 130563.3 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **-0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 24, ILS × 8, VNS × 8.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): -0.01% de gap a favor del afinado, IC95 [-0.02%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 38 (numéricos por defecto) ✔ | 0.6847 | 0.6862, 0.6868, 0.6811 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 34 | 0.7136 | 0.7124, 0.7197, 0.7088 | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| 3 | 0.7152 | 0.7117, 0.7186, 0.7152 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 12 | 0.7196 | 0.7241, 0.7175, 0.7171 | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| 14 | 0.7217 | 0.7236, 0.7181, 0.7235 | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 34 (numéricos por defecto) | 0.7275 | 0.7331, 0.7247, 0.7247 | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| 38 | 0.7447 | 0.7469, 0.7463, 0.7409 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 0* | 0.7821 | 0.7860, 0.7778, 0.7824 | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |

## Réplica r2

### Catálogo `generated`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3208 s de tuning

esqueletos: `SA`, `ILS`, `VNS` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

Componentes LLM en el catálogo: `clustered_item_windowing`, `critical_period_seeding`, `item_line_reset`, `low_value_setup_removal`, `window_capacity_shock`, `capacity_pressure_balance`, `forward_cover_cost`, `setup_consolidation_urgency`, `remove_redundant_setup`, `shift_setup_in_time`, `swap_capacity_pressure`, `backward_lot_shift`, `merge_adjacent_lots`, `remove_low_value_setup_and_recover`

**Mejor en train**: `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` = 0.6864 (mejor default: 0.7734, `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **4.82%** | **90454.4** | 16368 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_forward_cover_cost | 4.82% | 90454.4 | 16368 | +31.5% | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_forward_cover_cost | 8.50% | 93679.4 | 17353 | +29.1% | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:constructor=greedy_setup_consolidation_urgency | 9.49% | 94651.1 | 18200 | +28.4% | `SA[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| SA:constructor=critical_period_seeding | 9.99% | 94910.1 | 17142 | +28.2% | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_forward_cover_cost | 9.99% | 94901.3 | 17096 | +28.2% | `VNS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| default:SA | 10.29% | 95279.1 | 18028 | +27.9% | `SA[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| SA:constructor=greedy_capacity_pressure_balance | 11.78% | 96565.5 | 18196 | +26.9% | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| VNS:constructor=greedy_setup_consolidation_urgency | 16.61% | 100931.3 | 20384 | +23.6% | `VNS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup]` |
| default:VNS | 17.51% | 101460.9 | 19230 | +23.2% | `VNS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup]` |
| default:ILS | 18.00% | 102185.0 | 21070 | +22.6% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=critical_period_seeding | 18.05% | 102065.8 | 20029 | +22.7% | `VNS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_setup_consolidation_urgency | 18.41% | 102394.3 | 20446 | +22.5% | `ILS[constructor=greedy_setup_consolidation_urgency, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| SA:neighborhood=swap_capacity_pressure | 19.80% | 103432.0 | 19197 | +21.7% | `SA[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:constructor=critical_period_seeding | 20.68% | 104641.6 | 22601 | +20.8% | `ILS[constructor=critical_period_seeding, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| VNS:constructor=greedy_capacity_pressure_balance | 21.55% | 105072.6 | 20534 | +20.5% | `VNS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| ILS:constructor=greedy_capacity_pressure_balance | 24.15% | 107345.6 | 21217 | +18.7% | `ILS[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
| ILS:neighborhood=swap_capacity_pressure | 24.16% | 107201.2 | 20075 | +18.9% | `ILS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure, perturbation=backward_lot_shift]` |
| VNS:neighborhood=swap_capacity_pressure | 24.73% | 107810.8 | 20826 | +18.4% | `VNS[constructor=clustered_item_windowing, neighborhood=swap_capacity_pressure]` |
| ILS:perturbation=merge_adjacent_lots | 26.62% | 108975.1 | 18477 | +17.5% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=merge_adjacent_lots]` |
| ILS:perturbation=remove_low_value_setup_and_recover | 27.98% | 110720.7 | 22175 | +16.2% | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| SA:neighborhood=shift_setup_in_time | 51.03% | 130563.9 | 25144 | +1.2% | `SA[constructor=clustered_item_windowing, neighborhood=shift_setup_in_time]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: SA × 25, ILS × 8, VNS × 7.

Afinado vs `SA:constructor=greedy_forward_cover_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 15 ✔ | 0.6864 | 0.6847, 0.6886, 0.6857 | `SA[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup]` |
| 34 | 0.6954 | 0.6982, 0.6957, 0.6923 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| 25 | 0.7137 | 0.7113, 0.7148, 0.7150 | `SA[constructor=greedy_forward_cover_cost, neighborhood=swap_capacity_pressure]` |
| 29 | 0.7196 | 0.7230, 0.7230, 0.7127 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 34 (numéricos por defecto) | 0.7200 | 0.7175, 0.7207, 0.7219 | `ILS[constructor=greedy_forward_cover_cost, neighborhood=remove_redundant_setup, perturbation=remove_low_value_setup_and_recover]` |
| 29 (numéricos por defecto) | 0.7203 | 0.7212, 0.7198, 0.7200 | `SA[constructor=critical_period_seeding, neighborhood=remove_redundant_setup]` |
| 9 | 0.7252 | 0.7242, 0.7309, 0.7206 | `SA[constructor=greedy_capacity_pressure_balance, neighborhood=remove_redundant_setup]` |
| 25 (numéricos por defecto) | 0.7254 | 0.7270, 0.7241, 0.7252 | `SA[constructor=greedy_forward_cover_cost, neighborhood=swap_capacity_pressure]` |
| 1* | 0.7806 | 0.7734, 0.7864, 0.7819 | `ILS[constructor=clustered_item_windowing, neighborhood=remove_redundant_setup, perturbation=backward_lot_shift]` |
