# ME 4405 Powerplant Design Project — C++ OOP Version

This is a C++17 object-oriented conversion of the modular ME 4405 Rankine-cycle project.

## Structure

- `config.h` — project constants and assumptions
- `properties.h/.cpp` — CoolProp water/steam property wrapper
- `components.h/.cpp` — Turbine, Pump, Boiler, Reheater, Condenser, FWH and Generator classes
- `cycle.h/.cpp` — complete regenerative Rankine cycle and state calculations
- `optimization.h/.cpp` — two-parameter grid search and optimum selection
- `analysis.h/.cpp` — baseline/optimum comparisons
- `plotter.h/.cpp` — PNG graph/table generation using gnuplot
- `main.cpp` — main executable
- `plots/` — generated PNGs and plotting data/scripts

## External dependencies

### 1. CoolProp C++ library

The cycle calculations use CoolProp's C++ API. Install/build CoolProp and make its headers and library available to CMake.

The source wrapper uses the standard API:

```cpp
#include "CoolProp.h"
CoolProp::PropsSI("H", "P", pressure, "T", temperature, "Water");
```

### 2. gnuplot

The calculations and optimization are pure C++. Gnuplot is only used as an external plotting executable to turn generated data into PNG files. Make sure `gnuplot` is in your system PATH.

## Build with CMake

From the project directory:

```bash
cmake -S . -B build -DCOOLPROP_ROOT=C:/path/to/CoolProp
cmake --build build --config Release
```

Then run:

```bash
build/Release/ME4405_Rankine.exe
```

On MinGW or Linux the executable location may differ.

## What the program does

The program automatically:

1. Calculates the baseline cycle at 600 °C and 0.08 bar.
2. Prints the complete state table.
3. Prints mass flow rates and component inlet/outlet states.
4. Performs whole-cycle and component-level first-law analysis.
5. Performs whole-cycle and component-level second-law/exergy analysis.
6. Performs the 5 × 5 optimization over main steam temperature and condenser pressure.
7. Recalculates the optimum cycle.
8. Compares baseline and optimum results.
9. Saves efficiency, optimization, exergy and thermodynamic property plots.
10. Saves the important tables as PNG files.

The T-s, P-h and h-s diagrams include the water saturation dome.

## Generated PNGs

The `plots` folder will contain files such as:

- `baseline_state_table.png`
- `optimum_state_table.png`
- `baseline_first_law_components.png`
- `baseline_second_law_components.png`
- `optimum_second_law_components.png`
- `baseline_vs_optimum_comparison.png`
- `exergy_destruction_comparison.png`
- `optimization_grid.png`
- `eta_vs_main_temperature.png`
- `eta_vs_condenser_pressure.png`
- `thermal_efficiency_contour.png`
- `component_exergy_destruction.png`
- `Ts_diagram_baseline_vs_optimum.png`
- `Ph_diagram_baseline_vs_optimum.png`
- `hs_diagram_baseline_vs_optimum.png`

## Important

The numerical model follows the same cycle equations and assumptions as the previous modular Python version. CoolProp and gnuplot are external libraries/programs; they are not reimplemented in this project.
