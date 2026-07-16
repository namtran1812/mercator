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
    src/yield_curve.cpp
    src/dependency_graph.cpp
    src/dependency_resolver.cpp
    src/repricing_service.cpp
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
    src/yield_curve.cpp
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

add_executable(
    mercator-yield-curve-tests
    tests/yield_curve_test.cpp
    src/cashflow.cpp
    src/analytics.cpp
    src/yield_curve.cpp
)

target_include_directories(
    mercator-yield-curve-tests
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-yield-curve-tests
    PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
)

add_test(
    NAME mercator-yield-curve-tests
    COMMAND mercator-yield-curve-tests
)

add_executable(
    mercator-dependency-graph-tests
    tests/dependency_graph_test.cpp
    src/cashflow.cpp
    src/analytics.cpp
    src/yield_curve.cpp
    src/dependency_graph.cpp
    src/dependency_resolver.cpp
)

target_include_directories(
    mercator-dependency-graph-tests
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-dependency-graph-tests
    PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
)

add_test(
    NAME mercator-dependency-graph-tests
    COMMAND mercator-dependency-graph-tests
)

add_executable(
    mercator-incremental-repricing-benchmark
    benchmarks/incremental_repricing.cpp
    src/cashflow.cpp
    src/analytics.cpp
    src/yield_curve.cpp
    src/dependency_graph.cpp
    src/dependency_resolver.cpp
)

target_include_directories(
    mercator-incremental-repricing-benchmark
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-incremental-repricing-benchmark
    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)

add_executable(
    mercator-selective-repricing-benchmark
    benchmarks/selective_repricing.cpp
    src/cashflow.cpp
    src/analytics.cpp
    src/yield_curve.cpp
    src/dependency_graph.cpp
    src/dependency_resolver.cpp
)

target_include_directories(
    mercator-selective-repricing-benchmark
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-selective-repricing-benchmark
    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)

add_executable(
    mercator-repricing-demo
    src/repricing_demo.cpp
    src/cashflow.cpp
    src/analytics.cpp
    src/yield_curve.cpp
    src/dependency_graph.cpp
    src/dependency_resolver.cpp
    src/repricing_service.cpp
)

target_include_directories(
    mercator-repricing-demo
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-repricing-demo
    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)

add_executable(
    mercator-data-quality-tests
    tests/data_quality_test.cpp
    src/data_quality.cpp
)

target_include_directories(
    mercator-data-quality-tests
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(
    mercator-data-quality-tests
    PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
)

add_test(
    NAME mercator-data-quality-tests
    COMMAND mercator-data-quality-tests
)
