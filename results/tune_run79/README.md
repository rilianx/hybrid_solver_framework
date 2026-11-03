## Réplicas del tuning (3)

### Catálogo `generated`

81 trials · 60.0 s · 9 train / 3 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.00% | `ILS[constructor=trivial, neighborhood=composite, perturbation=window_wagner_whitin_rebuild]` |
| r1 | 1 | 0.67% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=period_window]` |
| r2 | 2 | 0.77% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=random_setups]` |

**Afinado entre réplicas**: media 0.81%, desvío 0.14%, rango [0.67%, 1.00%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.18%. Afinado vs ese: -0.63% de gap a favor del afinado, IC95 [-1.38%, +0.10%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 0 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

81 trials · 60.0 s/corrida · 9 train / 3 test (clsp 6x15,12x30,24x30) · 0 configuraciones fallidas · 13786 s de tuning

esqueletos: `HYB`, `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=composite, perturbation=window_wagner_whitin_rebuild]` = 0.6349

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.80%** | **228617.5** | 158922 | +35.8% | `ILS[constructor=trivial, neighborhood=composite, perturbation=window_wagner_whitin_rebuild]` |
| default:HYB | 0.12% | 225882.2 | 155836 | +36.5% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:ILS | 2.76% | 234645.5 | 164463 | +34.1% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |

Ganancia del afinado sobre el mejor default: **-1.21%**; gana en 1/3 instancias de test. Esqueletos explorados: ILS × 5, HYB × 2.

Afinado vs `default:HYB` (mejor default por gap): -0.68% de gap a favor del afinado, IC95 [-1.61%, +0.35%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

81 trials · 60.0 s/corrida · 9 train / 3 test (clsp 6x15,12x30,24x30) · 0 configuraciones fallidas · 12346 s de tuning

esqueletos: `HYB`, `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=period_window]` = 0.6339

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.63%** | **227546.1** | 157889 | +36.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=lot_shift_merge_swap_repair, destruction=period_window]` |
| default:HYB | 0.00% | 225316.9 | 155495 | +36.7% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:ILS | 2.72% | 234239.3 | 164473 | +34.2% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |

Ganancia del afinado sobre el mejor default: **-0.99%**; gana en 0/3 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:HYB` (mejor default por gap): -0.63% de gap a favor del afinado, IC95 [-1.29%, +0.00%] — **no se distingue del ruido** con estas instancias.

## Réplica r2

### Catálogo `generated`

81 trials · 60.0 s/corrida · 9 train / 3 test (clsp 6x15,12x30,24x30) · 0 configuraciones fallidas · 13160 s de tuning

esqueletos: `HYB`, `ILS` · objetivo de tuning: `ratio`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=random_setups]` = 0.6343

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.58%** | **227422.2** | 157443 | +36.1% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=window_wagner_whitin_rebuild, destruction=random_setups]` |
| default:HYB | 0.00% | 225365.1 | 155170 | +36.7% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=period_window]` |
| default:ILS | 2.77% | 234645.5 | 164463 | +34.1% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |

Ganancia del afinado sobre el mejor default: **-0.91%**; gana en 0/3 instancias de test. Esqueletos explorados: HYB × 6, ILS × 1.

Afinado vs `default:HYB` (mejor default por gap): -0.58% de gap a favor del afinado, IC95 [-1.22%, -0.06%].
