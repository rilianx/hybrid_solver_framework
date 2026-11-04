"""Configuración automática sobre el espacio de configuración (§8).

`Assembler.config_space()` es el espacio y `Assembler.evaluate()` el *target runner*; este paquete conecta ambos
con un tuner real:

- `irace_runner.tune_with_irace` e `irace_scenario.write_irace_scenario`: irace (R) con el target-runner del
  framework (`scripts/irace_target_runner.py`).
- `staged.run_staged`: primero la estructura (esqueleto y componentes), después irace en el espacio reducido.
- `evaluation.evaluate_on_test`: la configuración ganadora se mide en instancias que el tuner NO vio, contra los
  defaults de cada esqueleto.
"""

from .evaluation import TestReport, best_known_costs, evaluate_on_test, one_slot_baselines, paired_comparison

__all__ = ["TestReport", "best_known_costs", "evaluate_on_test", "one_slot_baselines", "paired_comparison"]
