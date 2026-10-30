## Réplicas del tuning (3)

### Catálogo `handwritten`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 4.02% | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| r1 | 1 | 2.71% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| r2 | 2 | 2.94% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |

**Afinado entre réplicas**: media 3.22%, desvío 0.57%, rango [2.71%, 4.02%].

**Mejor no afinado** (media entre réplicas): `ILS:constructor=greedy_earliest_end` = 3.63%. Afinado vs ese: +0.41% de gap a favor del afinado, IC95 [-2.95%, +3.61%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3062 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` = 0.2150 (mejor default: 0.2271, `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **3.80%** | **872.0** | 54 | +78.1% | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| ILS:constructor=greedy_earliest_end | 3.53% | 870.4 | 61 | +78.1% | `ILS[constructor=greedy_earliest_end, neighborhood=critical_swap, perturbation=critical_kick]` |
| ILS:constructor=greedy_most_work_remaining | 3.80% | 872.0 | 54 | +78.1% | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| VNS:constructor=greedy_most_work_remaining | 3.82% | 872.0 | 46 | +78.1% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| SA:constructor=greedy_most_work_remaining | 4.96% | 882.1 | 60 | +77.8% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| VNS:constructor=greedy_earliest_end | 5.13% | 883.7 | 66 | +77.8% | `VNS[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| SA:constructor=greedy_earliest_end | 6.03% | 891.0 | 62 | +77.6% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| LNS_MIP:constructor=greedy_earliest_end | 6.52% | 895.0 | 53 | +77.5% | `LNS_MIP[constructor=greedy_earliest_end, destruction=time_window_removal]` |
| LNS_MIP:constructor=greedy_most_work_remaining | 7.43% | 901.9 | 62 | +77.3% | `LNS_MIP[constructor=greedy_most_work_remaining, destruction=time_window_removal]` |
| default:ILS | 11.25% | 934.9 | 70 | +76.5% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.60% | 953.8 | 85 | +76.0% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:LNS_MIP | 17.12% | 985.6 | 90 | +75.2% | `LNS_MIP[constructor=job_order, destruction=time_window_removal]` |
| ILS:neighborhood=critical_insert | 18.38% | 994.8 | 92 | +75.0% | `ILS[constructor=job_order, neighborhood=critical_insert, perturbation=critical_kick]` |
| VNS:neighborhood=critical_insert | 24.22% | 1043.7 | 93 | +73.8% | `VNS[constructor=job_order, neighborhood=critical_insert]` |
| LNS_MIP:destruction=machine_removal | 28.24% | 1078.3 | 134 | +72.9% | `LNS_MIP[constructor=job_order, destruction=machine_removal]` |
| default:SA | 34.10% | 1125.9 | 120 | +71.7% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| SA:neighborhood=critical_insert | 371.99% | 3973.9 | 482 | +0.1% | `SA[constructor=job_order, neighborhood=critical_insert]` |

Ganancia del afinado sobre el mejor default: **-0.19%**; gana en 6/10 instancias de test. Esqueletos explorados: ILS × 19, VNS × 10, SA × 6, LNS_MIP × 5.

Afinado vs `ILS:constructor=greedy_earliest_end` (mejor default por gap): -0.27% de gap a favor del afinado, IC95 [-3.82%, +3.32%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 13 ✔ | 0.2150 | 0.2151, 0.2153, 0.2140, 0.2156, 0.2144, 0.2152 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| 14 | 0.2159 | 0.2155, 0.2154, 0.2151, 0.2164, 0.2157, 0.2172 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 12 | 0.2168 | 0.2165, 0.2175, 0.2164 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 27 | 0.2186 | 0.2182, 0.2187, 0.2188 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_insert]` |
| 15 | 0.2207 | 0.2206, 0.2203, 0.2212 | `LNS_MIP[constructor=greedy_most_work_remaining, destruction=time_window_removal]` |
| 27 (numéricos por defecto) | 0.2213 | 0.2222, 0.2198, 0.2218 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_insert]` |
| 1* | 0.2293 | 0.2271, 0.2284, 0.2324 | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |

## Réplica r1

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 2932 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` = 0.2136 (mejor default: 0.2282, `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.70%** | **860.9** | 47 | +78.4% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| ILS:constructor=greedy_earliest_end | 3.71% | 870.1 | 60 | +78.1% | `ILS[constructor=greedy_earliest_end, neighborhood=critical_swap, perturbation=critical_kick]` |
| ILS:constructor=greedy_most_work_remaining | 4.00% | 872.0 | 54 | +78.1% | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| VNS:constructor=greedy_most_work_remaining | 4.03% | 872.0 | 46 | +78.1% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| SA:constructor=greedy_most_work_remaining | 5.24% | 882.6 | 60 | +77.8% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| VNS:constructor=greedy_earliest_end | 5.35% | 883.7 | 66 | +77.8% | `VNS[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| SA:constructor=greedy_earliest_end | 6.14% | 890.0 | 61 | +77.6% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| LNS_MIP:constructor=greedy_earliest_end | 6.77% | 895.3 | 53 | +77.5% | `LNS_MIP[constructor=greedy_earliest_end, destruction=time_window_removal]` |
| LNS_MIP:constructor=greedy_most_work_remaining | 7.57% | 901.3 | 62 | +77.3% | `LNS_MIP[constructor=greedy_most_work_remaining, destruction=time_window_removal]` |
| default:ILS | 11.50% | 934.9 | 70 | +76.5% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.84% | 953.8 | 85 | +76.0% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:LNS_MIP | 17.23% | 984.3 | 90 | +75.2% | `LNS_MIP[constructor=job_order, destruction=time_window_removal]` |
| ILS:neighborhood=critical_insert | 18.63% | 994.8 | 92 | +75.0% | `ILS[constructor=job_order, neighborhood=critical_insert, perturbation=critical_kick]` |
| VNS:neighborhood=critical_insert | 24.48% | 1043.7 | 93 | +73.8% | `VNS[constructor=job_order, neighborhood=critical_insert]` |
| LNS_MIP:destruction=machine_removal | 28.46% | 1078.0 | 135 | +72.9% | `LNS_MIP[constructor=job_order, destruction=machine_removal]` |
| default:SA | 33.89% | 1121.6 | 122 | +71.8% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| SA:neighborhood=critical_insert | 373.07% | 3973.9 | 482 | +0.1% | `SA[constructor=job_order, neighborhood=critical_insert]` |

Ganancia del afinado sobre el mejor default: **+1.06%**; gana en 6/10 instancias de test. Esqueletos explorados: VNS × 23, SA × 6, ILS × 6, LNS_MIP × 5.

Afinado vs `ILS:constructor=greedy_earliest_end` (mejor default por gap): +1.01% de gap a favor del afinado, IC95 [-2.39%, +4.05%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 19 ✔ | 0.2136 | 0.2126, 0.2142, 0.2138 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 13 | 0.2151 | 0.2149, 0.2143, 0.2161 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| 19 (numéricos por defecto) | 0.2158 | 0.2141, 0.2170, 0.2164 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 12 | 0.2174 | 0.2164, 0.2185, 0.2174 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 35 | 0.2189 | 0.2199, 0.2195, 0.2173 | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| 15 | 0.2208 | 0.2195, 0.2216, 0.2213 | `LNS_MIP[constructor=greedy_most_work_remaining, destruction=time_window_removal]` |
| 1* | 0.2252 | 0.2282, 0.2241, 0.2232 | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| 35 (numéricos por defecto) | 0.2326 | 0.2371, 0.2282, 0.2326 | `VNS[constructor=job_order, neighborhood=critical_swap]` |

## Réplica r2

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (jobshop 10x10) · 0 configuraciones fallidas · 3160 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` = 0.2140 (mejor default: 0.2248, `LNS_MIP[constructor=job_order, destruction=time_window_removal]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.94%** | **862.8** | 49 | +78.3% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| ILS:constructor=greedy_earliest_end | 3.41% | 867.4 | 58 | +78.2% | `ILS[constructor=greedy_earliest_end, neighborhood=critical_swap, perturbation=critical_kick]` |
| ILS:constructor=greedy_most_work_remaining | 3.92% | 871.2 | 54 | +78.1% | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| VNS:constructor=greedy_most_work_remaining | 4.04% | 872.0 | 46 | +78.1% | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| SA:constructor=greedy_most_work_remaining | 4.88% | 879.4 | 58 | +77.9% | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| SA:constructor=greedy_earliest_end | 5.11% | 881.4 | 56 | +77.8% | `SA[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| VNS:constructor=greedy_earliest_end | 5.12% | 881.5 | 63 | +77.8% | `VNS[constructor=greedy_earliest_end, neighborhood=critical_swap]` |
| LNS_MIP:constructor=greedy_earliest_end | 6.09% | 889.6 | 53 | +77.6% | `LNS_MIP[constructor=greedy_earliest_end, destruction=time_window_removal]` |
| LNS_MIP:constructor=greedy_most_work_remaining | 7.11% | 897.5 | 62 | +77.4% | `LNS_MIP[constructor=greedy_most_work_remaining, destruction=time_window_removal]` |
| default:ILS | 11.32% | 933.3 | 70 | +76.5% | `ILS[constructor=job_order, neighborhood=critical_swap, perturbation=critical_kick]` |
| default:VNS | 13.84% | 953.8 | 85 | +76.0% | `VNS[constructor=job_order, neighborhood=critical_swap]` |
| default:LNS_MIP | 13.99% | 957.0 | 89 | +75.9% | `LNS_MIP[constructor=job_order, destruction=time_window_removal]` |
| ILS:neighborhood=critical_insert | 18.28% | 991.6 | 90 | +75.1% | `ILS[constructor=job_order, neighborhood=critical_insert, perturbation=critical_kick]` |
| LNS_MIP:destruction=machine_removal | 21.34% | 1017.0 | 118 | +74.4% | `LNS_MIP[constructor=job_order, destruction=machine_removal]` |
| default:SA | 24.38% | 1042.3 | 88 | +73.8% | `SA[constructor=job_order, neighborhood=critical_swap]` |
| VNS:neighborhood=critical_insert | 24.49% | 1043.7 | 93 | +73.8% | `VNS[constructor=job_order, neighborhood=critical_insert]` |
| SA:neighborhood=critical_insert | 373.13% | 3973.9 | 482 | +0.1% | `SA[constructor=job_order, neighborhood=critical_insert]` |

Ganancia del afinado sobre el mejor default: **+0.53%**; gana en 6/10 instancias de test. Esqueletos explorados: VNS × 23, SA × 7, ILS × 5, LNS_MIP × 5.

Afinado vs `ILS:constructor=greedy_earliest_end` (mejor default por gap): +0.47% de gap a favor del afinado, IC95 [-2.92%, +3.56%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 22 ✔ | 0.2140 | 0.2127, 0.2148, 0.2148, 0.2135, 0.2140 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 13 | 0.2154 | 0.2165, 0.2153, 0.2140, 0.2152, 0.2161 | `ILS[constructor=greedy_most_work_remaining, neighborhood=critical_swap, perturbation=critical_kick]` |
| 22 (numéricos por defecto) | 0.2159 | 0.2150, 0.2152, 0.2164, 0.2171 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 12 | 0.2178 | 0.2177, 0.2178, 0.2178 | `SA[constructor=greedy_most_work_remaining, neighborhood=critical_swap]` |
| 18 | 0.2185 | 0.2185, 0.2190, 0.2181 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_insert]` |
| 15 | 0.2208 | 0.2213, 0.2215, 0.2196 | `LNS_MIP[constructor=greedy_most_work_remaining, destruction=time_window_removal]` |
| 18 (numéricos por defecto) | 0.2217 | 0.2212, 0.2207, 0.2230 | `VNS[constructor=greedy_most_work_remaining, neighborhood=critical_insert]` |
| 3* | 0.2291 | 0.2248, 0.2233, 0.2393 | `LNS_MIP[constructor=job_order, destruction=time_window_removal]` |
