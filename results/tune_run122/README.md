## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 2.5 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.41% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| r1 | 1 | 0.28% | `ILS[constructor=random, neighborhood=job_insertion_shift, perturbation=iterated_greedy_destruct_reconstruct]` |

**Afinado entre réplicas**: media 0.34%, desvío 0.06%, rango [0.28%, 0.41%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 0.94%. Afinado vs ese: +0.60% de gap a favor del afinado, IC95 [+0.38%, +0.84%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 11826 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `lr_index_greedy_rcl`, `neh_flowtime_insertion_pruned`, `beam_search_append_idle`, `job_insertion_shift`, `pairwise_job_interchange`, `bounded_segment_reversal`, `random_insertion_chain_kick`, `iterated_greedy_destruct_reconstruct`, `adjacent_block_exchange_double_bridge`

**Mejor en train**: `ILS[constructor=lr_index_greedy_rcl, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` = 0.7829

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.19%** | **573961.0** | 497069 | +19.0% | `ILS[constructor=lr_index_greedy_rcl, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:TS | 0.76% | 577697.4 | 500842 | +18.5% | `TS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:VNS | 2.52% | 589795.1 | 512568 | +16.8% | `VNS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:ILS | 3.03% | 591194.6 | 512136 | +16.6% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:SA | 3.41% | 592772.1 | 514605 | +16.4% | `SA[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:GRASP | 7.21% | 619482.8 | 540115 | +12.6% | `GRASP[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |

Ganancia del afinado sobre el mejor default: **+0.65%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:TS` (mejor default por gap): +0.56% de gap a favor del afinado, IC95 [+0.35%, +0.80%].

## Réplica r1

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop 50x10,100x20,200x20) · 0 configuraciones fallidas · 10206 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `lr_index_greedy_rcl`, `neh_flowtime_insertion_pruned`, `beam_search_append_idle`, `job_insertion_shift`, `pairwise_job_interchange`, `bounded_segment_reversal`, `random_insertion_chain_kick`, `iterated_greedy_destruct_reconstruct`, `adjacent_block_exchange_double_bridge`

**Mejor en train**: `ILS[constructor=random, neighborhood=job_insertion_shift, perturbation=iterated_greedy_destruct_reconstruct]` = 0.7812

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.22%** | **572309.5** | 495457 | +19.3% | `ILS[constructor=random, neighborhood=job_insertion_shift, perturbation=iterated_greedy_destruct_reconstruct]` |
| default:TS | 0.86% | 577521.1 | 500752 | +18.5% | `TS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:VNS | 2.65% | 589480.4 | 512261 | +16.8% | `VNS[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:ILS | 3.13% | 590912.4 | 511932 | +16.6% | `ILS[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |
| default:SA | 3.49% | 591880.4 | 513847 | +16.5% | `SA[constructor=trivial, neighborhood=job_insertion_shift]` |
| default:GRASP | 7.30% | 619151.1 | 539902 | +12.7% | `GRASP[constructor=trivial, neighborhood=job_insertion_shift, perturbation=random_insertion_chain_kick]` |

Ganancia del afinado sobre el mejor default: **+0.90%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7, GRASP × 1.

Afinado vs `default:TS` (mejor default por gap): +0.64% de gap a favor del afinado, IC95 [+0.32%, +0.94%].
