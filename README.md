# ggadt-analysis

Tools for running GGADT parameter batches and plotting GGADT outputs.

## What is in this repo

- `run_ggadt.py`: batch runner for `.ini` scenarios in `params/<name>/`.
- `analyze_ggadt.py`: plotting tools for GGADT `.dat` outputs and grain geometry.
- `params/ggadt_template.ini`: editable template for new GGADT parameter files.
- `grains/`: grain/agglomerate geometry input files.
- [`parameter_reference.md`](parameter_reference.md): full GGADT parameter documentation and examples.

## Quick Start

Use one shared run name across `params/`, `grains/`, and `ggadt_output/`.
The example below uses a new name: `edge_scan_v1`.

1. Create matching folders:
   - `mkdir -p params/edge_scan_v1 grains/edge_scan_v1`
2. Create a parameter file from the template:
   - `cp params/ggadt_template.ini params/edge_scan_v1/main.ini`
3. Edit `params/edge_scan_v1/main.ini` for your run settings.
4. Validate what will run:
   - `python3 run_ggadt.py edge_scan_v1 --dry-run`
5. Run GGADT:
   - `python3 run_ggadt.py edge_scan_v1`
6. Optional: generate a material table from n/k files and override `material-file` at runtime:
   - `python3 run_ggadt.py edge_scan_v1 --material a-MgFeSiO4`

## Output Layout

For the Quick Start example `edge_scan_v1`, outputs are written to:

- `../ggadt_output/edge_scan_v1/results` (GGADT `.dat` outputs)
- `../ggadt_output/edge_scan_v1/logs` (run logs / stderr)
- `../ggadt_output/edge_scan_v1/a_MgFeSiO4_material.dat` (when `--material a-MgFeSiO4` is used)

## Plotting

- Plot GGADT data tables:
  - `python3 analyze_ggadt.py plot-dat edge_scan_v1`
- Plot specific grain geometry from parameter files:
  - `python3 analyze_ggadt.py plot-grain edge_scan_v1`
- Plot raw `.targ` geometry from grains:
  - `python3 analyze_ggadt.py plot-targ edge_scan_v1`

## Reference

For full parameter definitions, run modes, and detailed examples, see [`parameter_reference.md`](parameter_reference.md).
