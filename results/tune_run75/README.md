## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 2.5 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.36% | `ILS[constructor=neh_flowtime_prefix_insertion, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |
| r1 | 1 | 0.28% | `ILS[constructor=neh_flowtime_prefix_insertion, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |
| r2 | 2 | 0.36% | `ILS[constructor=grasp_lr_index_append, neighborhood=pairwise_job_swap, perturbation=ig_destruct_greedy_reinsert]` |

**Afinado entre réplicas**: media 0.33%, desvío 0.04%, rango [0.28%, 0.36%].

**Mejor no afinado** (media entre réplicas): `default:ILS` = 1.34%. Afinado vs ese: +1.01% de gap a favor del afinado, IC95 [+0.86%, +1.17%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 2.5 s/corrida · 12 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 9521 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=neh_flowtime_prefix_insertion, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` = 0.7841

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.27%** | **572896.6** | 496034 | +19.2% | `ILS[constructor=neh_flowtime_prefix_insertion, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |
| default:ILS | 1.26% | 578571.6 | 501318 | +18.4% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |

Ganancia del afinado sobre el mejor default: **+0.98%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6.

Afinado vs `default:ILS` (mejor default por gap): +0.99% de gap a favor del afinado, IC95 [+0.83%, +1.13%].

## Réplica r1

### Catálogo `generated`

84 trials · 2.5 s/corrida · 12 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 9247 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=neh_flowtime_prefix_insertion, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` = 0.7835

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.15%** | **571690.9** | 494328 | +19.3% | `ILS[constructor=neh_flowtime_prefix_insertion, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |
| default:ILS | 1.21% | 578536.6 | 501301 | +18.4% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.18%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6.

Afinado vs `default:ILS` (mejor default por gap): +1.05% de gap a favor del afinado, IC95 [+0.87%, +1.26%].

## Réplica r2

### Catálogo `generated`

84 trials · 2.5 s/corrida · 12 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 10823 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=grasp_lr_index_append, neighborhood=pairwise_job_swap, perturbation=ig_destruct_greedy_reinsert]` = 0.7841

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.20%** | **572315.3** | 495181 | +19.3% | `ILS[constructor=grasp_lr_index_append, neighborhood=pairwise_job_swap, perturbation=ig_destruct_greedy_reinsert]` |
| default:ILS | 1.19% | 578569.7 | 501320 | +18.4% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.08%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6.

Afinado vs `default:ILS` (mejor default por gap): +0.98% de gap a favor del afinado, IC95 [+0.84%, +1.18%].
