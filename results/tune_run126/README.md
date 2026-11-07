## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 20.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.04% | `ILS[constructor=trivial, neighborhood=composite, perturbation=sisr_string_removal_blink_insert]` |
| r1 | 1 | 0.58% | `ILS[constructor=trivial, neighborhood=composite, perturbation=random_feasible_cross_exchange_walk]` |

**Afinado entre réplicas**: media 0.31%, desvío 0.27%, rango [0.04%, 0.58%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.46%. Afinado vs ese: +1.15% de gap a favor del afinado, IC95 [+0.52%, +1.81%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp u50,u100) · 0 configuraciones fallidas · 8012 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=composite, perturbation=sisr_string_removal_blink_insert]` = 0.1851

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.04%** | **10.4** | 2 | +82.1% | `ILS[constructor=trivial, neighborhood=composite, perturbation=sisr_string_removal_blink_insert]` |
| default:TS | 1.43% | 10.5 | 2 | +81.8% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 1.62% | 10.5 | 2 | +81.8% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:HYB | 2.53% | 10.6 | 2 | +81.6% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:VNS | 4.34% | 10.8 | 3 | +81.3% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 6.06% | 11.1 | 3 | +80.9% | `SA[constructor=trivial, neighborhood=granular_relocate]` |
| default:GRASP | 31.58% | 13.8 | 4 | +76.1% | `GRASP[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.58%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:TS` (mejor default por gap): +1.39% de gap a favor del afinado, IC95 [+0.58%, +2.27%].

## Réplica r1

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp u50,u100) · 0 configuraciones fallidas · 8114 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=composite, perturbation=random_feasible_cross_exchange_walk]` = 0.1852

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.31%** | **10.4** | 2 | +82.0% | `ILS[constructor=trivial, neighborhood=composite, perturbation=random_feasible_cross_exchange_walk]` |
| default:TS | 1.22% | 10.5 | 2 | +81.8% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 1.35% | 10.5 | 2 | +81.8% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:HYB | 2.09% | 10.6 | 2 | +81.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:VNS | 4.22% | 10.9 | 3 | +81.2% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 6.99% | 11.2 | 3 | +80.7% | `SA[constructor=trivial, neighborhood=granular_relocate]` |
| default:GRASP | 32.27% | 13.9 | 4 | +75.9% | `GRASP[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |

Ganancia del afinado sobre el mejor default: **+1.03%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 6, HYB × 2.

Afinado vs `default:TS` (mejor default por gap): +0.91% de gap a favor del afinado, IC95 [+0.43%, +1.40%].
