## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 20.0 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.46% | `ILS[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| r1 | 1 | 0.11% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| r2 | 2 | 0.42% | `ILS[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |

**Afinado entre réplicas**: media 0.33%, desvío 0.16%, rango [0.11%, 0.46%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 1.01%. Afinado vs ese: +0.68% de gap a favor del afinado, IC95 [+0.20%, +1.19%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 20.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15,20x20) · 0 configuraciones fallidas · 5653 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` = 0.1171

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.06%** | **1382.3** | 159 | +88.9% | `ILS[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| default:PR | 0.63% | 1389.8 | 157 | +88.9% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 0.87% | 1393.7 | 161 | +88.9% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 1.04% | 1395.3 | 156 | +88.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 21.74% | 1697.8 | 350 | +86.4% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |
| default:VNS | 22.41% | 1705.7 | 328 | +86.4% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.54%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:PR` (mejor default por gap): +0.57% de gap a favor del afinado, IC95 [+0.10%, +1.10%].

## Réplica r1

### Catálogo `generated`

84 trials · 20.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15,20x20) · 0 configuraciones fallidas · 5925 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` = 0.1172

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.07%** | **1377.7** | 159 | +89.0% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| default:PR | 0.94% | 1389.2 | 157 | +88.9% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:TS | 1.11% | 1391.8 | 159 | +88.9% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:SA | 1.14% | 1393.2 | 168 | +88.9% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 21.87% | 1693.7 | 344 | +86.5% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |
| default:VNS | 21.90% | 1691.2 | 310 | +86.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.83%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:PR` (mejor default por gap): +0.87% de gap a favor del afinado, IC95 [+0.25%, +1.47%].

## Réplica r2

### Catálogo `generated`

84 trials · 20.0 s/corrida · 12 train / 6 test (jobshop_gen 15x15,20x15,20x20) · 0 configuraciones fallidas · 5685 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` = 0.1170

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.06%** | **1382.0** | 160 | +88.9% | `ILS[constructor=giffler_thompson_grasp_active, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_block_insertion]` |
| default:PR | 0.65% | 1389.7 | 157 | +88.9% | `PR[constructor=trivial, neighborhood=critical_arc_adjacent_swap, relink=swap_cycle_relink, perturbation=jssp_critical_swap_walk]` |
| default:SA | 0.82% | 1392.7 | 163 | +88.9% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:TS | 0.91% | 1393.7 | 161 | +88.9% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |
| default:ILS | 21.49% | 1693.7 | 344 | +86.5% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap, perturbation=jssp_critical_swap_walk]` |
| default:VNS | 21.60% | 1692.5 | 312 | +86.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.55%**; gana en 4/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:PR` (mejor default por gap): +0.59% de gap a favor del afinado, IC95 [+0.05%, +1.18%].
