## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.44% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=lot_merge_interval, perturbation=setup_shift_domino, destruction=group_window]` |
| r1 | 1 | 0.23% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=single_setup_flip, perturbation=random_feasible_setup_flips, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.34%, desvío 0.11%, rango [0.23%, 0.44%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 13.54%. Afinado vs ese: +13.21% de gap a favor del afinado, IC95 [+11.28%, +15.15%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 10281 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `backward_econ_deferral_fill`, `wagner_whitin_backshift_repair`, `forward_dixon_silver_lookahead`, `setup_time_shift`, `lot_merge_interval`, `single_setup_flip`, `random_feasible_setup_flips`, `item_wagner_whitin_reoptimize`, `setup_shift_domino`

**Mejor en train**: `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=lot_merge_interval, perturbation=setup_shift_domino, destruction=group_window]` = 0.5155

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **230603.1** | 29428 | +47.6% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=lot_merge_interval, perturbation=setup_shift_domino, destruction=group_window]` |
| default:HYB | 11.90% | 257435.9 | 35686 | +41.6% | `HYB[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:ILS | 64.89% | 378618.7 | 46991 | +14.0% | `ILS[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:VNS | 68.05% | 385683.5 | 48665 | +12.4% | `VNS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:GRASP | 91.12% | 438375.9 | 50340 | +0.5% | `GRASP[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:TS | 91.15% | 438446.1 | 50362 | +0.5% | `TS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:SA | 91.65% | 439554.4 | 50396 | +0.2% | `SA[constructor=trivial, neighborhood=setup_time_shift]` |

Ganancia del afinado sobre el mejor default: **+10.42%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 8.

Afinado vs `default:HYB` (mejor default por gap): +11.64% de gap a favor del afinado, IC95 [+9.16%, +13.93%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 10008 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `backward_econ_deferral_fill`, `wagner_whitin_backshift_repair`, `forward_dixon_silver_lookahead`, `setup_time_shift`, `lot_merge_interval`, `single_setup_flip`, `random_feasible_setup_flips`, `item_wagner_whitin_reoptimize`, `setup_shift_domino`

**Mejor en train**: `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=single_setup_flip, perturbation=random_feasible_setup_flips, destruction=random_variables]` = 0.5152

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.16%** | **230129.9** | 29469 | +47.8% | `HYB[constructor=forward_dixon_silver_lookahead, neighborhood=single_setup_flip, perturbation=random_feasible_setup_flips, destruction=random_variables]` |
| default:HYB | 14.90% | 263742.0 | 35036 | +40.1% | `HYB[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips, destruction=group_window]` |
| default:ILS | 71.04% | 392068.6 | 47461 | +11.0% | `ILS[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:VNS | 76.05% | 403247.8 | 47474 | +8.4% | `VNS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:GRASP | 91.36% | 438375.9 | 50340 | +0.5% | `GRASP[constructor=trivial, neighborhood=setup_time_shift, perturbation=random_feasible_setup_flips]` |
| default:TS | 91.39% | 438446.1 | 50362 | +0.5% | `TS[constructor=trivial, neighborhood=setup_time_shift]` |
| default:SA | 91.88% | 439554.4 | 50396 | +0.2% | `SA[constructor=trivial, neighborhood=setup_time_shift]` |

Ganancia del afinado sobre el mejor default: **+12.74%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): +14.74% de gap a favor del afinado, IC95 [+13.07%, +16.62%].
