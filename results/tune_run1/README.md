# Tuning, corrida 1 (Actions, 4 de septiembre de 2026)

Corrida [#1 de `tune.yml`](https://github.com/rilianx/hybrid_solver_framework/actions/runs/33872624713)
sobre `main` en `77776ba`: Optuna, 60 trials por catálogo, 5 instancias de
entrenamiento y 5 de test (Trigeiro 10×15), 5 s por corrida, 3 semillas en test.
Es la corrida que resume el artefacto del proyecto ("¿El catálogo ampliado ayuda o
diluye? Ni lo uno ni lo otro"). Rescatada del adjunto `tuning-1` antes de que expirara.

**Lo central:** los dos catálogos convergen a la misma configuración
(`LNS_MIP` con `random_setups`) y al mismo costo en test, 85 910,5 (lot-for-lot: 129 394,4),
así que la diferencia es 0,00 %. En el catálogo `all`, 35 de los 60 trials usaron algún
componente generado; el mejor de ellos quedó a +0,60 % del ganador en train.

**Contexto para leerla:**

- El catálogo `all` es el de la **corrida 7** de generación (el `generated/clsp` de `main`
  en ese momento), no el de la 8.
- Es anterior al gap por instancia: el costo medio lo domina la quinta instancia de test
  (116 063 contra 70–83 mil de las otras cuatro). Las columnas de gap salen como "—".
- `mip_time_share` todavía tenía el piso de 1 s, así que en esta corrida era inerte.
- `irace/` quedó tal como lo escribió el runner: rutas absolutas de
  `/home/runner/...` y parámetros del catálogo de la corrida 7. Para correr irace hoy,
  regenera el escenario con `examples.lotsizing.tune --irace DIR`, que ahora escribe
  rutas relativas.

Archivos: `handwritten.json`, `all.json` (trials, configuraciones, costos por
instancia), `comparison.json`, `tune.log`.

---

### Catálogo `handwritten`

60 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1631 s de tuning

**Mejor en train**: `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` = 72823.7 (mejor default: 73359.7, `LOCAL_BRANCH[constructor=lot_for_lot]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **—** | **85910.5** | 15815 | +33.6% | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| default:LOCAL_BRANCH | — | 86521.1 | 16849 | +33.1% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LNS_MIP | — | 86564.9 | 15621 | +33.1% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:FIX_OPT | — | 88158.9 | 14088 | +31.9% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | — | 92491.2 | 16174 | +28.5% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | — | 117109.0 | 21272 | +9.5% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | — | 118483.0 | 21568 | +8.4% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | — | 119048.9 | 21520 | +8.0% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:GRASP | — | 119738.8 | 22762 | +7.5% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.71%**; gana en 3/5 instancias de test. Esqueletos explorados: LNS_MIP × 23, LOCAL_BRANCH × 13, SA × 4, ILS × 4, FIX_OPT × 4, TS × 4, VNS × 4, GRASP × 4.

### Catálogo `all`

60 trials · 5.0 s/corrida · 5 train / 5 test (10×15) · 0 configuraciones fallidas · 1672 s de tuning

Componentes LLM en el catálogo: `consecutive_lot_merge_constructor`, `cumulative_backward_repair`, `randomized_priority_capacity_packing`, `capacity_bottleneck_destruction`, `item_chain_destruction`, `low_leverage_setup_destruction`, `cross_period_setup_exchange`, `redundant_setup_pruner`, `same_period_setup_swap`, `neighbor_shift_perturbation`, `period_compaction_perturbation`, `two_item_swap_perturbation`

**Mejor en train**: `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` = 72823.7 (mejor default: 73316.5, `LOCAL_BRANCH[constructor=lot_for_lot]`)

| en TEST | gap vs mejor conocido | costo medio | ± | vs lot-for-lot | configuración |
|---|---|---|---|---|---|
| **afinado** | **—** | **85910.5** | 15815 | +33.6% | `LNS_MIP[constructor=lot_for_lot, destruction=random_setups]` |
| default:LOCAL_BRANCH | — | 86454.0 | 16722 | +33.2% | `LOCAL_BRANCH[constructor=lot_for_lot]` |
| default:LNS_MIP | — | 86564.9 | 15621 | +33.1% | `LNS_MIP[constructor=lot_for_lot, destruction=period_window]` |
| default:FIX_OPT | — | 88158.9 | 14088 | +31.9% | `FIX_OPT[constructor=lot_for_lot, fixing_policy=sliding_window]` |
| default:SA | — | 92607.5 | 16110 | +28.4% | `SA[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:ILS | — | 117109.0 | 21272 | +9.5% | `ILS[constructor=lot_for_lot, neighborhood=setup_flip, perturbation=setup_flip_perturbation]` |
| default:VNS | — | 118962.2 | 22145 | +8.1% | `VNS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:TS | — | 119048.9 | 21520 | +8.0% | `TS[constructor=lot_for_lot, neighborhood=setup_flip]` |
| default:GRASP | — | 119845.0 | 22704 | +7.4% | `GRASP[constructor=lot_for_lot, neighborhood=setup_flip]` |

Ganancia del afinado sobre el mejor default: **+0.63%**; gana en 3/5 instancias de test. Esqueletos explorados: LOCAL_BRANCH × 22, LNS_MIP × 17, SA × 4, ILS × 4, VNS × 4, FIX_OPT × 3, TS × 3, GRASP × 3.

### ¿Ayuda o diluye?

Afinado en test — a mano: 85910.5 (`LNS_MIP[constructor=lot_for_lot, destruction=random_setups]`) · con LLM: 85910.5 (`LNS_MIP[constructor=lot_for_lot, destruction=random_setups]`) → **+0.00%**, **empate**: el tuner eligió lo mismo o equivalente.
