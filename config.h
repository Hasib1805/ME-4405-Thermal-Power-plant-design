#pragma once

#include <string>

struct CycleConfig {
    std::string fluid = "Water";
    double boilerPressure = 25e6;       // Pa
    double reheatPressure = 5e6;        // Pa
    double lpHeaterPressure = 1e6;      // Pa
    double condenserPressureBar = 0.08; // bar
    double reheatTemperatureC = 620.0;

    double turbineIsentropicEfficiency = 0.90;
    double pumpIsentropicEfficiency = 0.85;
    double generatorEfficiency = 0.985;

    double electricalPower = 250e6; // W

    double T0 = 298.15;             // K
    double P0 = 101325.0;           // Pa

    // Effective external source temperatures used in the project model.
    double sourceTemperatureBoiler = 1500.0; // K
    double sourceTemperatureReheat = 900.0;  // K

    double reheatTemperature() const { return reheatTemperatureC + 273.15; }
    double condenserPressure() const { return condenserPressureBar * 1e5; }
};
