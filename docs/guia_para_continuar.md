# Hybrid Solver Framework: estado y guía para continuar

> Copia exportada del documento vivo: https://claude.ai/artifact/Cw2ShC5FCKguX9r7gBFkSu (la versión de referencia es esa).

Nov 6, 2026 · Ignacio Araya

## Para qué es este documento

Los 7 problemas ya tienen datos, referencias y solvers generados con el mismo protocolo; falta afinar, elegir la configuración final y evaluar contra la literatura y los métodos con LLM. Este documento es para quien continúa ese trabajo: dice dónde está todo, qué decisiones ya se tomaron y qué hacer, en orden.

El framework (repositorio [rilianx/hybrid\_solver\_framework](https://github.com/rilianx/hybrid_solver_framework), rama `claude/ecstatic-darwin-lmwxzk`) arma solvers híbridos para problemas de optimización combinatoria. Una persona escribe lo mínimo del problema: la instancia y su generador, una descripción en lenguaje natural, casos de prueba con respuestas conocidas y un oráculo en Python que calcula violaciones y costo. Un LLM escribe el resto: el modelo C++, los componentes (constructores, vecindarios, perturbaciones) y la vista MIP.

Cada pieza generada pasa por una validación en capas (compilación, contrato, operación, calidad, diversidad) antes de entrar al catálogo. Después irace elige el esqueleto (SA, ILS, TS, VNS, PR o HYB, el híbrido con sub-MIP), los componentes y sus parámetros. El borrador técnico del método está en [Solvers híbridos generados por LLM](https://claude.ai/artifact/NVRsT6xucJsirtnczZEBct).

## Estado actual

Los 7 problemas tienen generados el modelo C++, 9 componentes y (salvo los flow shop) la vista MIP con el protocolo v2: 63 de 63 componentes aceptados, 53 en la primera ronda, 8,88 USD en total. Al 6 de noviembre de 2026 corren 9 tunings, uno por tipo de instancia (runs 109–117 de `tune.yml`).

| Problema | Benchmark de OR (referencias) | Sets de los trabajos con LLM | Comparación publicada con LLM |
| --- | --- | --- | --- |
| CVRP | X de Uchoa, 100 (`examples/cvrp/uchoa`) | FrontierCO: Golden, valid, Arnold (`frontierco`); test de ReEvo (`reevo`) y de MCTS-AHD (`mcts_ahd`), con referencia HGS | MCTS-AHD tabla 2; FrontierCO tabla 7 |
| MKP | OR-Library mknap1, mknap2, mknapcb (325, `examples/mkp/orlib`) | test de ReEvo = MKP de MCTS-AHD (320, `fetch --reevo`; óptimos CBC) | MCTS-AHD tabla 2; CO-Bench tabla 24 |
| Flow shop (makespan y flowtime) | Taillard, 120 (`examples/flowshop/taillard`) | los mismos | EoH tablas 3 y 12; CO-Bench tabla 17 |
| Job shop | Taillard ta01–ta80 y OR-Library, 162 (`examples/jobshop/bench`) | ta01–ta80 | CO-Bench tabla 21 |
| SSCFLP (nuevo) | Holmberg, Díaz-Fernández, Yang, TB4, OR-Library; TBED1 con `--large` (329, `examples/sscflp/bench`) | i1000 de FrontierCO (con demanda divisible allá) | FrontierCO tabla 8 (CFLP) |
| CLSP | Trigeiro (`examples/lotsizing/trigeiro`) | ninguno | ninguna |

Los resultados publicados de ReEvo, MCTS-AHD, HSEvo, EoH, CO-Bench y FrontierCO están transcritos con tabla y página en `results/llm_sota/` (README con los cuidados al comparar). Los catálogos generados están en `generated/v2/<problema>`; los de antes (`generated/<problema>_native`) quedaron intactos con sus tunings y resultados.

## Cómo está organizado y cómo se corre

Todo lo que gasta tokens o mucho cómputo corre en GitHub Actions; en local se corren los tests, los scripts de datos y `bench_eval`.

| Dónde | Qué hay |
| --- | --- |
| `examples/<problema>/` | lo humano: `instance.py` (datos y generador), `llm_spec.py` (descripción para el LLM), `cases.py` + `cases.json`, `model_parts.py` (oráculo), `pack.py`, `fetch.py` (benchmarks) |
| `generated/v2/<problema>/` | lo que escribió el LLM: `model/`, `constructor/`, `neighborhood/`, `perturbation/`, `mip/`, `catalog.json` y los `*stats.json` (tokens, costo, rechazos) |
| `native/include/hsf/` | el contrato C++ (`core.hpp`, `generic.hpp`) y los esqueletos |
| `core/validation/` | las capas de validación |
| `llm/` | generadores de modelo, componentes, MIP y optimizaciones |
| `tuning/`, `scripts/bench_eval.py` | irace y la evaluación en los benchmarks |
| `results/` | corridas de tuning (`tune_runNN`), `README.md` con el historial, `llm_sota/` |

Comandos de uso diario:

```
pip install -r requirements.txt
python -m pytest -q                          # unos 4 min; el test de optimización encadenada falla a veces bajo carga
python -m examples.sscflp.fetch --large       # instancias grandes (fuera de git)
python -m examples.mkp.fetch --reevo
python -m scripts.bench_eval cvrp_mcts_ahd results/tune_runNN --generated generated/v2/cvrp --seeds 3
```

Workflows (pestaña Actions, rama `claude/ecstatic-darwin-lmwxzk`):

- **`generate.yml`**: `target` = model, components, mip, optimize o model\_optimize; `workspace` = `generated/v2/<problema>`; `provider` = anthropic. Deja lo generado en una rama `llm-generated/<problema>-<target>-anthropic-runNN` que hay que fusionar a mano (`open_pr: false`).
- **`tune.yml`**: `generated_dir` = `generated/v2/<problema>`, `size`, `budget`, `trials`, `replicas`, y `extra_args: --scale-budget`. Los resultados quedan en el artefacto de la corrida y se copian a `results/tune_runNN`, como en las runs 98–101.

## Lo que falta, en orden

Quedan cinco pasos: traer los 9 tunings, elegir una configuración por tipo de instancia, evaluar cada una en su familia de benchmark, armar las tablas de comparación y escribir los resultados.

1. **Traer los tunings.** Cuando terminen las runs 109–117, descargar sus artefactos y copiarlos a `results/tune_runNN` con el mismo formato que las runs 98–101 (carpetas `r0`, `r1` y `replicas.json`). Si alguna falló, mirar el log del job antes de relanzar.
2. **Elegir la configuración de cada tipo.** De las 2 réplicas, la de menor brecha media en las 6 instancias generadas de test del tuning. Nunca elegir mirando el benchmark. Anotar en el README de la run cuál se eligió y por qué.
3. **Evaluar en el benchmark con `bench_eval`**, la configuración elegida y la otra réplica (para mostrar la variabilidad), 3 semillas. Cada tipo de instancia se evalúa solo en su familia (tabla de abajo).
4. **Armar las tablas de comparación** contra las referencias de OR y contra lo publicado por los métodos con LLM (`results/llm_sota/`), respetando la métrica y el tiempo de cada fuente.
5. **Escribir los resultados** en `results/README.md` y en el borrador técnico.

| Run de tuning | Tipo de instancia (tamaños) | Evaluar en (`bench_eval`) | Tiempo de evaluación |
| --- | --- | --- | --- |
| flowshop | tipo Taillard (50×10 a 200×20) | `flowshop` | protocolo n·m/2·t ms |
| flowshop\_cmax | tipo Taillard | `flowshop_cmax`; contra CO-Bench, `--budget 10` | protocolo y 10 s |
| jobshop | tipo Taillard (15×15, 20×15) | `jobshop`; contra CO-Bench, `--budget 10` | protocolo y 10 s |
| clsp | tipo Trigeiro (20×20) | `clsp` | protocolo |
| cvrp (x100, x200, x250) | tipo X de Uchoa | `cvrp`, `cvrp_frontierco` (Golden, valid) | protocolo (2,4·n s con t = 240) |
| cvrp (u50, u100) | uniforme como ReEvo | `cvrp_mcts_ahd`, `cvrp_reevo` | a definir (MCTS-AHD no fija tiempo) |
| sscflp | tipo Holmberg (20×100 a 60×200) | `sscflp` (H, D, Y, TB4, cap) | protocolo |
| mkp (100×5 a 250×10) | tipo Chu y Beasley | `mkp`; contra CO-Bench, `--budget 10` | protocolo y 10 s |
| mkp (n100×5 a n500×5) | normalizado como ReEvo | `mkp_reevo` | a definir |

El tiempo completo de la literatura es caro: en el CVRP son 240 s por instancia de 100 clientes y 2400 s en las de 1000. Conviene correr primero con un `t` menor (por ejemplo 10 % del protocolo, `--t 24` en CVRP o `--t 6` en los demás) y reportarlo como tal.

## Decisiones de protocolo ya tomadas

No cambiar estas reglas sin consultarlo: varias costaron corridas enteras y son las que el paper va a declarar.

| Decisión | Regla | Por qué |
| --- | --- | --- |
| Generación uniforme (v2) | Opus 5.5, prompts compactos, n = 3 por slot, hasta 3 rondas, validación actual; los 7 problemas igual | tasas de aceptación y costos comparables entre problemas |
| Una configuración por tipo de instancia | un tuning por familia de benchmark (p. ej. CVRP tipo X y CVRP uniforme por separado) | irace rinde con instancias homogéneas; los métodos con LLM también afinan por set |
| Tuning con instancias generadas | generadores que imitan cada benchmark, otras semillas; el benchmark nunca se usa para afinar ni para elegir | el benchmark queda como test intocado |
| Tiempo que crece con el tamaño | tuning con `--scale-budget` (base × tamaño / tamaño de referencia); evaluación con el protocolo de `bench_eval` | con tiempo fijo, las instancias grandes casi no avanzan y el tuner premia lo que converge rápido |
| Protocolos de tiempo | flow shop n·m/2·t ms (Taillard; Ruiz y Stützle); CVRP 2,4·n s (Vidal 2022); en job shop, CLSP, SSCFLP y MKP la misma forma que el flow shop | solo flow shop y CVRP tienen una regla establecida; la de los demás es nuestra y se declara así |
| Presupuesto de irace | 80 trials × 6 instancias de train, 6 de test, 2 réplicas | con 480 corridas irace ve unas 5 a 8 instancias por carrera: más instancias no ayudan sin más presupuesto |
| Elección de réplica | la de menor brecha en el test generado; se reportan ambas en el benchmark | el tuning es parte del método: su variabilidad se muestra |
| Comparaciones con LLM | la métrica y el tiempo de cada fuente: CO-Bench 10 s y score propio; FrontierCO gap primal; MCTS-AHD objetivo medio | sus números no son comparables entre sí ni con nuestro gap |

## Trampas conocidas

Casi todos los fallos de generación de esta etapa fueron errores de especificación del problema, no del LLM. Al agregar un problema nuevo, revisar esta lista antes de lanzar nada.

**Al especificar un problema**

- La respuesta y la solución C++ son siempre una lista de listas de enteros (`vector<vector<int>>`). Una asignación plana va como `[[2, 0, 2, 2]]`, como en el flow shop; con listas planas fallan las 3 rondas.
- La descripción tiene que decir cuál es la solución trivial. La validación exige penalización = 10 · (|costo de la trivial del oráculo| + 1): si el LLM elige otra trivial, el modelo se rechaza (pasó en MKP y SSCFLP).
- En un problema de maximización el costo es el valor con signo menos y la trivial no puede costar 0 (en MKP es la greedy, no la mochila vacía); si no, la penalización queda en 10 y lo infactible conviene.
- Definir `well_formed(inst, sol)` en el oráculo: la validación revisa la forma de todo lo que producen el modelo y los componentes. Sin eso, una perturbación del SSCFLP con otra forma pasó, porque a una perturbación se le permite dejar infactible.

**Al trabajar con workspaces**

- Un workspace propio (`generated/v2/<p>`) usa su `model/model.hpp` (`generation_for`). Si se copia un catálogo sin su modelo, se compila contra el modelo por defecto.
- Lo que genera un workflow queda en una rama `llm-generated/...`: hay que fusionarla a la rama de trabajo antes de lanzar el paso siguiente (componentes después del modelo).

**Al comparar con referencias externas**

- JSPLIB tenía mal ta11, ta15, ta19 y ta20; las referencias del job shop salen de Weise (2020).
- CO-Bench lee mknap2 con la matriz de consumos transpuesta: sus 48 instancias no son las de la literatura. Las nuestras se leen por recurso y CBC reproduce los óptimos.
- Las cap41–cap134 de CO-Bench son del CFLP con demanda divisible y no tienen solución de fuente única; para el SSCFLP se usan las de OR-Brescia.
- FrontierCO mezcla convenciones en el CVRP: Golden y valid con distancias reales, Arnold con distancias redondeadas.
- Los test de CVRP de MCTS-AHD no son los de ReEvo (el generador corre sin el test20); los de MKP sí.
- El gap de MCTS-AHD es contra el mejor método de su columna: comparar el objetivo medio, no el gap.

## Pendientes y preguntas abiertas

Además de la secuencia de arriba, quedan estas tareas sueltas y decisiones que corresponden al investigador.

- [ ] Fijar el tiempo de evaluación contra MCTS-AHD y ReEvo, que no fijan tiempo sino iteraciones del ACO: ¿mismo tiempo por instancia que tardó su ACO, o nuestro protocolo por tamaño?
- [ ] Decidir si se afinan y evalúan las instancias grandes (TBED1 i1000 del SSCFLP y las Arnold de 6000–30000 clientes del CVRP): son otro régimen de tamaño y necesitarían su propio tuning.
- [ ] Completar las referencias de Díaz-Fernández en el SSCFLP: 38 de 57 sin óptimo; no hay tabla publicada (`python -m examples.sscflp.best_known --cbc D-`, varias llegan al límite de 10 min).
- [ ] Agregar `well_formed` al CVRP si se quiere cubrir también ahí el chequeo de forma (hoy no lo define).
- [ ] Revisar el test de optimización encadenada (`test_chained_passes_reoptimize_what_improved_and_show_the_profile`), que falla a veces cuando la máquina está cargada.
- [ ] Decidir si se re-ejecutan baselines con LLM (ReEvo, EoH) con el mismo modelo que el framework. Gastan tokens; la decisión por ahora es usar lo publicado.
- [ ] Decidir el rol de CLSP y del flow shop con flowtime en el paper (sin baseline LLM): ¿demostración de generalidad o fuera?

Para dudas sobre por qué algo es como es, el historial de decisiones y resultados está en `results/README.md` y en los mensajes de commit de la rama.
