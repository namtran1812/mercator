cmake_minimum_required(VERSION 3.24)

project(mercator_pricing_engine VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(
    mercator-pricing-engine
    src/main.cpp
    src/cashflow.cpp
    src/analytics.cpp
)

target_include_directories(
    mercator-pricing-engine
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-pricing-engine
    PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
)

enable_testing()

add_executable(
    mercator-pricing-tests
    tests/analytics_test.cpp
    src/cashflow.cpp
    src/analytics.cpp
)

target_include_directories(
    mercator-pricing-tests
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-pricing-tests
    PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
)

add_test(
    NAME mercator-pricing-tests
    COMMAND mercator-pricing-tests
)
