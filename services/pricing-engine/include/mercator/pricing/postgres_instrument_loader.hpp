#pragma once

#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/repricing_service.hpp"

#include <string>
#include <unordered_map>

namespace mercator::pricing {

struct LoadedInstrumentUniverse {
    PricingDependencyGraph dependency_graph;

    std::unordered_map<
        InstrumentId,
        PricingInstrument
    > instruments;
};

[[nodiscard]]
LoadedInstrumentUniverse load_instruments_from_postgres(
    const std::string& postgres_dsn,
    Date valuation_date
);

}  // namespace mercator::pricing
