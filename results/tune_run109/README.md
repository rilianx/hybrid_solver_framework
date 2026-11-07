## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 2.5 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.41% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=pairwise_job_interchange, perturbation=iterated_greedy_destruct_reconstruct]` |
| r1 | 1 | 0.35% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=pairwise_job_interchange, perturbation=iterated_greedy_destruct_reconstruct]` |

**Afinado entre réplicas**: media 0.38%, desvío 0.03%, rango [0.35%, 0.41%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.07%. Afinado vs ese: +0.69% de gap a favor del afinado, IC95 [+0.45%, +0.95%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 7888 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `lr_index_greedy_rcl`, `neh_flowtime_insertion_pruned`, `beam_search_append_idle`, `job_insertion_shift`, `pairwise_job_interchange`, `bounded_segment_reversal`, `random_insertion_chain_kick`, `iterated_greedy_destruct_reconstruct`, `adjacent_block_exchange_double_bridge`

**Mejor en train**: `ILS[constructor=lr_index_greedy_rcl, neighborhood=pairwise_job_interchange, perturbation=iterated_greedy_destruct_reconstruct]` = 0.7817

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.28%** | **572164.1** | 494572 | +19.3% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=pairwise_job_interchange, perturbation=iterated_greedy_destruct_reconstruct]` |
| default:TS | 0.94% | 577681.3 | 500858 | +18.5% | `TS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:VNS | 2.74% | 589901.0 | 512680 | +16.8% | `VNS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:ILS | 3.23% | 591194.6 | 512136 | +16.6% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:SA | 3.57% | 592277.8 | 513896 | +16.4% | `SA[constructor=trivial, neighborhood=job_insertion_shift]` |

Ganancia del afinado sobre el mejor default: **+0.96%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.66% de gap a favor del afinado, IC95 [+0.36%, +1.04%].

## Réplica r1

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 8091 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `lr_index_greedy_rcl`, `neh_flowtime_insertion_pruned`, `beam_search_append_idle`, `job_insertion_shift`, `pairwise_job_interchange`, `bounded_segment_reversal`, `random_insertion_chain_kick`, `iterated_greedy_destruct_reconstruct`, `adjacent_block_exchange_double_bridge`

**Mejor en train**: `ILS[constructor=lr_index_greedy_rcl, neighborhood=pairwise_job_interchange, perturbation=iterated_greedy_destruct_reconstruct]` = 0.7795

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **572825.4** | 496198 | +19.2% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=pairwise_job_interchange, perturbation=iterated_greedy_destruct_reconstruct]` |
| default:TS | 0.97% | 577555.1 | 500685 | +18.5% | `TS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:VNS | 2.74% | 589538.4 | 512303 | +16.8% | `VNS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:ILS | 3.23% | 590923.0 | 511921 | +16.6% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:SA | 3.63% | 592180.8 | 513752 | +16.5% | `SA[constructor=trivial, neighborhood=job_insertion_shift]` |

Ganancia del afinado sobre el mejor default: **+0.82%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.71% de gap a favor del afinado, IC95 [+0.52%, +0.87%].
