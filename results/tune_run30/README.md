## Réplicas del tuning (3)

### Catálogo `handwritten`

40 trials · 5.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.24% | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| r1 | 1 | 0.46% | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| r2 | 2 | 2.22% | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |

**Afinado entre réplicas**: media 1.30%, desvío 0.72%, rango [0.46%, 2.22%].

**Mejor no afinado** (media entre réplicas): `default:ILS` = 2.31%. Afinado vs ese: +1.01% de gap a favor del afinado, IC95 [+0.31%, +1.76%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp 30) · 0 configuraciones fallidas · 3037 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` = 0.3222 (mejor default: 0.3235, `VNS[constructor=singleton_routes, neighborhood=relocate]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.23%** | **676.9** | 157 | +66.4% | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| default:ILS | 2.38% | 683.2 | 154 | +66.1% | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| ILS:constructor=greedy_nearest_from_depot | 2.82% | 686.2 | 156 | +65.9% | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| ILS:constructor=greedy_cheapest_insertion | 3.08% | 687.3 | 153 | +65.9% | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| default:VNS | 3.34% | 689.6 | 156 | +65.8% | `VNS[constructor=singleton_routes, neighborhood=relocate]` |
| VNS:constructor=greedy_cheapest_insertion | 3.46% | 691.1 | 159 | +65.7% | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| VNS:constructor=greedy_nearest_from_depot | 3.67% | 692.7 | 160 | +65.6% | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| default:SA | 9.20% | 730.2 | 174 | +63.7% | `SA[constructor=singleton_routes, neighborhood=relocate]` |
| SA:constructor=greedy_cheapest_insertion | 9.62% | 732.3 | 171 | +63.6% | `SA[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| SA:constructor=greedy_nearest_from_depot | 10.04% | 735.9 | 172 | +63.5% | `SA[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| LNS_MIP:constructor=greedy_cheapest_insertion | 28.92% | 860.5 | 201 | +57.3% | `LNS_MIP[constructor=greedy_cheapest_insertion, destruction=random_removal]` |
| LNS_MIP:constructor=greedy_nearest_from_depot | 53.11% | 1036.7 | 295 | +48.5% | `LNS_MIP[constructor=greedy_nearest_from_depot, destruction=random_removal]` |
| LNS_MIP:destruction=radial_removal | 62.52% | 1082.0 | 291 | +46.3% | `LNS_MIP[constructor=singleton_routes, destruction=radial_removal]` |
| default:LNS_MIP | 80.62% | 1195.0 | 252 | +40.7% | `LNS_MIP[constructor=singleton_routes, destruction=random_removal]` |
| ILS:neighborhood=two_opt | 123.70% | 1496.9 | 406 | +25.7% | `ILS[constructor=singleton_routes, neighborhood=two_opt, perturbation=relocate_kick]` |
| VNS:neighborhood=two_opt | 153.17% | 1687.1 | 430 | +16.2% | `VNS[constructor=singleton_routes, neighborhood=two_opt]` |
| SA:neighborhood=two_opt | 202.35% | 2013.6 | 442 | +0.0% | `SA[constructor=singleton_routes, neighborhood=two_opt]` |

Ganancia del afinado sobre el mejor default: **+0.93%**; gana en 8/10 instancias de test. Esqueletos explorados: VNS × 24, SA × 6, ILS × 5, LNS_MIP × 5.

Afinado vs `default:ILS` (mejor default por gap): +1.15% de gap a favor del afinado, IC95 [+0.21%, +2.18%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 27 ✔ | 0.3222 | 0.3216, 0.3211, 0.3237 | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| 25 | 0.3224 | 0.3204, 0.3232, 0.3236 | `VNS[constructor=singleton_routes, neighborhood=relocate]` |
| 19 | 0.3224 | 0.3235, 0.3229, 0.3208 | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| 13 | 0.3253 | 0.3267, 0.3228, 0.3263 | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| 1* | 0.3257 | 0.3253, 0.3264, 0.3253 | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| 25 (numéricos por defecto) | 0.3261 | 0.3234, 0.3305, 0.3244 | `VNS[constructor=singleton_routes, neighborhood=relocate]` |
| 19 (numéricos por defecto) | 0.3285 | 0.3240, 0.3314, 0.3300 | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| 27 (numéricos por defecto) | 0.3285 | 0.3283, 0.3303, 0.3269 | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |

## Réplica r1

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp 30) · 0 configuraciones fallidas · 3159 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` = 0.3198 (mejor default: 0.3237, `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.41%** | **670.5** | 152 | +66.7% | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| default:ILS | 2.14% | 681.7 | 154 | +66.1% | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| ILS:constructor=greedy_cheapest_insertion | 2.27% | 682.5 | 153 | +66.1% | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| ILS:constructor=greedy_nearest_from_depot | 2.27% | 682.7 | 154 | +66.1% | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| default:VNS | 3.00% | 687.2 | 154 | +65.9% | `VNS[constructor=singleton_routes, neighborhood=relocate]` |
| VNS:constructor=greedy_cheapest_insertion | 3.08% | 688.3 | 156 | +65.8% | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| VNS:constructor=greedy_nearest_from_depot | 3.28% | 690.7 | 161 | +65.7% | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| default:SA | 9.16% | 730.2 | 174 | +63.7% | `SA[constructor=singleton_routes, neighborhood=relocate]` |
| SA:constructor=greedy_cheapest_insertion | 9.57% | 732.3 | 171 | +63.6% | `SA[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| SA:constructor=greedy_nearest_from_depot | 10.00% | 735.9 | 172 | +63.5% | `SA[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| LNS_MIP:constructor=greedy_cheapest_insertion | 27.84% | 853.6 | 201 | +57.6% | `LNS_MIP[constructor=greedy_cheapest_insertion, destruction=random_removal]` |
| LNS_MIP:constructor=greedy_nearest_from_depot | 47.24% | 994.1 | 284 | +50.6% | `LNS_MIP[constructor=greedy_nearest_from_depot, destruction=random_removal]` |
| LNS_MIP:destruction=radial_removal | 62.86% | 1084.7 | 291 | +46.1% | `LNS_MIP[constructor=singleton_routes, destruction=radial_removal]` |
| default:LNS_MIP | 74.13% | 1158.1 | 260 | +42.5% | `LNS_MIP[constructor=singleton_routes, destruction=random_removal]` |
| ILS:neighborhood=two_opt | 124.96% | 1504.0 | 393 | +25.3% | `ILS[constructor=singleton_routes, neighborhood=two_opt, perturbation=relocate_kick]` |
| VNS:neighborhood=two_opt | 158.03% | 1724.7 | 414 | +14.4% | `VNS[constructor=singleton_routes, neighborhood=two_opt]` |
| SA:neighborhood=two_opt | 202.25% | 2013.6 | 442 | +0.0% | `SA[constructor=singleton_routes, neighborhood=two_opt]` |

Ganancia del afinado sobre el mejor default: **+1.64%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 20, VNS × 10, SA × 5, LNS_MIP × 5.

Afinado vs `default:ILS` (mejor default por gap): +1.73% de gap a favor del afinado, IC95 [+1.14%, +2.29%].

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 17 ✔ | 0.3198 | 0.3198, 0.3201, 0.3194 | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| 29 | 0.3203 | 0.3199, 0.3204, 0.3207 | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| 28 | 0.3218 | 0.3218, 0.3208, 0.3227 | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| 17 (numéricos por defecto) | 0.3235 | 0.3241, 0.3222, 0.3242 | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| 1* | 0.3244 | 0.3237, 0.3231, 0.3263 | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| 38 | 0.3246 | 0.3234, 0.3257, 0.3248 | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| 28 (numéricos por defecto) | 0.3251 | 0.3242, 0.3259, 0.3251 | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| 29 (numéricos por defecto) | 0.3261 | 0.3277, 0.3264, 0.3241 | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| 38 (numéricos por defecto) | 0.3277 | 0.3268, 0.3266, 0.3297 | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |

## Réplica r2

### Catálogo `handwritten`

40 trials · 5.0 s/corrida · 10 train / 10 test (cvrp 30) · 1 configuraciones fallidas · 2952 s de tuning

esqueletos: `SA`, `ILS`, `VNS`, `LNS_MIP` · objetivo de tuning: `ratio` · referencia del gap: mejor corrida o MIP completo 60 s

**Mejor en train**: `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` = 0.3219 (mejor default: 0.3246, `VNS[constructor=singleton_routes, neighborhood=relocate]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.10%** | **682.8** | 157 | +66.1% | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| default:ILS | 2.24% | 683.0 | 154 | +66.1% | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| ILS:constructor=greedy_nearest_from_depot | 2.65% | 686.0 | 156 | +65.9% | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| ILS:constructor=greedy_cheapest_insertion | 2.95% | 687.1 | 153 | +65.9% | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| default:VNS | 3.22% | 689.6 | 156 | +65.8% | `VNS[constructor=singleton_routes, neighborhood=relocate]` |
| VNS:constructor=greedy_cheapest_insertion | 3.31% | 690.7 | 159 | +65.7% | `VNS[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| VNS:constructor=greedy_nearest_from_depot | 3.53% | 692.5 | 160 | +65.6% | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| default:SA | 9.08% | 730.2 | 174 | +63.7% | `SA[constructor=singleton_routes, neighborhood=relocate]` |
| SA:constructor=greedy_cheapest_insertion | 9.50% | 732.3 | 171 | +63.6% | `SA[constructor=greedy_cheapest_insertion, neighborhood=relocate]` |
| SA:constructor=greedy_nearest_from_depot | 9.92% | 735.9 | 172 | +63.5% | `SA[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
| LNS_MIP:constructor=greedy_cheapest_insertion | 29.08% | 862.3 | 200 | +57.2% | `LNS_MIP[constructor=greedy_cheapest_insertion, destruction=random_removal]` |
| LNS_MIP:constructor=greedy_nearest_from_depot | 53.42% | 1040.5 | 300 | +48.3% | `LNS_MIP[constructor=greedy_nearest_from_depot, destruction=random_removal]` |
| LNS_MIP:destruction=radial_removal | 62.24% | 1081.3 | 293 | +46.3% | `LNS_MIP[constructor=singleton_routes, destruction=radial_removal]` |
| default:LNS_MIP | 80.64% | 1200.4 | 262 | +40.4% | `LNS_MIP[constructor=singleton_routes, destruction=random_removal]` |
| ILS:neighborhood=two_opt | 121.98% | 1494.0 | 412 | +25.8% | `ILS[constructor=singleton_routes, neighborhood=two_opt, perturbation=relocate_kick]` |
| VNS:neighborhood=two_opt | 153.03% | 1689.7 | 435 | +16.1% | `VNS[constructor=singleton_routes, neighborhood=two_opt]` |
| SA:neighborhood=two_opt | 202.05% | 2013.6 | 442 | +0.0% | `SA[constructor=singleton_routes, neighborhood=two_opt]` |

Ganancia del afinado sobre el mejor default: **+0.03%**; gana en 6/10 instancias de test. Esqueletos explorados: ILS × 23, SA × 6, VNS × 6, LNS_MIP × 5.

Afinado vs `default:ILS` (mejor default por gap): +0.14% de gap a favor del afinado, IC95 [-0.63%, +0.96%] — **no se distingue del ruido** con estas instancias.

Selección final por re-evaluación en train (media sobre semillas; * = default del esqueleto, "numéricos por defecto" = los componentes de ese trial sin afinar sus parámetros):

| trial | media | costos | configuración |
|---|---|---|---|
| 33 ✔ | 0.3219 | 0.3214, 0.3217, 0.3225 | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| 30 | 0.3223 | 0.3203, 0.3242, 0.3222 | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| 36 | 0.3229 | 0.3212, 0.3242, 0.3234 | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| 33 (numéricos por defecto) | 0.3251 | 0.3260, 0.3240, 0.3252 | `ILS[constructor=singleton_routes, neighborhood=relocate, perturbation=relocate_kick]` |
| 36 (numéricos por defecto) | 0.3255 | 0.3257, 0.3265, 0.3243 | `ILS[constructor=greedy_cheapest_insertion, neighborhood=relocate, perturbation=relocate_kick]` |
| 2* | 0.3258 | 0.3246, 0.3259, 0.3268 | `VNS[constructor=singleton_routes, neighborhood=relocate]` |
| 30 (numéricos por defecto) | 0.3261 | 0.3231, 0.3253, 0.3297 | `ILS[constructor=greedy_nearest_from_depot, neighborhood=relocate, perturbation=relocate_kick]` |
| 14 | 0.3261 | 0.3260, 0.3278, 0.3245 | `VNS[constructor=greedy_nearest_from_depot, neighborhood=relocate]` |
