## Réplicas del tuning (3)

### Catálogo `generated`

70 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.81% | `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| r1 | 1 | 0.51% | `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| r2 | 2 | 0.88% | `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` |

**Afinado entre réplicas**: media 0.73%, desvío 0.16%, rango [0.51%, 0.88%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.72%. Afinado vs ese: +0.99% de gap a favor del afinado, IC95 [+0.63%, +1.33%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7284 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` = 0.1397

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.55%** | **1210.6** | 66 | +86.5% | `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 1.30% | 1219.6 | 68 | +86.4% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.65% | 1224.1 | 73 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 13.13% | 1363.2 | 147 | +84.8% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.00% | 1529.0 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.74%**; gana en 9/10 instancias de test. Esqueletos explorados: TS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.75% de gap a favor del afinado, IC95 [+0.42%, +1.08%].

## Réplica r1

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7188 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` = 0.1392

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.31%** | **1206.9** | 66 | +86.6% | `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 1.59% | 1222.4 | 70 | +86.4% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.73% | 1224.1 | 69 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 13.52% | 1367.0 | 154 | +84.8% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.16% | 1529.7 | 159 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+1.27%**; gana en 10/10 instancias de test. Esqueletos explorados: TS × 7.

Afinado vs `default:TS` (mejor default por gap): +1.27% de gap a favor del afinado, IC95 [+0.87%, +1.67%].

## Réplica r2

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7278 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` = 0.1392

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.39%** | **1211.4** | 66 | +86.5% | `TS[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 1.32% | 1222.8 | 70 | +86.4% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.67% | 1227.3 | 75 | +86.3% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 13.86% | 1375.2 | 160 | +84.7% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 26.88% | 1531.1 | 161 | +82.9% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.93%**; gana en 10/10 instancias de test. Esqueletos explorados: TS × 6.

Afinado vs `default:TS` (mejor default por gap): +0.93% de gap a favor del afinado, IC95 [+0.48%, +1.37%].
