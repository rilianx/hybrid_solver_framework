"""Descarga y convierte los benchmarks del SSCFLP a `examples/sscflp/bench/` (formato de `SSCFLPInstance.to_text`).

    python -m examples.sscflp.fetch            # los conjuntos chicos (los que están en el repositorio)
    python -m examples.sscflp.fetch --large    # además capa–capc y TBED1 (unos 850 MB convertidos; fuera de git)

| prefijo | conjunto | instancias | centros×clientes | fuente |
|---|---|---|---|---|
| `H-` | Holmberg et al. (1999), p1–p71 | 71 | 10×50 a 30×200 | OR-Brescia |
| `D-` | Díaz y Fernández (2002), TB1 | 57 | 10×20 a 30×90 | MOrepo-Gadegaard16 |
| `Y-` | Yang et al. (2012), TB3 | 20 | 30×200 a 80×400 | OR-Brescia |
| `TB4-` | Gadegaard et al. (2018), TB4 | 45 | 50×100 a 60×300 | SSCFLPsolver (Gadegaard) |
| `cap` | OR-Library para el SSCFLP, cap61–cap134 | 24 | 16×50 a 50×50 | OR-Brescia |
| `capa`–`capc` | OR-Library para el SSCFLP (`--large`) | 12 | 100×1000 | OR-Brescia |
| `i300_` … `i1000_`, `i3001500_` | TBED1, Avella y Boccia (2009) (`--large`) | 100 | 300×300 a 1000×1000 y 300×1500 | OR-Brescia |

OR-Brescia (or-brescia.unibs.it/instances/instances_sscflp) es la colección de Guastaroba y Speranza (2014), con los
valores de las soluciones (`bench/refs/`); sus archivos están en Google Drive. Las cap de la OR-Library son las
versiones del SSCFLP de esa colección (las originales del CFLP, las de CO-Bench, tienen clientes con más demanda que la
capacidad de cualquier centro). Las i1000 de TBED1 son además las "easy" del CFLP de FrontierCO (ICLR 2026), donde se
evalúan con demanda divisible. Díaz-Fernández viene de los archivos biobjetivo de MOrepo (Gadegaard 2016): los datos del
SSCFLP original seguidos de una segunda matriz que se descarta. Las referencias: `bench/best_known.json`
(`examples/sscflp/best_known.py`).
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .instance import SSCFLPInstance

BENCH = Path(__file__).with_name("bench")
REFS = BENCH / "refs"
MOREPO = "https://github.com/MCDMSociety/MOrepo-Gadegaard16.git"
SSCFLPSOLVER = "https://github.com/SuneGadegaard/SSCFLPsolver.git"
# OR-Brescia en Google Drive: (id, resourcekey)
DRIVE = {
    "holmberg": ("0B6LVUFLjwlvdOU51cVVoSGE3d0k", "0-Ig2oWvThZBLhZosHbFPUNQ"),
    "yang": ("0B6LVUFLjwlvdUUhxaGduX0pHSDg", "0-5g0gLUl69bMr1rgVcOKM-A"),
    "orlib": ("0B6LVUFLjwlvdNnhtcC1aOHQ5Z0E", "0-S6lTc-C-9bv3DjYJx8q6sw"),
    "tbed1_300": ("0B6LVUFLjwlvdSl8yQnBRb05OLTA", "0-2cKtD_PkC_yDQWbzb89T7A"),
    "tbed1_300_1500": ("0B6LVUFLjwlvdZ2lRMFpCRVJocjA", "0-APGXm8J-nF6DFAJYV6-3Sw"),
    "tbed1_500": ("0B6LVUFLjwlvdbkc5T2dfendNREE", "0-zyLgYwiwbtnGMw_Zc6kIjQ"),
    "tbed1_700": ("0B6LVUFLjwlvddlJMdW84Rkg5SHc", "0-CswCJ2e1gc84wWTWuPZlwg"),
    "tbed1_1000": ("0B6LVUFLjwlvdN00yQUhfTDZGM1U", "0-EOYkHY5z2t2GbfAiJO0VPg"),
}
DRIVE_REFS = {
    "Holmberg_Solution_Values.txt": ("0B6LVUFLjwlvdVkI0VlhUellfbGc", "0-TuGsKsJAKWjyBBGLS08Dxw"),
    "Yang_Solution_Values.txt": ("0B6LVUFLjwlvdN3RDdW5qdzVSS28", "0-4vFFt9RnC1h7idZ7QBHgSw"),
    "OR-Library_Solution_Values.txt": ("0B6LVUFLjwlvdMDBQNlg3OUhreGc", "0-K3TCQtKHZQ8u157xWSjgHA"),
    "TBED1_Solution_Values.txt": ("0B6LVUFLjwlvdclZES1hkZXJvaEk", "0-BqVU7PauRjfPHR67FFBBaw"),
}


def _drive(file_id: str, key: str) -> bytes:
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t&resourcekey={key}"
    with urllib.request.urlopen(url, timeout=600) as r:
        data = r.read()
    assert not data.lstrip().startswith(b"<"), "Google Drive devolvió una página en lugar del archivo"
    return data


def _zip(name: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(_drive(*DRIVE[name])))


def _clone(url: str, into: Path) -> Path:
    subprocess.run(["git", "clone", "-q", "--depth", "1", url, str(into)], check=True)
    return into


def _write(name: str, inst: SSCFLPInstance) -> None:
    inst.save(str(BENCH / f"{name}.txt"))


def _files(z: zipfile.ZipFile):
    """(nombre, texto) de cada archivo del zip, sin directorios ni el Readme."""
    for info in z.infolist():
        name = Path(info.filename).name
        if not info.is_dir() and not name.lower().startswith(("readme", "reame")):
            yield name, z.read(info).decode("latin1")


def fetch_holmberg() -> None:
    for name, text in _files(_zip("holmberg")):
        if re.fullmatch(r"p\d+", name):
            _write(f"H-{name}", SSCFLPInstance.parse(text))


def fetch_yang() -> None:
    for name, text in _files(_zip("yang")):
        if name.endswith(".dat"):  # 30-200/30-200-1.dat -> Y-30_200_1
            _write("Y-" + Path(name).stem.replace("-", "_"), SSCFLPInstance.parse(text))


def fetch_orlib(large: bool) -> None:
    for name, text in _files(_zip("orlib")):
        if re.fullmatch(r"cap\d+", name) or (large and re.fullmatch(r"cap[abc]\d", name)):
            _write(name, SSCFLPInstance.parse(text))


def fetch_tbed1() -> None:
    for group in ("300", "300_1500", "500", "700", "1000"):
        for name, text in _files(_zip(f"tbed1_{group}")):
            if name.endswith(".plc"):  # i3001500-18.plc -> i3001500_18
                _write(Path(name).stem.replace("-", "_"), SSCFLPInstance.parse_tbed1(text))


def fetch_diaz(tmp: Path) -> None:
    d = _clone(MOREPO, tmp / "morepo") / "instances" / "raw" / "SSCFLP"
    for f in sorted(d.glob("Gadegaard16_SSCFLP_Diaz_p*_0.raw")):
        num = re.match(r"Gadegaard16_SSCFLP_Diaz_p(\d+)_0\.raw", f.name).group(1)
        _write(f"D-p{int(num):02d}", SSCFLPInstance.parse(f.read_text()))


def fetch_tb4(tmp: Path) -> None:
    repo = _clone(SSCFLPSOLVER, tmp / "sscflpsolver")
    with zipfile.ZipFile(repo / "All_instances_for_Imp_CnS.zip") as z:
        for info in z.infolist():
            p = info.filename
            if "(TB4)" in p and p.endswith(".dat"):
                # 50-100/50-100-2/50-100-1.dat -> TB4-50_100_2_1 (carpeta: razón capacidad/demanda; archivo: réplica)
                group, rep = Path(p).parent.name, Path(p).stem.rsplit("-", 1)[1]
                _write(f"TB4-{group.replace('-', '_')}_{rep}", SSCFLPInstance.parse(z.read(info).decode()))


def fetch_refs() -> None:
    REFS.mkdir(exist_ok=True)
    for name, (fid, key) in DRIVE_REFS.items():
        (REFS / name).write_text(_drive(fid, key).decode("latin1").replace("\r\n", "\n"))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--large", action="store_true", help="también capa–capc y TBED1 (fuera de git)")
    ap.add_argument("--only", nargs="*", default=None, help="conjuntos: holmberg yang orlib diaz tb4 refs tbed1")
    args = ap.parse_args(argv)
    BENCH.mkdir(exist_ok=True)
    only = set(args.only or ["holmberg", "yang", "orlib", "diaz", "tb4", "refs"] + (["tbed1"] if args.large else []))
    steps = {"holmberg": fetch_holmberg, "yang": fetch_yang, "orlib": lambda: fetch_orlib(args.large),
             "refs": fetch_refs, "tbed1": fetch_tbed1}
    for name, fn in steps.items():
        if name in only:
            fn()
    with tempfile.TemporaryDirectory() as tmp:
        if "diaz" in only:
            fetch_diaz(Path(tmp))
        if "tb4" in only:
            fetch_tb4(Path(tmp))
    print(f"{len(list(BENCH.glob('*.txt')))} instancias en {BENCH}")


if __name__ == "__main__":
    main()
