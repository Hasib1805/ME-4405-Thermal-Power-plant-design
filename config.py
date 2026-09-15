"""Project-wide constants for the ME 4405 Rankine-cycle model."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CycleConfig:
    fluid: str = "Water"

    # Pressures [Pa]
    boiler_pressure: float = 25e6
    reheat_pressure: float = 5e6
    lp_heater_pressure: float = 1e6
    condenser_pressure_bar: float = 0.08

    # Temperatures
    reheat_temperature_C: float = 620.0

    # Component efficiencies
    turbine_isentropic_efficiency: float = 0.90
    pump_isentropic_efficiency: float = 0.85
    generator_efficiency: float = 0.985

    # Electrical design target [W]
    electrical_power: float = 250e6

    # Dead state
    T0: float = 298.15
    P0: float = 101325.0

    # Effective external source temperatures used for exergy of heat input
    source_temperature_boiler: float = 1500.0
    source_temperature_reheat: float = 900.0

    @property
    def reheat_temperature(self):
        return self.reheat_temperature_C + 273.15

    @property
    def condenser_pressure(self):
        return self.condenser_pressure_bar * 1e5
