## Réplicas del tuning (3)

### Catálogo `generated`

70 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.22% | `PR[constructor=random, neighborhood=critical_block_end_insertion, relink=hamming_position_swap_relink]` |
| r1 | 1 | 0.46% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |
| r2 | 2 | 0.27% | `PR[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |

**Afinado entre réplicas**: media 0.32%, desvío 0.10%, rango [0.22%, 0.46%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 0.87%. Afinado vs ese: +0.55% de gap a favor del afinado, IC95 [+0.30%, +0.77%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7202 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=random, neighborhood=critical_block_end_insertion, relink=hamming_position_swap_relink]` = 0.1385

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.21%** | **1199.5** | 65 | +86.6% | `PR[constructor=random, neighborhood=critical_block_end_insertion, relink=hamming_position_swap_relink]` |
| default:PR | 0.84% | 1207.2 | 68 | +86.5% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=kendall_adjacent_swap_relink]` |
| default:TS | 1.31% | 1212.9 | 69 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.61% | 1216.5 | 70 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 12.21% | 1343.9 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.70% | 1528.3 | 160 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.64%**; gana en 10/10 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:PR` (mejor default por gap): +0.63% de gap a favor del afinado, IC95 [+0.38%, +0.87%].

## Réplica r1

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7376 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` = 0.1385

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.21%** | **1202.4** | 65 | +86.6% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |
| default:PR | 0.62% | 1207.4 | 67 | +86.5% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=kendall_adjacent_swap_relink]` |
| default:TS | 1.23% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 2.00% | 1224.1 | 73 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 12.13% | 1346.1 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.52% | 1529.6 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.41%**; gana en 8/10 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:PR` (mejor default por gap): +0.41% de gap a favor del afinado, IC95 [+0.16%, +0.62%].

## Réplica r2

### Catálogo `generated`

70 trials · 10.0 s/corrida · 10 train / 10 test (jobshop 15x15) · 0 configuraciones fallidas · 7147 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `PR[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` = 0.1384

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.20%** | **1200.1** | 65 | +86.6% | `PR[constructor=greedy_bottleneck_weighted_work, neighborhood=critical_path_adjacent_swap, relink=lis_insertion_relink]` |
| default:PR | 0.81% | 1207.4 | 67 | +86.5% | `PR[constructor=trivial, neighborhood=critical_path_adjacent_swap, relink=kendall_adjacent_swap_relink]` |
| default:TS | 1.42% | 1214.7 | 67 | +86.5% | `TS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:SA | 1.87% | 1220.2 | 70 | +86.4% | `SA[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |
| default:ILS | 12.33% | 1346.1 | 136 | +85.0% | `ILS[constructor=trivial, neighborhood=critical_path_adjacent_swap, perturbation=critical_arc_swap_kick]` |
| default:VNS | 27.73% | 1529.6 | 161 | +83.0% | `VNS[constructor=trivial, neighborhood=critical_path_adjacent_swap]` |

Ganancia del afinado sobre el mejor default: **+0.60%**; gana en 9/10 instancias de test. Esqueletos explorados: PR × 7.

Afinado vs `default:PR` (mejor default por gap): +0.60% de gap a favor del afinado, IC95 [+0.34%, +0.86%].
