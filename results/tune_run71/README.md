## Réplicas del tuning (3)

### Catálogo `generated`

50 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.69% | `HYB[constructor=random, neighborhood=lot_consolidation_window, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` |
| r1 | 1 | 0.25% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` |
| r2 | 2 | 0.36% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` |

**Afinado entre réplicas**: media 0.43%, desvío 0.19%, rango [0.25%, 0.69%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.50%. Afinado vs ese: +0.07% de gap a favor del afinado, IC95 [-0.07%, +0.21%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 10275 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `HYB[constructor=random, neighborhood=lot_consolidation_window, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` = 0.6506

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.53%** | **86509.8** | 15200 | +34.5% | `HYB[constructor=random, neighborhood=lot_consolidation_window, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` |
| default:HYB | 0.42% | 86406.1 | 15141 | +34.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:TS | 1.21% | 87106.1 | 15390 | +34.1% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 1.21% | 87106.2 | 15390 | +34.1% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:VNS | 2.01% | 87826.4 | 15704 | +33.5% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:ILS | 2.55% | 88277.3 | 15748 | +33.2% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:SA | 9.00% | 93891.4 | 17320 | +28.9% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **-0.12%**; gana en 4/10 instancias de test. Esqueletos explorados: HYB × 8.

Afinado vs `default:HYB` (mejor default por gap): -0.12% de gap a favor del afinado, IC95 [-0.43%, +0.15%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 10208 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` = 0.6481

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.25%** | **86156.3** | 15298 | +34.8% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` |
| default:HYB | 0.38% | 86242.2 | 15129 | +34.7% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:TS | 1.35% | 87084.8 | 15370 | +34.1% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 1.35% | 87086.9 | 15368 | +34.1% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:VNS | 1.75% | 87485.2 | 15737 | +33.8% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:ILS | 2.40% | 88019.1 | 15768 | +33.4% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:SA | 9.13% | 93860.3 | 17339 | +29.0% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **+0.10%**; gana en 7/10 instancias de test. Esqueletos explorados: HYB × 8.

Afinado vs `default:HYB` (mejor default por gap): +0.13% de gap a favor del afinado, IC95 [-0.05%, +0.32%] — **no se distingue del ruido** con estas instancias.

## Réplica r2

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 10231 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` = 0.6476

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.31%** | **86258.4** | 15351 | +34.7% | `HYB[constructor=random, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=period_window]` |
| default:HYB | 0.51% | 86394.2 | 15147 | +34.6% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:TS | 1.33% | 87122.8 | 15422 | +34.1% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 1.33% | 87122.8 | 15422 | +34.1% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:VNS | 2.02% | 87748.5 | 15700 | +33.6% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:ILS | 2.64% | 88263.6 | 15752 | +33.2% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:SA | 9.18% | 93945.3 | 17278 | +28.9% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **+0.16%**; gana en 8/10 instancias de test. Esqueletos explorados: HYB × 8.

Afinado vs `default:HYB` (mejor default por gap): +0.20% de gap a favor del afinado, IC95 [-0.01%, +0.39%] — **no se distingue del ruido** con estas instancias.
