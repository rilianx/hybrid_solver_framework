"""irace como tuner (`tuning.cli --tuner irace`): lectura de la élite y una corrida corta en C++ si hay R
con el paquete irace."""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from tuning.irace_runner import parse_elites

OUT = """
# Best configurations (first number is the configuration ID; listed from best to worst according to the sum of ranks):
   skeleton constructor
12 ILS greedy_x
# Best configurations as commandlines (first number is the configuration ID; listed from best to worst according to the sum of ranks):
12  --skeleton=ILS --constructor=greedy_x --ILS.strength=3 --ILS.ls_strategy="first"
7   --skeleton=SA --SA.T0=12.5
"""


def test_the_elite_is_read_from_the_irace_output_in_order():
    assert parse_elites(OUT) == [["--skeleton=ILS", "--constructor=greedy_x", "--ILS.strength=3", '--ILS.ls_strategy="first"'],
                                 ["--skeleton=SA", "--SA.T0=12.5"]]


def _has_irace() -> bool:
    if shutil.which("Rscript") is None or shutil.which("g++") is None:
        return False
    return subprocess.run(["Rscript", "-e", "library(irace)"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _has_irace(), reason="sin R/irace o sin g++")
def test_irace_tunes_natively_and_the_choice_is_evaluated_in_test(tmp_path):
    import os

    from examples.jobshop.tune import main

    out = os.path.relpath(tmp_path)  # --out relativo a la raíz del repo, como en CI (corrida 51)
    main(["--tuner", "irace", "--native", "--catalog", "handwritten", "--size", "6x4", "--trials", "60", "--budget", "0.02",
          "--train", "5", "--test", "1", "--seeds", "1", "--skeletons", "SA", "ILS", "--out", out])
    out = json.loads((tmp_path / "handwritten.json").read_text())
    assert out["settings"]["tuner"] == "irace" and out["tuning"]["tuner"] == "irace"
    assert out["tuning"]["n_trials"] >= 300 and out["test"]["tuned"]["summary"].split("[")[0] in ("SA", "ILS")
