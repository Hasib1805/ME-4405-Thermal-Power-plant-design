#include "properties.h"
#include <stdexcept>
#include "CoolProp.h"

using CoolProp::PropsSI;

WaterProperties::WaterProperties(const std::string& fluid) : fluid_(fluid) {}

double WaterProperties::h_ps(double p, double s) const { return PropsSI("H","P",p,"S",s,fluid_); }
double WaterProperties::h_pt(double p, double T) const { return PropsSI("H","P",p,"T",T,fluid_); }
double WaterProperties::h_pq(double p, double q) const { return PropsSI("H","P",p,"Q",q,fluid_); }
double WaterProperties::s_pt(double p, double T) const { return PropsSI("S","P",p,"T",T,fluid_); }
double WaterProperties::s_ph(double p, double h) const { return PropsSI("S","P",p,"H",h,fluid_); }
double WaterProperties::s_pq(double p, double q) const { return PropsSI("S","P",p,"Q",q,fluid_); }
double WaterProperties::T_ph(double p, double h) const { return PropsSI("T","P",p,"H",h,fluid_); }
double WaterProperties::T_pq(double p, double q) const { return PropsSI("T","P",p,"Q",q,fluid_); }
double WaterProperties::saturationPressure(double T) const { return PropsSI("P","T",T,"Q",0,fluid_); }
double WaterProperties::saturationEnthalpy(double T, double q) const { return PropsSI("H","T",T,"Q",q,fluid_); }
double WaterProperties::saturationEntropy(double T, double q) const { return PropsSI("S","T",T,"Q",q,fluid_); }
double WaterProperties::criticalTemperature() const { return PropsSI("Tcrit",fluid_); }
double WaterProperties::tripleTemperature() const { return PropsSI("Ttriple",fluid_); }
