#include "mercator/pricing/postgres_instrument_loader.hpp"

#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(
            message
        );
    }
}

}  // namespace


int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const char* dsn =
        std::getenv(
            "POSTGRES_DSN"
        );

    if (dsn == nullptr) {
        throw std::runtime_error(
            "POSTGRES_DSN is not set"
        );
    }

    const Date valuation_date{
        year{2026},
        month{8},
        day{8},
    };

    const auto universe =
        load_instruments_from_postgres(
            std::string{dsn},
            valuation_date
        );

    const std::size_t count =
        universe.instruments.size();

    std::cout
        << "Loaded instruments: "
        << count
        << "\n";

    std::cout
        << "Dependency graph instruments: "
        << universe
            .dependency_graph
            .instrument_count()
        << "\n";


    require(
        count > 9'000,
        "expected more than 9,000 active bonds"
    );

    require(
        universe
            .dependency_graph
            .instrument_count()
        == count,
        "dependency graph count mismatch"
    );


    const auto iterator =
        universe.instruments.find(
            1
        );

    require(
        iterator
        != universe.instruments.end(),
        "instrument 1 was not loaded"
    );

    const auto& instrument =
        iterator->second;

    require(
        instrument.instrument_id == 1,
        "instrument id mismatch"
    );

    require(
        !instrument
            .schedule
            .cashflows
            .empty(),
        "instrument has no cashflows"
    );

    require(
        instrument.spread_bps >= 50.0,
        "spread fallback too low"
    );

    require(
        instrument.spread_bps <= 400.0,
        "spread fallback too high"
    );

    require(
        instrument.market_confidence
        == 0.95,
        "market confidence mismatch"
    );


    const auto dependencies =
        universe
            .dependency_graph
            .dependencies_for(
                1
            );

    require(
        !dependencies.empty(),
        "instrument 1 has no curve dependencies"
    );


    std::cout
        << "Instrument 1 cashflows: "
        << instrument
            .schedule
            .cashflows
            .size()
        << "\n";

    std::cout
        << "Instrument 1 dependencies: "
        << dependencies.size()
        << "\n";

    std::cout
        << "Instrument 1 spread: "
        << instrument.spread_bps
        << " bp\n";

    std::cout
        << "Instrument 1 reference version: "
        << instrument.reference_version
        << "\n";


    std::cout
        << "Postgres instrument loader test passed.\n";

    return 0;
}
