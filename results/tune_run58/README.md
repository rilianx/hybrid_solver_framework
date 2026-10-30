## Réplicas del tuning (3)

### Catálogo `generated`

70 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.42% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| r1 | 1 | 0.74% | `TS[constructor=greedy_ect_mwkr_dispatch, neighborhood=critical_path_adjacent_swap]` |
| r2 | 2 | 0.54% | `SA[constructor=random, neighborhood=critical_path_adjacent_swap]` |

**Afinado entre réplicas**: media 0.56%, desvío 0.13%, rango [0.42%, 0.74%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.13%. Afinado vs ese: +0.57% de gap a favor del afinado, IC95 [+0.28%, +0.83%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7305 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` = 0.1390

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **1205.8** | 66 | +86.6% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 0.91% | 1213.7 | 68 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.33% | 1219.0 | 74 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 11.71% | 1344.3 | 137 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.12% | 1528.6 | 160 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.65%**; gana en 10/10 instancias de test. Esqueletos explorados: TS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.65% de gap a favor del afinado, IC95 [+0.40%, +0.90%].

## Réplica r1

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7175 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=greedy_ect_mwkr_dispatch, neighborhood=critical_path_adjacent_swap]` = 0.1388

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.34%** | **1209.6** | 67 | +86.5% | `TS[constructor=greedy_ect_mwkr_dispatch, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 0.77% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.05% | 1218.4 | 72 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 11.61% | 1346.1 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 26.85% | 1529.0 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.42%**; gana en 8/10 instancias de test. Esqueletos explorados: TS × 3, SA × 4.

Afinado vs `default:TS` (mejor default por gap): +0.42% de gap a favor del afinado, IC95 [+0.11%, +0.74%].

## Réplica r2

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7328 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `SA[constructor=random, neighborhood=critical_path_adjacent_swap]` = 0.1392

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.46%** | **1207.2** | 66 | +86.5% | `SA[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 1.08% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.44% | 1219.3 | 73 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 11.94% | 1346.0 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.24% | 1529.0 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.62%**; gana en 8/10 instancias de test. Esqueletos explorados: SA × 7.

Afinado vs `default:TS` (mejor default por gap): +0.62% de gap a favor del afinado, IC95 [+0.27%, +0.93%].
