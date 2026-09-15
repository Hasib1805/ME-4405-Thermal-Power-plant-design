#pragma once

#include "config.h"
#include "components.h"
#include <array>
#include <string>
#include <vector>
#include <map>

struct CycleResult {
    double T_main_C{}, P_cond_bar{};
    std::array<State,12> states{}; // 1..11 used
    double y_HP{}, y_LP{}, y_cond{}, m_dot{};
    double W_HP{}, W_IP{}, W_LP{}, W_turbine{};
    double W_P1{}, W_P2{}, W_P3{}, W_pump{}, W_net{};
    double Q_boiler{}, Q_reheat{}, Q_in{}, Q_out{};
    double eta_cycle{}, eta_electrical{};
};

struct Stream {
    State state; double massFlow{};
};
struct ComponentStreams { std::vector<Stream> inlets, outlets; };

struct FirstLawRow {
    std::string component; double massFlow{}, Q{}, W{}, netEnergy{}, residual{};
};
struct SecondLawRow {
    std::string component; double massFlow{}, exergySupplied{}, exergyDestroyed{};
};

class Cycle {
public:
    explicit Cycle(const CycleConfig& config = CycleConfig());
    CycleResult calculate(double T_main_C=600.0, double P_cond_bar=-1.0);

    std::map<std::string,double> massFlows(const CycleResult& r) const;
    std::map<std::string,ComponentStreams> componentStreams(const CycleResult& r) const;
    double flowExergy(const State& st) const;

    std::vector<FirstLawRow> firstLawComponents(const CycleResult& r) const;
    std::map<std::string,double> firstLawCycle(const CycleResult& r) const;
    std::vector<SecondLawRow> secondLawComponents(const CycleResult& r) const;
    std::map<std::string,double> secondLawCycle(const CycleResult& r) const;

    const CycleConfig& config() const { return config_; }
    const WaterProperties& properties() const { return props_; }
    std::vector<std::vector<std::string>> stateTable(const CycleResult& r) const;
    std::vector<std::vector<std::string>> firstLawTable(const CycleResult& r) const;
    std::vector<std::vector<std::string>> secondLawTable(const CycleResult& r) const;

private:
    CycleConfig config_; WaterProperties props_;
    Boiler boiler_; Turbine hpT_, ipT_, lpT_; Reheater reheater_; Condenser condenser_;
    Pump pump1_, pump2_, pump3_; OpenFeedwaterHeater lpFWH_, hpFWH_; Generator generator_;
};
