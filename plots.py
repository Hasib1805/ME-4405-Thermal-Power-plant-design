"""Plotting and table-export functions for the ME 4405 project."""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI


class CyclePlotter:
    """Creates and saves report-ready PNG figures and tables."""

    def __init__(self, cycle, output_dir="plots"):
        self.cycle = cycle
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, save_path, default_name):
        if save_path is None:
            path = self.output_dir / default_name
        else:
            path = Path(save_path)
            if path.parent != Path("."):
                path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _finish(self, fig, save_path, default_name, show=False):
        path = self._path(save_path, default_name)
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Graph saved: {path.resolve()}")
        if show:
            plt.show()
        plt.close(fig)

    # ---------------------------------------------------------------
    # TABLES
    # ---------------------------------------------------------------

    def dataframe_to_png(self, df, filename, title=None,
                         fontsize=9, scale=(1.2, 1.5)):
        """Save any pandas DataFrame as a clean PNG table."""
        if df is None:
            raise ValueError("DataFrame cannot be None.")

        data = df.copy()
        # Convert values to readable strings while retaining useful precision.
        for col in data.columns:
            if np.issubdtype(data[col].dtype, np.number):
                data[col] = data[col].map(lambda x: f"{x:.4f}")

        nrows, ncols = data.shape
        fig_width = max(8, min(18, 1.6 * ncols + 2))
        fig_height = max(2.5, 0.45 * (nrows + 2))

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.axis("off")

        table = ax.table(
            cellText=data.values,
            colLabels=data.columns,
            loc="center",
            cellLoc="center",
            colLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)
        table.scale(*scale)

        if title:
            ax.set_title(title, fontsize=13, pad=16)

        path = self._path(filename, "table.png")
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print(f"Table saved: {path.resolve()}")
        plt.close(fig)
        return path

    def save_state_table(self, result, filename="baseline_state_table.png"):
        df = self.cycle.state_table(result)
        return self.dataframe_to_png(
            df, filename,
            title=(
                f"State Properties — {result.T_main_C:.0f} °C, "
                f"{result.P_cond_bar:.3f} bar"
            ),
            fontsize=9,
            scale=(1.25, 1.55),
        )

    # ---------------------------------------------------------------
    # PARAMETRIC PLOTS
    # ---------------------------------------------------------------

    def efficiency_vs_temperature(self, T_values, P_cond_bar,
                                  show=False, save_path=None):
        from optimization import RankineOptimizer
        df = RankineOptimizer(self.cycle).temperature_sweep(
            T_values, P_cond_bar
        )

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(df["T_main_C"], df["eta_percent"], marker="o")
        ax.set_xlabel("Main steam temperature [°C]")
        ax.set_ylabel("Thermal efficiency [%]")
        ax.set_title(
            f"Efficiency vs Main Steam Temperature "
            f"({P_cond_bar:.2f} bar condenser)"
        )
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self._finish(fig, save_path, "eta_vs_main_temperature.png", show)

    def efficiency_vs_condenser_pressure(self, P_values, T_main_C,
                                         show=False, save_path=None):
        from optimization import RankineOptimizer
        df = RankineOptimizer(self.cycle).condenser_pressure_sweep(
            P_values, T_main_C
        )

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(df["P_cond_bar"], df["eta_percent"], marker="o")
        ax.set_xlabel("Condenser pressure [bar]")
        ax.set_ylabel("Thermal efficiency [%]")
        ax.set_title(
            f"Efficiency vs Condenser Pressure "
            f"({T_main_C:.0f} °C main steam)"
        )
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self._finish(fig, save_path, "eta_vs_condenser_pressure.png", show)

    def efficiency_contour(self, T_values, P_values,
                           show=False, save_path=None):
        from optimization import RankineOptimizer

        df = RankineOptimizer(self.cycle).grid_search(T_values, P_values)
        pivot = df.pivot(
            index="P_cond_bar", columns="T_main_C", values="eta_percent"
        )

        X, Y = np.meshgrid(pivot.columns.values, pivot.index.values)
        Z = pivot.values

        fig, ax = plt.subplots(figsize=(8, 6))
        contour = ax.contourf(X, Y, Z, levels=20)
        fig.colorbar(contour, ax=ax, label="Thermal efficiency [%]")
        ax.set_xlabel("Main steam temperature [°C]")
        ax.set_ylabel("Condenser pressure [bar]")
        ax.set_title("Thermal Efficiency Map")
        fig.tight_layout()
        self._finish(fig, save_path, "thermal_efficiency_contour.png", show)

    # ---------------------------------------------------------------
    # EXERGY PLOT
    # ---------------------------------------------------------------

    def component_exergy_bar(self, baseline, optimum,
                             show=False, save_path=None):
        from analysis import exergy_comparison

        df = exergy_comparison(self.cycle, baseline, optimum)
        df = df.sort_values("Baseline [MW]", ascending=False)

        y = np.arange(len(df))
        h = 0.36

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(
            y - h / 2, df["Baseline [MW]"], height=h,
            label=(
                f"Baseline ({baseline.T_main_C:.0f}°C, "
                f"{baseline.P_cond_bar * 100:.0f} kPa)"
            )
        )
        ax.barh(
            y + h / 2, df["Optimum [MW]"], height=h,
            label=(
                f"Optimum ({optimum.T_main_C:.0f}°C, "
                f"{optimum.P_cond_bar * 100:.0f} kPa)"
            )
        )

        ax.set_yticks(y)
        ax.set_yticklabels(df["Component"])
        ax.set_xlabel("Exergy destroyed [MW]")
        ax.set_title("Component Exergy Destruction: Baseline vs Optimum")
        ax.grid(axis="x", linestyle="--", alpha=0.35)
        ax.legend()
        fig.tight_layout()
        self._finish(fig, save_path, "component_exergy_destruction.png", show)

    # ---------------------------------------------------------------
    # PROPERTY DIAGRAMS
    # ---------------------------------------------------------------

    def _saturation_dome(self):
        """Return saturation-liquid/vapor curves for water.

        The dome is calculated from the saturated liquid (Q=0) and
        saturated vapor (Q=1) states.  It is used on all three
        thermodynamic property diagrams: T-s, P-h and h-s.
        """
        Tcrit = PropsSI("Tcrit", "Water")
        # Start just above the triple point to avoid numerical issues.
        T_sat = np.linspace(273.16, Tcrit - 0.2, 500)

        P_sat = np.array([
            PropsSI("P", "T", T, "Q", 0, "Water") / 1e6
            for T in T_sat
        ])
        h_l = np.array([
            PropsSI("H", "T", T, "Q", 0, "Water") / 1000
            for T in T_sat
        ])
        h_v = np.array([
            PropsSI("H", "T", T, "Q", 1, "Water") / 1000
            for T in T_sat
        ])
        s_l = np.array([
            PropsSI("S", "T", T, "Q", 0, "Water") / 1000
            for T in T_sat
        ])
        s_v = np.array([
            PropsSI("S", "T", T, "Q", 1, "Water") / 1000
            for T in T_sat
        ])

        return T_sat, P_sat, h_l, h_v, s_l, s_v

    def _plot_cycle_segments(self, ax, result, xkey, ykey, label,
                             marker):
        """Plot the physical cycle path from the state dictionary."""
        s = result.states

        # Main thermodynamic path: 1-2-3-4-5-6-7-8-9-10-11-1
        main = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        x = [xkey(s[i]) for i in main]
        y = [ykey(s[i]) for i in main]
        ax.plot(
            x, y, marker=marker, linewidth=1.4, markersize=4,
            label=label
        )

        # Close the cycle: 11 -> 1.
        ax.plot(
            [xkey(s[11]), xkey(s[1])],
            [ykey(s[11]), ykey(s[1])],
            linestyle="-", linewidth=1.2
        )

    def _property_diagram(self, baseline, optimum,
                          diagram="Ts", show=False, save_path=None):
        """Create T-s, P-h or h-s diagram with saturation dome.

        The saturation dome is included in every thermodynamic property
        plot.  It is deliberately not added to efficiency/exergy plots,
        because those have different physical axes and units.
        """
        T_sat, P_sat, h_l, h_v, s_l, s_v = self._saturation_dome()

        if diagram == "Ts":
            Ts_C = T_sat - 273.15

            fig, ax = plt.subplots(figsize=(9, 6))

            # Saturation dome
            ax.plot(
                s_l, Ts_C, linewidth=1.8,
                linestyle="--", label="Saturation dome"
            )
            ax.plot(
                s_v, Ts_C, linewidth=1.8,
                linestyle="--"
            )

            # Cycle paths
            self._plot_cycle_segments(
                ax, baseline,
                lambda st: st.entropy / 1000,
                lambda st: st.temperature - 273.15,
                "Baseline", "o"
            )
            self._plot_cycle_segments(
                ax, optimum,
                lambda st: st.entropy / 1000,
                lambda st: st.temperature - 273.15,
                "Optimum", "s"
            )

            ax.set_xlabel("Entropy, s [kJ/kg·K]")
            ax.set_ylabel("Temperature, T [°C]")
            ax.set_title("T-s Diagram: Baseline vs Optimum")
            ax.grid(True, alpha=0.25)
            ax.legend()
            fig.tight_layout()
            default = "Ts_diagram_baseline_vs_optimum.png"

        elif diagram == "Ph":
            fig, ax = plt.subplots(figsize=(9, 6))

            # Saturation dome in P-h coordinates
            ax.plot(
                h_l, P_sat, linewidth=1.8,
                linestyle="--", label="Saturation dome"
            )
            ax.plot(
                h_v, P_sat, linewidth=1.8,
                linestyle="--"
            )

            self._plot_cycle_segments(
                ax, baseline,
                lambda st: st.enthalpy / 1000,
                lambda st: st.pressure / 1e6,
                "Baseline", "o"
            )
            self._plot_cycle_segments(
                ax, optimum,
                lambda st: st.enthalpy / 1000,
                lambda st: st.pressure / 1e6,
                "Optimum", "s"
            )

            ax.set_yscale("log")
            ax.set_xlabel("Specific enthalpy, h [kJ/kg]")
            ax.set_ylabel("Pressure, P [MPa]")
            ax.set_title("P-h Diagram: Baseline vs Optimum")
            ax.grid(True, alpha=0.25, which="both")
            ax.legend()
            fig.tight_layout()
            default = "Ph_diagram_baseline_vs_optimum.png"

        elif diagram == "hs":
            fig, ax = plt.subplots(figsize=(9, 6))

            # Saturation dome in h-s coordinates
            ax.plot(
                s_l, h_l, linewidth=1.8,
                linestyle="--", label="Saturation dome"
            )
            ax.plot(
                s_v, h_v, linewidth=1.8,
                linestyle="--"
            )

            self._plot_cycle_segments(
                ax, baseline,
                lambda st: st.entropy / 1000,
                lambda st: st.enthalpy / 1000,
                "Baseline", "o"
            )
            self._plot_cycle_segments(
                ax, optimum,
                lambda st: st.entropy / 1000,
                lambda st: st.enthalpy / 1000,
                "Optimum", "s"
            )

            ax.set_xlabel("Entropy, s [kJ/kg·K]")
            ax.set_ylabel("Enthalpy, h [kJ/kg]")
            ax.set_title("h-s Diagram: Baseline vs Optimum")
            ax.grid(True, alpha=0.25)
            ax.legend()
            fig.tight_layout()
            default = "hs_diagram_baseline_vs_optimum.png"

        else:
            raise ValueError("diagram must be 'Ts', 'Ph', or 'hs'")

        self._finish(fig, save_path, default, show)

    def ts_diagram(self, baseline, optimum, **kwargs):
        self._property_diagram(baseline, optimum, "Ts", **kwargs)

    def ph_diagram(self, baseline, optimum, **kwargs):
        self._property_diagram(baseline, optimum, "Ph", **kwargs)

    def hs_diagram(self, baseline, optimum, **kwargs):
        self._property_diagram(baseline, optimum, "hs", **kwargs)
