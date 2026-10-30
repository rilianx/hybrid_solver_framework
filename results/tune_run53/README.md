## Réplicas del tuning (3)

### Catálogo `handwritten`

70 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.42% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| r1 | 1 | 0.25% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| r2 | 2 | 0.15% | `TS[constructor=greedy_earliest_end, neighborhood=critical_swap]` |

**Afinado entre réplicas**: media 0.27%, desvío 0.11%, rango [0.15%, 0.42%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 0.09%. Afinado vs ese: -0.19% de gap a favor del afinado, IC95 [-0.43%, +0.06%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3545 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `TS[constructor=job_order, neighborhood=critical_swap]` = 0.2075

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.40%** | **836.1** | 44 | +79.0% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 0.06% | 833.2 | 41 | +79.0% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 0.71% | 838.5 | 40 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.53% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.38% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **-0.35%**; gana en 1/10 instancias de test. Esqueletos explorados: TS × 3, SA × 3.

Afinado vs `default:TS` (mejor default por gap): -0.33% de gap a favor del afinado, IC95 [-0.82%, +0.04%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `handwritten`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3529 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` = 0.2080

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.25%** | **834.6** | 42 | +79.0% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| default:TS | 0.09% | 833.2 | 41 | +79.0% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 1.00% | 841.0 | 46 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.56% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.40% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **-0.17%**; gana en 2/10 instancias de test. Esqueletos explorados: SA × 6.

Afinado vs `default:TS` (mejor default por gap): -0.16% de gap a favor del afinado, IC95 [-0.45%, +0.10%] — **no se distingue del ruido** con estas instancias.

## Réplica r2

### Catálogo `handwritten`

70 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3569 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `TS[constructor=greedy_earliest_end, neighborhood=critical_swap]` = 0.2074

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.13%** | **833.7** | 41 | +79.0% | `TS[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| default:TS | 0.07% | 833.2 | 41 | +79.0% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 0.81% | 839.2 | 38 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.55% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.39% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **-0.06%**; gana en 2/10 instancias de test. Esqueletos explorados: TS × 3, SA × 3.

Afinado vs `default:TS` (mejor default por gap): -0.06% de gap a favor del afinado, IC95 [-0.25%, +0.15%] — **no se distingue del ruido** con estas instancias.
