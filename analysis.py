"""Higher-level reporting helpers."""

import pandas as pd

def compare_results(baseline, optimum):
    rows = [
        ("Main steam temperature [°C]", baseline.T_main_C, optimum.T_main_C),
        ("Condenser pressure [bar]", baseline.P_cond_bar, optimum.P_cond_bar),
        ("Thermal efficiency [%]", baseline.eta_cycle*100, optimum.eta_cycle*100),
        ("Electrical efficiency [%]", baseline.eta_electrical*100, optimum.eta_electrical*100),
        ("Net work [kJ/kg]", baseline.W_net/1000, optimum.W_net/1000),
        ("Mass flow [kg/s]", baseline.m_dot, optimum.m_dot),
        ("HP extraction fraction", baseline.y_HP, optimum.y_HP),
        ("LP extraction fraction", baseline.y_LP, optimum.y_LP),
        ("Condenser fraction", baseline.y_cond, optimum.y_cond),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Baseline", "Optimum"])

def exergy_comparison(cycle, baseline, optimum):
    _, bdf = cycle.second_law_analysis(baseline)
    _, odf = cycle.second_law_analysis(optimum)

    b = bdf.set_index("Component")
    o = odf.set_index("Component")

    names = b.index.tolist()
    rows = []
    for name in names:
        rows.append({
            "Component": name,
            "Baseline [MW]": b.loc[name, "Exergy destruction [MW]"],
            "Optimum [MW]": o.loc[name, "Exergy destruction [MW]"],
        })
    return pd.DataFrame(rows)
