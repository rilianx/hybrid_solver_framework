## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 10.0 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.10% | `TS[constructor=random, neighborhood=critical_arc_adjacent_swap_n1]` |
| r1 | 1 | 0.36% | `HYB[constructor=multistart_nondelay_composite_rule, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=random_variables]` |

**Afinado entre réplicas**: media 0.73%, desvío 0.37%, rango [0.36%, 1.10%].

**Mejor no afinado** (media entre réplicas): `default:SA` = 1.63%. Afinado vs ese: +0.90% de gap a favor del afinado, IC95 [+0.62%, +1.14%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 11957 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp`, `multistart_nondelay_composite_rule`, `neh_operation_sequence_insertion`, `critical_arc_adjacent_swap_n1`, `critical_segment_reversal_2opt`, `critical_block_boundary_insertion`, `critical_block_adjacent_swap`, `operation_sequence_shift_decode`, `giffler_thompson_machine_ruin_rebuild`

**Mejor en train**: `TS[constructor=random, neighborhood=critical_arc_adjacent_swap_n1]` = 0.1272

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.35%** | **1308.0** | 100 | +87.8% | `TS[constructor=random, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:TS | 0.96% | 1315.6 | 96 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:SA | 1.10% | 1317.8 | 100 | +87.7% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:VNS | 17.89% | 1542.3 | 220 | +85.6% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:HYB | 21.93% | 1597.3 | 268 | +85.1% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=group_window]` |
| default:ILS | 34.15% | 1756.7 | 298 | +83.6% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |
| default:GRASP | 292.58% | 5142.8 | 818 | +52.0% | `GRASP[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.58%**; gana en 5/6 instancias de test. Esqueletos explorados: TS × 8.

Afinado vs `default:TS` (mejor default por gap): +0.61% de gap a favor del afinado, IC95 [+0.09%, +1.20%].

## Réplica r1

### Catálogo `generated`

80 trials · 10.0 s/corrida · 6 train / 6 test (jobshop 15x15,20x15) · 0 configuraciones fallidas · 11669 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `giffler_thompson_grasp`, `multistart_nondelay_composite_rule`, `neh_operation_sequence_insertion`, `critical_arc_adjacent_swap_n1`, `critical_segment_reversal_2opt`, `critical_block_boundary_insertion`, `critical_block_adjacent_swap`, `operation_sequence_shift_decode`, `giffler_thompson_machine_ruin_rebuild`

**Mejor en train**: `HYB[constructor=multistart_nondelay_composite_rule, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=random_variables]` = 0.1274

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.36%** | **1298.3** | 97 | +87.9% | `HYB[constructor=multistart_nondelay_composite_rule, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=random_variables]` |
| default:SA | 1.41% | 1312.1 | 100 | +87.8% | `SA[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:TS | 1.64% | 1314.7 | 96 | +87.7% | `TS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:VNS | 18.77% | 1542.3 | 220 | +85.6% | `VNS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1]` |
| default:HYB | 20.97% | 1574.2 | 263 | +85.3% | `HYB[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap, destruction=group_window]` |
| default:ILS | 34.68% | 1749.8 | 295 | +83.7% | `ILS[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |
| default:GRASP | 295.44% | 5142.8 | 818 | +52.0% | `GRASP[constructor=trivial, neighborhood=critical_arc_adjacent_swap_n1, perturbation=critical_block_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+1.05%**; gana en 6/6 instancias de test. Esqueletos explorados: HYB × 8.

Afinado vs `default:SA` (mejor default por gap): +1.05% de gap a favor del afinado, IC95 [+0.67%, +1.38%].
