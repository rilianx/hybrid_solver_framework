# Notas: resultados publicados LLM-AHD (ReEvo, MCTS-AHD, HSEvo, EoH)

PDFs (versión más reciente de arXiv) y texto extraído en `pdfs/`. Clones de solo lectura de los repos MCTS-AHD, HSEvo y ReEvo en `code/` (no ejecuté nada de esos repos). El script `scripts/compare_sets.py` es mío: reimplementa el generador documentado y compara contra los .npy/.npz que MCTS-AHD tiene commiteados.

## Qué quedó verificado
- **MKP (MCTS-AHD):** los test100/200/300/500/1000 commiteados en el repo de MCTS-AHD son idénticos a los que produce el generador de ReEvo (semilla 4567, 64 instancias, m=5). Por lo tanto, el MKP100/MKP200 de la Tabla 2 de MCTS-AHD es el mismo set que el de ReEvo.
- **CVRP (MCTS-AHD): no es el mismo set.** El gen_inst.py de MCTS-AHD usa la semilla 1234, pero genera solo test50 y test100 (ReEvo genera test20, test50 y test100). Esto desplaza el stream del RNG. Los test50.npy y test100.npy commiteados coinciden con el orden de MCTS-AHD y **no** con los de ReEvo. El test20.npy commiteado sí es el de ReEvo, pero la Tabla 2 no lo usa. train50 y val20/50/100 son idénticos.
- **HSEvo:** su `cvrp_aco/gen_inst.py` y su `mkp_aco/gen_inst.py` son byte a byte iguales a los de ReEvo. Si se generaran, darían los mismos sets que ReEvo. Pero HSEvo **no publica** resultados de CVRP ni de MKP; solo de BPO, TSP-GLS y OP-ACO.

## Lo que no pude confirmar
- **Gap de la Tabla 2 de MCTS-AHD:** el paper no define la referencia. Por los números, es relativa al mejor método de cada columna (0.00% para DeepACO o MCTS-AHD). No es un gap contra HGS, LKH ni el óptimo.
- **Iteraciones de test de MKP en MCTS-AHD:** el paper dice 100, pero `eval-test.py` del repo usa 50 (y recorre los tamaños 100/300/500, no 100/200). No sé cuál se usó.
- **ReEvo Tabla 3 (CVRP200/500/1000 con POMO/LEHD):** ReEvo solo dice "test instances provided by LEHD". Que sean 128 instancias por tamaño y que la referencia del gap sea HGS lo sé por el paper de LEHD, no por ReEvo.
- **ReEvo, CVRP y MKP con ACO:** solo hay curvas (Fig. 2 y Fig. 4), no hay valores numéricos en tablas. Los números habría que sacarlos del repo o README de ReEvo, que no revisé.
- **Presupuesto de EoH en FSSP:** EoH da 20 generaciones × población 10, pero no da el número de evaluaciones. Las "810 evaluaciones" las calcula MCTS-AHD (App. D). EoH reporta una sola corrida.
- **Referencia del gap en EoH FSSP:** el caption de la Tabla 12 dice "best-known", el texto dice "upper bounds de Taillard (1993)" y el caption de la Tabla 3 dice "relative makespan to the baseline". El -0.04 en 100x5 sugiere una UB antigua. Además, la columna "PFSPNet" de la Tabla 12 coincide con "PFSPNet NEH" de la Tabla 3, así que probablemente es PFSPNet_NEH.
- **Presupuesto de HSEvo:** la Tabla 1 dice 425K tokens y el Apéndice B dice 450K tokens. Es una inconsistencia interna del paper.
- **ReEvo re-ejecutado en MCTS-AHD:** la Tabla 2 de MCTS-AHD usa GPT-4o-mini y, presumiblemente, T=1000 evaluaciones también para EoH y ReEvo. El paper dice "for almost all tasks... T=1,000" y que siguen los parámetros de cada baseline. No es la configuración original de ReEvo (GPT-3.5-turbo, 100 evaluaciones).
- No hay resultados de job shop ni de facility location en ninguno de los cuatro papers.
- Transcripción: los valores salen de `pdftotext -layout`. Las tablas revisadas no tienen celdas partidas y verifiqué la consistencia gap↔obj en la Tabla 2 de MCTS-AHD. No revisé visualmente el PDF renderizado.
