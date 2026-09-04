### Catálogo `handwritten`

30 trials · 5.0 s/corrida · 3 train / 3 test (10×15) · 0 configuraciones fallidas · 490 s de tuning

**Mejor en train**: `LOCAL_BRANCH[constructor=lot_for_lot]` = 73694.8 (mejor default: 74094.3, `LOCAL_BRANCH[constructor=lot_for_lot]`)

| en TEST | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|
| **afinado** | **77605.2** | 5095 | +33.7% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LOCAL_BRANCH | 77740.6 | 5393 | +33.6% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LNS_MIP | 77847.2 | 5465 | +33.5% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:FIX_OPT | 79927.5 | 2939 | +31.7% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | 85917.7 | 5567 | +26.6% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 107730.8 | 9445 | +8.0% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | 108964.8 | 9074 | +6.9% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | 110682.6 | 6856 | +5.5% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:GRASP | 111163.6 | 10442 | +5.1% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.17%**; gana en 1/3 instancias de test. Esqueletos explorados: LOCAL_BRANCH × 14, LNS_MIP × 3, GRASP × 3, SA × 2, ILS × 2, FIX_OPT × 2, TS × 2, VNS × 2.

### Catálogo `all`

30 trials · 5.0 s/corrida · 3 train / 3 test (10×15) · 0 configuraciones fallidas · 491 s de tuning

Componentes LLM en el catálogo: `backward_capacity_packing`, `earliest_slack_repair`, `adjacent_pair_merge_destruction`, `capacity_critical_period_destruction`, `whole_item_destruction`, `drop_single_setup`, `left_shift_setup_chain`, `merge_consecutive_setups`, `congested_period_relocation_perturbation`, `item_block_compaction_perturbation`, `period_swap_relink_perturbation`

**Mejor en train**: `LOCAL_BRANCH[constructor=backward_capacity_packing]` = 73720.8 (mejor default: 74086.3, `LOCAL_BRANCH[constructor=lot_for_lot]`)

| en TEST | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|
| **afinado** | **76861.3** | 5287 | +34.4% | `LOCAL_BRANCH[constructor=backward_capacity_packing]` |
| default:LOCAL_BRANCH | 77676.2 | 5490 | +33.7% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LNS_MIP | 77845.3 | 5467 | +33.5% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:FIX_OPT | 79927.5 | 2939 | +31.7% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | 85656.3 | 5377 | +26.9% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | 107307.5 | 9459 | +8.4% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | 110730.4 | 10608 | +5.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | 110983.6 | 6861 | +5.2% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:GRASP | 111016.2 | 10325 | +5.2% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+1.05%**; gana en 3/3 instancias de test. Esqueletos explorados: LOCAL_BRANCH × 14, SA × 3, VNS × 3, ILS × 2, LNS_MIP × 2, FIX_OPT × 2, TS × 2, GRASP × 2.

### ¿Ayuda o diluye?

Afinado en test — a mano: 77605.2 (`LOCAL_BRANCH[constructor=lot_for_lot]`) · con LLM: 76861.3 (`LOCAL_BRANCH[constructor=backward_capacity_packing]`) → **+0.96%**, el catálogo ampliado **ayuda**.
