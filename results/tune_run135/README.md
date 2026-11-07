## Réplicas del tuning (2)

### Catálogo `generated`

168 trials · 2.5 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.21% | `ILS[constructor=random, neighborhood=bounded_segment_reversal, perturbation=iterated_greedy_destruct_reconstruct]` |
| r1 | 1 | 0.33% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=job_insertion_shift, perturbation=iterated_greedy_destruct_reconstruct]` |

**Afinado entre réplicas**: media 0.27%, desvío 0.06%, rango [0.21%, 0.33%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.05%. Afinado vs ese: +0.78% de gap a favor del afinado, IC95 [+0.42%, +1.19%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

168 trials · 2.5 s/corrida · 6 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 11380 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `lr_index_greedy_rcl`, `neh_flowtime_insertion_pruned`, `beam_search_append_idle`, `job_insertion_shift`, `pairwise_job_interchange`, `bounded_segment_reversal`, `random_insertion_chain_kick`, `iterated_greedy_destruct_reconstruct`, `adjacent_block_exchange_double_bridge`

**Mejor en train**: `ILS[constructor=random, neighborhood=bounded_segment_reversal, perturbation=iterated_greedy_destruct_reconstruct]` = 0.7790

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.20%** | **571001.8** | 493558 | +19.4% | `ILS[constructor=random, neighborhood=bounded_segment_reversal, perturbation=iterated_greedy_destruct_reconstruct]` |
| default:TS | 1.03% | 577697.4 | 500842 | +18.5% | `TS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:VNS | 2.80% | 589766.7 | 512560 | +16.8% | `VNS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:ILS | 3.31% | 591194.6 | 512136 | +16.6% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:SA | 3.72% | 592747.1 | 514513 | +16.4% | `SA[constructor=trivial, neighborhood=job_insertion_shift]` |

Ganancia del afinado sobre el mejor default: **+1.16%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.84% de gap a favor del afinado, IC95 [+0.53%, +1.17%].

## Réplica r1

### Catálogo `generated`

168 trials · 2.5 s/corrida · 6 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 11097 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `lr_index_greedy_rcl`, `neh_flowtime_insertion_pruned`, `beam_search_append_idle`, `job_insertion_shift`, `pairwise_job_interchange`, `bounded_segment_reversal`, `random_insertion_chain_kick`, `iterated_greedy_destruct_reconstruct`, `adjacent_block_exchange_double_bridge`

**Mejor en train**: `ILS[constructor=lr_index_greedy_rcl, neighborhood=job_insertion_shift, perturbation=iterated_greedy_destruct_reconstruct]` = 0.7807

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.19%** | **570894.4** | 492797 | +19.5% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=job_insertion_shift, perturbation=iterated_greedy_destruct_reconstruct]` |
| default:TS | 0.91% | 577697.4 | 500842 | +18.5% | `TS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:VNS | 2.68% | 589766.7 | 512560 | +16.8% | `VNS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:ILS | 3.18% | 591194.6 | 512136 | +16.6% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:SA | 3.58% | 592781.7 | 514596 | +16.4% | `SA[constructor=trivial, neighborhood=job_insertion_shift]` |

Ganancia del afinado sobre el mejor default: **+1.18%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 4.

Afinado vs `default:TS` (mejor default por gap): +0.72% de gap a favor del afinado, IC95 [+0.28%, +1.20%].
