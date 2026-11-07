## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 20.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r1 | 1 | 0.12% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.12%, desvío 0.00%, rango [0.12%, 0.12%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 3.92%. Afinado vs ese: +3.80% de gap a favor del afinado, IC95 [+3.22%, +4.41%] sobre las instancias; el afinado queda por delante en 1 de 1 réplicas.


## Réplica r0

> No hay resultados en `results/tune_run141/r0`: el tuning no llegó a completarse (revisa el log).

## Réplica r1

### Catálogo `generated`

80 trials · 20.0 s/corrida · 6 train / 6 test (cvrp x100,x200,x250) · 0 configuraciones fallidas · 9978 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `randomized_parallel_savings`, `multi_start_polar_sweep_2opt`, `giant_tour_optimal_split`, `granular_relocate`, `granular_two_opt_star`, `granular_cross_exchange`, `random_removal_regret2_reinsert`, `sisr_string_removal_blink_insert`, `random_feasible_cross_exchange_walk`

**Mejor en train**: `HYB[constructor=random, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=random_variables]` = 0.1391

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.12%** | **19295.7** | 7885 | +87.5% | `HYB[constructor=random, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=random_variables]` |
| default:HYB | 3.92% | 20040.6 | 8221 | +87.0% | `HYB[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert, destruction=group_window]` |
| default:ILS | 4.06% | 19975.8 | 7983 | +87.1% | `ILS[constructor=trivial, neighborhood=granular_relocate, perturbation=random_removal_regret2_reinsert]` |
| default:TS | 4.44% | 20111.8 | 8188 | +87.0% | `TS[constructor=trivial, neighborhood=granular_relocate]` |
| default:SA | 5.95% | 20391.0 | 8267 | +86.8% | `SA[constructor=trivial, neighborhood=granular_relocate]` |
| default:VNS | 7.27% | 20603.7 | 8235 | +86.6% | `VNS[constructor=trivial, neighborhood=granular_relocate]` |

Ganancia del afinado sobre el mejor default: **+3.40%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 3.

Afinado vs `default:HYB` (mejor default por gap): +3.80% de gap a favor del afinado, IC95 [+3.22%, +4.41%].
