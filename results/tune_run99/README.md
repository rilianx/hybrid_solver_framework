## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.60% | `ILS[constructor=trivial, neighborhood=composite, perturbation=random_flip_with_staged_undo]` |
| r1 | 1 | 0.56% | `SA[constructor=trivial, neighborhood=composite]` |

**Afinado entre réplicas**: media 0.58%, desvío 0.02%, rango [0.56%, 0.60%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 0.90%. Afinado vs ese: +0.32% de gap a favor del afinado, IC95 [-0.04%, +0.67%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 3004 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_shift_merge`, `lot_block_consolidation`, `setup_bit_flip`, `random_flip_with_staged_undo`, `window_ruin_silver_meal_rebuild`, `setup_time_shift_merge`, `hamming_setup_bitflip`, `item_plan_row_copy`, `setup_shift_relink`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=composite, perturbation=random_flip_with_staged_undo]` = 0.5190

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.46%** | **232319.8** | 29659 | +47.3% | `ILS[constructor=trivial, neighborhood=composite, perturbation=random_flip_with_staged_undo]` |
| default:TS | 0.75% | 233096.6 | 30455 | +47.1% | `TS[constructor=trivial, neighborhood=setup_shift_merge]` |
| default:PR | 0.75% | 233096.6 | 30455 | +47.1% | `PR[constructor=trivial, neighborhood=setup_shift_merge, relink=hamming_setup_bitflip, perturbation=random_flip_with_staged_undo]` |
| default:HYB | 1.18% | 233933.2 | 29514 | +46.9% | `HYB[constructor=trivial, neighborhood=setup_shift_merge, perturbation=random_flip_with_staged_undo, destruction=group_window]` |
| default:SA | 2.22% | 236549.8 | 31567 | +46.3% | `SA[constructor=trivial, neighborhood=setup_shift_merge]` |
| default:ILS | 2.54% | 237154.1 | 30414 | +46.2% | `ILS[constructor=trivial, neighborhood=setup_shift_merge, perturbation=random_flip_with_staged_undo]` |
| default:VNS | 2.87% | 237953.7 | 31008 | +46.0% | `VNS[constructor=trivial, neighborhood=setup_shift_merge]` |

Ganancia del afinado sobre el mejor default: **+0.33%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 1.

Afinado vs `default:TS` (mejor default por gap): +0.30% de gap a favor del afinado, IC95 [-0.33%, +0.73%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 2952 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_shift_merge`, `lot_block_consolidation`, `setup_bit_flip`, `random_flip_with_staged_undo`, `window_ruin_silver_meal_rebuild`, `setup_time_shift_merge`, `hamming_setup_bitflip`, `item_plan_row_copy`, `setup_shift_relink`

**Mejor en train**: `SA[constructor=trivial, neighborhood=composite]` = 0.5227

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.49%** | **232249.8** | 29915 | +47.3% | `SA[constructor=trivial, neighborhood=composite]` |
| default:TS | 0.83% | 233096.6 | 30455 | +47.1% | `TS[constructor=trivial, neighborhood=setup_shift_merge]` |
| default:PR | 0.83% | 233096.6 | 30455 | +47.1% | `PR[constructor=trivial, neighborhood=setup_shift_merge, relink=hamming_setup_bitflip, perturbation=random_flip_with_staged_undo]` |
| default:SA | 2.05% | 235958.4 | 31275 | +46.4% | `SA[constructor=trivial, neighborhood=setup_shift_merge]` |
| default:HYB | 2.74% | 237334.0 | 30285 | +46.1% | `HYB[constructor=trivial, neighborhood=setup_shift_merge, perturbation=random_flip_with_staged_undo, destruction=group_window]` |
| default:ILS | 2.79% | 237575.7 | 30655 | +46.1% | `ILS[constructor=trivial, neighborhood=setup_shift_merge, perturbation=random_flip_with_staged_undo]` |
| default:VNS | 3.08% | 238276.5 | 31072 | +45.9% | `VNS[constructor=trivial, neighborhood=setup_shift_merge]` |

Ganancia del afinado sobre el mejor default: **+0.36%**; gana en 5/6 instancias de test. Esqueletos explorados: SA × 8.

Afinado vs `default:TS` (mejor default por gap): +0.34% de gap a favor del afinado, IC95 [-0.00%, +0.67%] — **no se distingue del ruido** con estas instancias.
