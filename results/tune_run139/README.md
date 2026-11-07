## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 20.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.17% | `ILS[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=random_removal_regret2_reinsert]` |
| r1 | 1 | 2.51% | `ILS[constructor=trivial, neighborhood=composite, perturbation=random_feasible_cross_exchange_walk]` |

**Afinado entre réplicas**: media 1.34%, desvío 1.17%, rango [0.17%, 2.51%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 3.83%. Afinado vs ese: +2.49% de gap a favor del afinado, IC95 [+1.45%, +3.52%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp x100,x200,x250) · 0 configuraciones fallidas · 9979 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=random_removal_regret2_reinsert]` = 0.1391

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.16%** | **19308.4** | 7910 | +87.5% | `ILS[constructor=trivial, neighborhood=granular_two_opt_star, perturbation=random_removal_regret2_reinsert]` |
| default:HYB | 3.88% | 20059.0 | 8309 | +87.0% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:ILS | 4.02% | 19959.1 | 7963 | +87.1% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:TS | 4.46% | 20111.2 | 8188 | +87.0% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 6.02% | 20397.3 | 8274 | +86.8% | `SA[constructor=trivial, neighborhood=granular_relocate]` |
| default:VNS | 7.29% | 20603.2 | 8234 | +86.6% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:GRASP | 55.67% | 29133.7 | 10448 | +81.1% | `GRASP[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |

Ganancia del afinado sobre el mejor default: **+3.26%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 3.

Afinado vs `default:HYB` (mejor default por gap): +3.72% de gap a favor del afinado, IC95 [+3.11%, +4.36%].

## Réplica r1

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp x100,x200,x250) · 0 configuraciones fallidas · 11846 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=composite, perturbation=random_feasible_cross_exchange_walk]` = 0.1396

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **2.16%** | **19650.2** | 7764 | +87.3% | `ILS[constructor=trivial, neighborhood=composite, perturbation=random_feasible_cross_exchange_walk]` |
| default:HYB | 3.41% | 20056.9 | 8371 | +87.0% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:ILS | 3.61% | 19948.6 | 7967 | +87.1% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:TS | 3.85% | 20042.4 | 8112 | +87.0% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 5.21% | 20306.0 | 8219 | +86.8% | `SA[constructor=trivial, neighborhood=granular_relocate]` |
| default:VNS | 6.79% | 20576.5 | 8226 | +86.7% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:GRASP | 55.06% | 29122.1 | 10461 | +81.1% | `GRASP[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.50%**; gana en 4/6 instancias de test. Esqueletos explorados: ILS × 7, HYB × 1.

Afinado vs `default:HYB` (mejor default por gap): +1.26% de gap a favor del afinado, IC95 [-0.90%, +3.16%] — **no se distingue del ruido** con estas instancias.
