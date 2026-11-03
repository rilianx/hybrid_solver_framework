## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 10.0 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 2.24% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild]` |
| r1 | 1 | 1.14% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| r2 | 2 | 0.81% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild]` |

**Afinado entre réplicas**: media 1.39%, desvío 0.61%, rango [0.81%, 2.24%].

**Mejor no afinado** (media entre réplicas): `default:VNS` = 4.40%. Afinado vs ese: +3.01% de gap a favor del afinado, IC95 [+1.17%, +4.74%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 10.0 s/corrida · 12 train / 6 test (clsp 6x15,12x30,24x30) · 0 configuraciones fallidas · 10500 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild]` = 0.6499

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.37%** | **233655.6** | 161617 | +33.7% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild]` |
| default:VNS | 3.70% | 240085.0 | 165545 | +31.8% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:ILS | 3.98% | 241182.3 | 166455 | +31.5% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:HYB | 4.09% | 246028.1 | 178711 | +30.2% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:SA | 7.17% | 242074.1 | 162315 | +31.3% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:TS | 7.98% | 261048.5 | 197381 | +25.9% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 8.01% | 261180.6 | 197562 | +25.9% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |

Ganancia del afinado sobre el mejor default: **+2.68%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:VNS` (mejor default por gap): +2.32% de gap a favor del afinado, IC95 [+0.77%, +3.83%].

## Réplica r1

### Catálogo `generated`

84 trials · 10.0 s/corrida · 12 train / 6 test (clsp 6x15,12x30,24x30) · 0 configuraciones fallidas · 10205 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=trivial, neighborhood=setup_toggle_flip]` = 0.6459

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.11%** | **228394.5** | 154473 | +35.2% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:HYB | 2.17% | 234252.4 | 163253 | +33.5% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:VNS | 4.03% | 239083.6 | 165452 | +32.1% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 4.27% | 241256.8 | 171063 | +31.5% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:ILS | 4.27% | 239737.0 | 165669 | +31.9% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:TS | 4.43% | 241938.5 | 171964 | +31.3% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:SA | 7.88% | 241749.4 | 162251 | +31.4% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **+2.50%**; gana en 2/6 instancias de test. Esqueletos explorados: TS × 8.

Afinado vs `default:HYB` (mejor default por gap): +1.06% de gap a favor del afinado, IC95 [-0.87%, +3.50%] — **no se distingue del ruido** con estas instancias.

## Réplica r2

### Catálogo `generated`

84 trials · 10.0 s/corrida · 12 train / 6 test (clsp 6x15,12x30,24x30) · 0 configuraciones fallidas · 10463 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild]` = 0.6418

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.57%** | **227324.1** | 153261 | +35.5% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild]` |
| default:VNS | 4.32% | 240015.7 | 165464 | +31.9% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:ILS | 4.72% | 241454.4 | 166570 | +31.5% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:HYB | 5.91% | 250950.7 | 185395 | +28.8% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:SA | 7.80% | 242074.1 | 162315 | +31.3% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 8.80% | 261207.6 | 197601 | +25.9% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:TS | 8.84% | 261370.9 | 197821 | +25.8% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **+5.29%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:VNS` (mejor default por gap): +3.74% de gap a favor del afinado, IC95 [+1.43%, +5.92%].
