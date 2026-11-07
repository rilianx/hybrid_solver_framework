## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.47% | `ILS[constructor=giffler_thompson_grasp, neighborhood=critical_segment_reversal_2opt, perturbation=critical_block_adjacent_swap]` |
| r1 | 1 | 0.76% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.62%, desvío 0.15%, rango [0.47%, 0.76%].

**Mejor no afinado** (media entre réplicas): `default:SA` = 1.42%. Afinado vs ese: +0.80% de gap a favor del afinado, IC95 [+0.47%, +1.06%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 8422 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp`, `multistart_nondelay_composite_rule`, `neh_operation_sequence_insertion`, `critical_arc_adjacent_swap_n1`, `critical_segment_reversal_2opt`, `critical_block_boundary_insertion`, `critical_block_adjacent_swap`, `operation_sequence_shift_decode`, `giffler_thompson_machine_ruin_rebuild`

**Mejor en train**: `ILS[constructor=giffler_thompson_grasp, neighborhood=critical_segment_reversal_2opt, perturbation=critical_block_adjacent_swap]` = 0.1268

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.47%** | **1302.2** | 95 | +87.9% | `ILS[constructor=giffler_thompson_grasp, neighborhood=critical_segment_reversal_2opt, perturbation=critical_block_adjacent_swap]` |
| default:SA | 1.05% | 1309.8 | 98 | +87.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:TS | 1.48% | 1315.2 | 95 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:VNS | 18.53% | 1542.3 | 220 | +85.6% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:HYB | 21.79% | 1588.5 | 271 | +85.2% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=group_window]` |
| default:ILS | 34.40% | 1749.8 | 295 | +83.7% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.58%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 4, HYB × 3.

Afinado vs `default:SA` (mejor default por gap): +0.58% de gap a favor del afinado, IC95 [+0.24%, +0.81%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 8606 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp`, `multistart_nondelay_composite_rule`, `neh_operation_sequence_insertion`, `critical_arc_adjacent_swap_n1`, `critical_segment_reversal_2opt`, `critical_block_boundary_insertion`, `critical_block_adjacent_swap`, `operation_sequence_shift_decode`, `giffler_thompson_machine_ruin_rebuild`

**Mejor en train**: `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=random_variables]` = 0.1274

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.48%** | **1306.1** | 97 | +87.8% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=random_variables]` |
| default:TS | 1.28% | 1316.4 | 97 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:SA | 1.51% | 1319.8 | 103 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:VNS | 18.79% | 1550.4 | 221 | +85.5% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:HYB | 28.48% | 1678.8 | 304 | +84.3% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=group_window]` |
| default:ILS | 34.53% | 1756.7 | 298 | +83.6% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.78%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 7.

Afinado vs `default:TS` (mejor default por gap): +0.80% de gap a favor del afinado, IC95 [+0.50%, +1.10%].
