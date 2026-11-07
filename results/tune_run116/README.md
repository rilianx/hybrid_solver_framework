## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 20.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.03% | `ILS[constructor=multi_start_polar_sweep_2opt, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| r1 | 1 | 0.03% | `HYB[constructor=multi_start_polar_sweep_2opt, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.03%, desvío 0.00%, rango [0.03%, 0.03%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.58%. Afinado vs ese: +1.55% de gap a favor del afinado, IC95 [+0.66%, +2.54%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp u50,u100) · 0 configuraciones fallidas · 14998 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `ILS[constructor=multi_start_polar_sweep_2opt, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` = 0.1848

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.03%** | **10.3** | 2 | +82.1% | `ILS[constructor=multi_start_polar_sweep_2opt, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:TS | 1.56% | 10.5 | 2 | +81.8% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 1.72% | 10.5 | 2 | +81.8% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:HYB | 2.50% | 10.6 | 2 | +81.7% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:VNS | 4.48% | 10.8 | 3 | +81.3% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 7.38% | 11.2 | 3 | +80.6% | `SA[constructor=trivial, neighborhood=granular_relocate]` |

Ganancia del afinado sobre el mejor default: **+1.74%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 2, HYB × 2.

Afinado vs `default:TS` (mejor default por gap): +1.53% de gap a favor del afinado, IC95 [+0.65%, +2.51%].

## Réplica r1

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp u50,u100) · 0 configuraciones fallidas · 14988 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `HYB[constructor=multi_start_polar_sweep_2opt, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=random_variables]` = 0.1850

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.01%** | **10.3** | 2 | +82.1% | `HYB[constructor=multi_start_polar_sweep_2opt, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=random_variables]` |
| default:TS | 1.59% | 10.5 | 2 | +81.8% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:ILS | 1.71% | 10.5 | 2 | +81.8% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:HYB | 2.59% | 10.6 | 2 | +81.6% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:VNS | 4.64% | 10.9 | 3 | +81.2% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 9.24% | 11.4 | 3 | +80.3% | `SA[constructor=trivial, neighborhood=granular_relocate]` |

Ganancia del afinado sobre el mejor default: **+1.79%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 8.

Afinado vs `default:TS` (mejor default por gap): +1.57% de gap a favor del afinado, IC95 [+0.68%, +2.56%].
