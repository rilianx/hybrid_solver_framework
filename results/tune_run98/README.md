## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.62% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| r1 | 1 | 0.59% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |

**Afinado entre réplicas**: media 0.61%, desvío 0.02%, rango [0.59%, 0.62%].

**Mejor no afinado** (media entre réplicas): `default:HYB` = 0.81%. Afinado vs ese: +0.20% de gap a favor del afinado, IC95 [-0.11%, +0.60%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 3106 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_toggle_flip`, `lot_consolidation_window`, `random_setup_flips_flow_repair`, `lot_shift_merge_swap_repair`, `window_wagner_whitin_rebuild`, `hamming_single_setup_flip`, `differing_run_segment_copy`, `period_column_transplant`

**Mejor en train**: `TS[constructor=trivial, neighborhood=setup_toggle_flip]` = 0.5211

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.42%** | **233098.9** | 29272 | +47.1% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:HYB | 0.62% | 233647.0 | 29868 | +47.0% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| default:TS | 0.70% | 233851.4 | 30144 | +46.9% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 0.70% | 233851.4 | 30144 | +46.9% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:ILS | 5.61% | 245207.4 | 31378 | +44.3% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:VNS | 5.93% | 245984.9 | 31554 | +44.2% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:SA | 7.50% | 249700.9 | 32582 | +43.3% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **+0.23%**; gana en 3/6 instancias de test. Esqueletos explorados: TS × 2, HYB × 6.

Afinado vs `default:HYB` (mejor default por gap): +0.20% de gap a favor del afinado, IC95 [-0.11%, +0.60%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (clsp 20x20) · 0 configuraciones fallidas · 2961 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `setup_toggle_flip`, `lot_consolidation_window`, `random_setup_flips_flow_repair`, `lot_shift_merge_swap_repair`, `window_wagner_whitin_rebuild`, `hamming_single_setup_flip`, `differing_run_segment_copy`, `period_column_transplant`

**Mejor en train**: `TS[constructor=trivial, neighborhood=setup_toggle_flip]` = 0.5235

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.53%** | **233043.9** | 29427 | +47.1% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:HYB | 0.74% | 233555.5 | 29845 | +47.0% | `HYB[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair, destruction=group_window]` |
| default:TS | 0.82% | 233778.9 | 30140 | +46.9% | `TS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:PR | 0.82% | 233778.9 | 30140 | +46.9% | `PR[constructor=trivial, neighborhood=setup_toggle_flip, relink=hamming_single_setup_flip, perturbation=random_setup_flips_flow_repair]` |
| default:ILS | 5.28% | 244001.4 | 30586 | +44.6% | `ILS[constructor=trivial, neighborhood=setup_toggle_flip, perturbation=random_setup_flips_flow_repair]` |
| default:VNS | 5.79% | 245257.2 | 31301 | +44.3% | `VNS[constructor=trivial, neighborhood=setup_toggle_flip]` |
| default:SA | 7.60% | 249567.1 | 32711 | +43.3% | `SA[constructor=trivial, neighborhood=setup_toggle_flip]` |

Ganancia del afinado sobre el mejor default: **+0.22%**; gana en 3/6 instancias de test. Esqueletos explorados: TS × 8.

Afinado vs `default:HYB` (mejor default por gap): +0.20% de gap a favor del afinado, IC95 [-0.21%, +0.67%] — **no se distingue del ruido** con estas instancias.
