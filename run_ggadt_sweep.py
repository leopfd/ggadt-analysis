#!/usr/bin/env python3
"""Minimal GGADT runner for a few hand-picked examples.

This version is intentionally simple:
- no large CLI
- parameter files go to code/params (in repo)
- run outputs/logs go to ../ggadt_output
- grain/agglomerate files live in code/grains
"""

from __future__ import annotations

from bisect import bisect_left
from pathlib import Path
import subprocess
import sys


# --- edit these paths/values as needed ---
BASE_DIR = Path(__file__).resolve().parent
GGADT_BINARY = Path("~/bin/ggadt").expanduser()
MATERIAL_DIR = Path("~/Documents/Dust/OK_edge/a-MgFeSiO4").expanduser()
EPHOT_KEV = 0.53

# Grain geometry files live in code/grains
GRAIN_DIR = BASE_DIR / "grains"
AGGLOM_FILES = {
    "compact": GRAIN_DIR / "BA.256.1.targ",
    "medium": GRAIN_DIR / "BAM1.256.1.targ",
    "fluffy": GRAIN_DIR / "BAM2.256.1.targ",
}

# Keep this list short and explicit.
EXAMPLES = [
    {"name": "sphere_a0p10", "geometry": "sphere", "aeff": 0.10},
    {"name": "sphere_a0p20", "geometry": "sphere", "aeff": 0.20},
    {
        "name": "ellipsoid_112_a0p10",
        "geometry": "ellipsoid",
        "aeff": 0.10,
        "axes": (1.0, 1.0, 2.0),
    },
    {
        "name": "agglomerate_compact_a0p10",
        "geometry": "spheres",
        "aeff": 0.10,
        "porosity": "compact",
    },
    {
        "name": "agglomerate_fluffy_a0p10",
        "geometry": "spheres",
        "aeff": 0.10,
        "porosity": "fluffy",
    },
]

# Common GGADT settings for these quick examples.
NGRAIN = 128
NORIENTATIONS = 32
DTHETA_ARCSEC = 25.0
MAX_ANGLE_ARCSEC = 6000.0

# Keep run outputs/logs out of the repo.
OUTPUT_DIR = BASE_DIR.parent / "ggadt_output" / "quick_examples"
PARAM_DIR = BASE_DIR / "params" / "quick_examples"
RESULT_DIR = OUTPUT_DIR / "results"
LOG_DIR = OUTPUT_DIR / "logs"


def load_two_col(path: Path) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            a, b = line.split()[:2]
            xs.append(float(a))
            ys.append(float(b))
    pairs = sorted(zip(xs, ys), key=lambda t: t[0])
    return [p[0] for p in pairs], [p[1] for p in pairs]


def interp(x: list[float], y: list[float], target: float) -> float:
    if target < x[0] or target > x[-1]:
        raise ValueError(f"Energy {target} eV outside [{x[0]}, {x[-1]}] eV")
    i = bisect_left(x, target)
    if i < len(x) and x[i] == target:
        return y[i]
    x0, x1 = x[i - 1], x[i]
    y0, y1 = y[i - 1], y[i]
    return y0 + (target - x0) * (y1 - y0) / (x1 - x0)


def build_param_text(example: dict, ior_re: float, ior_im: float) -> str:
    axes = example.get("axes", (1.0, 1.0, 1.0))
    agglom_file = ""
    if example["geometry"] == "spheres":
        agglom_file = str(AGGLOM_FILES[example["porosity"]].resolve())

    return f"""# Auto-generated simple example
grain-geometry                 = '{example['geometry']}'
verbose                        = F
use-efficiencies               = T
integrated                     = F
do-full-2d-fft                 = F

# shape / size
aeff                           = {example['aeff']}
ngrain                         = {NGRAIN}
grain-axis-x                   = {axes[0]}
grain-axis-y                   = {axes[1]}
grain-axis-z                   = {axes[2]}
agglom-file                    = '{agglom_file}'

# optical constants (from n/k at one energy)
ephot                          = {EPHOT_KEV}
ior-re                         = {ior_re:.9g}
ior-im                         = {ior_im:.9g}

# angular sampling
dtheta                         = {DTHETA_ARCSEC}
max-angle                      = {MAX_ANGLE_ARCSEC}
angle-mode                     = 'random'
norientations                  = {NORIENTATIONS}
"""


def ensure_inputs() -> None:
    if not GGADT_BINARY.exists():
        raise FileNotFoundError(f"GGADT binary not found: {GGADT_BINARY}")

    n_file = MATERIAL_DIR / "n_after_kkcalc.txt"
    k_file = MATERIAL_DIR / "k_after_kkcalc.txt"
    if not n_file.exists() or not k_file.exists():
        raise FileNotFoundError(
            f"Missing n/k files in {MATERIAL_DIR}. Need n_after_kkcalc.txt and k_after_kkcalc.txt"
        )

    needed = {e.get("porosity") for e in EXAMPLES if e["geometry"] == "spheres"}
    for porosity in sorted(p for p in needed if p):
        targ = AGGLOM_FILES[porosity]
        if not targ.exists():
            raise FileNotFoundError(
                f"Missing {targ}. Put BA/BAM1/BAM2 .targ files in {GRAIN_DIR}"
            )


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    try:
        ensure_inputs()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    n_file = MATERIAL_DIR / "n_after_kkcalc.txt"
    k_file = MATERIAL_DIR / "k_after_kkcalc.txt"
    n_e, n_v = load_two_col(n_file)
    k_e, k_v = load_two_col(k_file)

    e_ev = EPHOT_KEV * 1000.0
    n = interp(n_e, n_v, e_ev)
    k = interp(k_e, k_v, e_ev)
    ior_re = n - 1.0
    ior_im = k

    print(f"Material: a-MgFeSiO4 @ {EPHOT_KEV} keV -> n={n:.7g}, k={k:.7g}")

    PARAM_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for i, example in enumerate(EXAMPLES, start=1):
        run_id = f"{i:02d}_{example['name']}"
        param_path = PARAM_DIR / f"{run_id}.ini"
        out_path = RESULT_DIR / f"{run_id}.dat"
        log_path = LOG_DIR / f"{run_id}.log"

        param_path.write_text(build_param_text(example, ior_re, ior_im), encoding="utf-8")

        if dry_run:
            print(f"DRY-RUN {run_id}")
            continue

        with out_path.open("w", encoding="utf-8") as out_f, log_path.open("w", encoding="utf-8") as log_f:
            rc = subprocess.run(
                [str(GGADT_BINARY), f"--parameter-file={param_path}"],
                stdout=out_f,
                stderr=log_f,
                check=False,
            ).returncode

        if rc == 0:
            print(f"OK      {run_id}")
        else:
            print(f"FAILED  {run_id} (see {log_path})", file=sys.stderr)
            return rc

    print("Done.")
    print(f"  Params:  {PARAM_DIR}")
    print(f"  Results: {RESULT_DIR}")
    print(f"  Logs:    {LOG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
