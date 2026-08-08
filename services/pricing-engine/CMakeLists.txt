cmake_minimum_required(VERSION 3.24)

project(
    mercator_pricing_engine
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(
    nlohmann_json
    CONFIG
    REQUIRED
)


find_package(
    PkgConfig
    REQUIRED
)

pkg_check_modules(
    RDKAFKA
    REQUIRED
    IMPORTED_TARGET
    rdkafka
)


pkg_check_modules(
    LIBPQ
    REQUIRED
    IMPORTED_TARGET
    libpq
)


pkg_check_modules(
    LIBCURL
    REQUIRED
    IMPORTED_TARGET
    libcurl
)


pkg_check_modules(
    HIREDIS
    REQUIRED
    IMPORTED_TARGET
    hiredis
)


# ============================================================
# Shared pricing core
# ============================================================

add_library(
    mercator-pricing-core
    STATIC

    src/cashflow.cpp
    src/analytics.cpp
    src/yield_curve.cpp
    src/dependency_graph.cpp
    src/dependency_resolver.cpp
    src/repricing_service.cpp
    src/data_quality.cpp
    src/quote_reconciliation.cpp
    src/adaptive_repricing.cpp
    src/curve_event_parser.cpp
    src/version_guard.cpp
    src/postgres_instrument_loader.cpp
    src/clickhouse_price_sink.cpp
    src/redis_price_sink.cpp
)

target_include_directories(
    mercator-pricing-core

    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(
    mercator-pricing-core

    PUBLIC
    nlohmann_json::nlohmann_json
    PkgConfig::LIBPQ
    PkgConfig::LIBCURL
    PkgConfig::HIREDIS
)

target_compile_options(
    mercator-pricing-core

    PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -Wconversion
    -Wshadow
)


# ============================================================
# Main pricing executable
# ============================================================

add_executable(
    mercator-pricing-engine
    src/main.cpp
)

target_link_libraries(
    mercator-pricing-engine

    PRIVATE
    mercator-pricing-core
)


# ============================================================
# Repricing demo
# ============================================================

add_executable(
    mercator-repricing-demo
    src/repricing_demo.cpp
)

target_link_libraries(
    mercator-repricing-demo

    PRIVATE
    mercator-pricing-core
)

target_compile_options(
    mercator-repricing-demo

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Tests
# ============================================================

enable_testing()


add_executable(
    mercator-pricing-tests
    tests/analytics_test.cpp
)

target_link_libraries(
    mercator-pricing-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-pricing-tests
    COMMAND mercator-pricing-tests
)


add_executable(
    mercator-yield-curve-tests
    tests/yield_curve_test.cpp
)

target_link_libraries(
    mercator-yield-curve-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-yield-curve-tests
    COMMAND mercator-yield-curve-tests
)


add_executable(
    mercator-dependency-graph-tests
    tests/dependency_graph_test.cpp
)

target_link_libraries(
    mercator-dependency-graph-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-dependency-graph-tests
    COMMAND mercator-dependency-graph-tests
)


add_executable(
    mercator-data-quality-tests
    tests/data_quality_test.cpp
)

target_link_libraries(
    mercator-data-quality-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-data-quality-tests
    COMMAND mercator-data-quality-tests
)


add_executable(
    mercator-clean-price-tests
    tests/clean_price_test.cpp
)

target_link_libraries(
    mercator-clean-price-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-clean-price-tests
    COMMAND mercator-clean-price-tests
)


add_executable(
    mercator-quote-reconciliation-tests
    tests/quote_reconciliation_test.cpp
)

target_link_libraries(
    mercator-quote-reconciliation-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-quote-reconciliation-tests
    COMMAND mercator-quote-reconciliation-tests
)


# ============================================================
# Curve event pipeline tests
# ============================================================

add_executable(
    mercator-curve-event-pipeline-tests
    tests/curve_event_pipeline_test.cpp
)

target_link_libraries(
    mercator-curve-event-pipeline-tests
    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-curve-event-pipeline-tests
    COMMAND mercator-curve-event-pipeline-tests
)



# ============================================================
# Benchmarks
# ============================================================

add_executable(
    mercator-incremental-repricing-benchmark
    benchmarks/incremental_repricing.cpp
)

target_link_libraries(
    mercator-incremental-repricing-benchmark

    PRIVATE
    mercator-pricing-core
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
)

target_link_libraries(
    mercator-selective-repricing-benchmark

    PRIVATE
    mercator-pricing-core
)

target_compile_options(
    mercator-selective-repricing-benchmark

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Dependency fan-out benchmark
# ============================================================

add_executable(
    mercator-dependency-fanout-benchmark
    benchmarks/dependency_fanout.cpp
)

target_link_libraries(
    mercator-dependency-fanout-benchmark

    PRIVATE
    mercator-pricing-core
)

target_compile_options(
    mercator-dependency-fanout-benchmark

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Material key-rate repricing benchmark
# ============================================================

add_executable(
    mercator-material-repricing-benchmark
    benchmarks/material_repricing.cpp
)

target_link_libraries(
    mercator-material-repricing-benchmark

    PRIVATE
    mercator-pricing-core
)

target_compile_options(
    mercator-material-repricing-benchmark

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Sensitivity-budget repricing benchmark
# ============================================================

add_executable(
    mercator-sensitivity-repricing-benchmark
    benchmarks/sensitivity_repricing.cpp
)

target_link_libraries(
    mercator-sensitivity-repricing-benchmark

    PRIVATE
    mercator-pricing-core
)

target_compile_options(
    mercator-sensitivity-repricing-benchmark

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Adaptive repricing benchmark
# ============================================================

add_executable(
    mercator-adaptive-repricing-benchmark
    benchmarks/adaptive_repricing.cpp
)

target_link_libraries(
    mercator-adaptive-repricing-benchmark

    PRIVATE
    mercator-pricing-core
)

target_compile_options(
    mercator-adaptive-repricing-benchmark

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Adaptive repricing policy tests
# ============================================================

add_executable(
    mercator-adaptive-repricing-tests
    tests/adaptive_repricing_test.cpp
)

target_link_libraries(
    mercator-adaptive-repricing-tests

    PRIVATE
    mercator-pricing-core
)

add_test(
    NAME mercator-adaptive-repricing-tests
    COMMAND mercator-adaptive-repricing-tests
)


# ============================================================
# Curve event contract CLI
# ============================================================

add_executable(
    mercator-curve-event-cli
    src/curve_event_cli.cpp
)

target_link_libraries(
    mercator-curve-event-cli
    PRIVATE
    mercator-pricing-core
)


# ============================================================
# Event-driven pricing worker
# ============================================================

add_executable(
    mercator-pricing-worker
    src/pricing_worker.cpp
)

target_link_libraries(
    mercator-pricing-worker

    PRIVATE
    mercator-pricing-core
    PkgConfig::RDKAFKA
)

target_compile_options(
    mercator-pricing-worker

    PRIVATE
    -O3
    -Wall
    -Wextra
    -Wpedantic
)


# ============================================================
# Postgres instrument loader test
# ============================================================

add_executable(
    mercator-postgres-instrument-loader-test
    tests/postgres_instrument_loader_test.cpp
)

target_link_libraries(
    mercator-postgres-instrument-loader-test

    PRIVATE
    mercator-pricing-core
)
