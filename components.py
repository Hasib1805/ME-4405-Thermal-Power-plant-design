"""Object-oriented thermodynamic component classes."""

from dataclasses import dataclass
from properties import WaterProperties

@dataclass
class State:
    number: int
    pressure: float
    enthalpy: float
    entropy: float
    temperature: float

class Component:
    def __init__(self, name):
        self.name = name

class Turbine(Component):
    def __init__(self, name, efficiency, props=None):
        super().__init__(name)
        self.efficiency = efficiency
        self.props = props or WaterProperties()

    def calculate(self, inlet: State, outlet_pressure: float):
        h_is = self.props.h_ps(outlet_pressure, inlet.entropy)
        h_out = inlet.enthalpy - self.efficiency * (inlet.enthalpy - h_is)
        s_out = self.props.s_ph(outlet_pressure, h_out)
        T_out = self.props.T_ph(outlet_pressure, h_out)
        return {
            "h_out": h_out,
            "s_out": s_out,
            "T_out": T_out,
            "h_is": h_is,
            "specific_work": inlet.enthalpy - h_out,
            "specific_work_is": inlet.enthalpy - h_is,
        }

    def first_law(self, inlet, outlet, mass_flow):
        return {
            "Q": 0.0,
            "W": mass_flow * (inlet.enthalpy - outlet.enthalpy),
            "mass_flow": mass_flow,
        }

    def second_law(self, inlet, outlet, mass_flow, T0):
        return mass_flow * T0 * (outlet.entropy - inlet.entropy)

class Pump(Component):
    def __init__(self, name, efficiency, props=None):
        super().__init__(name)
        self.efficiency = efficiency
        self.props = props or WaterProperties()

    def calculate(self, inlet: State, outlet_pressure: float):
        h_is = self.props.h_ps(outlet_pressure, inlet.entropy)
        h_out = inlet.enthalpy + (h_is - inlet.enthalpy) / self.efficiency
        s_out = self.props.s_ph(outlet_pressure, h_out)
        T_out = self.props.T_ph(outlet_pressure, h_out)
        return {
            "h_out": h_out,
            "s_out": s_out,
            "T_out": T_out,
            "h_is": h_is,
            "specific_work": h_out - inlet.enthalpy,
            "specific_work_is": h_is - inlet.enthalpy,
        }

    def first_law(self, inlet, outlet, mass_flow):
        return {
            "Q": 0.0,
            "W": -mass_flow * (outlet.enthalpy - inlet.enthalpy),
            "mass_flow": mass_flow,
        }

    def second_law(self, inlet, outlet, mass_flow, T0):
        return mass_flow * T0 * (outlet.entropy - inlet.entropy)

class Boiler(Component):
    def __init__(self, name="Boiler", props=None):
        super().__init__(name)
        self.props = props or WaterProperties()

    def outlet(self, pressure, temperature):
        h = self.props.h_pt(pressure, temperature)
        s = self.props.s_pt(pressure, temperature)
        return h, s

    def first_law(self, inlet, outlet, mass_flow):
        Q = mass_flow * (outlet.enthalpy - inlet.enthalpy)
        return {"Q": Q, "W": 0.0, "mass_flow": mass_flow}

class Reheater(Component):
    def __init__(self, name="Reheater", props=None):
        super().__init__(name)
        self.props = props or WaterProperties()

    def outlet(self, pressure, temperature):
        h = self.props.h_pt(pressure, temperature)
        s = self.props.s_pt(pressure, temperature)
        return h, s

    def first_law(self, inlet, outlet, mass_flow):
        Q = mass_flow * (outlet.enthalpy - inlet.enthalpy)
        return {"Q": Q, "W": 0.0, "mass_flow": mass_flow}

class Condenser(Component):
    def __init__(self, name="Condenser", props=None):
        super().__init__(name)
        self.props = props or WaterProperties()

    def outlet_saturated_liquid(self, pressure):
        h = self.props.h_pq(pressure, 0)
        s = self.props.s_pq(pressure, 0)
        T = self.props.T_pq(pressure, 0)
        return h, s, T

    def first_law(self, inlet, outlet, mass_flow):
        Q = mass_flow * (outlet.enthalpy - inlet.enthalpy)
        return {"Q": Q, "W": 0.0, "mass_flow": mass_flow}

class OpenFeedwaterHeater(Component):
    """Ideal direct-contact/open feedwater heater."""

    def __init__(self, name, pressure, props=None):
        super().__init__(name)
        self.pressure = pressure
        self.props = props or WaterProperties()

    def outlet_saturated_liquid(self):
        h = self.props.h_pq(self.pressure, 0)
        s = self.props.s_pq(self.pressure, 0)
        T = self.props.T_pq(self.pressure, 0)
        return h, s, T

    def first_law(self, inlet1, m1, inlet2, m2, outlet, m_out):
        energy_in = m1 * inlet1.enthalpy + m2 * inlet2.enthalpy
        energy_out = m_out * outlet.enthalpy
        return {
            "Q": 0.0,
            "W": 0.0,
            "mass_flow": m_out,
            "energy_balance_residual": energy_in - energy_out,
        }

class ClosedFeedwaterHeater(Component):
    """Generic closed/surface feedwater-heater class for future expansion."""

    def __init__(self, name, pressure, props=None):
        super().__init__(name)
        self.pressure = pressure
        self.props = props or WaterProperties()

    def first_law(self, hot_in, hot_out, cold_in, cold_out,
                  m_hot, m_cold):
        # Heat gained by feedwater; positive Q_to_cold is reported.
        Q_to_cold = m_cold * (cold_out.enthalpy - cold_in.enthalpy)
        Q_from_hot = m_hot * (hot_in.enthalpy - hot_out.enthalpy)
        return {
            "Q_to_cold": Q_to_cold,
            "Q_from_hot": Q_from_hot,
            "energy_balance_residual": Q_from_hot - Q_to_cold,
        }

class Generator(Component):
    def __init__(self, efficiency):
        super().__init__("Generator")
        self.efficiency = efficiency

    def first_law(self, shaft_power):
        electric_power = self.efficiency * shaft_power
        loss = shaft_power - electric_power
        return {
            "shaft_power": shaft_power,
            "electric_power": electric_power,
            "loss": loss,
        }
