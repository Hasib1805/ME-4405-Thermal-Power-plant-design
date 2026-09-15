#include "analysis.h"
std::vector<ComparisonRow> compareResults(const CycleResult&b,const CycleResult&o){return{
{"Main steam temperature [°C]",b.T_main_C,o.T_main_C},{"Condenser pressure [bar]",b.P_cond_bar,o.P_cond_bar},
{"Thermal efficiency [%]",b.eta_cycle*100,o.eta_cycle*100},{"Electrical efficiency [%]",b.eta_electrical*100,o.eta_electrical*100},
{"Net work [kJ/kg]",b.W_net/1000,o.W_net/1000},{"Mass flow [kg/s]",b.m_dot,o.m_dot},{"HP extraction fraction",b.y_HP,o.y_HP},{"LP extraction fraction",b.y_LP,o.y_LP},{"Condenser fraction",b.y_cond,o.y_cond}};}
std::vector<ExergyComparisonRow> exergyComparison(const Cycle&c,const CycleResult&b,const CycleResult&o){auto B=c.secondLawComponents(b),O=c.secondLawComponents(o);std::vector<ExergyComparisonRow>v;for(size_t i=0;i<B.size();++i)v.push_back({B[i].component,B[i].exergyDestroyed/1e6,O[i].exergyDestroyed/1e6});return v;}
