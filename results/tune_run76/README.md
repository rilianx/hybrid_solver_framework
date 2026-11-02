## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 2.5 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.27% | `ILS[constructor=trivial, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |
| r1 | 1 | 0.18% | `ILS[constructor=neh_taillard_noisy, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |
| r2 | 2 | 0.45% | `ILS[constructor=grasp_liu_reeves_append, neighborhood=head_tail_pair_swap, perturbation=ig_destroy_rebuild_taillard]` |

**Afinado entre réplicas**: media 0.30%, desvío 0.12%, rango [0.18%, 0.45%].

**Mejor no afinado** (media entre réplicas): `default:ILS` = 1.48%. Afinado vs ese: +1.18% de gap a favor del afinado, IC95 [+0.58%, +1.86%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 2.5 s/corrida · 12 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 10150 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` = 0.8191

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.13%** | **6961.3** | 3490 | +17.8% | `ILS[constructor=trivial, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |
| default:ILS | 1.33% | 7034.3 | 3491 | +16.9% | `ILS[constructor=trivial, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |

Ganancia del afinado sobre el mejor default: **+1.04%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6.

Afinado vs `default:ILS` (mejor default por gap): +1.20% de gap a favor del afinado, IC95 [+0.61%, +1.84%].

## Réplica r1

### Catálogo `generated`

84 trials · 2.5 s/corrida · 12 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 10633 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=neh_taillard_noisy, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` = 0.8186

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.16%** | **6953.9** | 3486 | +17.9% | `ILS[constructor=neh_taillard_noisy, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |
| default:ILS | 1.43% | 7032.5 | 3491 | +17.0% | `ILS[constructor=trivial, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |

Ganancia del afinado sobre el mejor default: **+1.12%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6.

Afinado vs `default:ILS` (mejor default por gap): +1.26% de gap a favor del afinado, IC95 [+0.59%, +2.04%].

## Réplica r2

### Catálogo `generated`

84 trials · 2.5 s/corrida · 12 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 10780 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=grasp_liu_reeves_append, neighborhood=head_tail_pair_swap, perturbation=ig_destroy_rebuild_taillard]` = 0.8198

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.11%** | **6971.6** | 3489 | +17.7% | `ILS[constructor=grasp_liu_reeves_append, neighborhood=head_tail_pair_swap, perturbation=ig_destroy_rebuild_taillard]` |
| default:ILS | 1.19% | 7039.7 | 3494 | +16.9% | `ILS[constructor=trivial, neighborhood=taillard_job_insertion, perturbation=ig_destroy_rebuild_taillard]` |

Ganancia del afinado sobre el mejor default: **+0.97%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6.

Afinado vs `default:ILS` (mejor default por gap): +1.08% de gap a favor del afinado, IC95 [+0.52%, +1.71%].
