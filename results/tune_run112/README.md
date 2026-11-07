## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.31% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=setup_time_shift, perturbation=setup_shift_domino, destruction=group_window]` |
| r1 | 1 | 0.90% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=single_setup_flip, perturbation=item_wagner_whitin_reoptimize, destruction=group_window]` |

**Afinado entre réplicas**: media 0.61%, desvío 0.30%, rango [0.31%, 0.90%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 14.32%. Afinado vs ese: +13.71% de gap a favor del afinado, IC95 [+11.87%, +15.53%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 7414 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `backward_econ_deferral_fill`, `wagner_whitin_backshift_repair`, `forward_dixon_silver_lookahead`, `setup_time_shift`, `lot_merge_interval`, `single_setup_flip`, `random_feasible_setup_flips`, `item_wagner_whitin_reoptimize`, `setup_shift_domino`

**Mejor en train**: `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=setup_time_shift, perturbation=setup_shift_domino, destruction=group_window]` = 0.5142

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.29%** | **230607.1** | 29545 | +47.6% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=setup_time_shift, perturbation=setup_shift_domino, destruction=group_window]` |
| default:HYB | 14.34% | 262862.7 | 36170 | +40.3% | `HYB[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:ILS | 68.92% | 387469.2 | 46486 | +12.0% | `ILS[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:VNS | 74.35% | 399594.5 | 46425 | +9.3% | `VNS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:TS | 91.24% | 438446.1 | 50362 | +0.5% | `TS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:SA | 91.73% | 439554.4 | 50396 | +0.2% | `SA[constructor=trivial, neighborhood=setup_time_shift]` |

Ganancia del afinado sobre el mejor default: **+12.27%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): +14.05% de gap a favor del afinado, IC95 [+12.30%, +15.79%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 7455 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `backward_econ_deferral_fill`, `wagner_whitin_backshift_repair`, `forward_dixon_silver_lookahead`, `setup_time_shift`, `lot_merge_interval`, `single_setup_flip`, `random_feasible_setup_flips`, `item_wagner_whitin_reoptimize`, `setup_shift_domino`

**Mejor en train**: `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=single_setup_flip, perturbation=item_wagner_whitin_reoptimize, destruction=group_window]` = 0.5211

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.71%** | **231961.6** | 29697 | +47.3% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=single_setup_flip, perturbation=item_wagner_whitin_reoptimize, destruction=group_window]` |
| default:HYB | 14.06% | 262610.3 | 35901 | +40.4% | `HYB[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:ILS | 68.59% | 387363.9 | 46341 | +12.1% | `ILS[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:VNS | 73.84% | 399076.5 | 46440 | +9.4% | `VNS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:TS | 90.91% | 438446.1 | 50362 | +0.5% | `TS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:SA | 91.41% | 439554.4 | 50396 | +0.2% | `SA[constructor=trivial, neighborhood=setup_time_shift]` |

Ganancia del afinado sobre el mejor default: **+11.67%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): +13.35% de gap a favor del afinado, IC95 [+11.47%, +15.27%].
