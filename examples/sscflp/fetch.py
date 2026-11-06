"""Descarga y convierte los benchmarks del SSCFLP a `examples/sscflp/bench/` (formato de `SSCFLPInstance.to_text`).

    python -m examples.sscflp.fetch            # los conjuntos chicos (los que están en el repositorio)
    python -m examples.sscflp.fetch --large    # además TBED1 i1000 (1000×1000, 240 MB; no van al repositorio)

| prefijo | conjunto | instancias | tamaño (centros×clientes) | fuente |
|---|---|---|---|---|
| `H-` | Holmberg et al. (1999), p1–p71 | 71 | 10×50 a 30×200 | MOrepo-Gadegaard16 (primer objetivo) |
| `D-` | Díaz y Fernández (2002), TB1 | 57 | 10×20 a 30×90 | MOrepo-Gadegaard16 (primer objetivo) |
| `Y-` | Yang et al. (2012), TB3 | 20 | 30×200 a 80×400 | SSCFLPsolver (Gadegaard) |
| `TB4-` | Gadegaard et al. (2018), TB4 | 45 | 50×100 a 60×300 | SSCFLPsolver (Gadegaard) |
| `i1000_` | Avella y Boccia (2009), TBED1 i1000 (`--large`) | 20 | 1000×1000 | FrontierCO (HuggingFace) |

Holmberg y Díaz-Fernández vienen de los archivos biobjetivo de MOrepo (Gadegaard 2016): los datos del SSCFLP original
(capacidades, costos fijos, demandas y la primera matriz de costos) seguidos de una segunda matriz que se descarta.
Las i1000 de TBED1 son las "easy" del CFLP de FrontierCO (ICLR 2026), donde se evalúan con demanda divisible; aquí son
de fuente única, como en la literatura del SSCFLP. Las cap41–cap134 y capa–capc de la OR-Library (las del "Capacitated
warehouse location" de CO-Bench) no están: tienen clientes con más demanda que la capacidad de cualquier centro (en
cap41, 12912 contra 5000), así que solo son factibles con demanda divisible (CFLP). Las mejores conocidas están en
`bench/best_known.json` (`examples/sscflp/best_known.py`).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .instance import SSCFLPInstance

BENCH = Path(__file__).with_name("bench")
MOREPO = "https://github.com/MCDMSociety/MOrepo-Gadegaard16.git"
SSCFLPSOLVER = "https://github.com/SuneGadegaard/SSCFLPsolver.git"
HF = "https://huggingface.co/datasets/CO-Bench"


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as r:
        return r.read()


def _clone(url: str, into: Path) -> Path:
    subprocess.run(["git", "clone", "-q", "--depth", "1", url, str(into)], check=True)
    return into


def _write(name: str, inst: SSCFLPInstance) -> None:
    inst.save(str(BENCH / f"{name}.txt"))


def fetch_morepo(tmp: Path) -> None:
    d = _clone(MOREPO, tmp / "morepo") / "instances" / "raw" / "SSCFLP"
    for f in sorted(d.glob("Gadegaard16_SSCFLP_*_0.raw")):
        origin, num = re.match(r"Gadegaard16_SSCFLP_(\w+?)_p(\d+)_0\.raw", f.name).groups()
        name = f"H-p{int(num)}" if origin == "Holmberg" else f"D-p{int(num):02d}"
        _write(name, SSCFLPInstance.parse(f.read_text()))


def fetch_gadegaard(tmp: Path) -> None:
    repo = _clone(SSCFLPSOLVER, tmp / "sscflpsolver")
    with zipfile.ZipFile(repo / "All_instances_for_Imp_CnS.zip") as z:
        for info in z.infolist():
            p = info.filename
            if info.is_dir():
                continue
            if "Yang (TB3)/All/" in p:  # p1..p20: 30-200-1..5, 60-200-1..5, 60-300-1..5, 80-400-1..5
                k = int(Path(p).name[1:]) - 1
                size = ["30_200", "60_200", "60_300", "80_400"][k // 5]
                _write(f"Y-{size}_{k % 5 + 1}", SSCFLPInstance.parse(z.read(info).decode()))
            elif "(TB4)" in p and p.endswith(".dat"):
                # 50-100/50-100-2/50-100-1.dat -> TB4-50_100_2_1 (carpeta: razón capacidad/demanda; archivo: réplica)
                group, rep = Path(p).parent.name, Path(p).stem.rsplit("-", 1)[1]
                _write(f"TB4-{group.replace('-', '_')}_{rep}", SSCFLPInstance.parse(z.read(info).decode()))


def fetch_tbed1_i1000() -> None:
    base = f"{HF}/FrontierCO/resolve/main/CFLP/easy_test_instances"
    for k in range(1, 21):
        _write(f"i1000_{k}", SSCFLPInstance.parse(_get(f"{base}/i1000_{k}.plc").decode()))


def _check_yang_order() -> None:
    """Los p1..p20 de Yang vienen sin tamaño en el nombre: se verifica el orden supuesto con las dimensiones."""
    for f in BENCH.glob("Y-*.txt"):
        n, m = map(int, f.read_text().split()[:2])
        want = tuple(map(int, f.stem[2:].split("_")[:2]))
        assert (n, m) == want, f"{f.name}: {n}×{m}"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--large", action="store_true", help="también TBED1 i1000 (240 MB; no van al repositorio)")
    ap.add_argument("--only", nargs="*", default=None, help="conjuntos: holmberg_diaz gadegaard")
    args = ap.parse_args(argv)
    BENCH.mkdir(exist_ok=True)
    only = set(args.only or ["holmberg_diaz", "gadegaard"])
    with tempfile.TemporaryDirectory() as tmp:
        if "holmberg_diaz" in only:
            fetch_morepo(Path(tmp))
        if "gadegaard" in only:
            fetch_gadegaard(Path(tmp))
            _check_yang_order()
    if args.large:
        fetch_tbed1_i1000()
    print(f"{len(list(BENCH.glob('*.txt')))} instancias en {BENCH}")


if __name__ == "__main__":
    main()
