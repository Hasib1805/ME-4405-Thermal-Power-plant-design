#pragma once
#include "cycle.h"
#include <vector>
#include <string>
struct ComparisonRow { std::string metric; double baseline{}, optimum{}; };
struct ExergyComparisonRow { std::string component; double baseline{}, optimum{}; };
std::vector<ComparisonRow> compareResults(const CycleResult& b,const CycleResult&o);
std::vector<ExergyComparisonRow> exergyComparison(const Cycle& c,const CycleResult&b,const CycleResult&o);
