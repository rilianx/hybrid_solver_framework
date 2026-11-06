"""Descarga el benchmark del job shop a `examples/jobshop/bench/` (formato de `JSSPInstance.to_text`) con sus referencias.

    python -m examples.jobshop.fetch

| instancias | n×m | origen |
|---|---|---|
| ta01–ta80 (Taillard 1993) | 15×15 a 100×20 | las del job shop de CO-Bench |
| abz5–9, ft06/10/20, la01–40, orb01–10, swv01–20, yn1–4 | 6×6 a 50×20 | OR-Library |

Instancias: JSPLIB (github.com/tamy0612/JSPLIB). Referencias (`bench/best_known.json`, por instancia `ub` = mejor
conocida, `lb` = mejor cota inferior, `opt` = ub probado óptimo): Weise, jsspInstancesAndResults
(github.com/thomasWeise/jsspInstancesAndResults, `instances_with_bks.txt`, 2020), que recopila las de la literatura.
"""

from __future__ import annotations

import csv
import json
import subprocess
import tempfile
from pathlib import Path

from .instance import JSSPInstance

BENCH = Path(__file__).with_name("bench")
JSPLIB = "https://github.com/tamy0612/JSPLIB.git"
WEISE = "https://github.com/thomasWeise/jsspInstancesAndResults.git"


def _clone(url: str, into: Path) -> Path:
    subprocess.run(["git", "clone", "-q", "--depth", "1", url, str(into)], check=True)
    return into


def main() -> None:
    BENCH.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        jsplib = _clone(JSPLIB, Path(tmp) / "jsplib")
        names = []
        for entry in json.loads((jsplib / "instances.json").read_text()):
            text = "\n".join(ln for ln in (jsplib / entry["path"]).read_text().splitlines() if not ln.startswith("#"))
            JSSPInstance.parse(text).save(str(BENCH / f"{entry['name']}.txt"))
            names.append(entry["name"])
        weise = _clone(WEISE, Path(tmp) / "weise")
        rows = csv.DictReader((weise / "data-raw" / "instances" / "instances_with_bks.txt").open())
        refs = {}
        for r in rows:
            if r["inst.id"] in names:
                lb, ub = float(r["inst.opt.bound.lower"]), float(r["inst.bks"])
                refs[r["inst.id"]] = {"ub": ub, "lb": lb, "opt": lb == ub,
                                      "source": f"Weise (2020): lb {r['inst.opt.bound.lower.ref']}, ub {r['inst.bks.ref']}"}
    missing = sorted(set(names) - set(refs))
    assert not missing, missing
    data = {"_fuente": "Weise, jsspInstancesAndResults (2020, instances_with_bks.txt): ub = mejor conocida, lb = mejor cota "
                       "inferior, opt = ub probado óptimo. Instancias de JSPLIB."}
    data.update({k: refs[k] for k in sorted(refs, key=lambda k: (k.rstrip("0123456789"), int("0" + k[len(k.rstrip("0123456789")):])))})
    (BENCH / "best_known.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(names)} instancias en {BENCH}")


if __name__ == "__main__":
    main()
