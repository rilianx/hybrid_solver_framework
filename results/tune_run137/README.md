## Réplicas del tuning (2)

### Catálogo `generated`

168 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.92% | `TS[constructor=multistart_nondelay_composite_rule, neighborhood=critical_segment_reversal_2opt]` |
| r1 | 1 | 0.42% | `ILS[constructor=multistart_nondelay_composite_rule, neighborhood=composite, perturbation=critical_block_adjacent_swap]` |

**Afinado entre réplicas**: media 1.17%, desvío 0.75%, rango [0.42%, 1.92%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.45%. Afinado vs ese: +0.28% de gap a favor del afinado, IC95 [-0.51%, +0.78%] sobre las instancias (**no se distingue del ruido**); el afinado queda por delante en 1 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

168 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 11501 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp`, `multistart_nondelay_composite_rule`, `neh_operation_sequence_insertion`, `critical_arc_adjacent_swap_n1`, `critical_segment_reversal_2opt`, `critical_block_boundary_insertion`, `critical_block_adjacent_swap`, `operation_sequence_shift_decode`, `giffler_thompson_machine_ruin_rebuild`

**Mejor en train**: `TS[constructor=multistart_nondelay_composite_rule, neighborhood=critical_segment_reversal_2opt]` = 0.1277

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.05%** | **1319.4** | 114 | +87.7% | `TS[constructor=multistart_nondelay_composite_rule, neighborhood=critical_segment_reversal_2opt]` |
| default:TS | 0.70% | 1314.2 | 95 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:SA | 0.95% | 1317.8 | 102 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:VNS | 17.41% | 1537.8 | 219 | +85.7% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:HYB | 20.60% | 1583.6 | 279 | +85.2% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=group_window]` |
| default:ILS | 33.47% | 1749.8 | 295 | +83.7% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **-0.40%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 7.

Afinado vs `default:TS` (mejor default por gap): -0.34% de gap a favor del afinado, IC95 [-1.94%, +0.60%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

168 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 11561 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR`, `HYB` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp`, `multistart_nondelay_composite_rule`, `neh_operation_sequence_insertion`, `critical_arc_adjacent_swap_n1`, `critical_segment_reversal_2opt`, `critical_block_boundary_insertion`, `critical_block_adjacent_swap`, `operation_sequence_shift_decode`, `giffler_thompson_machine_ruin_rebuild`

**Mejor en train**: `ILS[constructor=multistart_nondelay_composite_rule, neighborhood=composite, perturbation=critical_block_adjacent_swap]` = 0.1270

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.42%** | **1299.1** | 93 | +87.9% | `ILS[constructor=multistart_nondelay_composite_rule, neighborhood=composite, perturbation=critical_block_adjacent_swap]` |
| default:SA | 1.32% | 1311.1 | 97 | +87.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:TS | 1.33% | 1310.9 | 95 | +87.8% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:VNS | 17.37% | 1523.6 | 203 | +85.8% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:HYB | 18.24% | 1537.8 | 250 | +85.7% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=group_window]` |
| default:ILS | 33.75% | 1737.1 | 280 | +83.8% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.90%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:SA` (mejor default por gap): +0.90% de gap a favor del afinado, IC95 [+0.60%, +1.24%].
