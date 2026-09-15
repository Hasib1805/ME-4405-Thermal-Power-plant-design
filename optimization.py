"""Sensitivity study and grid-search optimization."""

import pandas as pd

class RankineOptimizer:
    def __init__(self, cycle):
        self.cycle = cycle

    def grid_search(self, T_values, P_cond_values):
        rows = []
        for T in T_values:
            for P in P_cond_values:
                r = self.cycle.calculate(float(T), float(P))
                rows.append({
                    "T_main_C": float(T),
                    "P_cond_bar": float(P),
                    "eta": r.eta_cycle,
                    "eta_percent": r.eta_cycle*100,
                    "W_net": r.W_net,
                    "m_dot": r.m_dot,
                    "y_HP": r.y_HP,
                    "y_LP": r.y_LP,
                    "y_cond": r.y_cond,
                })
        return pd.DataFrame(rows)

    def find_optimum(self, df):
        return df.loc[df["eta"].idxmax()]

    def temperature_sweep(self, T_values, P_cond_bar):
        rows = []
        for T in T_values:
            r = self.cycle.calculate(float(T), float(P_cond_bar))
            rows.append({"T_main_C": float(T), "eta_percent": r.eta_cycle*100})
        return pd.DataFrame(rows)

    def condenser_pressure_sweep(self, P_values, T_main_C):
        rows = []
        for P in P_values:
            r = self.cycle.calculate(float(T_main_C), float(P))
            rows.append({"P_cond_bar": float(P), "eta_percent": r.eta_cycle*100})
        return pd.DataFrame(rows)
