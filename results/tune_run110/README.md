## Réplicas del tuning (2)

### Catálogo `generated`

80 trials · 2.5 s · 6 train / 6 test · gaps contra el mejor conocido común a las réplicas

| réplica | semilla del tuner | gap afinado | configuración elegida |
|---|---|---|---|
| r0 | 0 | 0.27% | `ILS[constructor=neh_taillard_noisy_order, neighborhood=pfsp_block_reversal_2opt, perturbation=ig_destruct_reconstruct_taillard]` |
| r1 | 1 | 0.44% | `ILS[constructor=neh_taillard_noisy_order, neighborhood=composite, perturbation=ig_destruct_reconstruct_taillard]` |

**Afinado entre réplicas**: media 0.35%, desvío 0.08%, rango [0.27%, 0.44%].

**Mejor no afinado** (media entre réplicas): `default:TS` = 1.18%. Afinado vs ese: +0.83% de gap a favor del afinado, IC95 [+0.41%, +1.36%] sobre las instancias; el afinado queda por delante en 2 de 2 réplicas.


## Réplica r0

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 8004 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `neh_taillard_noisy_order`, `cds_johnson_palmer_best`, `grasp_lr_index_append`, `pfsp_job_insertion_taillard`, `pfsp_pairwise_swap_headtail`, `pfsp_block_reversal_2opt`, `random_insert_swap_kick`, `ig_destruct_reconstruct_taillard`, `segment_double_bridge_exchange`

**Mejor en train**: `ILS[constructor=neh_taillard_noisy_order, neighborhood=pfsp_block_reversal_2opt, perturbation=ig_destruct_reconstruct_taillard]` = 0.8149

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.26%** | **6985.5** | 3491 | +17.5% | `ILS[constructor=neh_taillard_noisy_order, neighborhood=pfsp_block_reversal_2opt, perturbation=ig_destruct_reconstruct_taillard]` |
| default:TS | 1.14% | 7042.2 | 3500 | +16.8% | `TS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:SA | 1.44% | 7067.7 | 3526 | +16.5% | `SA[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:VNS | 2.23% | 7134.1 | 3570 | +15.8% | `VNS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:ILS | 3.79% | 7241.4 | 3613 | +14.5% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |

Ganancia del afinado sobre el mejor default: **+0.81%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.88% de gap a favor del afinado, IC95 [+0.46%, +1.41%].

## Réplica r1

### Catálogo `generated`

80 trials · 2.5 s/corrida · 6 train / 6 test (flowshop_cmax 50x10,100x20,200x20) · 0 configuraciones fallidas · 7443 s de tuning

objetivo de tuning: `ratio`

Componentes LLM en el catálogo: `neh_taillard_noisy_order`, `cds_johnson_palmer_best`, `grasp_lr_index_append`, `pfsp_job_insertion_taillard`, `pfsp_pairwise_swap_headtail`, `pfsp_block_reversal_2opt`, `random_insert_swap_kick`, `ig_destruct_reconstruct_taillard`, `segment_double_bridge_exchange`

**Mejor en train**: `ILS[constructor=neh_taillard_noisy_order, neighborhood=composite, perturbation=ig_destruct_reconstruct_taillard]` = 0.8168

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **0.13%** | **6994.0** | 3491 | +17.4% | `ILS[constructor=neh_taillard_noisy_order, neighborhood=composite, perturbation=ig_destruct_reconstruct_taillard]` |
| default:TS | 0.91% | 7046.8 | 3503 | +16.8% | `TS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:SA | 1.60% | 7104.7 | 3553 | +16.1% | `SA[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:VNS | 2.25% | 7153.8 | 3572 | +15.5% | `VNS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard]` |
| default:ILS | 3.80% | 7261.8 | 3619 | +14.3% | `ILS[constructor=trivial, neighborhood=pfsp_job_insertion_taillard, perturbation=random_insert_swap_kick]` |

Ganancia del afinado sobre el mejor default: **+0.75%**; gana en 6/6 instancias de test. Esqueletos explorados: ILS × 7.

Afinado vs `default:TS` (mejor default por gap): +0.77% de gap a favor del afinado, IC95 [+0.36%, +1.30%].
