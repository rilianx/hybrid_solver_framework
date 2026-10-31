## Réplicas del tuning (3)

### Catálogo `generated`

70 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.32% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| r1 | 1 | 0.25% | `TS[constructor=greedy_lookahead_lower_bound, neighborhood=critical_path_adjacent_swap]` |
| r2 | 2 | 0.53% | `SA[constructor=random, neighborhood=critical_path_adjacent_swap]` |

**Afinado entre réplicas**: media 0.36%, desvío 0.12%, rango [0.25%, 0.53%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.22%. Afinado vs ese: +0.86% de gap a favor del afinado, IC95 [+0.61%, +1.07%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 6975 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` = 0.1386

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.15%** | **1203.8** | 65 | +86.6% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 1.05% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.47% | 1219.9 | 71 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 11.93% | 1346.0 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.23% | 1529.0 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.90%**; gana en 10/10 instancias de test. Esqueletos explorados: TS × 4.

Afinado vs `default:TS` (mejor default por gap): +0.90% de gap a favor del afinado, IC95 [+0.67%, +1.11%].

## Réplica r1

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7176 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=greedy_lookahead_lower_bound, neighborhood=critical_path_adjacent_swap]` = 0.1387

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.21%** | **1203.0** | 66 | +86.6% | `TS[constructor=greedy_lookahead_lower_bound, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 1.18% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.87% | 1223.2 | 73 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 12.06% | 1346.0 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.39% | 1529.0 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.96%**; gana en 10/10 instancias de test. Esqueletos explorados: TS × 6, SA × 1.

Afinado vs `default:TS` (mejor default por gap): +0.97% de gap a favor del afinado, IC95 [+0.78%, +1.14%].

## Réplica r2

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7319 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `SA[constructor=random, neighborhood=critical_path_adjacent_swap]` = 0.1392

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.30%** | **1206.4** | 66 | +86.6% | `SA[constructor=random, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 0.99% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.70% | 1223.5 | 71 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 11.85% | 1346.1 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.13% | 1529.0 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.69%**; gana en 9/10 instancias de test. Esqueletos explorados: SA × 7.

Afinado vs `default:TS` (mejor default por gap): +0.69% de gap a favor del afinado, IC95 [+0.34%, +0.99%].
