## Réplicas del tuning (3)

### Catálogo `generated`

84 trials · 20.0 s · 12 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.85% | `ILS[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=random_feasible_move_chain_kick]` |
| r1 | 1 | 0.06% | `PR[constructor=polar_sweep_2opt, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, relink=route_copy_relink]` |
| r2 | 2 | 0.40% | `PR[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, relink=route_prefix_growth_relink]` |

**Afinado entre réplicas**: media 0.44%, desvío 0.32%, rango [0.06%, 0.85%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 2.76%. Afinado vs ese: +2.32% de gap a favor del afinado, IC95 [+1.12%, +3.54%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

84 trials · 20.0 s/corrida · 12 train / 6 test (cvrp_gen x100,x200,x250) · 0 configuraciones fallidas · 5935 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=random_feasible_move_chain_kick]` = 0.1372

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **19445.8** | 7875 | +87.4% | `ILS[constructor=trivial, neighborhood=route_dissolve_reinsert, perturbation=random_feasible_move_chain_kick]` |
| default:PR | 1.84% | 19885.7 | 8418 | +87.1% | `PR[constructor=trivial, neighborhood=granular_relocate, relink=route_copy_relink, perturbation=radial_ruin_cheapest_blink_insert]` |
| default:TS | 3.21% | 19995.7 | 8041 | +87.0% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 4.40% | 20244.5 | 8205 | +86.9% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert]` |
| default:VNS | 4.48% | 20318.7 | 8398 | +86.8% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 6.37% | 20611.8 | 8301 | +86.6% | `SA[constructor=trivial, neighborhood=granular_relocate]` |

Ganancia del afinado sobre el mejor default: **+2.21%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 4, PR × 2, TS × 2.

Afinado vs `default:PR` (mejor default por gap): +1.58% de gap a favor del afinado, IC95 [+0.11%, +3.04%].

## Réplica r1

### Catálogo `generated`

84 trials · 20.0 s/corrida · 12 train / 6 test (cvrp_gen x100,x200,x250) · 0 configuraciones fallidas · 5776 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=polar_sweep_2opt, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, relink=route_copy_relink]` = 0.1369

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **19329.3** | 7916 | +87.5% | `PR[constructor=polar_sweep_2opt, neighborhood=route_dissolve_reinsert, perturbation=radial_ruin_cheapest_blink_insert, relink=route_copy_relink]` |
| default:PR | 3.03% | 20038.7 | 8533 | +87.0% | `PR[constructor=trivial, neighborhood=granular_relocate, relink=route_copy_relink, perturbation=radial_ruin_cheapest_blink_insert]` |
| default:TS | 3.89% | 20017.0 | 8033 | +87.0% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 5.24% | 20321.3 | 8290 | +86.8% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert]` |
| default:VNS | 5.73% | 20414.5 | 8359 | +86.8% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 8.36% | 20853.0 | 8287 | +86.5% | `SA[constructor=trivial, neighborhood=granular_relocate]` |

Ganancia del afinado sobre el mejor default: **+3.44%**; gana en 6/6 instancias de test. Esqueletos explorados: PR × 7, TS × 1.

Afinado vs `default:PR` (mejor default por gap): +3.03% de gap a favor del afinado, IC95 [+1.69%, +4.38%].

## Réplica r2

### Catálogo `generated`

84 trials · 20.0 s/corrida · 12 train / 6 test (cvrp_gen x100,x200,x250) · 0 configuraciones fallidas · 5574 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, relink=route_prefix_growth_relink]` = 0.1373

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.00%** | **19425.8** | 8034 | +87.4% | `PR[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=radial_ruin_cheapest_blink_insert, relink=route_prefix_growth_relink]` |
| default:PR | 2.35% | 19973.5 | 8515 | +87.1% | `PR[constructor=trivial, neighborhood=granular_relocate, relink=route_copy_relink, perturbation=radial_ruin_cheapest_blink_insert]` |
| default:TS | 3.54% | 20017.0 | 8033 | +87.0% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 4.89% | 20321.3 | 8290 | +86.8% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=radial_ruin_cheapest_blink_insert]` |
| default:VNS | 5.37% | 20414.5 | 8359 | +86.8% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 8.42% | 20942.5 | 8322 | +86.4% | `SA[constructor=trivial, neighborhood=granular_relocate]` |

Ganancia del afinado sobre el mejor default: **+2.74%**; gana en 6/6 instancias de test. Esqueletos explorados: PR × 8.

Afinado vs `default:PR` (mejor default por gap): +2.35% de gap a favor del afinado, IC95 [+1.41%, +3.40%].
