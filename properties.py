"""CoolProp wrapper.

Units:
    pressure: Pa
    temperature: K
    enthalpy: J/kg
    entropy: J/(kg K)
"""
from CoolProp.CoolProp import PropsSI

class WaterProperties:
    def __init__(self, fluid="Water"):
        self.fluid = fluid

    def h_ps(self, p, s):
        return PropsSI("H", "P", p, "S", s, self.fluid)

    def h_pt(self, p, T):
        return PropsSI("H", "P", p, "T", T, self.fluid)

    def h_pq(self, p, q):
        return PropsSI("H", "P", p, "Q", q, self.fluid)

    def s_pt(self, p, T):
        return PropsSI("S", "P", p, "T", T, self.fluid)

    def s_ph(self, p, h):
        return PropsSI("S", "P", p, "H", h, self.fluid)

    def s_pq(self, p, q):
        return PropsSI("S", "P", p, "Q", q, self.fluid)

    def T_ph(self, p, h):
        return PropsSI("T", "P", p, "H", h, self.fluid)

    def T_pq(self, p, q):
        return PropsSI("T", "P", p, "Q", q, self.fluid)

    def critical_temperature(self):
        return PropsSI("Tcrit", self.fluid)
