## Main OOP structure

```text
Cycle
├── Boiler
├── HP Turbine
├── Reheater
├── IP Turbine
├── LP Turbine
├── Condenser
├── Pump 1
├── LP Open FWH
├── Pump 2
├── HP Open FWH
├── Pump 3
└── Generator
```

There is also a `ClosedFeedwaterHeater` class in `components.py` for future
expansion, although the current project configuration uses two OPEN heaters.

## 1. Whole-cycle first-law analysis

```python
cycle = Cycle()
baseline = cycle.calculate(600, 0.08)

cycle_1st, component_1st = cycle.first_law_analysis(baseline)

print(cycle_1st)
print(component_1st)
```

`cycle_1st` contains:
- boiler heat input
- reheater heat input
- total heat input/output
- HP/IP/LP turbine work
- pump work
- net work
- thermal efficiency
- electrical efficiency
- electrical output

`component_1st` contains one row for every component.

## 2. Whole-cycle second-law analysis

```python
cycle_2nd, component_2nd = cycle.second_law_analysis(baseline)

print(cycle_2nd)
print(component_2nd)
```

The component table contains exergy destruction for:
- Boiler
- HP turbine
- Reheater
- IP turbine
- LP turbine
- Condenser
- Pump 1
- LP open FWH
- Pump 2
- HP open FWH
- Pump 3
- Generator

## 3. Component inlet/outlet states

```python
cycle.print_component_streams(baseline)
```

This prints pressure, temperature, enthalpy, entropy and mass flow for every
component stream. Open FWHs correctly show TWO inlet streams.

## 4. Important mass-flow relationship

For this regenerative cycle:

```text
HP turbine flow = main flow

IP turbine flow = main flow - HP extraction

LP turbine flow = condenser fraction × main flow

HP extraction = y_HP × main flow

LP extraction = y_LP × main flow
```

Therefore:

```text
m_HP = m_IP + m_HP_extraction
```

and, because the IP outlet splits between the LP FWH and LP turbine:

```text
m_IP = m_LP + m_LP_extraction
```

This is the correct physical flow split.

## 5. Colab

Upload all `.py` files into the same Colab directory and run:

```python
from main import main
main()
```

Or work interactively:

```python
from cycle import Cycle

cycle = Cycle()
r = cycle.calculate(T_main_C=600, P_cond_bar=0.08)

cycle.summary(r)
cycle.print_component_streams(r)

first_cycle, first_components = cycle.first_law_analysis(r)
second_cycle, second_components = cycle.second_law_analysis(r)

display(first_components)
display(second_components)
```

## 6. Units

Internally:
- pressure = Pa
- temperature = K
- enthalpy = J/kg
- entropy = J/(kg K)
- work/heat/exergy = W

Tables convert these to engineering units such as MW, kJ/kg and °C.
