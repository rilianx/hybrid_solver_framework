## Réplicas del tuning (3)

### Catálogo `generated`

50 trials · 10.0 s · 10 train / 10 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 1.48% | `TS[constructor=greedy_farthest_first_route_filling, neighborhood=composite]` |
| r1 | 1 | 1.30% | `TS[constructor=greedy_farthest_first_route_filling, neighborhood=composite]` |
| r2 | 2 | 0.32% | `ILS[constructor=greedy_demand_weighted_insertion_ratio, neighborhood=granular_two_opt_star_tail_exchange, perturbation=radial_ruin_greedy_blink_recreate]` |

**Afinado entre réplicas**: media 1.04%, desvío 0.51%, rango [0.32%, 1.48%].

**Mejor no afinado** (media entre réplicas): `default:PR` = 4.70%. Afinado vs ese: +3.66% de gap a favor del afinado, IC95 [+1.45%, +6.19%] sobre las instancias; el afinado queda por delante en 3 de 3 réplicas.


## Réplica r0

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (cvrp x150) · 0 configuraciones fallidas · 10243 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=greedy_farthest_first_route_filling, neighborhood=composite]` = 0.1638

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.70%** | **21951.2** | 10370 | +87.7% | `TS[constructor=greedy_farthest_first_route_filling, neighborhood=composite]` |
| default:PR | 3.88% | 22472.3 | 10383 | +87.4% | `PR[constructor=trivial, neighborhood=granular_relocate_customer, relink=successor_chain_relink]` |
| default:ILS | 4.54% | 22918.3 | 11087 | +87.2% | `ILS[constructor=trivial, neighborhood=granular_relocate_customer, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:VNS | 5.41% | 22871.2 | 10581 | +87.2% | `VNS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:TS | 5.49% | 22710.4 | 10245 | +87.3% | `TS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:SA | 8.60% | 23358.2 | 10457 | +86.9% | `SA[constructor=trivial, neighborhood=granular_relocate_customer]` |

Ganancia del afinado sobre el mejor default: **+2.32%**; gana en 9/10 instancias de test. Esqueletos explorados: TS × 8.

Afinado vs `default:PR` (mejor default por gap): +3.18% de gap a favor del afinado, IC95 [+0.94%, +5.78%].

## Réplica r1

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (cvrp x150) · 0 configuraciones fallidas · 10185 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `TS[constructor=greedy_farthest_first_route_filling, neighborhood=composite]` = 0.1641

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.44%** | **21946.0** | 10463 | +87.7% | `TS[constructor=greedy_farthest_first_route_filling, neighborhood=composite]` |
| default:PR | 3.77% | 22467.5 | 10383 | +87.4% | `PR[constructor=trivial, neighborhood=granular_relocate_customer, relink=successor_chain_relink]` |
| default:ILS | 4.37% | 22902.1 | 11082 | +87.2% | `ILS[constructor=trivial, neighborhood=granular_relocate_customer, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:VNS | 5.09% | 22828.8 | 10587 | +87.2% | `VNS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:TS | 5.37% | 22706.0 | 10247 | +87.3% | `TS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:SA | 7.02% | 23143.1 | 10573 | +87.0% | `SA[constructor=trivial, neighborhood=granular_relocate_customer]` |

Ganancia del afinado sobre el mejor default: **+2.32%**; gana en 9/10 instancias de test. Esqueletos explorados: TS × 4, ILS × 4.

Afinado vs `default:PR` (mejor default por gap): +3.33% de gap a favor del afinado, IC95 [+1.21%, +5.72%].

## Réplica r2

### Catálogo `generated`

50 trials · 10.0 s/corrida · 10 train / 10 test (cvrp x150) · 0 configuraciones fallidas · 10213 s de tuning

objetivo de tuning: `ratio`

**Mejor en train**: `ILS[constructor=greedy_demand_weighted_insertion_ratio, neighborhood=granular_two_opt_star_tail_exchange, perturbation=radial_ruin_greedy_blink_recreate]` = 0.1632

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.24%** | **21767.2** | 10443 | +87.8% | `ILS[constructor=greedy_demand_weighted_insertion_ratio, neighborhood=granular_two_opt_star_tail_exchange, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:PR | 4.66% | 22480.9 | 10379 | +87.4% | `PR[constructor=trivial, neighborhood=granular_relocate_customer, relink=successor_chain_relink]` |
| default:ILS | 5.23% | 22913.1 | 11087 | +87.2% | `ILS[constructor=trivial, neighborhood=granular_relocate_customer, perturbation=radial_ruin_greedy_blink_recreate]` |
| default:VNS | 6.15% | 22871.4 | 10582 | +87.2% | `VNS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:TS | 6.36% | 22728.0 | 10234 | +87.3% | `TS[constructor=trivial, neighborhood=granular_relocate_customer]` |
| default:SA | 9.14% | 23336.1 | 10500 | +86.9% | `SA[constructor=trivial, neighborhood=granular_relocate_customer]` |

Ganancia del afinado sobre el mejor default: **+3.17%**; gana en 10/10 instancias de test. Esqueletos explorados: ILS × 7, PR × 1.

Afinado vs `default:PR` (mejor default por gap): +4.42% de gap a favor del afinado, IC95 [+2.08%, +6.98%].
