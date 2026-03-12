#!/usr/bin/env python3
"""Visualization utilities for GGADT outputs and grain geometry."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import sys

import numpy as np


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = BASE_DIR.parent / "ggadt_output"
PARAMS_ROOT = BASE_DIR / "params"
GRAINS_ROOT = BASE_DIR / "grains"
DEFAULT_CHILD = "a_MgFeSiO4_examples"
PLOT_DPI = 400

# Explicit contribution-line colors for integrated outputs.
LINE_COLORS = {
    "Q_sca": "#0000FF",  # pure blue
    "Q_abs": "#FF0000",  # pure red
    "Q_ext": "#000000",  # black
}
DEFAULT_LINE_WIDTH = 1.8
QEXT_LINE_WIDTH = 2.4


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "matplotlib is required for plotting. Install it with: python3 -m pip install matplotlib"
        ) from exc
    return plt


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
        raise FileNotFoundError("No input files found")
    return unique


def _resolve_child_dir(base: Path, child: str, arg_label: str) -> Path:
    value = child.strip()
    if not value:
        raise ValueError(f"{arg_label} cannot be empty")

    candidate = Path(value)
    if candidate.is_absolute() or len(candidate.parts) != 1 or value in {".", ".."}:
        raise ValueError(
            f"{arg_label} must be a single child folder name (example: a_MgFeSiO4_examples)"
        )
    return (base / candidate).resolve()


def _resolve_plot_outdir(raw_outdir: str, output_child: str, kind: str) -> Path:
    value = raw_outdir.strip()
    if value:
        return Path(value).expanduser()
    return _resolve_child_dir(OUTPUT_ROOT, output_child, "name") / "plots" / kind


def _display_path(path: Path) -> str:
    try:
        return os.path.relpath(path.resolve(), start=Path.cwd().resolve())
    except Exception:
        return str(path)


def _parse_ggadt_dat(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    ncols: int | None = None
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                values = [float(tok) for tok in line.split()]
            except ValueError:
                continue
            if ncols is None:
                ncols = len(values)
            if len(values) != ncols:
                continue
            rows.append(values)
    if not rows:
        raise ValueError(f"No numeric data rows found in {path}")
    return rows


def _dat_labels(ncols: int) -> tuple[str, list[str], str]:
    if ncols == 4:
        return (
            "Energy (keV)",
            ["Q_sca", "Q_abs", "Q_ext"],
            "Integrated Cross Sections vs Energy",
        )
    if ncols == 2:
        return ("Angle (arcsec)", ["dQ_sca/dOmega"], "Differential Scattering")
    return ("x", [f"col_{i}" for i in range(2, ncols + 1)], "GGADT Output")


def plot_dat_files(paths: list[Path], outdir: Path, show: bool) -> None:
    plt = _require_matplotlib()
    outdir.mkdir(parents=True, exist_ok=True)

    for dat_path in paths:
        rows = _parse_ggadt_dat(dat_path)
        ncols = len(rows[0])
        x_label, y_labels, title = _dat_labels(ncols)
        x = [row[0] for row in rows]

        fig, ax = plt.subplots(figsize=(8, 5))
        for i, y_label in enumerate(y_labels, start=1):
            y = [row[i] for row in rows]
            line_width = QEXT_LINE_WIDTH if y_label == "Q_ext" else DEFAULT_LINE_WIDTH
            ax.plot(
                x,
                y,
                linewidth=line_width,
                label=y_label,
                color=LINE_COLORS.get(y_label),
            )
        ax.set_xlabel(x_label)
        ax.set_ylabel("Value")
        ax.set_title(f"{title}: {dat_path.name}")
        ax.grid(True, alpha=0.3)
        if len(y_labels) > 1:
            ax.legend()

        out_path = outdir / f"{dat_path.stem}.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=PLOT_DPI)
        print(f"Wrote {_display_path(out_path)}")

        if show:
            plt.show()
        plt.close(fig)


def _parse_targ(path: Path) -> tuple[list[float], list[float], list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    ds: list[float] = []
    in_table = False

    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if "x(j)" in line and "2*a(j)" in line:
                in_table = True
                continue
            if not in_table:
                continue

            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                int(float(parts[0]))
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                d = float(parts[4])
            except ValueError:
                continue
            xs.append(x)
            ys.append(y)
            zs.append(z)
            ds.append(d)

    if not xs:
        raise ValueError(f"No monomer rows parsed from {path}")
    return xs, ys, zs, ds


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


def _raw_aeff_from_diameters(ds: list[float]) -> float:
    total_r3 = sum((0.5 * d) ** 3 for d in ds)
    if total_r3 <= 0.0:
        raise ValueError("Cannot compute raw aeff from non-positive monomer diameters")
    return total_r3 ** (1.0 / 3.0)


def _set_equal_3d_axes(ax, xs: list[float], ys: list[float], zs: list[float]) -> None:
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)

    x_mid = 0.5 * (x_min + x_max)
    y_mid = 0.5 * (y_min + y_max)
    z_mid = 0.5 * (z_min + z_max)
    radius = 0.5 * max(x_max - x_min, y_max - y_min, z_max - z_min)
    if radius <= 0:
        radius = 1.0

    ax.set_xlim(x_mid - radius, x_mid + radius)
    ax.set_ylim(y_mid - radius, y_mid + radius)
    ax.set_zlim(z_mid - radius, z_mid + radius)

    # Enforce an undistorted cube in display space; avoids "smushed" spheres.
    if hasattr(ax, "set_box_aspect"):
        ax.set_box_aspect((1.0, 1.0, 1.0))
    if hasattr(ax, "set_proj_type"):
        try:
            ax.set_proj_type("ortho")
        except Exception:
            pass


def plot_grain_files(paths: list[Path], outdir: Path, show: bool) -> None:
    plt = _require_matplotlib()
    outdir.mkdir(parents=True, exist_ok=True)

    for targ_path in paths:
        xs, ys, zs, ds = _parse_targ(targ_path)
        max_d = max(ds) if ds else 1.0
        sizes = [40.0 * (d / max_d) for d in ds]

        fig = plt.figure(figsize=(7, 7))
        ax = fig.add_subplot(111, projection="3d")
        scatter = ax.scatter(xs, ys, zs, s=sizes, c=ds, cmap="viridis", alpha=0.9)
        _set_equal_3d_axes(ax, xs, ys, zs)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")
        ax.set_title(f"{targ_path.name} ({len(xs)} monomers)")
        fig.colorbar(scatter, ax=ax, shrink=0.75, label="Monomer diameter (2a)")

        out_path = outdir / f"{targ_path.stem}_grain.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=PLOT_DPI)
        print(f"Wrote {_display_path(out_path)}")

        if show:
            plt.show()
        plt.close(fig)


def _sphere_mesh(
    ax_um: float, ay_um: float, az_um: float, n_theta: int = 48, n_phi: int = 24
) -> tuple[list[list[float]], list[list[float]], list[list[float]]]:
    xs: list[list[float]] = []
    ys: list[list[float]] = []
    zs: list[list[float]] = []
    for i in range(n_phi + 1):
        phi = math.pi * i / n_phi
        row_x: list[float] = []
        row_y: list[float] = []
        row_z: list[float] = []
        for j in range(n_theta + 1):
            theta = 2.0 * math.pi * j / n_theta
            row_x.append(ax_um * math.sin(phi) * math.cos(theta))
            row_y.append(ay_um * math.sin(phi) * math.sin(theta))
            row_z.append(az_um * math.cos(phi))
        xs.append(row_x)
        ys.append(row_y)
        zs.append(row_z)
    return xs, ys, zs


def _plot_scenario_from_param(
    plt, param_path: Path, outdir: Path, show: bool
) -> None:
    parsed = _parse_param_file(param_path)
    geometry = parsed.get("grain-geometry", "").strip().lower()
    if not geometry:
        raise ValueError(f"Missing grain-geometry in {param_path}")

    try:
        aeff_um = float(parsed["aeff"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Missing/invalid aeff in {param_path}") from exc
    if aeff_um <= 0.0:
        raise ValueError(f"aeff must be positive in {param_path}")

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="3d")

    if geometry in {"sphere", "ellipsoid"}:
        ax_ratio = float(parsed.get("grain-axis-x", "1.0"))
        ay_ratio = float(parsed.get("grain-axis-y", "1.0"))
        az_ratio = float(parsed.get("grain-axis-z", "1.0"))
        ratio_norm = (ax_ratio * ay_ratio * az_ratio) ** (1.0 / 3.0)
        if ratio_norm <= 0.0:
            raise ValueError(f"Invalid axis ratios in {param_path}")
        ax_um = aeff_um * ax_ratio / ratio_norm
        ay_um = aeff_um * ay_ratio / ratio_norm
        az_um = aeff_um * az_ratio / ratio_norm
        xs, ys, zs = _sphere_mesh(ax_um, ay_um, az_um)
        ax.plot_surface(
            np.array(xs), np.array(ys), np.array(zs), alpha=0.75, linewidth=0.0, color="#3d7ea6"
        )
        _set_equal_3d_axes(
            ax,
            [v for row in xs for v in row],
            [v for row in ys for v in row],
            [v for row in zs for v in row],
        )
        ax.set_title(f"{param_path.stem}: {geometry}, aeff={aeff_um:g} um")
    elif geometry in {"spheres", "agglomeration"}:
        agglom_file = parsed.get("agglom-file", "").strip()
        if not agglom_file:
            raise ValueError(f"Missing agglom-file for {geometry} in {param_path}")
        agglom_path = Path(agglom_file).expanduser()
        if not agglom_path.is_absolute():
            agglom_path = (param_path.parent / agglom_path).resolve()
        if not agglom_path.exists():
            raise FileNotFoundError(f"Agglom file not found: {agglom_path}")

        xs, ys, zs, ds = _parse_targ(agglom_path)
        raw_aeff = _raw_aeff_from_diameters(ds)
        scale = aeff_um / raw_aeff
        xs_um = [v * scale for v in xs]
        ys_um = [v * scale for v in ys]
        zs_um = [v * scale for v in zs]
        ds_um = [v * scale for v in ds]
        max_d = max(ds_um) if ds_um else 1.0
        sizes = [40.0 * (d / max_d) for d in ds_um]
        scatter = ax.scatter(xs_um, ys_um, zs_um, s=sizes, c=ds_um, cmap="viridis", alpha=0.9)
        _set_equal_3d_axes(ax, xs_um, ys_um, zs_um)
        fig.colorbar(scatter, ax=ax, shrink=0.75, label="Monomer diameter (um)")
        ax.set_title(
            f"{param_path.stem}: {geometry}, aeff={aeff_um:g} um, monomers={len(xs_um)}"
        )
    else:
        plt.close(fig)
        raise ValueError(f"Unsupported grain-geometry '{geometry}' in {param_path}")

    ax.set_xlabel("x (um)")
    ax.set_ylabel("y (um)")
    ax.set_zlabel("z (um)")

    out_path = outdir / f"{param_path.stem}_grain.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=PLOT_DPI)
    print(f"Wrote {_display_path(out_path)}")
    if show:
        plt.show()
    plt.close(fig)


def plot_scenarios(paths: list[Path], outdir: Path, show: bool) -> None:
    plt = _require_matplotlib()
    outdir.mkdir(parents=True, exist_ok=True)

    for param_path in paths:
        _plot_scenario_from_param(plt, param_path, outdir, show)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot GGADT outputs from output/params/grains child folders."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dat_parser = subparsers.add_parser(
        "plot-dat", help="Plot GGADT .dat output files from ggadt_output/<output>/results."
    )
    dat_parser.add_argument(
        "name",
        nargs="?",
        default=DEFAULT_CHILD,
        help="Output child name under ../ggadt_output/ (default: a_MgFeSiO4_examples).",
    )
    dat_parser.add_argument(
        "--outdir",
        default="",
        help=(
            "Directory for output images "
            "(default: ../ggadt_output/<name>/plots/dat)."
        ),
    )
    dat_parser.add_argument(
        "--show",
        action="store_true",
        help="Display interactive windows in addition to writing image files.",
    )

    scenario_parser = subparsers.add_parser(
        "plot-grain",
        help="Plot exactly one grain geometry image per .ini in params/<params>.",
    )
    scenario_parser.add_argument(
        "name",
        nargs="?",
        default=DEFAULT_CHILD,
        help="Params child name under params/ (default: a_MgFeSiO4_examples).",
    )
    scenario_parser.add_argument(
        "--outdir",
        default="",
        help="Directory for output scenario images (default: ../ggadt_output/<name>/plots/scenarios).",
    )
    scenario_parser.add_argument(
        "--show",
        action="store_true",
        help="Display interactive windows in addition to writing image files.",
    )

    targ_parser = subparsers.add_parser(
        "plot-targ", help="Render .targ grain geometry files from grains/<grains>."
    )
    targ_parser.add_argument(
        "name",
        nargs="?",
        default=DEFAULT_CHILD,
        help="Grains child name under grains/ (default: a_MgFeSiO4_examples).",
    )
    targ_parser.add_argument(
        "--outdir",
        default="",
        help="Directory for output .targ images (default: ../ggadt_output/<name>/plots/grains).",
    )
    targ_parser.add_argument(
        "--show",
        action="store_true",
        help="Display interactive windows in addition to writing image files.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "plot-dat":
            dat_dir = _resolve_child_dir(OUTPUT_ROOT, args.name, "name") / "results"
            files = _collect_input_files([str(dat_dir)], "*.dat")
            outdir = _resolve_plot_outdir(args.outdir, args.name, "dat")
            plot_dat_files(files, outdir, args.show)
        elif args.command == "plot-grain":
            params_dir = _resolve_child_dir(PARAMS_ROOT, args.name, "name")
            files = _collect_input_files([str(params_dir)], "*.ini")
            outdir = _resolve_plot_outdir(args.outdir, args.name, "scenarios")
            plot_scenarios(files, outdir, args.show)
        elif args.command == "plot-targ":
            grains_dir = _resolve_child_dir(GRAINS_ROOT, args.name, "name")
            files = _collect_input_files([str(grains_dir)], "*.targ")
            outdir = _resolve_plot_outdir(args.outdir, args.name, "grains")
            plot_grain_files(files, outdir, args.show)
        else:
            parser.error(f"Unknown command: {args.command}")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
