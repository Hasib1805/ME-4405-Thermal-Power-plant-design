#include "plotter.h"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstdlib>
#include <iostream>
#include <algorithm>
#include <cmath>

namespace fs=std::filesystem;
static std::string q(const std::string&s){std::string r="'";for(char c:s){if(c=='\'')r+="\\'";else r+=c;}return r+="'";}
static std::string gn(double x){std::ostringstream o;o<<std::setprecision(12)<<x;return o.str();}
Plotter::Plotter(const std::string&dir):dir_(dir){fs::create_directories(dir_);}
void Plotter::run(const std::string&script,const std::string&png){fs::path sp=fs::path(dir_)/(script+".plt");std::ofstream out(sp);out<<script;out.close();std::string cmd="gnuplot \""+sp.string()+"\"";int rc=std::system(cmd.c_str());if(rc!=0)std::cerr<<"Warning: gnuplot failed for "<<png<<". Make sure gnuplot is installed and in PATH.\n";else std::cout<<"Saved: "<<(fs::path(dir_)/png).string()<<"\n";}

void Plotter::efficiencyVsTemperature(Cycle&c,const std::vector<double>&T,double P){RankineOptimizer o(c);auto g=o.gridSearch(T,{P});fs::path dat=fs::path(dir_)/"eta_temperature.dat";std::ofstream d(dat);for(auto&r:g)d<<r.T_main_C<<" "<<r.eta*100<<"\n";std::ostringstream s;s<<"set terminal pngcairo size 1200,800 enhanced font 'Arial,16'\nset output '"<<(fs::path(dir_)/"eta_vs_main_temperature.png").string()<<"'\nset xlabel 'Main steam temperature [°C]'\nset ylabel 'Thermal efficiency [%]'\nset title 'Efficiency vs Main Steam Temperature ("<<P<<" bar condenser)'\nset grid\nplot '"<<dat.string()<<"' using 1:2 with linespoints lw 2 pt 7 title 'Thermal efficiency'\n";run(s.str(),"eta_vs_main_temperature.png");}
void Plotter::efficiencyVsPressure(Cycle&c,const std::vector<double>&P,double T){RankineOptimizer o(c);auto g=o.gridSearch({T},P);fs::path dat=fs::path(dir_)/"eta_pressure.dat";std::ofstream d(dat);for(auto&r:g)d<<r.P_cond_bar<<" "<<r.eta*100<<"\n";std::ostringstream s;s<<"set terminal pngcairo size 1200,800 enhanced font 'Arial,16'\nset output '"<<(fs::path(dir_)/"eta_vs_condenser_pressure.png").string()<<"'\nset xlabel 'Condenser pressure [bar]'\nset ylabel 'Thermal efficiency [%]'\nset title 'Efficiency vs Condenser Pressure ("<<T<<" °C main steam)'\nset grid\nplot '"<<dat.string()<<"' using 1:2 with linespoints lw 2 pt 7 title 'Thermal efficiency'\n";run(s.str(),"eta_vs_condenser_pressure.png");}
void Plotter::efficiencyContour(Cycle&c,const std::vector<double>&T,const std::vector<double>&P){RankineOptimizer o(c);auto g=o.gridSearch(T,P);fs::path dat=fs::path(dir_)/"efficiency_grid.dat";std::ofstream d(dat);for(auto&r:g)d<<r.T_main_C<<" "<<r.P_cond_bar<<" "<<r.eta*100<<"\n";std::ostringstream s;s<<"set terminal pngcairo size 1200,900 enhanced font 'Arial,16'\nset output '"<<(fs::path(dir_)/"thermal_efficiency_contour.png").string()<<"'\nset xlabel 'Main steam temperature [°C]'\nset ylabel 'Condenser pressure [bar]'\nset title 'Thermal Efficiency Map'\nset pm3d map\nset palette defined (0 '#313695', 0.5 '#ffffbf', 1 '#a50026')\nset colorbox\nset cblabel 'Thermal efficiency [%]'\nset dgrid3d "<<T.size()<<","<<P.size()<<",2\nsplot '"<<dat.string()<<"' using 1:2:3 notitle\n";run(s.str(),"thermal_efficiency_contour.png");}

void Plotter::exergyBar(const Cycle&c,const CycleResult&b,const CycleResult&o){auto v=exergyComparison(c,b,o);fs::path dat=fs::path(dir_)/"exergy_bar.dat";std::ofstream d(dat);for(size_t i=0;i<v.size();++i)d<<i<<" "<<v[i].baseline<<" "<<v[i].optimum<<"\n";fs::path lab=fs::path(dir_)/"exergy_labels.dat";std::ofstream l(lab);for(size_t i=0;i<v.size();++i)l<<i<<" '"<<v[i].component<<"'\n";std::ostringstream s;s<<"set terminal pngcairo size 1400,1000 enhanced font 'Arial,16'\nset output '"<<(fs::path(dir_)/"component_exergy_destruction.png").string()<<"'\nset xlabel 'Exergy destroyed [MW]'\nset title 'Component Exergy Destruction: Baseline vs Optimum'\nset style data histograms\nset style histogram clustered gap 1\nset style fill solid border -1\nset boxwidth 0.8\nset xtics rotate by -35\nset yrange [0:*]\nset grid ytics\nplot '"<<dat.string()<<"' using 2:xticlabels(1) title 'Baseline', '' using 3 title 'Optimum'\n";run(s.str(),"component_exergy_destruction.png");}

void Plotter::Ts(const Cycle&c,const CycleResult&b,const CycleResult&o){
    auto& p=c.properties();
    fs::path dome=fs::path(dir_)/"dome_ts.dat";
    std::ofstream d(dome);
    double tmin=p.tripleTemperature()+0.2,tmax=p.criticalTemperature()-0.2;
    for(int i=0;i<500;i++){double T=tmin+(tmax-tmin)*i/499.0; d<<p.saturationEntropy(T,0)/1000<<" "<<T-273.15<<"\n";}
    d<<"\n\n";
    for(int i=0;i<500;i++){double T=tmin+(tmax-tmin)*i/499.0; d<<p.saturationEntropy(T,1)/1000<<" "<<T-273.15<<"\n";}
    fs::path dat=fs::path(dir_)/"cycle_ts.dat";
    std::ofstream x(dat);
    for(auto& r:{b,o}){for(int i=1;i<=11;i++)x<<r.states[i].entropy/1000<<" "<<r.states[i].temperature-273.15<<"\n";x<<r.states[1].entropy/1000<<" "<<r.states[1].temperature-273.15<<"\n\n";}
    std::ostringstream s;
    s<<"set terminal pngcairo size 1200,800 enhanced font 'Arial,16'\n"
     <<"set output '"<<(fs::path(dir_)/"Ts_diagram_baseline_vs_optimum.png").string()<<"'\n"
     <<"set xlabel 'Entropy, s [kJ/kg-K]'\nset ylabel 'Temperature, T [°C]'\n"
     <<"set title 'T-s Diagram: Baseline vs Optimum'\nset grid\n"
     <<"plot '"<<dome.string()<<"' using 1:2 with lines dt 2 lw 2 title 'Saturation dome', '"<<dat.string()<<"' index 0 using 1:2 with linespoints lw 2 pt 7 title 'Baseline', '"<<dat.string()<<"' index 1 using 1:2 with linespoints lw 2 pt 5 title 'Optimum'\n";
    run(s.str(),"Ts_diagram_baseline_vs_optimum.png");
}

void Plotter::Ph(const Cycle&c,const CycleResult&b,const CycleResult&o){
    auto& p=c.properties();
    fs::path dome=fs::path(dir_)/"dome_ph.dat";
    std::ofstream d(dome);
    double tmin=p.tripleTemperature()+0.2,tmax=p.criticalTemperature()-0.2;
    for(int i=0;i<500;i++){double T=tmin+(tmax-tmin)*i/499.0; d<<p.saturationEnthalpy(T,0)/1000<<" "<<p.saturationPressure(T)/1e6<<"\n";}
    d<<"\n\n";
    for(int i=0;i<500;i++){double T=tmin+(tmax-tmin)*i/499.0; d<<p.saturationEnthalpy(T,1)/1000<<" "<<p.saturationPressure(T)/1e6<<"\n";}
    fs::path dat=fs::path(dir_)/"cycle_ph.dat"; std::ofstream x(dat);
    for(auto& r:{b,o}){for(int i=1;i<=11;i++)x<<r.states[i].enthalpy/1000<<" "<<r.states[i].pressure/1e6<<"\n";x<<r.states[1].enthalpy/1000<<" "<<r.states[1].pressure/1e6<<"\n\n";}
    std::ostringstream s;
    s<<"set terminal pngcairo size 1200,800 enhanced font 'Arial,16'\n"
     <<"set output '"<<(fs::path(dir_)/"Ph_diagram_baseline_vs_optimum.png").string()<<"'\n"
     <<"set xlabel 'Enthalpy, h [kJ/kg]'\nset ylabel 'Pressure, P [MPa]'\nset logscale y\n"
     <<"set title 'P-h Diagram: Baseline vs Optimum'\nset grid\n"
     <<"plot '"<<dome.string()<<"' using 1:2 with lines dt 2 lw 2 title 'Saturation dome', '"<<dat.string()<<"' index 0 using 1:2 with linespoints lw 2 pt 7 title 'Baseline', '"<<dat.string()<<"' index 1 using 1:2 with linespoints lw 2 pt 5 title 'Optimum'\n";
    run(s.str(),"Ph_diagram_baseline_vs_optimum.png");
}

void Plotter::hs(const Cycle&c,const CycleResult&b,const CycleResult&o){
    auto& p=c.properties();
    fs::path dome=fs::path(dir_)/"dome_hs.dat";
    std::ofstream d(dome);
    double tmin=p.tripleTemperature()+0.2,tmax=p.criticalTemperature()-0.2;
    for(int i=0;i<500;i++){double T=tmin+(tmax-tmin)*i/499.0; d<<p.saturationEntropy(T,0)/1000<<" "<<p.saturationEnthalpy(T,0)/1000<<"\n";}
    d<<"\n\n";
    for(int i=0;i<500;i++){double T=tmin+(tmax-tmin)*i/499.0; d<<p.saturationEntropy(T,1)/1000<<" "<<p.saturationEnthalpy(T,1)/1000<<"\n";}
    fs::path dat=fs::path(dir_)/"cycle_hs.dat"; std::ofstream x(dat);
    for(auto& r:{b,o}){for(int i=1;i<=11;i++)x<<r.states[i].entropy/1000<<" "<<r.states[i].enthalpy/1000<<"\n";x<<r.states[1].entropy/1000<<" "<<r.states[1].enthalpy/1000<<"\n\n";}
    std::ostringstream s;
    s<<"set terminal pngcairo size 1200,800 enhanced font 'Arial,16'\n"
     <<"set output '"<<(fs::path(dir_)/"hs_diagram_baseline_vs_optimum.png").string()<<"'\n"
     <<"set xlabel 'Entropy, s [kJ/kg-K]'\nset ylabel 'Enthalpy, h [kJ/kg]'\n"
     <<"set title 'h-s Diagram: Baseline vs Optimum'\nset grid\n"
     <<"plot '"<<dome.string()<<"' using 1:2 with lines dt 2 lw 2 title 'Saturation dome', '"<<dat.string()<<"' index 0 using 1:2 with linespoints lw 2 pt 7 title 'Baseline', '"<<dat.string()<<"' index 1 using 1:2 with linespoints lw 2 pt 5 title 'Optimum'\n";
    run(s.str(),"hs_diagram_baseline_vs_optimum.png");
}

void Plotter::saveTable(const std::vector<std::vector<std::string>>&rows,const std::string&name,const std::string&title){fs::path dat=fs::path(dir_)/(name+".txt");std::ofstream d(dat);for(auto&r:rows){for(size_t i=0;i<r.size();++i){if(i)d<<"\t";d<<r[i];}d<<"\n";}int ncol=rows.empty()?0:(int)rows[0].size();int nrow=(int)rows.size();fs::path png=fs::path(dir_)/(name+".png");std::ostringstream s;s<<"set terminal pngcairo size 1800,"<<std::max(500,120+nrow*55)<<" enhanced font 'Arial,15'\nset output '"<<png.string()<<"'\nset xrange [0:"<<ncol<<"]\nset yrange [0:"<<nrow<<"] reverse\nunset border\nunset tics\nset title '"<<title<<"' font ',20'\n";for(int i=0;i<nrow;i++)for(int j=0;j<ncol;j++){std::string txt=rows[i][j];for(char&ch:txt)if(ch=='_')ch=' ';s<<"set label '"<<txt<<"' at "<<j+0.5<<","<<i+0.65<<" center\n";}for(int i=0;i<=nrow;i++)s<<"set arrow from 0,"<<i<<" to "<<ncol<<","<<i<<" nohead lw 1\n";for(int j=0;j<=ncol;j++)s<<"set arrow from "<<j<<",0 to "<<j<<","<<nrow<<" nohead lw 1\n";run(s.str(),name+".png");}
void Plotter::saveStateTable(const Cycle&c,const CycleResult&r,const std::string&name){saveTable(c.stateTable(r),name,"State Properties");}
void Plotter::saveFirstLawTable(const Cycle&c,const CycleResult&r,const std::string&name){saveTable(c.firstLawTable(r),name,"Component First-Law Analysis");}
void Plotter::saveSecondLawTable(const Cycle&c,const CycleResult&r,const std::string&name){saveTable(c.secondLawTable(r),name,"Component Second-Law / Exergy Analysis");}
void Plotter::saveComparisonTable(const std::vector<ComparisonRow>&rows,const std::string&name,const std::string&title){std::vector<std::vector<std::string>>t={{"Metric","Baseline","Optimum"}};for(auto&r:rows){std::ostringstream a,b;a<<std::fixed<<std::setprecision(4)<<r.baseline;b<<std::fixed<<std::setprecision(4)<<r.optimum;t.push_back({r.metric,a.str(),b.str()});}saveTable(t,name,title);}
void Plotter::saveExergyComparisonTable(const std::vector<ExergyComparisonRow>&rows,const std::string&name,const std::string&title){std::vector<std::vector<std::string>>t={{"Component","Baseline [MW]","Optimum [MW]"}};for(auto&r:rows){std::ostringstream a,b;a<<std::fixed<<std::setprecision(4)<<r.baseline;b<<std::fixed<<std::setprecision(4)<<r.optimum;t.push_back({r.component,a.str(),b.str()});}saveTable(t,name,title);}
void Plotter::saveMassFlowTable(const Cycle&c,const CycleResult&r,const std::string&name){
    std::vector<std::vector<std::string>> t={{"Component","Mass flow [kg/s]"}};
    for(auto& kv:c.massFlows(r)){std::ostringstream x;x<<std::fixed<<std::setprecision(4)<<kv.second;t.push_back({kv.first,x.str()});}
    saveTable(t,name,"Component Mass Flow Rates");
}
void Plotter::saveComponentStreamTable(const Cycle&c,const CycleResult&r,const std::string&name){
    std::vector<std::vector<std::string>> t={{"Component","Stream","State","Mass flow [kg/s]","P [MPa]","T [°C]","h [kJ/kg]","s [kJ/kg-K]"}};
    for(auto& kv:c.componentStreams(r)){
        for(auto& x:kv.second.inlets){auto&st=x.state;t.push_back({kv.first,"Inlet",std::to_string(st.number),std::to_string(x.massFlow),std::to_string(st.pressure/1e6),std::to_string(st.temperature-273.15),std::to_string(st.enthalpy/1000),std::to_string(st.entropy/1000)});}
        for(auto& x:kv.second.outlets){auto&st=x.state;t.push_back({kv.first,"Outlet",std::to_string(st.number),std::to_string(x.massFlow),std::to_string(st.pressure/1e6),std::to_string(st.temperature-273.15),std::to_string(st.enthalpy/1000),std::to_string(st.entropy/1000)});}
    }
    saveTable(t,name,"Component Inlet / Outlet States and Mass Flow Rates");
}

void Plotter::saveOptimizationTable(const std::vector<OptRow>&rows,const std::string&name){std::vector<std::vector<std::string>>t={{"T main [°C]","P cond [bar]","Efficiency [%]","Wnet [J/kg]","m_dot [kg/s]","yHP","yLP","ycond"}};for(auto&r:rows){std::ostringstream a,b,c,d,e,f,g,h;a<<std::fixed<<std::setprecision(1)<<r.T_main_C;b<<std::fixed<<std::setprecision(3)<<r.P_cond_bar;c<<std::fixed<<std::setprecision(4)<<r.eta*100;d<<std::fixed<<std::setprecision(2)<<r.W_net;e<<std::fixed<<std::setprecision(3)<<r.m_dot;f<<std::fixed<<std::setprecision(5)<<r.y_HP;g<<std::fixed<<std::setprecision(5)<<r.y_LP;h<<std::fixed<<std::setprecision(5)<<r.y_cond;t.push_back({a.str(),b.str(),c.str(),d.str(),e.str(),f.str(),g.str(),h.str()});}saveTable(t,name,"Two-Parameter Sensitivity and Optimization Grid");}
