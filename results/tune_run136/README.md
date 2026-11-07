## Réplicas del tuning (2)

### Catálogo `generated`

168 trials · 2.5 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.42% | `ILS[constructor=cds_johnson_palmer_best, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |
| r1 | 1 | 0.18% | `ILS[constructor=grasp_lr_index_append, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |

**Afinado entre réplicas**: media 0.30%, desvío 0.12%, rango [0.18%, 0.42%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.33%. Afinado vs ese: +1.03% de gap a favor del afinado, IC95 [+0.44%, +1.64%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

168 trials · 2.5 s/corrida · 6 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 10832 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `neh_taillard_noisy_order`, `cds_johnson_palmer_best`, `grasp_lr_index_append`, `pfsp_job_insertion_taillard`, `pfsp_pairwise_swap_headtail`, `pfsp_block_reversal_2opt`, `random_insert_swap_kick`, `ig_destruct_reconstruct_taillard`, `segment_double_bridge_exchange`

**Mejor en train**: `ILS[constructor=cds_johnson_palmer_best, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` = 0.8142

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.16%** | **6978.3** | 3478 | +17.6% | `ILS[constructor=cds_johnson_palmer_best, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |
| default:TS | 1.04% | 7042.2 | 3500 | +16.8% | `TS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:SA | 1.36% | 7076.0 | 3544 | +16.4% | `SA[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:VNS | 2.13% | 7133.9 | 3570 | +15.8% | `VNS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:ILS | 3.69% | 7241.2 | 3613 | +14.5% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |

Ganancia del afinado sobre el mejor default: **+0.91%**; gana en 5/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.88% de gap a favor del afinado, IC95 [+0.33%, +1.43%].

## Réplica r1

### Catálogo `generated`

168 trials · 2.5 s/corrida · 6 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 11195 s de tuning

esqueletos: `SA`, `ILS`, `TS`, `VNS`, `PR` · objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `neh_taillard_noisy_order`, `cds_johnson_palmer_best`, `grasp_lr_index_append`, `pfsp_job_insertion_taillard`, `pfsp_pairwise_swap_headtail`, `pfsp_block_reversal_2opt`, `random_insert_swap_kick`, `ig_destruct_reconstruct_taillard`, `segment_double_bridge_exchange`

**Mejor en train**: `ILS[constructor=grasp_lr_index_append, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` = 0.8140

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.08%** | **6970.4** | 3495 | +17.7% | `ILS[constructor=grasp_lr_index_append, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |
| default:TS | 1.25% | 7045.3 | 3501 | +16.8% | `TS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:SA | 1.73% | 7098.1 | 3568 | +16.2% | `SA[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:VNS | 2.58% | 7152.1 | 3573 | +15.5% | `VNS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:ILS | 4.12% | 7257.1 | 3616 | +14.3% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |

Ganancia del afinado sobre el mejor default: **+1.06%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +1.17% de gap a favor del afinado, IC95 [+0.50%, +1.88%].
