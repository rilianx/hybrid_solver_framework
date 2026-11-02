## Réplicas del tuning (3)

### Catálogo `handwritten`

50 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.52% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| r1 | 1 | 1.31% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| r2 | 2 | 0.26% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |

**Afinado entre réplicas**: media 0.70%, desvío 0.45%, rango [0.26%, 1.31%].

**Mejor no afinado** (media entre réplicas): `default:LOCAL_BRANCH` = 0.53%. Afinado vs ese: -0.17% de gap a favor del afinado, IC95 [-0.73%, +0.26%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

50 trials · 10.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 7628 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` = 0.6501

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.52%** | **86499.0** | 16207 | +34.5% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| default:LNS_MIP | 0.31% | 86238.1 | 15550 | +34.7% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:LOCAL_BRANCH | 0.42% | 86345.8 | 15649 | +34.6% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:MIP_PERTURB | 1.39% | 87149.7 | 15548 | +34.0% | `MIP_PERTURB[constructor=lot_for_lot, destruction=period_window, neighborhood=setup_flip]` |
| default:FIX_OPT | 3.04% | 88419.3 | 15022 | +33.1% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | 6.96% | 91971.2 | 16672 | +30.4% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:VNS | 8.56% | 93369.1 | 17157 | +29.3% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 10.27% | 94943.0 | 18067 | +28.1% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:GRASP | 14.23% | 98283.6 | 18263 | +25.6% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | 27.59% | 109830.8 | 20918 | +16.9% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.30%**; gana en 7/10 instancias de test. Esqueletos explorados: LNS_MIP × 7.

Afinado vs `default:LNS_MIP` (mejor default por gap): -0.21% de gap a favor del afinado, IC95 [-0.83%, +0.14%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `handwritten`

50 trials · 10.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 7750 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` = 0.6615

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.30%** | **87226.8** | 16782 | +34.0% | `LNS_MIP[constructor=greedy_latest_source, destruction=period_window]` |
| default:LOCAL_BRANCH | 0.55% | 86479.1 | 15734 | +34.5% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LNS_MIP | 1.04% | 86908.4 | 15979 | +34.2% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:MIP_PERTURB | 2.43% | 88178.7 | 16592 | +33.3% | `MIP_PERTURB[constructor=lot_for_lot, destruction=period_window, neighborhood=setup_flip]` |
| default:FIX_OPT | 3.03% | 88419.3 | 15022 | +33.1% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | 7.88% | 92813.8 | 17166 | +29.7% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:VNS | 10.54% | 95159.8 | 17997 | +28.0% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 14.82% | 98780.5 | 18545 | +25.2% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:GRASP | 22.10% | 105018.3 | 19155 | +20.5% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | 37.40% | 118280.7 | 22404 | +10.5% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **-0.86%**; gana en 4/10 instancias de test. Esqueletos explorados: LNS_MIP × 7.

Afinado vs `default:LOCAL_BRANCH` (mejor default por gap): -0.75% de gap a favor del afinado, IC95 [-1.83%, +0.13%] — **no se distingue del ruido** con estas instancias.

## Réplica r2

### Catálogo `handwritten`

50 trials · 10.0 s/corrida · 10 train / 10 test (clsp 10x15) · 0 configuraciones fallidas · 7829 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` = 0.6497

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.23%** | **86191.0** | 15523 | +34.8% | `LNS_MIP[constructor=greedy_unit_marginal_cost, destruction=period_window]` |
| default:LOCAL_BRANCH | 0.59% | 86523.1 | 15766 | +34.5% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LNS_MIP | 0.59% | 86479.7 | 15485 | +34.5% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:MIP_PERTURB | 2.07% | 87766.7 | 15780 | +33.6% | `MIP_PERTURB[constructor=lot_for_lot, destruction=period_window, neighborhood=setup_flip]` |
| default:FIX_OPT | 3.02% | 88419.3 | 15022 | +33.1% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | 6.98% | 92017.2 | 16710 | +30.3% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:VNS | 8.45% | 93322.1 | 17272 | +29.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 11.30% | 95737.6 | 17553 | +27.5% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:GRASP | 15.26% | 99168.1 | 18218 | +24.9% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | 29.48% | 111483.4 | 21201 | +15.6% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.33%**; gana en 6/10 instancias de test. Esqueletos explorados: LNS_MIP × 7.

Afinado vs `default:LOCAL_BRANCH` (mejor default por gap): +0.35% de gap a favor del afinado, IC95 [+0.15%, +0.57%].
