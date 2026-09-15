#pragma once
#include "cycle.h"
#include <vector>

struct OptRow { double T_main_C{}, P_cond_bar{}, eta{}, W_net{}, m_dot{}, y_HP{}, y_LP{}, y_cond{}; };

class RankineOptimizer {
public:
    explicit RankineOptimizer(Cycle& cycle): cycle_(cycle) {}
    std::vector<OptRow> gridSearch(const std::vector<double>& T, const std::vector<double>& P);
    OptRow findOptimum(const std::vector<OptRow>& grid) const;
private: Cycle& cycle_;
};
