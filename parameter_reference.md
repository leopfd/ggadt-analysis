# GGADT Parameter Reference

This file documents every runtime parameter accepted by `ggadt`.


## Index

- [1. How Parameters Are Applied](#1-how-parameters-are-applied)
- [2. Parameter File Syntax](#2-parameter-file-syntax)
- [3. Parameter Index and Reference](#3-parameter-index-and-reference)
  - [Parameter Links](#parameter-links)
  - [3.1 Flags](#31-flags)
  - [3.2 General Run / Output Parameters](#32-general-run--output-parameters)
  - [3.3 Unit Parameters](#33-unit-parameters)
  - [3.4 Geometry / Grid Parameters](#34-geometry--grid-parameters)
  - [3.5 Material / Optical Property Parameters](#35-material--optical-property-parameters)
  - [3.6 Angular Scattering Parameters](#36-angular-scattering-parameters)
  - [3.7 Orientation Parameters](#37-orientation-parameters)
  - [3.8 Energy Sampling Parameters](#38-energy-sampling-parameters)
  - [3.9 Performance / Backend Parameters](#39-performance--backend-parameters)
- [4. Agglom, Grain, and Material Setup Workflow](#4-agglom-grain-and-material-setup-workflow)
- [5. Example Run Scenarios](#5-example-run-scenarios)
  - [Example File A: 1D Differential Scattering (Ellipsoid)](#example-file-a-1d-differential-scattering-ellipsoid)
  - [Example File B: 2D Differential Scattering Map](#example-file-b-2d-differential-scattering-map)
  - [Example File C: Phi-Averaged Differential Scattering](#example-file-c-phi-averaged-differential-scattering)
  - [Example File D: Integrated Cross Sections vs Energy](#example-file-d-integrated-cross-sections-vs-energy)
  - [Example File E: Lower Porosity (More Compact) Agglomerate](#example-file-e-lower-porosity-more-compact-agglomerate)
  - [Example File F: Higher Porosity (More Fluffy) Agglomerate](#example-file-f-higher-porosity-more-fluffy-agglomerate)
- [6. Notes and Caveats](#6-notes-and-caveats)
## 1. How Parameters Are Applied

GGADT applies parameter sources in this order:

1. Built-in option defaults
2. Installed defaults file (`default.params`)
3. Your `parameter-file`
4. Command-line options (highest priority)

This means command-line values override parameter-file values.

## 2. Parameter File Syntax

Each non-empty line sets exactly one parameter:

`parameter-name = value`

Plain-language rules:

- Left side (`parameter-name`) must be one of GGADT's parameter names (for example `ephot`, `grain-geometry`, `do-full-2d-fft`).
- Right side (`value`) is the assigned parameter value.
- Spaces around `=` are optional.
- Comments can start with `#` or `!` (at the start of a line, or after a value).
- Boolean values are case-insensitive and can be: `T`, `F`, `TRUE`, `FALSE`, `.TRUE.`, `.FALSE.`.

Common value examples:

- float: `ephot = 2.0`
- integer: `norientations = 64`
- boolean flag in file form: `integrated = T`
- string: `angle-mode = random`
- quoted path: `material-file = "index_silD03"`

Example:

```ini
# Example parameter file
grain-geometry = spheres
agglom-file = "BA.256.1.targ"
integrated = F
ephot = 2.0
norientations = 100
```

## 3. Parameter Index and Reference

### Parameter Links
**Flags:** [`help`](#help), [`version`](#version), [`verbose`](#verbose), [`use-efficiencies`](#use-efficiencies), [`timing`](#timing), [`integrated`](#integrated), [`force-numerical`](#force-numerical), [`quiet`](#quiet), [`do-full-2d-fft`](#do-full-2d-fft), [`save-shadow-function`](#save-shadow-function), [`save-orientations`](#save-orientations), [`do-phi-averaging`](#do-phi-averaging), [`use-padded-fft`](#use-padded-fft)

**General Run / Output:** [`parameter-file`](#parameter-file), [`save-file-root`](#save-file-root), [`output-sigfigs`](#output-sigfigs)

**Units:** [`units-file`](#units-file), [`input-unit-length`](#input-unit-length), [`input-unit-angle`](#input-unit-angle), [`input-unit-energy`](#input-unit-energy), [`output-unit-length`](#output-unit-length), [`output-unit-angle`](#output-unit-angle), [`output-unit-energy`](#output-unit-energy)

**Geometry / Grid:** [`grain-geometry`](#grain-geometry), [`agglom-file`](#agglom-file), [`aeff`](#aeff), [`grain-axis-x`](#grain-axis-x), [`grain-axis-y`](#grain-axis-y), [`grain-axis-z`](#grain-axis-z), [`ngrain`](#ngrain), [`grid-width`](#grid-width)

**Material / Optical Properties:** [`material`](#material), [`material-file`](#material-file), [`ior-re`](#ior-re), [`ior-im`](#ior-im), [`material-file1`](#material-file1), [`material-tag1`](#material-tag1), [`material-file2`](#material-file2), [`material-tag2`](#material-tag2), [`material-file3`](#material-file3), [`material-tag3`](#material-tag3), [`agglom-composition-file`](#agglom-composition-file)

**Angular Scattering:** [`max-angle`](#max-angle), [`dtheta`](#dtheta), [`nscatter`](#nscatter), [`nphi`](#nphi)

**Orientation:** [`angle-mode`](#angle-mode), [`angle-file`](#angle-file), [`norientations`](#norientations), [`axes-convention`](#axes-convention)

**Energy Sampling:** [`ephot`](#ephot), [`ephot-min`](#ephot-min), [`ephot-max`](#ephot-max), [`nephots`](#nephots), [`dephot`](#dephot)

**Performance / Backend:** [`nthreads`](#nthreads), [`fftw-optimization`](#fftw-optimization)

## 3.1 Flags

### `help`
**Type:** flag.  
**What it does:** Prints CLI help and exits immediately.  
**When to use:** Discover available options and their CLI spelling.  

### `version`
**Type:** flag.  
**What it does:** Prints version/build info and exits immediately.  
**When to use:** Confirm binary/version in scripts or bug reports.  

### `verbose`
**Type:** flag.  
**What it does:** Enables extra status output and parameter summaries.  
**When to use:** Debugging runs and confirming resolved parameter values.  
**Interaction notes:** Works independently of <small><code>quiet</code></small>; <small><code>quiet</code></small> mainly suppresses progress percentage lines.  

### `use-efficiencies`
**Type:** flag.  
**What it does:** Outputs dimensionless efficiencies (<small><code>Q</code></small>) instead of dimensional cross sections (<small><code>C</code></small>).  
**When to use:** Comparing results across grain sizes.  
**Interaction notes:** Changes output normalization only; physics calculation path is unchanged.  

### `timing`
**Type:** flag.  
**What it does:** In differential-scattering mode, exits before printing the large scattering output table.  
**When to use:** Timing/benchmark runs where output I/O would dominate.  
**Interaction notes:** This is mainly meaningful for differential runs, not integrated energy-sweep output.  

### `integrated`
**Type:** flag.  
**What it does:** Switches from differential scattering output to integrated <small><code>(sca, abs, ext)</code></small> cross sections over energy.  
**When to use:** Energy-dependent total cross-section studies.  
**Interaction notes:** Uses <small><code>ephot-min</code></small>, <small><code>ephot-max</code></small>, <small><code>nephots</code></small>, <small><code>dephot</code></small> family; disables differential-only behaviors.  

### `force-numerical`
**Type:** flag.  
**What it does:** For <small><code>grain-geometry=sphere</code></small>, disables the analytic sphere ADT path and forces the full numerical shadow-function + FFT path.  
**When to use:** Consistency checks against non-sphere numerical workflow.  
**Interaction notes:** Usually slower than default analytic sphere mode.  

### `quiet`
**Type:** flag.  
**What it does:** Suppresses progress messages during orientation loops.  
**When to use:** Cleaner logs or batch runs.  
**Interaction notes:** Does not suppress final data output.  

### `do-full-2d-fft`
**Type:** flag.  
**What it does:** Computes full 2D scattering (<small><code>theta_x</code></small>, <small><code>theta_y</code></small>) instead of assuming axisymmetry.  
**When to use:** Anisotropic scattering studies where azimuthal dependence matters.  
**Interaction notes:** Produces larger outputs and more compute cost.  

### `save-shadow-function`
**Type:** flag.  
**What it does:** Writes shadow-function grids to disk.  
**When to use:** Debugging/validation of projected grain phase.  
**Interaction notes:** Output files use <small><code>save-file-root</code></small> with suffix <small><code>_shadow_function_oXXXXX.dat</code></small>.  

### `save-orientations`
**Type:** flag.  
**What it does:** Saves the orientation angles used in the run.  
**When to use:** Reproducibility and debugging orientation sampling.  
**Interaction notes:** Output file uses <small><code>save-file-root</code></small> with suffix <small><code>_orientations.dat</code></small>.  

### `do-phi-averaging`
**Type:** flag.  
**What it does:** Averages the 2D scattering field over <small><code>phi</code></small> to produce a 1D curve.  
**When to use:** You need 1D output but want it derived from full-2D calculations.  
**Interaction notes:** Requires <small><code>do-full-2d-fft</code></small> and non-<small><code>integrated</code></small> mode.  

### `use-padded-fft`
**Type:** flag.  
**What it does:** Uses padded FFT strategy to get denser angular sampling in requested range.  
**When to use:** Consistency testing against default faster FFT strategy.  
**Interaction notes:** Slower; cannot be combined with manually set <small><code>grid-width</code></small>.  

## 3.2 General Run / Output Parameters

### `parameter-file`
**Type:** string path.  
**What it does:** Points GGADT to a user parameter file.  
**When to use:** Keep reusable run configs in files.  
**Interaction notes:** Values here are overridden by explicit CLI options.  

### `save-file-root`
**Type:** string.  
**What it does:** Prefix for saved auxiliary files.  
**When to use:** Separate outputs from different runs.  
**Interaction notes:** Used by <small><code>save-shadow-function</code></small> and <small><code>save-orientations</code></small>.  

### `output-sigfigs`
**Type:** integer.  
**What it does:** Sets significant digits in numeric output formatting.  
**When to use:** Control output precision and file size.  
**Interaction notes:** Values that imply format width > 99 are rejected.  

## 3.3 Unit Parameters

### `units-file`
**Type:** string path.  
**What it does:** Loads unit names, abbreviations, and scale factors used by input/output unit parameters.  
**When to use:** Add custom units or override defaults.  
**Required format:** one unit per line as <small><code>KIND NAME ABBREV VALUE</code></small>, where <small><code>KIND</code></small> is <small><code>LENGTH</code></small>, <small><code>ANGLE</code></small>, or <small><code>ENERGY</code></small>.  
**Example line:** <small><code>LENGTH micron um 1.0d-6</code></small>.  

### `input-unit-length`
**Type:** string.  
**What it does:** Declares unit used for input length values (<small><code>aeff</code></small>, <small><code>grid-width</code></small>, axis lengths).  
**When to use:** Enter parameters in units other than meters.  
**Interaction notes:** Can match either unit name or abbreviation from <small><code>units-file</code></small>.  

### `input-unit-angle`
**Type:** string.  
**What it does:** Declares unit used for input angles (<small><code>max-angle</code></small>, <small><code>dtheta</code></small>, angle-file values).  
**When to use:** Enter angles in arcsec/deg/rad, etc.  
**Interaction notes:** Can match either unit name or abbreviation from <small><code>units-file</code></small>.  

### `input-unit-energy`
**Type:** string.  
**What it does:** Declares unit used for input energies (<small><code>ephot</code></small>, <small><code>ephot-min</code></small>, <small><code>ephot-max</code></small>, <small><code>dephot</code></small>).  
**When to use:** Enter energies in keV/eV/J.  
**Interaction notes:** Can match either unit name or abbreviation from <small><code>units-file</code></small>.  

### `output-unit-length`
**Type:** string.  
**What it does:** Unit used when printing length-derived outputs.  
**When to use:** Choose convenient reporting units.  

### `output-unit-angle`
**Type:** string.  
**What it does:** Unit used when printing angles.  
**When to use:** Match downstream plotting/analysis expectations.  

### `output-unit-energy`
**Type:** string.  
**What it does:** Unit used when printing energies.  
**When to use:** Keep output consistent with the target analysis workflow.  

## 3.4 Geometry / Grid Parameters

### `grain-geometry`
**Type:** string.  
**What it does:** Selects shape model and solver branch.  
**Supported values in code:** <small><code>sphere</code></small>, <small><code>spheres</code></small>, <small><code>agglomeration</code></small>, <small><code>ellipsoid</code></small>, <small><code>custom</code></small>.  
**Interaction notes:** Supported agglomerate geometry keywords include <small><code>spheres</code></small> and <small><code>agglomeration</code></small>; <small><code>spheres</code></small> matches the current documentation and examples.  

### `agglom-file`
**Type:** string path.  
**What it does:** Provides multisphere target geometry for <small><code>grain-geometry=spheres</code></small>.  
**When to use:** Agglomerate of monomers (spherical components).  
**Parsing behavior:** header + monomer rows read as <small><code>index x y z diameter</code></small>; GGADT converts diameter to radius, recenters, rotates, then rescales cluster to configured <small><code>aeff</code></small>.  
**Header line 2 fields:** <small><code>NS VTOT alpha1 alpha2 alpha3</code></small>; in current source, <small><code>NS</code></small> controls monomer count, while <small><code>VTOT</code></small>/<small><code>alpha*</code></small> are parsed metadata.  
**How to create one:** use Section 4 ("Agglom, Grain, and Material Setup Workflow"), then set monomer rows as <small><code>index x y z diameter</code></small>.  
**Porosity note:** keeping diameters fixed, higher porosity comes from a connected but lower-coordination (more open) monomer network.  

### `aeff`
**Type:** float.  
**What it does:** Effective radius scale for the grain.  
**When to use:** Set overall grain size.  
**Interaction notes:** Agglomerates and ellipsoids are rescaled to enforce this effective radius.  

### `grain-axis-x`
**Type:** float.  
**What it does:** Ellipsoid x-axis parameter.  
**When to use:** <small><code>grain-geometry=ellipsoid</code></small>.  
**Interaction notes:** Axes are renormalized internally to preserve <small><code>aeff</code></small>.  

### `grain-axis-y`
**Type:** float.  
**What it does:** Ellipsoid y-axis parameter.  
**When to use:** <small><code>grain-geometry=ellipsoid</code></small>.  
**Interaction notes:** Axes are renormalized internally to preserve <small><code>aeff</code></small>.  

### `grain-axis-z`
**Type:** float.  
**What it does:** Ellipsoid z-axis parameter.  
**When to use:** <small><code>grain-geometry=ellipsoid</code></small>.  
**Interaction notes:** Axes are renormalized internally to preserve <small><code>aeff</code></small>.  

### `ngrain`
**Type:** integer.  
**What it does:** Base grid resolution per spatial dimension.  
**When to use:** Increase for higher fidelity at higher compute/memory cost.  
**Interaction notes:** Requested value is snapped to nearest allowed FFT-friendly size from <small><code>data/allowed_ngrid_values.txt</code></small>.  
**Distinction:** <small><code>ngrain</code></small> is grid resolution; <small><code>NS</code></small> is monomer count inside the <small><code>.targ</code></small> file.  

### `grid-width`
**Type:** float.  
**What it does:** Physical width of computational grid.  
**When to use:** Override automatic domain sizing.  
**Interaction notes:** Must use same length units as other length inputs; cannot be manually set when <small><code>use-padded-fft</code></small> is enabled.  

## 3.5 Material / Optical Property Parameters

### `material`
**Type:** string (legacy).  
**What it does:** Historical placeholder from older interface.  
**Current status:** Defined in CLI but not used in current runtime logic.  
**Operational note:** Use <small><code>material-file</code></small> or manual <small><code>ior-re</code></small>/<small><code>ior-im</code></small> for active optical-property input.  

### `material-file`
**Type:** string path.  
**What it does:** Supplies energy-dependent optical constants for single-material runs.  
**Expected file structure:** first line material header, second line column header, then data rows <small><code>E(eV) Re(n)-1 Im(n) Re(eps)-1 Im(eps)</code></small>.  
**Interaction notes:** If combined with manual <small><code>ior-re</code></small>/<small><code>ior-im</code></small>, precedence depends on source priority (CLI vs file/default rank).  

### `ior-re`
**Type:** float.  
**What it does:** Manual real part of <small><code>m-1</code></small>.  
**When to use:** Constant-index runs without material files.  
**Interaction notes:** May be overridden by material-file path depending on parameter source priority.  

### `ior-im`
**Type:** float.  
**What it does:** Manual imaginary part of <small><code>m-1</code></small>.  
**When to use:** Constant-index runs without material files.  
**Interaction notes:** May be overridden by material-file path depending on parameter source priority.  

### `material-file1`
**Type:** string path.  
**What it does:** Optical constants file for material slot 1 (multi-material agglomerates).  
**When to use:** Mixed-composition agglomerate runs.  
**Interaction notes:** Must pair with <small><code>material-tag1</code></small>.  

### `material-tag1`
**Type:** string.  
**What it does:** Tag name that identifies material slot 1.  
**When to use:** Multi-material agglomerates.  
**Interaction notes:** Must pair with <small><code>material-file1</code></small>; tag must appear in <small><code>agglom-composition-file</code></small>.  

### `material-file2`
**Type:** string path.  
**What it does:** Optical constants file for material slot 2.  
**When to use:** Multi-material agglomerates needing a second composition.  
**Interaction notes:** Must pair with <small><code>material-tag2</code></small>.  

### `material-tag2`
**Type:** string.  
**What it does:** Tag name for material slot 2.  
**When to use:** Multi-material agglomerates.  
**Interaction notes:** Must pair with <small><code>material-file2</code></small>.  

### `material-file3`
**Type:** string path.  
**What it does:** Optical constants file for material slot 3.  
**When to use:** Multi-material agglomerates needing a third composition.  
**Interaction notes:** Must pair with <small><code>material-tag3</code></small>.  

### `material-tag3`
**Type:** string.  
**What it does:** Tag name for material slot 3.  
**When to use:** Multi-material agglomerates.  
**Interaction notes:** Must pair with <small><code>material-file3</code></small>.  

### `agglom-composition-file`
**Type:** string path.  
**What it does:** Maps each monomer to a material tag for multi-material agglomerates.  
**Expected format:** first line ignored as header; then one line per monomer as <small><code>index tag</code></small>.  
**Interaction notes:** number/order of mapping lines must match monomers in <small><code>agglom-file</code></small>; tags must match one of <small><code>material-tag1..3</code></small>.  

## 3.6 Angular Scattering Parameters

### `max-angle`
**Type:** float.  
**What it does:** Maximum scattering angle to compute.  
**When to use:** Set extent of scattering curve/map.  
**Interaction notes:** Can trigger geometry/grid limits; large angles may require larger grids and can fail near 90 degrees.  

### `dtheta`
**Type:** float.  
**What it does:** Angular step size target.  
**When to use:** Control angular resolution directly.  
**Interaction notes:** If <small><code>dtheta</code></small> is provided, <small><code>nscatter</code></small> may be derived as <small><code>ceil(2*max-angle/dtheta)</code></small>.  

### `nscatter`
**Type:** integer.  
**What it does:** Number of angular samples.  
**When to use:** Control output grid size directly.  
**Interaction notes:** If both <small><code>nscatter</code></small> and <small><code>dtheta</code></small> are provided, code resolves precedence using parameter source priority.  

### `nphi`
**Type:** integer.  
**What it does:** Number of phi samples used by phi-averaging path.  
**When to use:** <small><code>do-phi-averaging</code></small> workflows.  
**Interaction notes:** Ignored unless full 2D mode is active and run is not integrated.  

## 3.7 Orientation Parameters

### `angle-mode`
**Type:** string.  
**What it does:** Chooses orientation sampling strategy.  
**Supported values:** <small><code>random</code></small>, <small><code>sequential</code></small>, <small><code>file</code></small>.  
**Interaction notes:** sequential mode snaps <small><code>norientations</code></small> to perfect square/cube forms required by its grid logic.  

### `angle-file`
**Type:** string path.  
**What it does:** Supplies explicit orientation list for <small><code>angle-mode=file</code></small>.  
**Expected format:** one orientation per line, exactly 3 angle values per line.  
**Interaction notes:** if file line count disagrees with <small><code>norientations</code></small>, GGADT warns and replaces <small><code>norientations</code></small> with line count.  

### `norientations`
**Type:** integer.  
**What it does:** Number of orientations to average.  
**When to use:** Increase for better orientation averaging convergence.  
**Interaction notes:** may be adjusted by <small><code>angle-mode</code></small> logic (<small><code>sequential</code></small> or <small><code>file</code></small> mode consistency fixes).  

### `axes-convention`
**Type:** string.  
**What it does:** Interprets orientation angle convention.  
**Allowed values:** <small><code>ddscat</code></small> or <small><code>mstm</code></small>.  
**Interaction notes:** <small><code>mstm</code></small> inputs are converted internally to DDSCAT convention before use.  

## 3.8 Energy Sampling Parameters

### `ephot`
**Type:** float.  
**What it does:** Single photon energy for differential runs.  
**When to use:** Non-integrated mode.  
**Interaction notes:** ignored as sweep driver in integrated mode, where <small><code>ephot-min/max</code></small> family is used.  

### `ephot-min`
**Type:** float.  
**What it does:** Lower bound of energy sweep.  
**When to use:** Integrated mode.  
**Interaction notes:** Combined with <small><code>ephot-max</code></small> and either <small><code>dephot</code></small> or <small><code>nephots</code></small>.  

### `ephot-max`
**Type:** float.  
**What it does:** Upper bound of energy sweep.  
**When to use:** Integrated mode.  
**Interaction notes:** Combined with <small><code>ephot-min</code></small> and either <small><code>dephot</code></small> or <small><code>nephots</code></small>.  

### `nephots`
**Type:** integer.  
**What it does:** Number of energy samples.  
**When to use:** Prefer fixed number of points across sweep range.  
**Interaction notes:** Can be derived from <small><code>dephot</code></small>; precedence is resolved by source priority.  

### `dephot`
**Type:** float.  
**What it does:** Energy spacing between samples.  
**When to use:** Prefer fixed energy step.  
**Interaction notes:** Can be derived from <small><code>nephots</code></small>; precedence is resolved by source priority.  

## 3.9 Performance / Backend Parameters

### `nthreads`
**Type:** integer.  
**What it does:** Sets OpenMP thread count when compiled with OpenMP.  
**When to use:** Performance tuning on multi-core systems.  
**Interaction notes:** <small><code>-1</code></small> means runtime/system default; if OpenMP is not enabled at build time, this has no effect.  

### `fftw-optimization`
**Type:** string.  
**What it does:** Exposes FFTW-style planning names (<small><code>estimate</code></small>, <small><code>measure</code></small>, <small><code>patient</code></small>, <small><code>exhaustive</code></small>).  
**Current status:** parsed and stored, but not actively used in current source path.  
**Operational note:** Default behavior is appropriate unless additional code paths explicitly consume this option.  

## 4. Agglom, Grain, and Material Setup Workflow
Workflow for building aggregate geometry and material inputs.

Definitions:

- `NS` (inside `.targ` line 2) = number of monomers in one grain geometry.
- `ngrain` (parameter in `.ini`) = simulation grid points per dimension.

`NS` is physical geometry complexity; `ngrain` is numerical resolution.

Example:

- `NS = 800`, `ngrain = 256` -> one grain made of 800 monomers sampled on a `256 x 256` grid.

1. Agglom file format (`agglom-file`)

How GGADT reads it:

1. Line 1: freeform header/comment (usually includes `MIGRATE` and `ISEED`).
2. Line 2: `NS VTOT alpha1 alpha2 alpha3`.
3. Line 3: `A_1` orientation vector (`x y z`).
4. Line 4: `A_2` orientation vector (`x y z`).
5. Line 5: column header text (informational).
6. Remaining lines: one monomer per line as `index x y z diameter`.

Monomer row columns:

- `index`: monomer ID (`1..NS`).
- `x y z`: monomer center position in cluster coordinates.
- `diameter`: monomer diameter (`2*a(j)` in the column label).

Line 2 field meanings:

- `NS`: number of monomer rows expected in the file.
- `VTOT`: total volume metadata from the generator.
- `alpha1 alpha2 alpha3`: normalized principal moments-of-inertia metadata (`alpha1 >= alpha2 >= alpha3` in generator convention).

Runtime usage in current source:

- `NS` is used directly to size arrays and to control monomer-row reads.
- `VTOT` and `alpha1..3` are parsed and stored from the header.
- Geometry construction and scaling are driven by monomer rows, `A_1`/`A_2`, and `aeff`; `VTOT` and `alpha1..3` are not used in later geometry calculations.

Required consistency checks:

1. `NS` must equal number of monomer rows.
2. Monomer indices should be sequential and match row order.
3. Diameters must be positive.
4. For one physical grain, monomers should form one connected touching network.
5. Keep `A_1` and `A_2` as perpendicular unit vectors (identity vectors are fine).

Minimal agglom template:
```text
multisphere target generated by agglom with MIGRATE= 0 ISEED=  -1
        4        4.00   1.000000   1.000000   1.000000 = NS, VTOT, alpha(1-3)
  1.000000  0.000000  0.000000 = A_1 vector
  0.000000  1.000000  0.000000 = A_2 vector
       j      x(j)        y(j)        z(j)     2*a(j)
       1    0.000000    0.000000    0.000000  1.000000
       2    1.000000    0.000000    0.000000  1.000000
       3   -1.000000    0.000000    0.000000  1.000000
       4    0.000000    1.000000    0.000000  1.000000
```

Parser/normalization behavior:

- GGADT reads diameter and converts to radius internally.
- GGADT recenters and rescales the whole cluster to the configured `aeff`.
- Raw `.targ` distances are relative geometry; `aeff` sets final absolute scale.

2. Optical-constant strategy

- Single-material grain: use `material-file` or constant `ior-re`/`ior-im`.
- Multi-material agglomerate: use `material-file1..3` + `material-tag1..3` + `agglom-composition-file`.
- Do not mix `material-file` with `material-file1..3`.
- `material-file` rows are read as: `E(eV) Re(n)-1 Im(n) Re(eps)-1 Im(eps)`.

Material-file example (`silicate.dat`):
```text
17 =ICOMP: amorphous olivine-like astrosilicate
    E(eV)      Re(n)-1    Im(n)    Re(eps)-1  Im(eps)
1.000000E-05  2.435E+00 1.119E-03  1.080E+01 7.688E-03
1.240000E-05  2.435E+00 1.388E-03  1.080E+01 9.534E-03
1.771000E-05  2.435E+00 1.982E-03  1.080E+01 1.362E-02
2.000000E-05  2.435E+00 2.239E-03  1.080E+01 1.538E-02
```

Format notes:

- Line 1 is a material identifier/header (the parser reads the leading integer and label text).
- Line 2 is a column header line.
- Data lines must provide five numeric columns in the order shown above.
- Energy is interpreted as eV in the file and converted internally.

Single-material configuration:
```ini
grain-geometry = spheres
agglom-file = "my_cluster.targ"
material-file = "index_silD03"
aeff = 0.2
ngrain = 256
```

Multi-material configuration:
```ini
grain-geometry = spheres
agglom-file = "my_cluster.targ"
material-file1 = "silicate.dat"
material-tag1 = "sil"
material-file2 = "carbon.dat"
material-tag2 = "carb"
agglom-composition-file = "my_cluster.comp"
aeff = 0.2
ngrain = 256
```

Composition mapping file:
```text
# index tag
1 sil
2 sil
3 carb
4 carb
```

3. Size and grid parameters (`aeff`, `ngrain`, `grid-width`)

- `aeff` = final physical grain size.
- `ngrain` = grid resolution (not grain count).
- `grid-width` = physical width of simulation box (use auto first).
- Approximate grid spacing: `dx ~ (grid-width * aeff) / (ngrain - 1)`.
- Ensure smallest monomer diameter spans several grid cells.
- If `use-padded-fft` is enabled, do not manually set `grid-width`.

4. Validation and production scaling

- Start with smaller `norientations` and lower sampling.
- Check warnings for file conflicts, missing composition tags, and auto-adjusted `ngrain`.
- Once inputs are verified, increase `norientations`, `ngrain`, and angular/energy sampling.

## 5. Example Run Scenarios
This section provides file examples plus the minimal run command using `--parameter-file`. Save each snippet under the filename shown in its header before running.

### Example File A: 1D Differential Scattering (Ellipsoid)
```ini
# example_a_diffscat_1d_ellipsoid.ini
grain-geometry = ellipsoid
grain-axis-x = 1.0
grain-axis-y = 0.8
grain-axis-z = 1.3

integrated = F
do-full-2d-fft = F
do-phi-averaging = F

aeff = 0.2
ngrain = 128

ephot = 2.0
dtheta = 25.0
max-angle = 3000.0

ior-re = -1.920E-4
ior-im = 2.807E-5

angle-mode = random
norientations = 32

use-efficiencies = T
verbose = F
quiet = F
```

Run with:
```bash
src/ggadt --parameter-file=example_a_diffscat_1d_ellipsoid.ini
```

### Example File B: 2D Differential Scattering Map
```ini
# example_b_diffscat_2d_ellipsoid.ini
grain-geometry = ellipsoid
grain-axis-x = 1.0
grain-axis-y = 1.0
grain-axis-z = 1.6

integrated = F
do-full-2d-fft = T
do-phi-averaging = F

aeff = 0.2
ngrain = 128

ephot = 1.0
dtheta = 25.0
max-angle = 3000.0

ior-re = -1.920E-4
ior-im = 2.807E-5

angle-mode = random
norientations = 16
```

Run with:
```bash
src/ggadt --parameter-file=example_b_diffscat_2d_ellipsoid.ini
```

### Example File C: Phi-Averaged Differential Scattering
```ini
# example_c_diffscat_phi_averaged.ini
grain-geometry = ellipsoid
grain-axis-x = 1.0
grain-axis-y = 1.0
grain-axis-z = 1.6

integrated = F
do-full-2d-fft = T
do-phi-averaging = T
nphi = 64

aeff = 0.2
ngrain = 128

ephot = 1.0
dtheta = 25.0
max-angle = 3000.0

ior-re = -1.920E-4
ior-im = 2.807E-5

angle-mode = random
norientations = 16
```

Run with:
```bash
src/ggadt --parameter-file=example_c_diffscat_phi_averaged.ini
```

### Example File D: Integrated Cross Sections vs Energy
```ini
# example_d_integrated_total_xs.ini
grain-geometry = ellipsoid
grain-axis-x = 1.0
grain-axis-y = 0.9
grain-axis-z = 1.2

aeff = 0.2
ngrain = 128

integrated = T
do-full-2d-fft = F

ior-re = -1.920E-4
ior-im = 2.807E-5

ephot-min = 0.2
ephot-max = 2.0
dephot = 0.2

angle-mode = random
norientations = 24

use-efficiencies = T
```

Run with:
```bash
src/ggadt --parameter-file=example_d_integrated_total_xs.ini
```

### Example File E: Lower Porosity (More Compact) Agglomerate
```ini
# example_e_porosity_low.ini
grain-geometry = spheres
agglom-file = "compact_cluster_8spheres.targ"

integrated = F
do-full-2d-fft = F
do-phi-averaging = F

aeff = 0.2
ngrain = 128

ephot = 2.0
dtheta = 25.0
max-angle = 3000.0

ior-re = -1.920E-4
ior-im = 2.807E-5

angle-mode = random
norientations = 24
```

Run with:
```bash
src/ggadt --parameter-file=example_e_porosity_low.ini
```

Supporting agglomerate file:
```text
# compact_cluster_8spheres.targ
multisphere target generated by agglom with MIGRATE= 0 ISEED=  -1
        8        8.00   1.000000   1.000000   1.000000 = NS, VTOT, alpha(1-3)
  1.000000  0.000000  0.000000 = A_1 vector
  0.000000  1.000000  0.000000 = A_2 vector
       j      x(j)        y(j)        z(j)     2*a(j)
       1    0.000000    0.000000    0.000000  1.000000
       2    1.000000    0.000000    0.000000  1.000000
       3   -1.000000    0.000000    0.000000  1.000000
       4    0.000000    1.000000    0.000000  1.000000
       5    0.000000   -1.000000    0.000000  1.000000
       6    0.000000    0.000000    1.000000  1.000000
       7    0.000000    0.000000   -1.000000  1.000000
       8    1.000000    1.000000    0.000000  1.000000
```

### Example File F: Higher Porosity (More Fluffy) Agglomerate
```ini
# example_f_porosity_high.ini
grain-geometry = spheres
agglom-file = "fluffy_cluster_8spheres.targ"

integrated = F
do-full-2d-fft = F
do-phi-averaging = F

aeff = 0.2
ngrain = 128

ephot = 2.0
dtheta = 25.0
max-angle = 3000.0

ior-re = -1.920E-4
ior-im = 2.807E-5

angle-mode = random
norientations = 24
```

Run with:
```bash
src/ggadt --parameter-file=example_f_porosity_high.ini
```

Supporting agglomerate file:
```text
# fluffy_cluster_8spheres.targ
multisphere target generated by agglom with MIGRATE= 0 ISEED=  -1
        8        8.00   1.000000   1.000000   1.000000 = NS, VTOT, alpha(1-3)
  1.000000  0.000000  0.000000 = A_1 vector
  0.000000  1.000000  0.000000 = A_2 vector
       j      x(j)        y(j)        z(j)     2*a(j)
       1    0.000000    0.000000    0.000000  1.000000
       2    1.000000    0.000000    0.000000  1.000000
       3    2.000000    0.000000    0.000000  1.000000
       4    3.000000    0.000000    0.000000  1.000000
       5    4.000000    0.000000    0.000000  1.000000
       6    2.000000    1.000000    0.000000  1.000000
       7    2.000000    2.000000    0.000000  1.000000
       8    2.000000    3.000000    0.000000  1.000000
```

With the same monomer diameters, a sparse touching network has higher porosity than a compact touching network.

Concrete interpretation:

- If `2*a(j) = 1.0`, each monomer radius is `0.5`.
- In both examples, nearest-neighbor touching happens at center distance `1.0`.
- The compact example has higher coordination (more touching neighbors per monomer), so it packs solid material into a smaller envelope.
- The fluffy example is a connected chain/branch with lower coordination, so it leaves more void space.
- Same monomer size + same touching distance, but less compact topology = higher porosity.

## 6. Notes and Caveats

`do-phi-averaging` requires `do-full-2d-fft` and non-integrated mode.

`nphi` only applies when phi-averaging is active.

`dtheta` and `nscatter` are coupled; one may be recomputed from the other.

`dephot` and `nephots` are coupled in integrated mode.

Do not mix `material-file` with `material-file1..3` in the same effective configuration.

If both manual `ior-re`/`ior-im` and material-file inputs are set, the higher-priority source (CLI > parameter-file > defaults) takes precedence.

For agglomerates, use `grain-geometry=spheres` with `agglom-file`.
