#include "components.h"

ComponentCalc Turbine::calculate(const State& inlet, double outletPressure) const {
    ComponentCalc r;
    r.h_is = props_.h_ps(outletPressure, inlet.entropy);
    r.h_out = inlet.enthalpy - eta_*(inlet.enthalpy-r.h_is);
    r.s_out = props_.s_ph(outletPressure, r.h_out);
    r.T_out = props_.T_ph(outletPressure, r.h_out);
    r.specificWork = inlet.enthalpy-r.h_out;
    r.specificWorkIs = inlet.enthalpy-r.h_is;
    return r;
}

ComponentCalc Pump::calculate(const State& inlet, double outletPressure) const {
    ComponentCalc r;
    r.h_is = props_.h_ps(outletPressure, inlet.entropy);
    r.h_out = inlet.enthalpy + (r.h_is-inlet.enthalpy)/eta_;
    r.s_out = props_.s_ph(outletPressure, r.h_out);
    r.T_out = props_.T_ph(outletPressure, r.h_out);
    r.specificWork = r.h_out-inlet.enthalpy;
    r.specificWorkIs = r.h_is-inlet.enthalpy;
    return r;
}

State Boiler::outlet(double pressure, double temperature) const {
    return {1, pressure, props_.h_pt(pressure,temperature), props_.s_pt(pressure,temperature), temperature};
}
State Reheater::outlet(double pressure, double temperature) const {
    return {3, pressure, props_.h_pt(pressure,temperature), props_.s_pt(pressure,temperature), temperature};
}
State Condenser::outletSaturatedLiquid(double pressure) const {
    return {6, pressure, props_.h_pq(pressure,0), props_.s_pq(pressure,0), props_.T_pq(pressure,0)};
}
State OpenFeedwaterHeater::outletSaturatedLiquid() const {
    return {0, pressure_, props_.h_pq(pressure_,0), props_.s_pq(pressure_,0), props_.T_pq(pressure_,0)};
}
