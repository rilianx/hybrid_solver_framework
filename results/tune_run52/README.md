## Réplicas del tuning (3)

### Catálogo `handwritten`

70 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.12% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| r1 | 1 | 0.31% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| r2 | 2 | 0.16% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |

**Afinado entre réplicas**: media 0.20%, desvío 0.08%, rango [0.12%, 0.31%].

**Mejor no afinado** (media entre réplicas): `default:SA` = 0.78%. Afinado vs ese: +0.58% de gap a favor del afinado, IC95 [+0.30%, +0.91%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3556 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` = 0.2077

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.08%** | **833.4** | 40 | +79.0% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| default:SA | 0.70% | 838.4 | 40 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.53% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.37% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 19.55% | 997.6 | 143 | +74.9% | `TS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.60%**; gana en 8/10 instancias de test. Esqueletos explorados: SA × 6.

Afinado vs `default:SA` (mejor default por gap): +0.62% de gap a favor del afinado, IC95 [+0.24%, +1.02%].

## Réplica r1

### Catálogo `handwritten`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3549 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` = 0.2083

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.23%** | **834.9** | 39 | +79.0% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| default:SA | 0.74% | 839.2 | 39 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.48% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.31% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 19.50% | 997.6 | 143 | +74.9% | `TS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.51%**; gana en 9/10 instancias de test. Esqueletos explorados: SA × 6.

Afinado vs `default:SA` (mejor default por gap): +0.52% de gap a favor del afinado, IC95 [+0.20%, +0.95%].

## Réplica r2

### Catálogo `handwritten`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3590 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` = 0.2079

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.15%** | **833.7** | 41 | +79.0% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| default:SA | 0.75% | 838.6 | 39 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.56% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.40% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 19.58% | 997.6 | 143 | +74.9% | `TS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.58%**; gana en 10/10 instancias de test. Esqueletos explorados: SA × 6.

Afinado vs `default:SA` (mejor default por gap): +0.61% de gap a favor del afinado, IC95 [+0.30%, +0.94%].
