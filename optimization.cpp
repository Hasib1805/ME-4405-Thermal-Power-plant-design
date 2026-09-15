#include "optimization.h"
#include <stdexcept>
std::vector<OptRow> RankineOptimizer::gridSearch(const std::vector<double>& T,const std::vector<double>& P){std::vector<OptRow>v;for(double t:T)for(double p:P){auto r=cycle_.calculate(t,p);v.push_back({t,p,r.eta_cycle,r.W_net,r.m_dot,r.y_HP,r.y_LP,r.y_cond});}return v;}
OptRow RankineOptimizer::findOptimum(const std::vector<OptRow>& g)const{if(g.empty())throw std::runtime_error("Empty optimization grid");auto b=g[0];for(auto&r:g)if(r.eta>b.eta)b=r;return b;}
