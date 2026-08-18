#pragma once

#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/repricing_service.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <cstdint>

namespace mercator::pricing {

enum class ReplayVerificationStatus {
    Verified,
    Mismatch
};

struct PersistedPriceSnapshot {
    double clean_price;
    double dirty_price;

    std::uint64_t curve_version;
    std::uint64_t reference_version;
};

struct PriceReplayResult {
    ReplayVerificationStatus status;

    PriceBreakdown replayed;

    double clean_price_error;
    double dirty_price_error;

    std::uint64_t curve_version;
    std::uint64_t reference_version;
};

[[nodiscard]]
PriceReplayResult verify_historical_price(
    const PricingInstrument& instrument,
    Date valuation_date,
    const YieldCurve& reconstructed_curve,
    const PersistedPriceSnapshot& persisted,
    double absolute_tolerance = 1e-10
);

}  // namespace mercator::pricing
