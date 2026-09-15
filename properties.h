#pragma once

#include <string>

class WaterProperties {
public:
    explicit WaterProperties(const std::string& fluid = "Water");

    double h_ps(double p, double s) const;
    double h_pt(double p, double T) const;
    double h_pq(double p, double q) const;
    double s_pt(double p, double T) const;
    double s_ph(double p, double h) const;
    double s_pq(double p, double q) const;
    double T_ph(double p, double h) const;
    double T_pq(double p, double q) const;
    double saturationPressure(double T) const;
    double saturationEnthalpy(double T, double q) const;
    double saturationEntropy(double T, double q) const;
    double criticalTemperature() const;
    double tripleTemperature() const;

private:
    std::string fluid_;
};
