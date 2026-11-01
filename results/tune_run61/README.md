## Réplicas del tuning (3)

### Catálogo `generated`

70 trials · 15.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.57% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |
| r1 | 1 | 0.57% | `PR[constructor=trivial, neighborhood=critical_block_end_insertion, relink=kendall_adjacent_swap_relink]` |
| r2 | 2 | 0.44% | `PR[constructor=random, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |

**Afinado entre réplicas**: media 0.53%, desvío 0.06%, rango [0.44%, 0.57%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.42%. Afinado vs ese: +0.89% de gap a favor del afinado, IC95 [+0.69%, +1.09%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

70 trials · 15.0 s/corrida · 10 train / 10 test (jobshop 20x15) · 0 configuraciones fallidas · 10744 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` = 0.1184

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.32%** | **1396.6** | 78 | +88.3% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |
| default:TS | 1.17% | 1408.4 | 78 | +88.2% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:PR | 1.77% | 1417.1 | 87 | +88.1% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=kendall_adjacent_swap_relink]` |
| default:SA | 2.76% | 1430.9 | 89 | +88.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 21.52% | 1689.9 | 121 | +85.8% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 34.90% | 1873.6 | 125 | +84.2% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.84%**; gana en 10/10 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:TS` (mejor default por gap): +0.85% de gap a favor del afinado, IC95 [+0.60%, +1.10%].

## Réplica r1

### Catálogo `generated`

70 trials · 15.0 s/corrida · 10 train / 10 test (jobshop 20x15) · 0 configuraciones fallidas · 10698 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=trivial, neighborhood=critical_block_end_insertion, relink=kendall_adjacent_swap_relink]` = 0.1181

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.20%** | **1396.6** | 76 | +88.3% | `PR[constructor=trivial, neighborhood=critical_block_end_insertion, relink=kendall_adjacent_swap_relink]` |
| default:TS | 1.04% | 1408.4 | 78 | +88.2% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:PR | 1.64% | 1417.1 | 87 | +88.1% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=kendall_adjacent_swap_relink]` |
| default:SA | 2.54% | 1429.5 | 86 | +88.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 21.37% | 1689.9 | 121 | +85.8% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 34.73% | 1873.6 | 125 | +84.2% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.84%**; gana en 10/10 instancias de test. Esqueletos explorados: PR × 6.

Afinado vs `default:TS` (mejor default por gap): +0.84% de gap a favor del afinado, IC95 [+0.60%, +1.04%].

## Réplica r2

### Catálogo `generated`

70 trials · 15.0 s/corrida · 10 train / 10 test (jobshop 20x15) · 0 configuraciones fallidas · 10742 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=random, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` = 0.1180

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.39%** | **1394.8** | 76 | +88.3% | `PR[constructor=random, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |
| default:TS | 1.36% | 1408.4 | 78 | +88.2% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:PR | 1.97% | 1417.1 | 87 | +88.1% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=kendall_adjacent_swap_relink]` |
| default:SA | 2.63% | 1426.0 | 82 | +88.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 21.76% | 1689.9 | 121 | +85.8% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 35.17% | 1873.6 | 125 | +84.2% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.97%**; gana en 10/10 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:TS` (mejor default por gap): +0.97% de gap a favor del afinado, IC95 [+0.78%, +1.18%].
