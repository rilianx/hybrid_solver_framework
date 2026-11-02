## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 1.0 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.32% | `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=job_insertion_shift, perturbation=segment_scramble]` |
| r1 | 1 | 0.26% | `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |
| r2 | 2 | 0.54% | `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=pairwise_job_swap, perturbation=ig_destruct_greedy_reinsert]` |

**Afinado entre réplicas**: media 0.37%, desvío 0.12%, rango [0.26%, 0.54%].

**Mejor no afinado** (media entre réplicas): `default:ILS` = 1.63%. Afinado vs ese: +1.26% de gap a favor del afinado, IC95 [+0.91%, +1.65%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 1.0 s/corrida · 12 train / 6 test (flowshop 50x10,200x20,500x20) · 0 configuraciones fallidas · 10094 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=job_insertion_shift, perturbation=segment_scramble]` = 0.7967

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.25%** | **2742263.8** | 2966120 | +17.5% | `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=job_insertion_shift, perturbation=segment_scramble]` |
| default:ILS | 1.57% | 2789389.4 | 3022863 | +16.1% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.69%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:ILS` (mejor default por gap): +1.32% de gap a favor del afinado, IC95 [+0.99%, +1.66%].

## Réplica r1

### Catálogo `generated`

84 trials · 1.0 s/corrida · 12 train / 6 test (flowshop 50x10,200x20,500x20) · 0 configuraciones fallidas · 9045 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` = 0.7962

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.18%** | **2737314.4** | 2958754 | +17.7% | `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |
| default:ILS | 1.54% | 2788733.4 | 3022202 | +16.1% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.84%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:ILS` (mejor default por gap): +1.35% de gap a favor del afinado, IC95 [+0.98%, +1.80%].

## Réplica r2

### Catálogo `generated`

84 trials · 1.0 s/corrida · 12 train / 6 test (flowshop 50x10,200x20,500x20) · 0 configuraciones fallidas · 9367 s de tuning

esqueletos: `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=pairwise_job_swap, perturbation=ig_destruct_greedy_reinsert]` = 0.7989

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.16%** | **2748498.4** | 2971165 | +17.3% | `ILS[constructor=weighted_priority_sort_adjacent_sweep, neighborhood=pairwise_job_swap, perturbation=ig_destruct_greedy_reinsert]` |
| default:ILS | 1.25% | 2789388.6 | 3022949 | +16.1% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=ig_destruct_greedy_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.47%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:ILS` (mejor default por gap): +1.09% de gap a favor del afinado, IC95 [+0.73%, +1.51%].
