## Réplicas del tuning (3)

### Catálogo `handwritten`

70 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.64% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| r1 | 1 | 0.53% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| r2 | 2 | 0.55% | `TS[constructor=job_order, neighborhood=critical_swap]` |

**Afinado entre réplicas**: media 0.57%, desvío 0.05%, rango [0.53%, 0.64%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.24%. Afinado vs ese: +0.66% de gap a favor del afinado, IC95 [+0.29%, +0.97%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 6988 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `SA[constructor=job_order, neighborhood=critical_swap]` = 0.1395

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.44%** | **1212.6** | 65 | +86.5% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 1.04% | 1219.9 | 66 | +86.4% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 1.74% | 1228.0 | 64 | +86.3% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 24.23% | 1499.0 | 149 | +83.3% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 32.28% | 1598.1 | 180 | +82.2% | `VNS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.60%**; gana en 10/10 instancias de test. Esqueletos explorados: SA × 6.

Afinado vs `default:TS` (mejor default por gap): +0.60% de gap a favor del afinado, IC95 [+0.34%, +0.89%].

## Réplica r1

### Catálogo `handwritten`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 6998 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=job_order, neighborhood=critical_swap]` = 0.1392

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.15%** | **1211.3** | 67 | +86.5% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 0.79% | 1218.9 | 65 | +86.4% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 1.12% | 1222.8 | 64 | +86.4% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 23.51% | 1492.7 | 154 | +83.4% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 32.08% | 1598.1 | 180 | +82.2% | `VNS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.62%**; gana en 9/10 instancias de test. Esqueletos explorados: TS × 6.

Afinado vs `default:TS` (mejor default por gap): +0.64% de gap a favor del afinado, IC95 [+0.20%, +1.06%].

## Réplica r2

### Catálogo `handwritten`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 6935 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=job_order, neighborhood=critical_swap]` = 0.1391

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.16%** | **1211.4** | 65 | +86.5% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 0.90% | 1220.5 | 66 | +86.4% | `TS[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 1.75% | 1230.9 | 72 | +86.3% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 24.93% | 1510.5 | 161 | +83.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 32.02% | 1598.1 | 180 | +82.2% | `VNS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.75%**; gana en 9/10 instancias de test. Esqueletos explorados: TS × 6.

Afinado vs `default:TS` (mejor default por gap): +0.75% de gap a favor del afinado, IC95 [+0.13%, +1.22%].
