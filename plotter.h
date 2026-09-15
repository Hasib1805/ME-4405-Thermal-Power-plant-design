#pragma once
#include "cycle.h"
#include "optimization.h"
#include "analysis.h"
#include <string>
#include <vector>

class Plotter {
public:
    explicit Plotter(const std::string& dir="plots");
    void efficiencyVsTemperature(Cycle& c,const std::vector<double>&T,double P);
    void efficiencyVsPressure(Cycle& c,const std::vector<double>&P,double T);
    void efficiencyContour(Cycle& c,const std::vector<double>&T,const std::vector<double>&P);
    void exergyBar(const Cycle&c,const CycleResult&b,const CycleResult&o);
    void Ts(const Cycle&c,const CycleResult&b,const CycleResult&o);
    void Ph(const Cycle&c,const CycleResult&b,const CycleResult&o);
    void hs(const Cycle&c,const CycleResult&b,const CycleResult&o);
    void saveStateTable(const Cycle&c,const CycleResult&r,const std::string&name);
    void saveFirstLawTable(const Cycle&c,const CycleResult&r,const std::string&name);
    void saveSecondLawTable(const Cycle&c,const CycleResult&r,const std::string&name);
    void saveComparisonTable(const std::vector<ComparisonRow>& rows,const std::string&name,const std::string&title);
    void saveExergyComparisonTable(const std::vector<ExergyComparisonRow>& rows,const std::string&name,const std::string&title);
    void saveOptimizationTable(const std::vector<OptRow>& rows,const std::string&name);
    void saveMassFlowTable(const Cycle&c,const CycleResult&r,const std::string&name);
    void saveComponentStreamTable(const Cycle&c,const CycleResult&r,const std::string&name);
private:
    std::string dir_;
    void run(const std::string& script,const std::string& png);
    void saveTable(const std::vector<std::vector<std::string>>& rows,const std::string&name,const std::string&title);
};
