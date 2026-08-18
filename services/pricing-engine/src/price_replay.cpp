#include "mercator/pricing/price_replay.hpp"

#include <cmath>
#include <stdexcept>

namespace mercator::pricing {

PriceReplayResult verify_historical_price(
    const PricingInstrument& instrument,
    const Date valuation_date,
    const YieldCurve& reconstructed_curve,
    const PersistedPriceSnapshot& persisted,
    const double absolute_tolerance
) {
    if (absolute_tolerance < 0.0) {
        throw std::invalid_argument(
            "replay absolute tolerance must be non-negative"
        );
    }

    if (
        reconstructed_curve.version()
        != persisted.curve_version
    ) {
        throw std::invalid_argument(
            "reconstructed curve version does not match "
            "persisted price curve version"
        );
    }

    if (
        instrument.reference_version
        != persisted.reference_version
    ) {
        throw std::invalid_argument(
            "instrument reference version does not match "
            "persisted price reference version"
        );
    }

    const PriceBreakdown replayed =
        price_from_curve(
            instrument.schedule,
            valuation_date,
            reconstructed_curve,
            instrument.spread_bps
        );

    const double clean_error =
        replayed.clean_price
        - persisted.clean_price;

    const double dirty_error =
        replayed.dirty_price
        - persisted.dirty_price;

    const bool verified =
        std::abs(clean_error)
            <= absolute_tolerance
        &&
        std::abs(dirty_error)
            <= absolute_tolerance;

    return PriceReplayResult{
        .status =
            verified
                ? ReplayVerificationStatus::Verified
                : ReplayVerificationStatus::Mismatch,

        .replayed = replayed,

        .clean_price_error = clean_error,
        .dirty_price_error = dirty_error,

        .curve_version =
            reconstructed_curve.version(),

        .reference_version =
            instrument.reference_version,
    };
}

}  // namespace mercator::pricing
