"""Tuning automático sobre el espacio de configuración (§8).

`Assembler.config_space()` es el espacio y `Assembler.evaluate()` el *target
runner*; este paquete conecta ambos con un tuner real:

- `optuna_tuner.tune_with_optuna`: TPE define-by-run sobre el espacio
  condicional, con los defaults de cada esqueleto como puntos de partida.
- `evaluation.evaluate_on_test`: la configuración ganadora se mide en
  instancias que el tuner NO vio, contra los defaults de cada esqueleto.
- `irace_scenario.write_irace_scenario`: `parameters.txt`, `instances.txt`,
  `scenario.txt` y el target-runner para correr irace afuera (R).
"""

from .evaluation import TestReport, evaluate_on_test
from .optuna_tuner import TuningResult, tune_with_optuna

__all__ = ["TestReport", "TuningResult", "evaluate_on_test", "tune_with_optuna"]
