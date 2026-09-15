#pragma once

#include "properties.h"
#include <string>

struct State {
    int number{};
    double pressure{};    // Pa
    double enthalpy{};    // J/kg
    double entropy{};     // J/kg-K
    double temperature{}; // K
};

struct ComponentCalc {
    double h_out{}, s_out{}, T_out{}, h_is{};
    double specificWork{}, specificWorkIs{};
};

class Component {
public:
    explicit Component(std::string name) : name_(std::move(name)) {}
    virtual ~Component() = default;
    const std::string& name() const { return name_; }
protected:
    std::string name_;
};

class Turbine : public Component {
public:
    Turbine(const std::string& name, double eta, const WaterProperties& props)
        : Component(name), eta_(eta), props_(props) {}
    ComponentCalc calculate(const State& inlet, double outletPressure) const;
private:
    double eta_; const WaterProperties& props_;
};

class Pump : public Component {
public:
    Pump(const std::string& name, double eta, const WaterProperties& props)
        : Component(name), eta_(eta), props_(props) {}
    ComponentCalc calculate(const State& inlet, double outletPressure) const;
private:
    double eta_; const WaterProperties& props_;
};

class Boiler : public Component {
public:
    Boiler(const WaterProperties& p) : Component("Boiler"), props_(p) {}
    State outlet(double pressure, double temperature) const;
private: const WaterProperties& props_;
};

class Reheater : public Component {
public:
    Reheater(const WaterProperties& p) : Component("Reheater"), props_(p) {}
    State outlet(double pressure, double temperature) const;
private: const WaterProperties& props_;
};

class Condenser : public Component {
public:
    Condenser(const WaterProperties& p) : Component("Condenser"), props_(p) {}
    State outletSaturatedLiquid(double pressure) const;
private: const WaterProperties& props_;
};

class OpenFeedwaterHeater : public Component {
public:
    OpenFeedwaterHeater(const std::string& name, double pressure, const WaterProperties& p)
        : Component(name), pressure_(pressure), props_(p) {}
    State outletSaturatedLiquid() const;
private: double pressure_; const WaterProperties& props_;
};

class Generator : public Component {
public:
    explicit Generator(double eta) : Component("Generator"), eta_(eta) {}
    double electricPower(double shaftPower) const { return eta_ * shaftPower; }
    double loss(double shaftPower) const { return shaftPower - electricPower(shaftPower); }
private: double eta_;
};
