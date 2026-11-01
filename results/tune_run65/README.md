## Réplicas del tuning (3)

### Catálogo `generated`

50 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.49% | `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_cross_exchange_segments]` |
| r1 | 1 | 1.14% | `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_cross_exchange_segments]` |
| r2 | 2 | 1.17% | `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_relocate_customer]` |

**Afinado entre réplicas**: media 1.27%, desvío 0.16%, rango [1.14%, 1.49%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 3.38%. Afinado vs ese: +2.11% de gap a favor del afinado, IC95 [+0.06%, +4.49%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (cvrp x150) · 0 configuraciones fallidas · 10202 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_cross_exchange_segments]` = 0.1651

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **1.10%** | **22144.4** | 10415 | +87.6% | `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_cross_exchange_segments]` |
| default:PR | 3.03% | 22403.3 | 10381 | +87.4% | `PR[constructor=trivial, neighborhood=granular_relocate_customer, relink=successor_chain_relink]` |
| default:ILS | 3.84% | 22865.1 | 11053 | +87.2% | `ILS[constructor=trivial, neighborhood=granular_relocate_customer, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:TS | 4.49% | 22619.1 | 10230 | +87.3% | `TS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:VNS | 4.64% | 22864.4 | 10719 | +87.2% | `VNS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:SA | 6.90% | 23151.4 | 10497 | +87.0% | `SA[constructor=trivial, neighborhood=granular_relocate_customer]` |

Ganancia del afinado sobre el mejor default: **+1.16%**; gana en 6/10 instancias de test. Esqueletos explorados: VNS × 6, ILS × 2.

Afinado vs `default:PR` (mejor default por gap): +1.93% de gap a favor del afinado, IC95 [-0.35%, +4.53%] — **no se distingue del ruido** con estas instancias.

## Réplica r1

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (cvrp x150) · 0 configuraciones fallidas · 10025 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_cross_exchange_segments]` = 0.1647

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.83%** | **22091.6** | 10504 | +87.6% | `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_cross_exchange_segments]` |
| default:PR | 2.97% | 22374.6 | 10375 | +87.5% | `PR[constructor=trivial, neighborhood=granular_relocate_customer, relink=successor_chain_relink]` |
| default:ILS | 3.83% | 22840.4 | 11031 | +87.2% | `ILS[constructor=trivial, neighborhood=granular_relocate_customer, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:TS | 4.15% | 22562.6 | 10263 | +87.4% | `TS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:VNS | 4.50% | 22817.6 | 10705 | +87.2% | `VNS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:SA | 6.01% | 22969.4 | 10487 | +87.1% | `SA[constructor=trivial, neighborhood=granular_relocate_customer]` |

Ganancia del afinado sobre el mejor default: **+1.26%**; gana en 6/10 instancias de test. Esqueletos explorados: VNS × 8.

Afinado vs `default:PR` (mejor default por gap): +2.15% de gap a favor del afinado, IC95 [+0.13%, +4.43%].

## Réplica r2

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (cvrp x150) · 0 configuraciones fallidas · 10042 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_relocate_customer]` = 0.1642

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.82%** | **22104.7** | 10555 | +87.6% | `VNS[constructor=greedy_farthest_first_route_filling, neighborhood=granular_relocate_customer]` |
| default:PR | 3.05% | 22402.8 | 10381 | +87.4% | `PR[constructor=trivial, neighborhood=granular_relocate_customer, relink=successor_chain_relink]` |
| default:ILS | 3.88% | 22866.3 | 11054 | +87.2% | `ILS[constructor=trivial, neighborhood=granular_relocate_customer, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:TS | 4.51% | 22619.1 | 10230 | +87.3% | `TS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:VNS | 4.64% | 22858.5 | 10719 | +87.2% | `VNS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:SA | 6.05% | 23044.5 | 10603 | +87.1% | `SA[constructor=trivial, neighborhood=granular_relocate_customer]` |

Ganancia del afinado sobre el mejor default: **+1.33%**; gana en 7/10 instancias de test. Esqueletos explorados: VNS × 2, ILS × 3.

Afinado vs `default:PR` (mejor default por gap): +2.23% de gap a favor del afinado, IC95 [+0.36%, +4.44%].
