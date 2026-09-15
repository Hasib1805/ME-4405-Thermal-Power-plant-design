#include "cycle.h"
#include <iomanip>
#include <sstream>
#include <cmath>
#include <stdexcept>

static std::string f(double x, int n=4) { std::ostringstream o; o<<std::fixed<<std::setprecision(n)<<x; return o.str(); }

Cycle::Cycle(const CycleConfig& c)
: config_(c), props_(c.fluid), boiler_(props_),
  hpT_("HP Turbine",c.turbineIsentropicEfficiency,props_),
  reheater_(props_), ipT_("IP Turbine",c.turbineIsentropicEfficiency,props_),
  lpT_("LP Turbine",c.turbineIsentropicEfficiency,props_), condenser_(props_),
  pump1_("Pump 1",c.pumpIsentropicEfficiency,props_),
  lpFWH_("LP Open FWH",c.lpHeaterPressure,props_),
  pump2_("Pump 2",c.pumpIsentropicEfficiency,props_),
  hpFWH_("HP Open FWH",c.reheatPressure,props_),
  pump3_("Pump 3",c.pumpIsentropicEfficiency,props_), generator_(c.generatorEfficiency) {}

CycleResult Cycle::calculate(double T_main_C, double P_cond_bar) {
    if(P_cond_bar<0) P_cond_bar=config_.condenserPressureBar;
    const double P1=config_.boilerPressure, P2=config_.reheatPressure;
    const double P4=config_.lpHeaterPressure, P5=P_cond_bar*1e5, T1=T_main_C+273.15;
    CycleResult r; r.T_main_C=T_main_C; r.P_cond_bar=P_cond_bar;

    r.states[1]=boiler_.outlet(P1,T1);
    auto a2=hpT_.calculate(r.states[1],P2); r.states[2]={2,P2,a2.h_out,a2.s_out,a2.T_out};
    r.states[3]=reheater_.outlet(P2,config_.reheatTemperature());
    auto a4=ipT_.calculate(r.states[3],P4); r.states[4]={4,P4,a4.h_out,a4.s_out,a4.T_out};
    auto a5=lpT_.calculate(r.states[4],P5); r.states[5]={5,P5,a5.h_out,a5.s_out,a5.T_out};
    r.states[6]=condenser_.outletSaturatedLiquid(P5);
    auto a7=pump1_.calculate(r.states[6],P4); r.states[7]={7,P4,a7.h_out,a7.s_out,a7.T_out};
    auto st8=lpFWH_.outletSaturatedLiquid(); r.states[8]={8,P4,st8.enthalpy,st8.entropy,st8.temperature};
    auto a9=pump2_.calculate(r.states[8],P2); r.states[9]={9,P2,a9.h_out,a9.s_out,a9.T_out};
    auto st10=hpFWH_.outletSaturatedLiquid(); r.states[10]={10,P2,st10.enthalpy,st10.entropy,st10.temperature};
    auto a11=pump3_.calculate(r.states[10],P1); r.states[11]={11,P1,a11.h_out,a11.s_out,a11.T_out};

    r.y_HP=(r.states[10].enthalpy-r.states[9].enthalpy)/(r.states[2].enthalpy-r.states[9].enthalpy);
    r.y_LP=((1-r.y_HP)*(r.states[8].enthalpy-r.states[7].enthalpy))/(r.states[4].enthalpy-r.states[7].enthalpy);
    r.y_cond=1-r.y_HP-r.y_LP;

    r.W_HP=r.states[1].enthalpy-r.states[2].enthalpy;
    r.W_IP=(1-r.y_HP)*(r.states[3].enthalpy-r.states[4].enthalpy);
    r.W_LP=r.y_cond*(r.states[4].enthalpy-r.states[5].enthalpy);
    r.W_turbine=r.W_HP+r.W_IP+r.W_LP;
    r.W_P1=r.y_cond*(r.states[7].enthalpy-r.states[6].enthalpy);
    r.W_P2=(1-r.y_HP)*(r.states[9].enthalpy-r.states[8].enthalpy);
    r.W_P3=r.states[11].enthalpy-r.states[10].enthalpy;
    r.W_pump=r.W_P1+r.W_P2+r.W_P3;
    r.W_net=r.W_turbine-r.W_pump;
    r.Q_boiler=r.states[1].enthalpy-r.states[11].enthalpy;
    r.Q_reheat=(1-r.y_HP)*(r.states[3].enthalpy-r.states[2].enthalpy);
    r.Q_in=r.Q_boiler+r.Q_reheat;
    r.Q_out=r.y_cond*(r.states[5].enthalpy-r.states[6].enthalpy);
    r.eta_cycle=r.W_net/r.Q_in;
    r.eta_electrical=r.eta_cycle*config_.generatorEfficiency;
    r.m_dot=config_.electricalPower/(config_.generatorEfficiency*r.W_net);
    return r;
}

std::map<std::string,double> Cycle::massFlows(const CycleResult& r) const {
    double m=r.m_dot,yH=r.y_HP,yL=r.y_LP,yc=r.y_cond;
    return {
        {"HP turbine",m},{"HP FWH extraction",yH*m},{"IP turbine",(1-yH)*m},
        {"LP FWH extraction",yL*m},{"LP turbine",yc*m},{"Condenser",yc*m},
        {"Pump 1",yc*m},{"LP FWH",(1-yH)*m},{"Pump 2",(1-yH)*m},
        {"HP FWH",m},{"Pump 3",m},{"Boiler",m},{"Reheater",(1-yH)*m}
    };
}

std::map<std::string,ComponentStreams> Cycle::componentStreams(const CycleResult& r) const {
    double m=r.m_dot,yH=r.y_HP,yL=r.y_LP,yc=r.y_cond; auto s=r.states;
    return {
      {"Boiler",{{{s[11],m}},{{s[1],m}}}},
      {"HP Turbine",{{{s[1],m}},{{s[2],m}}}},
      {"Reheater",{{{s[2],(1-yH)*m}},{{s[3],(1-yH)*m}}}},
      {"IP Turbine",{{{s[3],(1-yH)*m}},{{s[4],(1-yH)*m}}}},
      {"LP Turbine",{{{s[4],yc*m}},{{s[5],yc*m}}}},
      {"Condenser",{{{s[5],yc*m}},{{s[6],yc*m}}}},
      {"Pump 1",{{{s[6],yc*m}},{{s[7],yc*m}}}},
      {"LP Open FWH",{{{s[4],yL*m},{s[7],yc*m}},{{s[8],(1-yH)*m}}}},
      {"Pump 2",{{{s[8],(1-yH)*m}},{{s[9],(1-yH)*m}}}},
      {"HP Open FWH",{{{s[2],yH*m},{s[9],(1-yH)*m}},{{s[10],m}}}},
      {"Pump 3",{{{s[10],m}},{{s[11],m}}}}
    };
}

double Cycle::flowExergy(const State& st) const {
    double h0=props_.h_pt(config_.P0,config_.T0), s0=props_.s_pt(config_.P0,config_.T0);
    return (st.enthalpy-h0)-config_.T0*(st.entropy-s0);
}

std::vector<FirstLawRow> Cycle::firstLawComponents(const CycleResult& r) const {
    auto s=r.states; double m=r.m_dot,yH=r.y_HP,yL=r.y_LP,yc=r.y_cond;
    std::vector<FirstLawRow> v;
    double Q=m*(s[1].enthalpy-s[11].enthalpy); v.push_back({"Boiler",m,Q,0,Q,0});
    double W=m*(s[1].enthalpy-s[2].enthalpy); v.push_back({"HP Turbine",m,0,W,0,0});
    double mr=(1-yH)*m; Q=mr*(s[3].enthalpy-s[2].enthalpy); v.push_back({"Reheater",mr,Q,0,Q,0});
    W=mr*(s[3].enthalpy-s[4].enthalpy); v.push_back({"IP Turbine",mr,0,W,0,0});
    double mlp=yc*m; W=mlp*(s[4].enthalpy-s[5].enthalpy); v.push_back({"LP Turbine",mlp,0,W,0,0});
    Q=mlp*(s[6].enthalpy-s[5].enthalpy); v.push_back({"Condenser",mlp,Q,0,Q,0});
    W=-mlp*(s[7].enthalpy-s[6].enthalpy); v.push_back({"Pump 1",mlp,0,W,0,0});
    double mLPex=yL*m,mLPin=yc*m,mLPout=(1-yH)*m;
    double residual=mLPex*s[4].enthalpy+mLPin*s[7].enthalpy-mLPout*s[8].enthalpy;
    v.push_back({"LP Open FWH",mLPout,0,0,0,residual});
    double m2=(1-yH)*m; W=-m2*(s[9].enthalpy-s[8].enthalpy); v.push_back({"Pump 2",m2,0,W,0,0});
    double mHPex=yH*m; residual=mHPex*s[2].enthalpy+m2*s[9].enthalpy-m*s[10].enthalpy;
    v.push_back({"HP Open FWH",m,0,0,0,residual});
    W=-m*(s[11].enthalpy-s[10].enthalpy); v.push_back({"Pump 3",m,0,W,0,0});
    double shaft=m*r.W_turbine, loss=generator_.loss(shaft); v.push_back({"Generator",m,0,-loss,config_.electricalPower,0});
    return v;
}

std::map<std::string,double> Cycle::firstLawCycle(const CycleResult& r) const {
    double m=r.m_dot; return {
      {"Q_boiler_MW",m*r.Q_boiler/1e6},{"Q_reheat_MW",m*r.Q_reheat/1e6},{"Q_in_MW",m*r.Q_in/1e6},{"Q_out_MW",m*r.Q_out/1e6},
      {"W_HP_MW",m*r.W_HP/1e6},{"W_IP_MW",m*r.W_IP/1e6},{"W_LP_MW",m*r.W_LP/1e6},{"W_turbine_MW",m*r.W_turbine/1e6},
      {"W_P1_MW",m*r.W_P1/1e6},{"W_P2_MW",m*r.W_P2/1e6},{"W_P3_MW",m*r.W_P3/1e6},{"W_pump_MW",m*r.W_pump/1e6},{"W_net_MW",m*r.W_net/1e6},
      {"Thermal_efficiency_percent",r.eta_cycle*100},{"Electrical_efficiency_percent",r.eta_electrical*100},{"Electrical_output_MW",config_.electricalPower/1e6}
    }; }

std::vector<SecondLawRow> Cycle::secondLawComponents(const CycleResult& r) const {
    auto s=r.states; double m=r.m_dot,yH=r.y_HP,yL=r.y_LP,yc=r.y_cond,T0=config_.T0;
    std::array<double,12> e{}; for(int i=1;i<=11;i++) e[i]=flowExergy(s[i]);
    std::vector<SecondLawRow> v;
    double Qb=m*(s[1].enthalpy-s[11].enthalpy), ExQb=Qb*(1-T0/config_.sourceTemperatureBoiler);
    v.push_back({"Boiler",m,ExQb,ExQb+m*e[11]-m*e[1]});
    v.push_back({"HP Turbine",m,0,m*T0*(s[2].entropy-s[1].entropy)});
    double mr=(1-yH)*m,Qr=mr*(s[3].enthalpy-s[2].enthalpy),ExQr=Qr*(1-T0/config_.sourceTemperatureReheat);
    v.push_back({"Reheater",mr,ExQr,ExQr+mr*e[2]-mr*e[3]});
    v.push_back({"IP Turbine",mr,0,mr*T0*(s[4].entropy-s[3].entropy)});
    double mlp=yc*m; v.push_back({"LP Turbine",mlp,0,mlp*T0*(s[5].entropy-s[4].entropy)});
    double Qout=mlp*(s[6].enthalpy-s[5].enthalpy),Sgen=mlp*(s[6].entropy-s[5].entropy)-Qout/T0;
    v.push_back({"Condenser",mlp,0,T0*Sgen});
    v.push_back({"Pump 1",mlp,0,mlp*T0*(s[7].entropy-s[6].entropy)});
    double mLPex=yL*m,mLPin=yc*m,mLPout=(1-yH)*m; v.push_back({"LP Open FWH",mLPout,0,mLPex*e[4]+mLPin*e[7]-mLPout*e[8]});
    double m2=(1-yH)*m; v.push_back({"Pump 2",m2,0,m2*T0*(s[9].entropy-s[8].entropy)});
    double mHPex=yH*m; v.push_back({"HP Open FWH",m,0,mHPex*e[2]+m2*e[9]-m*e[10]});
    v.push_back({"Pump 3",m,0,m*T0*(s[11].entropy-s[10].entropy)});
    double shaft=m*r.W_turbine; v.push_back({"Generator",m,0,shaft-config_.electricalPower});
    return v;
}

std::map<std::string,double> Cycle::secondLawCycle(const CycleResult& r) const {
    double m=r.m_dot,Qb=m*r.Q_boiler,Qr=m*r.Q_reheat;
    double ExQb=Qb*(1-config_.T0/config_.sourceTemperatureBoiler), ExQr=Qr*(1-config_.T0/config_.sourceTemperatureReheat), total=ExQb+ExQr;
    double D=0; for(auto& x:secondLawComponents(r)) D+=x.exergyDestroyed;
    return {{"ExQ_boiler_MW",ExQb/1e6},{"ExQ_reheat_MW",ExQr/1e6},{"ExQ_total_MW",total/1e6},{"Total_exergy_destruction_MW",D/1e6},{"Electrical_output_MW",config_.electricalPower/1e6},{"Second_law_efficiency_percent",config_.electricalPower/total*100}};
}

std::vector<std::vector<std::string>> Cycle::stateTable(const CycleResult& r) const {
    std::vector<std::vector<std::string>> t={{"State","Pressure [MPa]","Temperature [°C]","Enthalpy [kJ/kg]","Entropy [kJ/kg-K]"}};
    for(int i=1;i<=11;i++){auto&s=r.states[i];t.push_back({std::to_string(i),f(s.pressure/1e6),f(s.temperature-273.15),f(s.enthalpy/1000),f(s.entropy/1000)});} return t;
}
std::vector<std::vector<std::string>> Cycle::firstLawTable(const CycleResult& r) const {
    std::vector<std::vector<std::string>> t={{"Component","Mass flow [kg/s]","Q [MW]","W [MW]","Net energy [MW]","Residual [MW]"}};
    for(auto&x:firstLawComponents(r))t.push_back({x.component,f(x.massFlow),f(x.Q/1e6),f(x.W/1e6),f(x.netEnergy/1e6),f(x.residual/1e6)});return t;
}
std::vector<std::vector<std::string>> Cycle::secondLawTable(const CycleResult& r) const {
    std::vector<std::vector<std::string>> t={{"Component","Mass flow [kg/s]","Exergy supplied [MW]","Exergy destroyed [MW]"}};
    for(auto&x:secondLawComponents(r))t.push_back({x.component,f(x.massFlow),f(x.exergySupplied/1e6),f(x.exergyDestroyed/1e6)});return t;
}
