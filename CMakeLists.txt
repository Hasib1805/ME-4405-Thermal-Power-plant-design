cmake_minimum_required(VERSION 3.16)
project(ME4405_Rankine_OOP_CPP LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set COOLPROP_ROOT to the folder containing CoolProp's C++ headers/library.
# Example on Windows:
#   cmake -S . -B build -DCOOLPROP_ROOT=C:/CoolProp

if(NOT DEFINED COOLPROP_ROOT)
    message(WARNING "COOLPROP_ROOT is not set. Set it to your CoolProp installation root.")
endif()

add_executable(ME4405_Rankine
    main.cpp properties.cpp components.cpp cycle.cpp optimization.cpp analysis.cpp plotter.cpp
)

target_include_directories(ME4405_Rankine PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${COOLPROP_ROOT}/include
)

if(WIN32)
    find_library(COOLPROP_LIBRARY NAMES CoolProp CoolPropLib PATHS ${COOLPROP_ROOT}/lib ${COOLPROP_ROOT}/bin)
else()
    find_library(COOLPROP_LIBRARY NAMES CoolProp libCoolProp PATHS ${COOLPROP_ROOT}/lib ${COOLPROP_ROOT})
endif()

if(NOT COOLPROP_LIBRARY)
    message(FATAL_ERROR "Could not find CoolProp library. Set COOLPROP_ROOT correctly.")
endif()

target_link_libraries(ME4405_Rankine PRIVATE ${COOLPROP_LIBRARY})
