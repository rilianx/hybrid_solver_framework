## Réplicas del tuning (3)

### Catálogo `generated`

70 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.17% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| r1 | 1 | 0.23% | `SA[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap]` |
| r2 | 2 | 0.25% | `TS[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap]` |

**Afinado entre réplicas**: media 0.22%, desvío 0.03%, rango [0.17%, 0.25%].

**Mejor no afinado** (media entre réplicas): `default:SA` = 0.36%. Afinado vs ese: +0.14% de gap a favor del afinado, IC95 [+0.03%, +0.25%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3665 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` = 0.2075

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.17%** | **834.0** | 40 | +79.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 0.30% | 835.1 | 42 | +79.0% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 0.35% | 835.4 | 38 | +79.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 3.65% | 863.4 | 58 | +78.3% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 10.79% | 922.3 | 64 | +76.8% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.13%**; gana en 4/10 instancias de test. Esqueletos explorados: SA × 7.

Afinado vs `default:TS` (mejor default por gap): +0.12% de gap a favor del afinado, IC95 [-0.13%, +0.39%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3642 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap]` = 0.2075

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.22%** | **834.4** | 38 | +79.0% | `SA[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 0.42% | 836.0 | 39 | +79.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 0.64% | 837.9 | 39 | +78.9% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 3.64% | 863.4 | 58 | +78.3% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 10.78% | 922.3 | 64 | +76.8% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.20%**; gana en 6/10 instancias de test. Esqueletos explorados: SA × 7.

Afinado vs `default:SA` (mejor default por gap): +0.20% de gap a favor del afinado, IC95 [+0.07%, +0.35%].

## Réplica r2

### Catálogo `generated`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3490 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `TS[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap]` = 0.2072

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.24%** | **834.5** | 38 | +79.0% | `TS[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap]` |
| default:TS | 0.23% | 834.7 | 42 | +79.0% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 0.28% | 834.9 | 39 | +79.0% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 3.54% | 862.6 | 57 | +78.3% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 10.77% | 922.2 | 64 | +76.8% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.02%**; gana en 3/10 instancias de test. Esqueletos explorados: TS × 5, SA × 1.

Afinado vs `default:TS` (mejor default por gap): -0.00% de gap a favor del afinado, IC95 [-0.43%, +0.36%] — **no se distingue del ruido** con estas instancias.
