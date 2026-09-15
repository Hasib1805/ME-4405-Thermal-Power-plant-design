"""Main OOP regenerative Rankine cycle model."""

from dataclasses import dataclass
import pandas as pd

from config import CycleConfig
from properties import WaterProperties
from components import (
    State, Turbine, Pump, Boiler, Reheater, Condenser,
    OpenFeedwaterHeater, Generator
)

@dataclass
class CycleResult:
    T_main_C: float
    P_cond_bar: float
    states: dict
    y_HP: float
    y_LP: float
    y_cond: float
    m_dot: float

    W_HP: float
    W_IP: float
    W_LP: float
    W_turbine: float
    W_P1: float
    W_P2: float
    W_P3: float
    W_pump: float
    W_net: float

    Q_boiler: float
    Q_reheat: float
    Q_in: float
    Q_out: float

    eta_cycle: float
    eta_electrical: float

    @property
    def h(self):
        return {i: s.enthalpy for i, s in self.states.items()}

    @property
    def s(self):
        return {i: s.entropy for i, s in self.states.items()}

    @property
    def T(self):
        return {i: s.temperature for i, s in self.states.items()}

    @property
    def P(self):
        return {i: s.pressure for i, s in self.states.items()}

class Cycle:
    """Regenerative Rankine cycle.

    HP turbine -> reheater -> IP turbine -> LP turbine
    -> condenser -> P1 -> LP open FWH -> P2 -> HP open FWH -> P3
    -> boiler.

    The Cycle owns all component objects and delegates component-level
    first- and second-law calculations to those objects.
    """

    def __init__(self, config=None):
        self.config = config or CycleConfig()
        self.props = WaterProperties(self.config.fluid)

        self.boiler = Boiler(props=self.props)
        self.hp_turbine = Turbine("HP Turbine", self.config.turbine_isentropic_efficiency, self.props)
        self.reheater = Reheater(props=self.props)
        self.ip_turbine = Turbine("IP Turbine", self.config.turbine_isentropic_efficiency, self.props)
        self.lp_turbine = Turbine("LP Turbine", self.config.turbine_isentropic_efficiency, self.props)
        self.condenser = Condenser(props=self.props)

        self.pump1 = Pump("Pump 1", self.config.pump_isentropic_efficiency, self.props)
        self.lp_fwh = OpenFeedwaterHeater("LP Open FWH", self.config.lp_heater_pressure, self.props)
        self.pump2 = Pump("Pump 2", self.config.pump_isentropic_efficiency, self.props)
        self.hp_fwh = OpenFeedwaterHeater("HP Open FWH", self.config.reheat_pressure, self.props)
        self.pump3 = Pump("Pump 3", self.config.pump_isentropic_efficiency, self.props)
        self.generator = Generator(self.config.generator_efficiency)

        self.last_result = None

    def calculate(self, T_main_C=600.0, P_cond_bar=None):
        if P_cond_bar is None:
            P_cond_bar = self.config.condenser_pressure_bar

        P1 = self.config.boiler_pressure
        P2 = self.config.reheat_pressure
        P4 = self.config.lp_heater_pressure
        P5 = P_cond_bar * 1e5
        T1 = T_main_C + 273.15

        # 1: boiler outlet / HP turbine inlet
        h1, s1 = self.boiler.outlet(P1, T1)

        # 2: HP turbine outlet / extraction
        r2 = self.hp_turbine.calculate(State(1, P1, h1, s1, T1), P2)
        h2, s2, T2 = r2["h_out"], r2["s_out"], r2["T_out"]

        # 3: reheater outlet / IP turbine inlet
        h3, s3 = self.reheater.outlet(P2, self.config.reheat_temperature)
        T3 = self.config.reheat_temperature

        # 4: IP turbine outlet / LP turbine inlet + LP extraction
        r4 = self.ip_turbine.calculate(State(3, P2, h3, s3, T3), P4)
        h4, s4, T4 = r4["h_out"], r4["s_out"], r4["T_out"]

        # 5: LP turbine exhaust
        r5 = self.lp_turbine.calculate(State(4, P4, h4, s4, T4), P5)
        h5, s5, T5 = r5["h_out"], r5["s_out"], r5["T_out"]

        # 6: condenser outlet
        h6, s6, T6 = self.condenser.outlet_saturated_liquid(P5)

        # 7: Pump 1 outlet
        r7 = self.pump1.calculate(State(6, P5, h6, s6, T6), P4)
        h7, s7, T7 = r7["h_out"], r7["s_out"], r7["T_out"]

        # 8: LP open FWH outlet
        h8, s8, T8 = self.lp_fwh.outlet_saturated_liquid()

        # 9: Pump 2 outlet
        r9 = self.pump2.calculate(State(8, P4, h8, s8, T8), P2)
        h9, s9, T9 = r9["h_out"], r9["s_out"], r9["T_out"]

        # 10: HP open FWH outlet
        h10, s10, T10 = self.hp_fwh.outlet_saturated_liquid()

        # 11: Pump 3 outlet
        r11 = self.pump3.calculate(State(10, P2, h10, s10, T10), P1)
        h11, s11, T11 = r11["h_out"], r11["s_out"], r11["T_out"]

        # Extraction fractions
        y_HP = (h10 - h9) / (h2 - h9)
        y_LP = ((1.0 - y_HP) * (h8 - h7)) / (h4 - h7)
        y_cond = 1.0 - y_HP - y_LP

        # Specific work / heat [J/kg of main flow]
        W_HP = h1 - h2
        W_IP = (1.0 - y_HP) * (h3 - h4)
        W_LP = y_cond * (h4 - h5)
        W_turbine = W_HP + W_IP + W_LP

        W_P1 = y_cond * (h7 - h6)
        W_P2 = (1.0 - y_HP) * (h9 - h8)
        W_P3 = h11 - h10
        W_pump = W_P1 + W_P2 + W_P3

        W_net = W_turbine - W_pump

        Q_boiler = h1 - h11
        Q_reheat = (1.0 - y_HP) * (h3 - h2)
        Q_in = Q_boiler + Q_reheat
        Q_out = y_cond * (h5 - h6)

        eta_cycle = W_net / Q_in
        eta_electrical = eta_cycle * self.config.generator_efficiency

        m_dot = self.config.electrical_power / (
            self.config.generator_efficiency * W_net
        )

        states = {
            1: State(1, P1, h1, s1, T1),
            2: State(2, P2, h2, s2, T2),
            3: State(3, P2, h3, s3, T3),
            4: State(4, P4, h4, s4, T4),
            5: State(5, P5, h5, s5, T5),
            6: State(6, P5, h6, s6, T6),
            7: State(7, P4, h7, s7, T7),
            8: State(8, P4, h8, s8, T8),
            9: State(9, P2, h9, s9, T9),
            10: State(10, P2, h10, s10, T10),
            11: State(11, P1, h11, s11, T11),
        }

        result = CycleResult(
            T_main_C=T_main_C, P_cond_bar=P_cond_bar, states=states,
            y_HP=y_HP, y_LP=y_LP, y_cond=y_cond, m_dot=m_dot,
            W_HP=W_HP, W_IP=W_IP, W_LP=W_LP, W_turbine=W_turbine,
            W_P1=W_P1, W_P2=W_P2, W_P3=W_P3, W_pump=W_pump,
            W_net=W_net, Q_boiler=Q_boiler, Q_reheat=Q_reheat,
            Q_in=Q_in, Q_out=Q_out, eta_cycle=eta_cycle,
            eta_electrical=eta_electrical
        )

        self.last_result = result
        return result

    # ---------------------------- flow rates ----------------------------

    def mass_flows(self, result=None):
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        m = result.m_dot
        return {
            "HP turbine": m,
            "HP FWH extraction": result.y_HP * m,
            "IP turbine": (1 - result.y_HP) * m,
            "LP FWH extraction": result.y_LP * m,
            "LP turbine": result.y_cond * m,
            "Condenser": result.y_cond * m,
            "Pump 1": result.y_cond * m,
            "LP FWH": (1 - result.y_HP) * m,
            "Pump 2": (1 - result.y_HP) * m,
            "HP FWH": m,
            "Pump 3": m,
            "Boiler": m,
            "Reheater": (1 - result.y_HP) * m,
            "Generator shaft": m,
        }

    # ---------------------------- state table ----------------------------

    def state_table(self, result=None):
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        rows = []
        for i in range(1, 12):
            st = result.states[i]
            rows.append({
                "State": i,
                "Pressure [MPa]": st.pressure / 1e6,
                "Temperature [°C]": st.temperature - 273.15,
                "Enthalpy [kJ/kg]": st.enthalpy / 1000,
                "Entropy [kJ/kg-K]": st.entropy / 1000,
            })
        return pd.DataFrame(rows)

    # ---------------------------- component streams ----------------------------

    def component_streams(self, result=None):
        """Return inlet/outlet states and mass flow for every component."""
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        s = result.states
        m = result.m_dot
        yH, yL, yc = result.y_HP, result.y_LP, result.y_cond

        return {
            "Boiler": {
                "inlets": [(s[11], m)],
                "outlets": [(s[1], m)]
            },
            "HP Turbine": {
                "inlets": [(s[1], m)],
                "outlets": [(s[2], m)]
            },
            "Reheater": {
                "inlets": [(s[2], (1-yH)*m)],
                "outlets": [(s[3], (1-yH)*m)]
            },
            "IP Turbine": {
                "inlets": [(s[3], (1-yH)*m)],
                "outlets": [(s[4], (1-yH)*m)]
            },
            "LP Turbine": {
                "inlets": [(s[4], yc*m)],
                "outlets": [(s[5], yc*m)]
            },
            "Condenser": {
                "inlets": [(s[5], yc*m)],
                "outlets": [(s[6], yc*m)]
            },
            "Pump 1": {
                "inlets": [(s[6], yc*m)],
                "outlets": [(s[7], yc*m)]
            },
            "LP Open FWH": {
                "inlets": [(s[4], yL*m), (s[7], yc*m)],
                "outlets": [(s[8], (1-yH)*m)]
            },
            "Pump 2": {
                "inlets": [(s[8], (1-yH)*m)],
                "outlets": [(s[9], (1-yH)*m)]
            },
            "HP Open FWH": {
                "inlets": [(s[2], yH*m), (s[9], (1-yH)*m)],
                "outlets": [(s[10], m)]
            },
            "Pump 3": {
                "inlets": [(s[10], m)],
                "outlets": [(s[11], m)]
            },
        }

    def print_component_streams(self, result=None):
        """Print each component's mass flow and inlet/outlet state data."""
        result = result or self.last_result
        streams = self.component_streams(result)

        def show_state(label, st, mdot):
            print(f"  {label} - State {st.number}")
            print(f"    Mass flow  = {mdot:.3f} kg/s")
            print(f"    Pressure   = {st.pressure/1e6:.5f} MPa")
            print(f"    Temperature= {st.temperature-273.15:.2f} °C")
            print(f"    Enthalpy   = {st.enthalpy/1000:.3f} kJ/kg")
            print(f"    Entropy    = {st.entropy/1000:.4f} kJ/kg-K")

        for name, data in streams.items():
            print("\n" + "="*65)
            print(name.upper())
            print("="*65)
            for st, mdot in data["inlets"]:
                show_state("Inlet", st, mdot)
            for st, mdot in data["outlets"]:
                show_state("Outlet", st, mdot)

    # ---------------------------- exergy ----------------------------

    def flow_exergy(self, state, T0=None, P0=None):
        T0 = T0 if T0 is not None else self.config.T0
        P0 = P0 if P0 is not None else self.config.P0
        h0 = self.props.h_pt(P0, T0)
        s0 = self.props.s_pt(P0, T0)
        return (state.enthalpy - h0) - T0 * (state.entropy - s0)

    # ---------------------------- first law ----------------------------

    def first_law_components(self, result=None):
        """Component-wise first-law table in MW.

        W is positive for power produced by a component and negative for
        power consumed. Q is positive when heat enters the component.
        """
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        s = result.states
        m = result.m_dot
        yH, yL, yc = result.y_HP, result.y_LP, result.y_cond

        rows = []

        # Boiler
        Q = m*(s[1].enthalpy-s[11].enthalpy)
        rows.append(("Boiler", m, Q, 0.0, Q, 0.0))

        # HP turbine
        W = m*(s[1].enthalpy-s[2].enthalpy)
        rows.append(("HP Turbine", m, 0.0, W, 0.0, 0.0))

        # Reheater
        mr = (1-yH)*m
        Q = mr*(s[3].enthalpy-s[2].enthalpy)
        rows.append(("Reheater", mr, Q, 0.0, Q, 0.0))

        # IP turbine
        W = mr*(s[3].enthalpy-s[4].enthalpy)
        rows.append(("IP Turbine", mr, 0.0, W, 0.0, 0.0))

        # LP turbine
        mlp = yc*m
        W = mlp*(s[4].enthalpy-s[5].enthalpy)
        rows.append(("LP Turbine", mlp, 0.0, W, 0.0, 0.0))

        # Condenser
        Q = mlp*(s[6].enthalpy-s[5].enthalpy)
        rows.append(("Condenser", mlp, Q, 0.0, Q, 0.0))

        # Pump 1
        W = -mlp*(s[7].enthalpy-s[6].enthalpy)
        rows.append(("Pump 1", mlp, 0.0, W, 0.0, 0.0))

        # LP FWH
        mLPex = yL*m
        mLPin = yc*m
        mLPout = (1-yH)*m
        residual = mLPex*s[4].enthalpy + mLPin*s[7].enthalpy - mLPout*s[8].enthalpy
        rows.append(("LP Open FWH", mLPout, 0.0, 0.0, 0.0, residual))

        # Pump 2
        m2 = (1-yH)*m
        W = -m2*(s[9].enthalpy-s[8].enthalpy)
        rows.append(("Pump 2", m2, 0.0, W, 0.0, 0.0))

        # HP FWH
        mHPex = yH*m
        residual = mHPex*s[2].enthalpy + m2*s[9].enthalpy - m*s[10].enthalpy
        rows.append(("HP Open FWH", m, 0.0, 0.0, 0.0, residual))

        # Pump 3
        W = -m*(s[11].enthalpy-s[10].enthalpy)
        rows.append(("Pump 3", m, 0.0, W, 0.0, 0.0))

        # Generator
        shaft = m*result.W_turbine
        gen = self.generator.first_law(shaft)
        rows.append(("Generator", m, 0.0, -gen["loss"], gen["electric_power"], 0.0))

        df = pd.DataFrame(rows, columns=[
            "Component", "Mass flow [kg/s]", "Q [W]", "W [W]",
            "Net energy transfer [W]", "Energy balance residual [W]"
        ])
        df["Q [MW]"] = df["Q [W]"]/1e6
        df["W [MW]"] = df["W [W]"]/1e6
        df["Net energy transfer [MW]"] = df["Net energy transfer [W]"]/1e6
        df["Energy balance residual [MW]"] = df["Energy balance residual [W]"]/1e6
        return df[[
            "Component", "Mass flow [kg/s]", "Q [MW]", "W [MW]",
            "Net energy transfer [MW]", "Energy balance residual [MW]"
        ]]

    def first_law_analysis(self, result=None):
        """Whole-cycle first-law analysis plus component table."""
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        component_df = self.first_law_components(result)

        cycle = {
            "T_main [°C]": result.T_main_C,
            "P_cond [bar]": result.P_cond_bar,
            "Q_boiler [MW]": result.m_dot*result.Q_boiler/1e6,
            "Q_reheat [MW]": result.m_dot*result.Q_reheat/1e6,
            "Q_in [MW]": result.m_dot*result.Q_in/1e6,
            "Q_out [MW]": result.m_dot*result.Q_out/1e6,
            "W_HP [MW]": result.m_dot*result.W_HP/1e6,
            "W_IP [MW]": result.m_dot*result.W_IP/1e6,
            "W_LP [MW]": result.m_dot*result.W_LP/1e6,
            "W_turbine [MW]": result.m_dot*result.W_turbine/1e6,
            "W_P1 [MW]": result.m_dot*result.W_P1/1e6,
            "W_P2 [MW]": result.m_dot*result.W_P2/1e6,
            "W_P3 [MW]": result.m_dot*result.W_P3/1e6,
            "W_pump [MW]": result.m_dot*result.W_pump/1e6,
            "W_net [MW]": result.m_dot*result.W_net/1e6,
            "Thermal efficiency [%]": result.eta_cycle*100,
            "Electrical efficiency [%]": result.eta_electrical*100,
            "Electrical output [MW]": self.config.electrical_power/1e6,
        }
        return cycle, component_df

    # ---------------------------- second law ----------------------------

    def second_law_components(self, result=None):
        """Component-wise exergy destruction table in MW."""
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        s = result.states
        m = result.m_dot
        yH, yL, yc = result.y_HP, result.y_LP, result.y_cond
        T0 = self.config.T0

        e = {i: self.flow_exergy(s[i]) for i in s}

        rows = []

        # Boiler: ExQ + Ex_in - Ex_out
        Qb = m*(s[1].enthalpy-s[11].enthalpy)
        ExQb = Qb*(1-T0/self.config.source_temperature_boiler)
        ExD = ExQb + m*e[11] - m*e[1]
        rows.append(("Boiler", m, ExQb, ExD))

        # HP turbine
        md = m
        ExD = md*T0*(s[2].entropy-s[1].entropy)
        rows.append(("HP Turbine", md, 0.0, ExD))

        # Reheater
        mr = (1-yH)*m
        Qr = mr*(s[3].enthalpy-s[2].enthalpy)
        ExQr = Qr*(1-T0/self.config.source_temperature_reheat)
        ExD = ExQr + mr*e[2] - mr*e[3]
        rows.append(("Reheater", mr, ExQr, ExD))

        # IP turbine
        ExD = mr*T0*(s[4].entropy-s[3].entropy)
        rows.append(("IP Turbine", mr, 0.0, ExD))

        # LP turbine
        mlp = yc*m
        ExD = mlp*T0*(s[5].entropy-s[4].entropy)
        rows.append(("LP Turbine", mlp, 0.0, ExD))

        # Condenser: Qout is rejected to ambient at T0 in this model
        Qout = mlp*(s[6].enthalpy-s[5].enthalpy)
        Sgen = mlp*(s[6].entropy-s[5].entropy) - Qout/T0
        ExD = T0*Sgen
        rows.append(("Condenser", mlp, 0.0, ExD))

        # Pumps
        ExD = mlp*T0*(s[7].entropy-s[6].entropy)
        rows.append(("Pump 1", mlp, 0.0, ExD))

        mLPex = yL*m
        mLPin = yc*m
        mLPout = (1-yH)*m
        ExD = mLPex*e[4] + mLPin*e[7] - mLPout*e[8]
        rows.append(("LP Open FWH", mLPout, 0.0, ExD))

        m2 = (1-yH)*m
        ExD = m2*T0*(s[9].entropy-s[8].entropy)
        rows.append(("Pump 2", m2, 0.0, ExD))

        mHPex = yH*m
        ExD = mHPex*e[2] + m2*e[9] - m*e[10]
        rows.append(("HP Open FWH", m, 0.0, ExD))

        ExD = m*T0*(s[11].entropy-s[10].entropy)
        rows.append(("Pump 3", m, 0.0, ExD))

        # Generator: turbine shaft power -> electrical power
        shaft = m*result.W_turbine
        electric = self.config.electrical_power
        ExD = shaft - electric
        rows.append(("Generator", m, 0.0, ExD))

        df = pd.DataFrame(rows, columns=[
            "Component", "Mass flow [kg/s]",
            "Exergy supplied [W]", "Exergy destruction [W]"
        ])
        df["Exergy supplied [MW]"] = df["Exergy supplied [W]"]/1e6
        df["Exergy destruction [MW]"] = df["Exergy destruction [W]"]/1e6
        return df[[
            "Component", "Mass flow [kg/s]",
            "Exergy supplied [MW]", "Exergy destruction [MW]"
        ]]

    def second_law_analysis(self, result=None):
        """Whole-cycle second-law analysis plus component exergy table."""
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        component_df = self.second_law_components(result)

        m = result.m_dot
        Qb = m*result.Q_boiler
        Qr = m*result.Q_reheat

        ExQ_boiler = Qb*(1-self.config.T0/self.config.source_temperature_boiler)
        ExQ_reheat = Qr*(1-self.config.T0/self.config.source_temperature_reheat)
        ExQ_total = ExQ_boiler + ExQ_reheat

        component_total = component_df["Exergy destruction [MW]"].sum()

        cycle = {
            "ExQ_boiler [MW]": ExQ_boiler/1e6,
            "ExQ_reheat [MW]": ExQ_reheat/1e6,
            "ExQ_total [MW]": ExQ_total/1e6,
            "Total exergy destruction [MW]": component_total,
            "Electrical output [MW]": self.config.electrical_power/1e6,
            "Second-law efficiency [%]": (
                self.config.electrical_power/ExQ_total*100
            ),
        }
        return cycle, component_df

    # ---------------------------- summary ----------------------------

    def summary(self, result=None):
        result = result or self.last_result
        if result is None:
            raise ValueError("Calculate the cycle first.")

        print("========== CYCLE SUMMARY ==========")
        print(f"Main steam temperature = {result.T_main_C:.1f} °C")
        print(f"Condenser pressure     = {result.P_cond_bar:.4f} bar")
        print(f"Thermal efficiency     = {result.eta_cycle*100:.3f} %")
        print(f"Electrical efficiency  = {result.eta_electrical*100:.3f} %")
        print(f"Net specific work      = {result.W_net/1000:.3f} kJ/kg")
        print(f"Main steam flow        = {result.m_dot:.3f} kg/s")
        print(f"HP extraction fraction = {result.y_HP:.5f}")
        print(f"LP extraction fraction = {result.y_LP:.5f}")
        print(f"Condenser fraction     = {result.y_cond:.5f}")
