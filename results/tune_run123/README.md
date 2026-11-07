## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 2.5 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.16% | `ILS[constructor=cds_johnson_palmer_best, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |
| r1 | 1 | 0.20% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |

**Afinado entre réplicas**: media 0.18%, desvío 0.02%, rango [0.16%, 0.20%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.32%. Afinado vs ese: +1.14% de gap a favor del afinado, IC95 [+0.50%, +1.84%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 11015 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `neh_taillard_noisy_order`, `cds_johnson_palmer_best`, `grasp_lr_index_append`, `pfsp_job_insertion_taillard`, `pfsp_pairwise_swap_headtail`, `pfsp_block_reversal_2opt`, `random_insert_swap_kick`, `ig_destruct_reconstruct_taillard`, `segment_double_bridge_exchange`

**Mejor en train**: `ILS[constructor=cds_johnson_palmer_best, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` = 0.8132

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.09%** | **6970.1** | 3491 | +17.7% | `ILS[constructor=cds_johnson_palmer_best, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |
| default:TS | 1.28% | 7048.9 | 3505 | +16.8% | `TS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:SA | 1.85% | 7103.7 | 3568 | +16.1% | `SA[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:VNS | 2.56% | 7151.1 | 3572 | +15.6% | `VNS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:ILS | 4.11% | 7257.1 | 3616 | +14.3% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |
| default:GRASP | 6.98% | 7491.4 | 3787 | +11.5% | `GRASP[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |

Ganancia del afinado sobre el mejor default: **+1.12%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:TS` (mejor default por gap): +1.18% de gap a favor del afinado, IC95 [+0.58%, +1.90%].

## Réplica r1

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 11559 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `neh_taillard_noisy_order`, `cds_johnson_palmer_best`, `grasp_lr_index_append`, `pfsp_job_insertion_taillard`, `pfsp_pairwise_swap_headtail`, `pfsp_block_reversal_2opt`, `random_insert_swap_kick`, `ig_destruct_reconstruct_taillard`, `segment_double_bridge_exchange`

**Mejor en train**: `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` = 0.8146

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.17%** | **6970.8** | 3488 | +17.7% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=ig_destruct_reconstruct_taillard]` |
| default:TS | 1.26% | 7044.4 | 3500 | +16.8% | `TS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:SA | 1.70% | 7084.9 | 3546 | +16.3% | `SA[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:VNS | 2.53% | 7147.8 | 3572 | +15.6% | `VNS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:ILS | 4.13% | 7256.8 | 3616 | +14.3% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |
| default:GRASP | 7.01% | 7491.4 | 3787 | +11.5% | `GRASP[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |

Ganancia del afinado sobre el mejor default: **+1.04%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 8.

Afinado vs `default:TS` (mejor default por gap): +1.09% de gap a favor del afinado, IC95 [+0.42%, +1.82%].
