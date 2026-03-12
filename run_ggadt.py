#!/usr/bin/env python3
"""Run GGADT batches from parameter folders.

Loads `.ini` scenarios from `params/<name>/`, optionally builds a material
table from n/k data, and writes results/logs to `../ggadt_output/<name>/`.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left
import os
from pathlib import Path
import shutil
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
PARAMS_ROOT = BASE_DIR / "params"
OUTPUT_ROOT = BASE_DIR.parent / "ggadt_output"
DEFAULT_GGADT_BINARY = Path("~/bin/ggadt").expanduser()


def _display_path(path: Path) -> str:
    try:
        return os.path.relpath(path.resolve(), start=Path.cwd().resolve())
    except Exception:
        return str(path)


def _collect_input_files(raw_paths: list[str], directory_glob: str) -> list[Path]:
    files: list[Path] = []
    for raw in raw_paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            files.extend(sorted(p for p in path.glob(directory_glob) if p.is_file()))
            continue
        if path.is_file():
            files.append(path)
            continue
        raise FileNotFoundError(f"Path not found: {path}")

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)

    if not unique:
        raise FileNotFoundError("No input parameter files found")
    return unique


def _resolve_child_dir(base: Path, child: str, label: str) -> Path:
    value = child.strip()
    if not value:
        raise ValueError(f"{label} cannot be empty")

    candidate = Path(value)
    if candidate.is_absolute() or len(candidate.parts) != 1 or value in {".", ".."}:
        raise ValueError(
            f"{label} must be a child folder name (example: my_examples)"
        )

    return (base / candidate).resolve()


def _parse_param_file(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key_raw, value_raw = line.split("=", 1)
            key = key_raw.strip().lower()
            value = value_raw.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            parsed[key] = value
    return parsed


def _resolve_param_value_path(raw_value: str, param_path: Path) -> Path:
    p = Path(raw_value).expanduser()
    if p.is_absolute():
        return p
    return (param_path.parent / p).resolve()


def _validate_param_material_settings(
    param_path: Path,
    material_override: Path | None,
) -> None:
    parsed = _parse_param_file(param_path)
    material_file = parsed.get("material-file", "").strip()
    has_fixed_ior = ("ior-re" in parsed) and ("ior-im" in parsed)
    has_multi_material = any(parsed.get(f"material-file{i}", "").strip() for i in (1, 2, 3))

    if material_override is not None:
        if material_file:
            print(
                f"NOTE: {param_path.name} has material-file set; "
                f"overriding with {_display_path(material_override)}"
            )
        return

    if material_file:
        resolved = _resolve_param_value_path(material_file, param_path)
        if not resolved.exists():
            raise FileNotFoundError(
                f"{param_path.name}: material-file does not exist: {resolved}"
            )
        return

    if has_fixed_ior or has_multi_material:
        print(f"NOTE: {param_path.name} uses optical constants defined in the parameter file.")
        return

    raise ValueError(
        f"{param_path.name}: no material-file, no ior-re/ior-im, and no material-file1..3."
    )


def _load_two_col(path: Path) -> tuple[list[float], list[float]]:
    pairs: list[tuple[float, float]] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                e = float(parts[0])
                v = float(parts[1])
            except ValueError:
                continue
            pairs.append((e, v))

    if not pairs:
        raise ValueError(f"No numeric two-column rows found in {path}")

    pairs.sort(key=lambda t: t[0])

    # Deduplicate repeated energies by keeping the last encountered value.
    dedup: dict[float, float] = {}
    for e, v in pairs:
        dedup[e] = v

    xs = sorted(dedup.keys())
    ys = [dedup[e] for e in xs]
    return xs, ys


def _interp(x: list[float], y: list[float], target: float) -> float:
    if target < x[0] or target > x[-1]:
        raise ValueError(f"Energy {target} eV outside [{x[0]}, {x[-1]}] eV")
    i = bisect_left(x, target)
    if i < len(x) and x[i] == target:
        return y[i]
    x0, x1 = x[i - 1], x[i]
    y0, y1 = y[i - 1], y[i]
    return y0 + (target - x0) * (y1 - y0) / (x1 - x0)


def _normalize_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _auto_material_roots() -> list[Path]:
    roots: list[Path] = []

    # Prefer roots near the repo path (works across different parent folder names).
    for parent in [BASE_DIR, *BASE_DIR.parents]:
        roots.append(parent / "OK_edge")

    # Common location under Documents without hardcoding a username-specific absolute path.
    docs = Path.home() / "Documents"
    roots.append(docs / "MIT" / "Dust" / "OK_edge")
    roots.append(docs / "Dust" / "OK_edge")

    return roots


def _candidate_material_roots(cli_roots: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in cli_roots:
        if raw.strip():
            roots.append(Path(raw).expanduser())

    for env_var in ("GGADT_MATERIALS_ROOT", "GGADT_MATERIAL_ROOT"):
        raw = os.environ.get(env_var, "").strip()
        if not raw:
            continue
        for item in raw.split(os.pathsep):
            if item.strip():
                roots.append(Path(item).expanduser())

    roots.extend(_auto_material_roots())

    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _resolve_material_dir(material_arg: str, material_roots: list[Path]) -> Path:
    raw = material_arg.strip()
    if not raw:
        raise ValueError("Empty --material value")

    direct = Path(raw).expanduser()
    if direct.is_dir():
        return direct.resolve()
    if direct.exists() and not direct.is_dir():
        raise ValueError(f"--material points to a file, expected directory: {direct}")

    # If user passed an explicit path-like value and it does not exist, fail early.
    if any(ch in raw for ch in ("/", "\\")):
        raise FileNotFoundError(f"Material directory not found: {direct}")

    variants = {raw, raw.replace("-", "_"), raw.replace("_", "-")}
    norm_target = _normalize_name(raw)

    tried: list[Path] = []
    for root in material_roots:
        if not root.exists():
            continue
        for variant in variants:
            cand = root / variant
            tried.append(cand)
            if cand.is_dir():
                return cand.resolve()

        # Fallback: normalized-name match for minor formatting differences.
        for child in root.iterdir():
            if not child.is_dir():
                continue
            if _normalize_name(child.name) == norm_target:
                return child.resolve()

    tried_text = "\n".join(f"  - {p}" for p in tried) if tried else "  (no existing roots)"
    roots_text = "\n".join(f"  - {r}" for r in material_roots)
    raise FileNotFoundError(
        "Could not find material directory for "
        f"'{raw}'.\nSearched roots:\n{roots_text}\nTried:\n{tried_text}\n"
        "Use --material with an absolute path or --material-root to add a search root."
    )


def _material_out_default(material_name: str, output_dir: Path) -> Path:
    slug = "".join(ch if ch.isalnum() else "_" for ch in material_name).strip("_")
    if not slug:
        slug = "material"
    return output_dir / f"{slug}_material.dat"


def _write_material_file_from_nk(
    material_dir: Path,
    output_path: Path,
    e_min_ev: float | None,
    e_max_ev: float | None,
) -> tuple[float, float, int, float, float, float, float]:
    n_file = material_dir / "n_after_kkcalc.txt"
    k_file = material_dir / "k_after_kkcalc.txt"
    if not n_file.exists() or not k_file.exists():
        raise FileNotFoundError(
            f"Missing n/k files in {material_dir}. Need n_after_kkcalc.txt and k_after_kkcalc.txt"
        )

    n_e, n_v = _load_two_col(n_file)
    k_e, k_v = _load_two_col(k_file)

    overlap_min = max(n_e[0], k_e[0])
    overlap_max = min(n_e[-1], k_e[-1])
    if overlap_min >= overlap_max:
        raise ValueError(
            f"n/k files have no overlapping energy range: n=[{n_e[0]}, {n_e[-1]}], "
            f"k=[{k_e[0]}, {k_e[-1]}] eV"
        )

    req_min = overlap_min if e_min_ev is None else e_min_ev
    req_max = overlap_max if e_max_ev is None else e_max_ev
    if req_min > req_max:
        raise ValueError(f"Invalid energy range: min {req_min} eV > max {req_max} eV")

    run_min = max(req_min, overlap_min)
    run_max = min(req_max, overlap_max)
    if run_min >= run_max:
        raise ValueError(
            f"Requested range [{req_min}, {req_max}] eV does not overlap available "
            f"n/k range [{overlap_min}, {overlap_max}] eV"
        )

    if run_min != req_min or run_max != req_max:
        print(
            "WARNING: requested sweep "
            f"[{req_min}, {req_max}] eV exceeds available n/k range "
            f"[{overlap_min}, {overlap_max}] eV; using [{run_min}, {run_max}] eV"
        )

    energies = sorted(
        set(
            [run_min, run_max]
            + [e for e in n_e if run_min <= e <= run_max]
            + [e for e in k_e if run_min <= e <= run_max]
        )
    )
    if len(energies) < 2:
        raise ValueError("Not enough energy points in selected overlap interval")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("17 =ICOMP: auto-generated from n_after_kkcalc.txt and k_after_kkcalc.txt\n")
        f.write("    E(eV)      Re(n)-1    Im(n)    Re(eps)-1  Im(eps)\n")
        for e in energies:
            n = _interp(n_e, n_v, e)
            k = _interp(k_e, k_v, e)
            re_n_minus_1 = n - 1.0
            im_n = k
            re_eps_minus_1 = (n * n - k * k) - 1.0
            im_eps = 2.0 * n * k
            f.write(
                f" {e: .6E} {re_n_minus_1: .6E} {im_n: .6E} "
                f"{re_eps_minus_1: .6E} {im_eps: .6E}\n"
            )

    n_min = _interp(n_e, n_v, run_min)
    k_min = _interp(k_e, k_v, run_min)
    n_max = _interp(n_e, n_v, run_max)
    k_max = _interp(k_e, k_v, run_max)
    return run_min, run_max, len(energies), n_min, k_min, n_max, k_max


def _resolve_ggadt_binary(raw: str, dry_run: bool) -> str:
    text = raw.strip()
    if not text:
        raise ValueError("Empty --ggadt-binary value")

    path_candidate = Path(text).expanduser()
    if path_candidate.exists():
        if not path_candidate.is_file():
            raise FileNotFoundError(f"GGADT binary path is not a file: {path_candidate}")
        return str(path_candidate.resolve())

    from_path = shutil.which(text)
    if from_path:
        return from_path

    if dry_run:
        # In dry-run mode, allow a non-existing command path to pass validation.
        if any(ch in text for ch in ("/", "\\")):
            return str(path_candidate.resolve())
        return text

    raise FileNotFoundError(
        f"GGADT binary not found: {text}. Provide --ggadt-binary /absolute/path/to/ggadt."
    )


def _run_one(
    ggadt_binary: str,
    param_path: Path,
    out_path: Path,
    log_path: Path,
    material_override: Path | None,
    dry_run: bool,
) -> int:
    cmd = [ggadt_binary, f"--parameter-file={param_path}"]
    if material_override is not None:
        cmd.append(f"--material-file={material_override}")

    if dry_run:
        print(f"DRY-RUN {param_path.stem}")
        print(f"  param: {_display_path(param_path)}")
        print(f"  out:   {_display_path(out_path)}")
        print(f"  log:   {_display_path(log_path)}")
        if material_override is not None:
            print(f"  using material-file override: {_display_path(material_override)}")
        return 0

    with out_path.open("w", encoding="utf-8") as out_f, log_path.open(
        "w", encoding="utf-8"
    ) as log_f:
        return subprocess.run(cmd, stdout=out_f, stderr=log_f, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run GGADT for all .ini files in params/<name> with outputs in ggadt_output/<name>."
    )
    parser.add_argument(
        "name",
        help="Shared child folder name for params/<name> and ../ggadt_output/<name>.",
    )
    parser.add_argument(
        "--ggadt-binary",
        default=str(DEFAULT_GGADT_BINARY),
        help="Path to ggadt executable.",
    )
    parser.add_argument(
        "--material",
        default="",
        help=(
            "Material directory path or material name to find under material roots. "
            "If set, generates a material table and overrides material-file at runtime."
        ),
    )
    parser.add_argument(
        "--material-root",
        action="append",
        default=[],
        help=(
            "Additional root directory to search for --material names. "
            "Can be repeated."
        ),
    )
    parser.add_argument(
        "--e-min-ev",
        type=float,
        default=None,
        help="Optional minimum energy for generated material table (eV).",
    )
    parser.add_argument(
        "--e-max-ev",
        type=float,
        default=None,
        help="Optional maximum energy for generated material table (eV).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print planned runs without executing ggadt.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        params_dir = _resolve_child_dir(PARAMS_ROOT, args.name, "name")
        output_dir = _resolve_child_dir(OUTPUT_ROOT, args.name, "name")
        results_dir = output_dir / "results"
        logs_dir = output_dir / "logs"

        param_files = _collect_input_files([str(params_dir)], "*.ini")
        ggadt_binary = _resolve_ggadt_binary(args.ggadt_binary, dry_run=args.dry_run)
        if not args.dry_run:
            results_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)

        material_override: Path | None = None
        if args.material.strip():
            roots = _candidate_material_roots(args.material_root)
            material_dir = _resolve_material_dir(args.material.strip(), roots)
            material_out = _material_out_default(material_dir.name, output_dir).resolve()

            (
                run_min,
                run_max,
                n_rows,
                n_min,
                k_min,
                n_max,
                k_max,
            ) = _write_material_file_from_nk(
                material_dir=material_dir,
                output_path=material_out,
                e_min_ev=args.e_min_ev,
                e_max_ev=args.e_max_ev,
            )
            material_override = material_out
            print(
                f"Material: {material_dir.name} sweep {run_min:.1f}-{run_max:.1f} eV "
                f"({run_min/1000.0:.3f}-{run_max/1000.0:.3f} keV)"
            )
            print(f"  using n/k files from: {_display_path(material_dir)}")
            print(f"  n,k @ {run_min:.1f} eV -> n={n_min:.6g}, k={k_min:.6g}")
            print(f"  n,k @ {run_max:.1f} eV -> n={n_max:.6g}, k={k_max:.6g}")
            print(f"  points: {n_rows}")
            print(f"Material file written: {_display_path(material_out)}")

        for param_path in param_files:
            _validate_param_material_settings(param_path, material_override)

        failures: list[tuple[Path, int, Path]] = []
        for param_path in param_files:
            run_name = param_path.stem
            out_path = results_dir / f"{run_name}.dat"
            log_path = logs_dir / f"{run_name}.log"
            rc = _run_one(
                ggadt_binary=ggadt_binary,
                param_path=param_path,
                out_path=out_path,
                log_path=log_path,
                material_override=material_override,
                dry_run=args.dry_run,
            )
            if rc == 0:
                if not args.dry_run:
                    print(f"OK      {run_name}")
            else:
                failures.append((param_path, rc, log_path))
                if not args.dry_run:
                    print(
                        f"FAILED  {run_name} (see {_display_path(log_path)})",
                        file=sys.stderr,
                    )
                    break

        print("Done.")
        print(f"  Params:  {len(param_files)} file(s)")
        print(f"  Results: {_display_path(results_dir)}")
        print(f"  Logs:    {_display_path(logs_dir)}")

        if failures:
            return failures[0][1]
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
