## Réplicas del tuning (3)

### Catálogo `handwritten`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.50% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| r1 | 1 | 0.82% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| r2 | 2 | 0.38% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |

**Afinado entre réplicas**: media 0.57%, desvío 0.18%, rango [0.38%, 0.82%].

**Mejor no afinado** (media entre réplicas): `default:SA` = 0.70%. Afinado vs ese: +0.14% de gap a favor del afinado, IC95 [-0.08%, +0.53%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3951 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` = 0.2080 (mejor default: 0.2081, `SA[constructor=job_order, neighborhood=critical_swap]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.42%** | **836.6** | 41 | +79.0% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| default:SA | 0.59% | 838.2 | 47 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.48% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.31% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 19.50% | 997.6 | 143 | +74.9% | `TS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.18%**; gana en 4/10 instancias de test. Esqueletos explorados: SA × 20, ILS × 7, VNS × 7, TS × 6.

Afinado vs `default:SA` (mejor default por gap): +0.16% de gap a favor del afinado, IC95 [-0.23%, +0.75%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 36 | 0.2080 | 0.2076, 0.2081, 0.2079, 0.2080, 0.2081, 0.2079, 0.2081 | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| 36 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.2080 | 0.2082, 0.2077, 0.2083, 0.2077, 0.2081, 0.2076, 0.2082 | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| 35 | 0.2080 | 0.2081, 0.2081, 0.2078, 0.2082, 0.2077, 0.2080, 0.2081 | `SA[constructor=job_order, neighborhood=critical_swap]` |
| 35 (numéricos por defecto) | 0.2081 | 0.2079, 0.2080, 0.2083, 0.2079, 0.2081, 0.2081, 0.2081 | `SA[constructor=job_order, neighborhood=critical_swap]` |
| 12 | 0.2081 | 0.2079, 0.2082, 0.2082, 0.2082, 0.2081, 0.2082, 0.2078 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 13 | 0.2137 | 0.2134, 0.2138, 0.2140 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| 26 | 0.2149 | 0.2142, 0.2157, 0.2146 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_insert, perturbation=critical_kick]` |
| 26 (numéricos por defecto) | 0.2174 | 0.2164, 0.2179, 0.2179 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_insert, perturbation=critical_kick]` |

## Réplica r1

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3451 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=job_order, neighborhood=critical_swap]` = 0.2081 (mejor default: 0.2076, `SA[constructor=job_order, neighborhood=critical_swap]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.73%** | **839.3** | 42 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:SA | 0.57% | 838.1 | 45 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.46% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.30% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 19.46% | 997.6 | 143 | +74.9% | `TS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **-0.14%**; gana en 3/10 instancias de test. Esqueletos explorados: SA × 20, ILS × 8, VNS × 6, TS × 6.

Afinado vs `default:SA` (mejor default por gap): -0.16% de gap a favor del afinado, IC95 [-0.48%, +0.14%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 34 | 0.2077 | 0.2076, 0.2078, 0.2074, 0.2075, 0.2079, 0.2082, 0.2079 | `SA[constructor=job_order, neighborhood=critical_swap]` |
| 36 | 0.2078 | 0.2081, 0.2073, 0.2076, 0.2081, 0.2079, 0.2078, 0.2079 | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| 12 | 0.2079 | 0.2079, 0.2077, 0.2078, 0.2083 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 34 (numéricos por defecto), preferido: el afinado no le gana por más que el ruido ✔ | 0.2081 | 0.2078, 0.2077, 0.2085, 0.2084 | `SA[constructor=job_order, neighborhood=critical_swap]` |
| 36 (numéricos por defecto) | 0.2082 | 0.2082, 0.2083, 0.2079 | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| 32 | 0.2119 | 0.2121, 0.2121, 0.2114 | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| 14 | 0.2149 | 0.2145, 0.2147, 0.2155 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 32 (numéricos por defecto) | 0.2291 | 0.2317, 0.2243, 0.2312 | `VNS[constructor=job_order, neighborhood=critical_swap]` |

## Réplica r2

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3601 s de tuning

objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` = 0.2079 (mejor default: 0.2080, `SA[constructor=job_order, neighborhood=critical_swap]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.37%** | **835.7** | 42 | +79.0% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| default:SA | 0.78% | 839.1 | 43 | +78.9% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| default:ILS | 8.55% | 904.7 | 73 | +77.2% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.39% | 943.1 | 60 | +76.3% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:TS | 19.57% | 997.6 | 143 | +74.9% | `TS[constructor=job_order, neighborhood=critical_swap]` |

Ganancia del afinado sobre el mejor default: **+0.40%**; gana en 6/10 instancias de test. Esqueletos explorados: SA × 21, ILS × 7, VNS × 7, TS × 5.

Afinado vs `default:SA` (mejor default por gap): +0.41% de gap a favor del afinado, IC95 [-0.06%, +0.94%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 ✔ | 0.2079 | 0.2076, 0.2081, 0.2079, 0.2080, 0.2080, 0.2080, 0.2079 | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| 38 | 0.2079 | 0.2076, 0.2075, 0.2081, 0.2083, 0.2081, 0.2080, 0.2081 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 38 (numéricos por defecto) | 0.2081 | 0.2076, 0.2080, 0.2081, 0.2077, 0.2084, 0.2080, 0.2085 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 0* | 0.2082 | 0.2080, 0.2082, 0.2083 | `SA[constructor=job_order, neighborhood=critical_swap]` |
| 33 (numéricos por defecto) | 0.2089 | 0.2081, 0.2091, 0.2091, 0.2095 | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| 13 | 0.2143 | 0.2135, 0.2147, 0.2146 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| 34 | 0.2166 | 0.2135, 0.2157, 0.2206 | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| 34 (numéricos por defecto) | 0.2338 | 0.2287, 0.2475, 0.2252 | `VNS[constructor=job_order, neighborhood=critical_swap]` |
