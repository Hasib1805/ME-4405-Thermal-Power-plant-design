"""Main driver for the ME 4405 modular OOP Rankine-cycle project."""

import numpy as np

from cycle import Cycle
from optimization import RankineOptimizer
from analysis import compare_results, exergy_comparison
from plots import CyclePlotter


def main():
    cycle = Cycle()

    # ============================================================
    # OUTPUT FOLDER
    # ============================================================
    # All graphs and report tables are saved here automatically.
    plotter = CyclePlotter(cycle, output_dir="plots")

    # ============================================================
    # BASELINE
    # ============================================================
    baseline = cycle.calculate(T_main_C=600, P_cond_bar=0.08)

    print("\n================ BASELINE ================")
    cycle.summary(baseline)

    baseline_state_df = cycle.state_table(baseline)
    print("\n================ STATE TABLE ================")
    print(baseline_state_df.to_string(index=False))

    print("\n================ COMPONENT STREAMS ================")
    cycle.print_component_streams(baseline)

    # Save baseline state table as PNG
    plotter.save_state_table(baseline, "baseline_state_table.png")

    # ============================================================
    # FIRST LAW
    # ============================================================
    cycle1, first_df = cycle.first_law_analysis(baseline)

    print("\n================ FIRST-LAW: ENTIRE CYCLE ================")
    for k, v in cycle1.items():
        print(f"{k:35s}: {v:.4f}")

    print("\n================ FIRST-LAW: INDIVIDUAL COMPONENTS ================")
    print(first_df.to_string(index=False))

    # Save first-law table
    plotter.dataframe_to_png(
        first_df,
        "baseline_first_law_components.png",
        title="Baseline Component First-Law Analysis",
        fontsize=8,
        scale=(1.15, 1.45),
    )

    # ============================================================
    # OPTIMIZATION
    # ============================================================
    T_values = np.array([560, 580, 600, 620, 640])
    P_values = np.array([0.04, 0.06, 0.08, 0.10, 0.12])

    optimizer = RankineOptimizer(cycle)
    grid = optimizer.grid_search(T_values, P_values)
    optimum_row = optimizer.find_optimum(grid)

    optimum = cycle.calculate(
        T_main_C=float(optimum_row["T_main_C"]),
        P_cond_bar=float(optimum_row["P_cond_bar"]),
    )

    print("\n================ OPTIMUM ================")
    print(optimum_row.to_string())

    optimum_state_df = cycle.state_table(optimum)
    print("\n================ OPTIMUM STATE TABLE ================")
    print(optimum_state_df.to_string(index=False))

    print("\n================ OPTIMUM COMPONENT STREAMS ================")
    cycle.print_component_streams(optimum)

    # Save optimum state table as PNG
    plotter.save_state_table(optimum, "optimum_state_table.png")

    # Save optimization grid as PNG table
    plotter.dataframe_to_png(
        grid,
        "optimization_grid.png",
        title="Two-Parameter Sensitivity and Optimization Grid",
        fontsize=7,
        scale=(1.1, 1.35),
    )

    # ============================================================
    # SECOND LAW
    # ============================================================
    cycle2_b, second_df_b = cycle.second_law_analysis(baseline)
    cycle2_o, second_df_o = cycle.second_law_analysis(optimum)

    print("\n================ SECOND-LAW: BASELINE CYCLE ================")
    for k, v in cycle2_b.items():
        print(f"{k:35s}: {v:.4f}")

    print("\n================ SECOND-LAW: BASELINE COMPONENTS ================")
    print(second_df_b.to_string(index=False))

    print("\n================ SECOND-LAW: OPTIMUM CYCLE ================")
    for k, v in cycle2_o.items():
        print(f"{k:35s}: {v:.4f}")

    print("\n================ SECOND-LAW: OPTIMUM COMPONENTS ================")
    print(second_df_o.to_string(index=False))

    # Save second-law tables
    plotter.dataframe_to_png(
        second_df_b,
        "baseline_second_law_components.png",
        title="Baseline Component Second-Law / Exergy Analysis",
        fontsize=8,
        scale=(1.15, 1.45),
    )

    plotter.dataframe_to_png(
        second_df_o,
        "optimum_second_law_components.png",
        title="Optimum Component Second-Law / Exergy Analysis",
        fontsize=8,
        scale=(1.15, 1.45),
    )

    # ============================================================
    # COMPARISON
    # ============================================================
    comparison_df = compare_results(baseline, optimum)
    exergy_df = exergy_comparison(cycle, baseline, optimum)

    print("\n================ BASELINE VS OPTIMUM ================")
    print(comparison_df.to_string(index=False))

    print("\n================ EXERGY DESTRUCTION COMPARISON ================")
    print(exergy_df.to_string(index=False))

    # Save comparison tables
    plotter.dataframe_to_png(
        comparison_df,
        "baseline_vs_optimum_comparison.png",
        title="Baseline vs Optimum Cycle Comparison",
        fontsize=9,
        scale=(1.2, 1.5),
    )

    plotter.dataframe_to_png(
        exergy_df,
        "exergy_destruction_comparison.png",
        title="Component Exergy Destruction — Baseline vs Optimum",
        fontsize=8,
        scale=(1.15, 1.45),
    )

    # ============================================================
    # PLOTS
    # ============================================================
    plotter.efficiency_vs_temperature(T_values, 0.08)
    plotter.efficiency_vs_condenser_pressure(P_values, 600)
    plotter.efficiency_contour(T_values, P_values)
    plotter.component_exergy_bar(baseline, optimum)

    plotter.ts_diagram(baseline, optimum)
    plotter.ph_diagram(baseline, optimum)
    plotter.hs_diagram(baseline, optimum)

    print("\n============================================================")
    print("All graphs and tables have been saved in the 'plots' folder.")
    print("============================================================")


if __name__ == "__main__":
    main()
