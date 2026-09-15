#include "cycle.h"
#include "optimization.h"
#include "analysis.h"
#include "plotter.h"
#include <iostream>
#include <iomanip>
#include <vector>
#include <filesystem>

static void printResult(const CycleResult&r){
 std::cout<<"\n========== CYCLE SUMMARY ==========\n";
 std::cout<<"Main steam temperature = "<<r.T_main_C<<" °C\nCondenser pressure = "<<r.P_cond_bar<<" bar\n";
 std::cout<<"Thermal efficiency = "<<r.eta_cycle*100<<" %\nElectrical efficiency = "<<r.eta_electrical*100<<" %\n";
 std::cout<<"Net specific work = "<<r.W_net/1000<<" kJ/kg\nMain steam flow = "<<r.m_dot<<" kg/s\n";
 std::cout<<"HP extraction fraction = "<<r.y_HP<<"\nLP extraction fraction = "<<r.y_LP<<"\nCondenser fraction = "<<r.y_cond<<"\n";
}
static void printStates(const CycleResult&r){std::cout<<"\n================ STATE TABLE ================\n"<<std::left<<std::setw(8)<<"State"<<std::setw(16)<<"P [MPa]"<<std::setw(18)<<"T [°C]"<<std::setw(20)<<"h [kJ/kg]"<<"s [kJ/kg-K]\n";for(int i=1;i<=11;i++){auto&s=r.states[i];std::cout<<std::setw(8)<<i<<std::setw(16)<<s.pressure/1e6<<std::setw(18)<<s.temperature-273.15<<std::setw(20)<<s.enthalpy/1000<<s.entropy/1000<<"\n";}}
static void printStreams(const Cycle&c,const CycleResult&r){std::cout<<"\n================ COMPONENT STREAMS ================\n";for(auto&[name,cs]:c.componentStreams(r)){std::cout<<"\n"<<name<<"\n";for(auto&x:cs.inlets)std::cout<<" Inlet  state "<<x.state.number<<" | mdot="<<x.massFlow<<" kg/s | P="<<x.state.pressure/1e6<<" MPa | T="<<x.state.temperature-273.15<<" C | h="<<x.state.enthalpy/1000<<" kJ/kg | s="<<x.state.entropy/1000<<" kJ/kg-K\n";for(auto&x:cs.outlets)std::cout<<" Outlet state "<<x.state.number<<" | mdot="<<x.massFlow<<" kg/s | P="<<x.state.pressure/1e6<<" MPa | T="<<x.state.temperature-273.15<<" C | h="<<x.state.enthalpy/1000<<" kJ/kg | s="<<x.state.entropy/1000<<" kJ/kg-K\n";}}
static void printFirst(const Cycle&c,const CycleResult&r){auto x=c.firstLawCycle(r);std::cout<<"\n================ FIRST LAW - ENTIRE CYCLE ================\n";for(auto&[k,v]:x)std::cout<<std::setw(34)<<std::left<<k<<": "<<v<<"\n";}
static void printSecond(const Cycle&c,const CycleResult&r,const std::string&label){auto x=c.secondLawCycle(r);std::cout<<"\n================ SECOND LAW - "<<label<<" ================\n";for(auto&[k,v]:x)std::cout<<std::setw(34)<<std::left<<k<<": "<<v<<"\n";}

int main(){
 try{
  Cycle cycle;
  Plotter plotter("plots");
  auto baseline=cycle.calculate(600,0.08); printResult(baseline); printStates(baseline); printStreams(cycle,baseline); printFirst(cycle,baseline); printSecond(cycle,baseline,"BASELINE");
  plotter.saveStateTable(cycle,baseline,"baseline_state_table");
  plotter.saveFirstLawTable(cycle,baseline,"baseline_first_law_components");
  plotter.saveSecondLawTable(cycle,baseline,"baseline_second_law_components");
  plotter.saveMassFlowTable(cycle,baseline,"baseline_mass_flows");
  plotter.saveComponentStreamTable(cycle,baseline,"baseline_component_streams");

  std::vector<double>T={560,580,600,620,640},P={0.04,0.06,0.08,0.10,0.12};
  RankineOptimizer opt(cycle); auto grid=opt.gridSearch(T,P); auto best=opt.findOptimum(grid); auto optimum=cycle.calculate(best.T_main_C,best.P_cond_bar);
  std::cout<<"\n================ OPTIMUM ================\nT = "<<best.T_main_C<<" °C\nPcond = "<<best.P_cond_bar<<" bar\nEfficiency = "<<best.eta*100<<" %\n";
  printResult(optimum); printStates(optimum); printStreams(cycle,optimum); printFirst(cycle,optimum); printSecond(cycle,optimum,"OPTIMUM");
  plotter.saveStateTable(cycle,optimum,"optimum_state_table"); plotter.saveFirstLawTable(cycle,optimum,"optimum_first_law_components"); plotter.saveSecondLawTable(cycle,optimum,"optimum_second_law_components");
  plotter.saveMassFlowTable(cycle,optimum,"optimum_mass_flows");
  plotter.saveComponentStreamTable(cycle,optimum,"optimum_component_streams"); plotter.saveOptimizationTable(grid,"optimization_grid");
  auto comp=compareResults(baseline,optimum); auto ex=exergyComparison(cycle,baseline,optimum);
  plotter.saveComparisonTable(comp,"baseline_vs_optimum_comparison","Baseline vs Optimum Cycle Comparison"); plotter.saveExergyComparisonTable(ex,"exergy_destruction_comparison","Component Exergy Destruction - Baseline vs Optimum");
  plotter.efficiencyVsTemperature(cycle,T,0.08); plotter.efficiencyVsPressure(cycle,P,600); plotter.efficiencyContour(cycle,T,P); plotter.exergyBar(cycle,baseline,optimum); plotter.Ts(cycle,baseline,optimum); plotter.Ph(cycle,baseline,optimum); plotter.hs(cycle,baseline,optimum);
  std::cout<<"\nAll PNG graphs and tables are in the plots folder.\n";
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 1;}return 0;
}
