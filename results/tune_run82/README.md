## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 30.0 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.53% | `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, relink=disjunctive_arc_flip_relink, perturbation=jssp_critical_block_insertion]` |
| r1 | 1 | 0.25% | `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| r2 | 2 | 0.39% | `PR[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, relink=disjunctive_arc_flip_relink, perturbation=jssp_critical_block_insertion]` |

**Afinado entre réplicas**: media 0.39%, desvío 0.11%, rango [0.25%, 0.53%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 1.21%. Afinado vs ese: +0.81% de gap a favor del afinado, IC95 [+0.36%, +1.24%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 30.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15) · 0 configuraciones fallidas · 8347 s de tuning

esqueletos: `PR`, `TS` · objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, relink=disjunctive_arc_flip_relink, perturbation=jssp_critical_block_insertion]` = 0.1268

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.18%** | **1301.5** | 102 | +87.9% | `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, relink=disjunctive_arc_flip_relink, perturbation=jssp_critical_block_insertion]` |
| default:PR | 0.85% | 1309.8 | 98 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 0.88% | 1310.2 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.64%**; gana en 5/6 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:PR` (mejor default por gap): +0.67% de gap a favor del afinado, IC95 [+0.08%, +1.43%].

## Réplica r1

### Catálogo `generated`

84 trials · 30.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15) · 0 configuraciones fallidas · 8348 s de tuning

esqueletos: `PR`, `TS` · objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` = 0.1267

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **1297.3** | 95 | +87.9% | `PR[constructor=random, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:PR | 0.95% | 1309.8 | 98 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 0.98% | 1310.2 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.95%**; gana en 6/6 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:PR` (mejor default por gap): +0.95% de gap a favor del afinado, IC95 [+0.51%, +1.37%].

## Réplica r2

### Catálogo `generated`

84 trials · 30.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15) · 0 configuraciones fallidas · 8799 s de tuning

esqueletos: `PR`, `TS` · objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, relink=disjunctive_arc_flip_relink, perturbation=jssp_critical_block_insertion]` = 0.1266

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.02%** | **1299.2** | 97 | +87.9% | `PR[constructor=neh_operation_insertion_partial_makespan, neighborhood=critical_arc_adjacent_swap, relink=disjunctive_arc_flip_relink, perturbation=jssp_critical_block_insertion]` |
| default:PR | 0.83% | 1309.7 | 98 | +87.8% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 0.88% | 1310.2 | 96 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.80%**; gana en 5/6 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:PR` (mejor default por gap): +0.81% de gap a favor del afinado, IC95 [+0.34%, +1.22%].
