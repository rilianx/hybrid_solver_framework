## Réplicas del tuning (2)

### Catálogo `generated`

168 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.31% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=lot_merge_interval, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| r1 | 1 | 0.29% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.30%, desvío 0.01%, rango [0.29%, 0.31%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 14.81%. Afinado vs ese: +14.51% de gap a favor del afinado, IC95 [+12.74%, +16.36%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

168 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 10286 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `backward_econ_deferral_fill`, `wagner_whitin_backshift_repair`, `forward_dixon_silver_lookahead`, `setup_time_shift`, `lot_merge_interval`, `single_setup_flip`, `random_feasible_setup_flips`, `item_wagner_whitin_reoptimize`, `setup_shift_domino`

**Mejor en train**: `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=lot_merge_interval, perturbation=random_feasible_setup_flips, destruction=group_window]` = 0.5156

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.22%** | **230524.0** | 29777 | +47.7% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=lot_merge_interval, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:HYB | 15.10% | 264541.6 | 35362 | +39.9% | `HYB[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:ILS | 72.97% | 396799.8 | 46672 | +9.9% | `ILS[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:VNS | 77.63% | 407467.0 | 48575 | +7.5% | `VNS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:TS | 91.19% | 438446.1 | 50362 | +0.5% | `TS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:SA | 91.69% | 439554.4 | 50396 | +0.2% | `SA[constructor=trivial, neighborhood=setup_time_shift]` |

Ganancia del afinado sobre el mejor default: **+12.86%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): +14.88% de gap a favor del afinado, IC95 [+12.94%, +16.92%].

## Réplica r1

### Catálogo `generated`

168 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 10035 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `backward_econ_deferral_fill`, `wagner_whitin_backshift_repair`, `forward_dixon_silver_lookahead`, `setup_time_shift`, `lot_merge_interval`, `single_setup_flip`, `random_feasible_setup_flips`, `item_wagner_whitin_reoptimize`, `setup_shift_domino`

**Mejor en train**: `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=random_variables]` = 0.5146

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.19%** | **230451.2** | 29639 | +47.7% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=random_variables]` |
| default:HYB | 14.30% | 262795.9 | 35907 | +40.3% | `HYB[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:ILS | 68.75% | 387155.1 | 46537 | +12.1% | `ILS[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:VNS | 74.18% | 399289.4 | 46573 | +9.3% | `VNS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:TS | 91.20% | 438446.1 | 50362 | +0.5% | `TS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:SA | 91.69% | 439554.4 | 50396 | +0.2% | `SA[constructor=trivial, neighborhood=setup_time_shift]` |

Ganancia del afinado sobre el mejor default: **+12.31%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 5.

Afinado vs `default:HYB` (mejor default por gap): +14.11% de gap a favor del afinado, IC95 [+12.29%, +16.02%].
