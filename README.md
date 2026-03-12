# ggadt-analysis

Tools for running GGADT parameter batches and plotting GGADT outputs.

## What is in this repo

- `run_ggadt.py`: batch runner for `.ini` scenarios in `params/<name>/`.
- `analyze_ggadt.py`: plotting tools for GGADT `.dat` outputs and grain geometry.
- `params/ggadt_template.ini`: editable template for new GGADT parameter files.
- `grains/`: grain/agglomerate geometry input files.
- [`parameter_reference.md`](parameter_reference.md): full GGADT parameter documentation and examples.

## Quick Start

1. Create or copy a parameter set folder under `params/`:
   - Example: `params/a_MgFeSiO4_examples/`
   - Also valid: `params/test_run_01/`
   - Naming convention: use the same set name across folders, e.g.
     `params/test_run_01`, `grains/test_run_01`, and `../ggadt_output/test_run_01`.
2. Run a dry-run check:
   - `python3 run_ggadt.py a_MgFeSiO4_examples --dry-run`
   - `python3 run_ggadt.py test_run_01 --dry-run`
3. Run GGADT:
   - `python3 run_ggadt.py a_MgFeSiO4_examples`
   - `python3 run_ggadt.py test_run_01`
4. Optional material generation from n/k files:
   - `python3 run_ggadt.py a_MgFeSiO4_examples --material a-MgFeSiO4`

## Output Layout

Runs write to:

- `../ggadt_output/<name>/results`
- `../ggadt_output/<name>/logs`
- `../ggadt_output/<name>/<material>_material.dat` (when `--material` is used)

## Plotting

- Plot GGADT data tables:
  - `python3 analyze_ggadt.py plot-dat a_MgFeSiO4_examples`
- Plot specific grain geometry from parameter files:
  - `python3 analyze_ggadt.py plot-grain a_MgFeSiO4_examples`
- Plot raw `.targ` geometry from grains:
  - `python3 analyze_ggadt.py plot-targ a_MgFeSiO4_examples`

## Reference

For full parameter definitions, run modes, and detailed examples, see [`parameter_reference.md`](parameter_reference.md).
