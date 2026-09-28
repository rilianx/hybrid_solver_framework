## Réplicas del tuning (3)

### Catálogo `handwritten`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.67% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| r1 | 1 | 0.62% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| r2 | 2 | 0.68% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |

**Afinado entre réplicas**: media 0.66%, desvío 0.03%, rango [0.62%, 0.68%].

**Mejor no afinado** (media entre réplicas): `LNS_MIP:constructor=greedy_unit_marginal_cost` = 0.65%. Afinado vs ese: -0.01% de gap a favor del afinado, IC95 [-0.03%, +0.01%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 4400 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` = 0.6516 (mejor default: 0.6642, `LNS_MIP[constructor=lot_for_lot, destruction=period_window]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.66%** | **86568.5** | 15601 | +34.5% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| LNS_MIP:constructor=greedy_unit_marginal_cost | 0.66% | 86568.5 | 15601 | +34.5% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| LNS_MIP:destruction=random_setups | 1.46% | 87254.0 | 15719 | +34.0% | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| default:LNS_MIP | 2.21% | 87920.8 | 16131 | +33.4% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| LNS_MIP:constructor=greedy_latest_source | 3.00% | 88846.7 | 18257 | +32.7% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| SA:constructor=greedy_unit_marginal_cost | 6.66% | 91856.5 | 17497 | +30.5% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| VNS:constructor=greedy_unit_marginal_cost | 8.72% | 93652.0 | 17899 | +29.1% | `VNS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| ILS:constructor=greedy_unit_marginal_cost | 9.52% | 94304.1 | 17787 | +28.6% | `ILS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:SA | 10.97% | 95491.8 | 17633 | +27.7% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=greedy_latest_source | 12.09% | 96474.1 | 18020 | +27.0% | `SA[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| default:VNS | 14.90% | 98842.6 | 18267 | +25.2% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| VNS:constructor=greedy_latest_source | 15.23% | 99182.1 | 18644 | +24.9% | `VNS[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| ILS:constructor=greedy_latest_source | 19.74% | 103219.0 | 20877 | +21.9% | `ILS[constructor=greedy_latest_source, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:ILS | 20.47% | 103800.6 | 20465 | +21.4% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |

Ganancia del afinado sobre el mejor default: **+0.00%**; gana en 0/10 instancias de test. Esqueletos explorados: LNS_MIP × 24, SA × 6, ILS × 5, VNS × 5.

Afinado vs `LNS_MIP:constructor=greedy_unit_marginal_cost` (mejor default por gap): +0.00% de gap a favor del afinado, IC95 [+0.00%, +0.00%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 15 (numéricos por defecto) ✔ | 0.6516 | 0.6544, 0.6530, 0.6509, 0.6514, 0.6490, 0.6519, 0.6507 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| 18 | 0.6527 | 0.6522, 0.6533, 0.6496, 0.6556, 0.6524, 0.6519, 0.6543 | `LNS_MIP[constructor=greedy_latest_source, destruction=random_setups]` |
| 17 | 0.6536 | 0.6507, 0.6517, 0.6593, 0.6539, 0.6554, 0.6533, 0.6512 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=random_setups]` |
| 16 | 0.6537 | 0.6502, 0.6506, 0.6574, 0.6542, 0.6540, 0.6537, 0.6560 | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| 18 (numéricos por defecto) | 0.6553 | 0.6590, 0.6524, 0.6546 | `LNS_MIP[constructor=greedy_latest_source, destruction=random_setups]` |
| 16 (numéricos por defecto) | 0.6554 | 0.6572, 0.6536, 0.6554 | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| 3* | 0.6556 | 0.6642, 0.6557, 0.6530, 0.6525, 0.6524 | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| 12 | 0.6557 | 0.6631, 0.6588, 0.6516, 0.6523, 0.6528 | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| 17 (numéricos por defecto) | 0.6557 | 0.6579, 0.6553, 0.6540 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=random_setups]` |
| 15 | 0.6575 | 0.6515, 0.6531, 0.6679 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |

## Réplica r1

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 2957 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` = 0.6497 (mejor default: 0.6574, `LNS_MIP[constructor=lot_for_lot, destruction=period_window]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.62%** | **86513.4** | 15527 | +34.5% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| LNS_MIP:constructor=greedy_unit_marginal_cost | 0.57% | 86471.8 | 15511 | +34.5% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| LNS_MIP:destruction=random_setups | 1.31% | 87113.1 | 15640 | +34.1% | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| default:LNS_MIP | 1.71% | 87457.7 | 15817 | +33.8% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| LNS_MIP:constructor=greedy_latest_source | 2.52% | 88402.9 | 18010 | +33.1% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| SA:constructor=greedy_unit_marginal_cost | 6.55% | 91754.4 | 17482 | +30.5% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| VNS:constructor=greedy_unit_marginal_cost | 8.51% | 93387.2 | 17341 | +29.3% | `VNS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| ILS:constructor=greedy_unit_marginal_cost | 8.86% | 93768.1 | 17990 | +29.0% | `ILS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:SA | 9.73% | 94397.9 | 17311 | +28.5% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=greedy_latest_source | 11.21% | 95733.9 | 17969 | +27.5% | `SA[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| default:VNS | 13.11% | 97262.3 | 17558 | +26.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| VNS:constructor=greedy_latest_source | 14.70% | 98546.6 | 17333 | +25.4% | `VNS[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| ILS:constructor=greedy_latest_source | 18.35% | 101810.4 | 19151 | +22.9% | `ILS[constructor=greedy_latest_source, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:ILS | 18.35% | 101905.2 | 19733 | +22.9% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |

Ganancia del afinado sobre el mejor default: **-0.05%**; gana en 1/10 instancias de test. Esqueletos explorados: LNS_MIP × 23, SA × 7, ILS × 5, VNS × 5.

Afinado vs `LNS_MIP:constructor=greedy_unit_marginal_cost` (mejor default por gap): -0.05% de gap a favor del afinado, IC95 [-0.15%, +0.02%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 7 ✔ | 0.6497 | 0.6482, 0.6521, 0.6488 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| 22 | 0.6531 | 0.6522, 0.6532, 0.6540 | `LNS_MIP[constructor=greedy_latest_source, destruction=random_setups]` |
| 11 | 0.6535 | 0.6530, 0.6547, 0.6528 | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| 22 (numéricos por defecto) | 0.6551 | 0.6545, 0.6547, 0.6562 | `LNS_MIP[constructor=greedy_latest_source, destruction=random_setups]` |
| 23 | 0.6564 | 0.6501, 0.6607, 0.6583 | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| 3* | 0.6568 | 0.6574, 0.6591, 0.6538 | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| 23 (numéricos por defecto) | 0.6574 | 0.6574, 0.6600, 0.6550 | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |

## Réplica r2

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 3641 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` = 0.6514 (mejor default: 0.6610, `LNS_MIP[constructor=lot_for_lot, destruction=period_window]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.67%** | **86578.2** | 15606 | +34.5% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| LNS_MIP:constructor=greedy_unit_marginal_cost | 0.69% | 86593.9 | 15610 | +34.5% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| LNS_MIP:destruction=random_setups | 1.51% | 87299.9 | 15714 | +33.9% | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| default:LNS_MIP | 2.20% | 87910.6 | 16107 | +33.5% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| LNS_MIP:constructor=greedy_latest_source | 3.02% | 88868.9 | 18268 | +32.7% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| SA:constructor=greedy_unit_marginal_cost | 6.95% | 92136.2 | 17729 | +30.3% | `SA[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| VNS:constructor=greedy_unit_marginal_cost | 8.96% | 93836.4 | 17780 | +29.0% | `VNS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip]` |
| ILS:constructor=greedy_unit_marginal_cost | 9.46% | 94299.3 | 18042 | +28.6% | `ILS[constructor=greedy_unit_marginal_cost, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:SA | 11.57% | 95994.7 | 17637 | +27.3% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| SA:constructor=greedy_latest_source | 12.58% | 96899.3 | 18094 | +26.6% | `SA[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| default:VNS | 16.03% | 99817.4 | 18365 | +24.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| VNS:constructor=greedy_latest_source | 16.97% | 100612.3 | 18560 | +23.8% | `VNS[constructor=greedy_latest_source, neighborhood=setup_flip]` |
| ILS:constructor=greedy_latest_source | 20.21% | 103347.8 | 18863 | +21.8% | `ILS[constructor=greedy_latest_source, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:ILS | 20.28% | 103552.1 | 20104 | +21.6% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |

Ganancia del afinado sobre el mejor default: **+0.02%**; gana en 1/10 instancias de test. Esqueletos explorados: LNS_MIP × 22, SA × 6, ILS × 6, VNS × 6.

Afinado vs `LNS_MIP:constructor=greedy_unit_marginal_cost` (mejor default por gap): +0.02% de gap a favor del afinado, IC95 [+0.00%, +0.05%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 26 (numéricos por defecto) ✔ | 0.6514 | 0.6528, 0.6491, 0.6516, 0.6510, 0.6516, 0.6497, 0.6540 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| 26 | 0.6518 | 0.6496, 0.6499, 0.6562, 0.6493, 0.6505, 0.6519, 0.6555 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| 21 (numéricos por defecto) | 0.6559 | 0.6591, 0.6555, 0.6531 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=random_setups]` |
| 11 | 0.6563 | 0.6565, 0.6562, 0.6564 | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| 21 | 0.6568 | 0.6561, 0.6548, 0.6595 | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=random_setups]` |
| 35 (numéricos por defecto) | 0.6568 | 0.6610, 0.6537, 0.6511, 0.6614 | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| 12 | 0.6573 | 0.6636, 0.6535, 0.6511, 0.6610 | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| 35 | 0.6616 | 0.6599, 0.6611, 0.6639 | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
