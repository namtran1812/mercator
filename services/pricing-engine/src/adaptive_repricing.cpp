#include "mercator/pricing/adaptive_repricing.hpp"

#include <stdexcept>

namespace mercator::pricing {

RepricingDecision choose_repricing_strategy(
    const std::size_t affected_instruments,
    const std::size_t total_instruments,
    const double estimated_omitted_error_bps,
    const AdaptiveRepricingPolicy& policy
) {
    if (total_instruments == 0) {
        throw std::invalid_argument(
            "total_instruments must be positive"
        );
    }

    if (
        affected_instruments
        > total_instruments
    ) {
        throw std::invalid_argument(
            "affected_instruments cannot exceed total"
        );
    }

    if (
        policy.error_budget_bps < 0.0
        || policy.full_reprice_fraction < 0.0
        || policy.full_reprice_fraction > 1.0
    ) {
        throw std::invalid_argument(
            "invalid adaptive repricing policy"
        );
    }

    if (estimated_omitted_error_bps < 0.0) {
        throw std::invalid_argument(
            "estimated omitted error cannot be negative"
        );
    }

    const double affected_fraction =
        static_cast<double>(
            affected_instruments
        )
        / static_cast<double>(
            total_instruments
        );

    RepricingStrategy strategy;

    /*
     * Nothing is materially affected and the estimated
     * omitted impact fits inside our error budget.
     */
    if (
        affected_instruments == 0
        && estimated_omitted_error_bps
            <= policy.error_budget_bps
    ) {
        strategy =
            RepricingStrategy::Skip;
    }

    /*
     * We cannot safely omit all updates.
     * If fan-out is too large, full repricing is cheaper
     * than paying selective-routing overhead.
     */
    else if (
        affected_fraction
        >= policy.full_reprice_fraction
    ) {
        strategy =
            RepricingStrategy::Full;
    }

    /*
     * Material fan-out is sufficiently sparse.
     */
    else {
        strategy =
            RepricingStrategy::Selective;
    }

    return RepricingDecision{
        .strategy =
            strategy,

        .affected_instruments =
            affected_instruments,

        .total_instruments =
            total_instruments,

        .affected_fraction =
            affected_fraction,

        .estimated_omitted_error_bps =
            estimated_omitted_error_bps,
    };
}


std::string_view to_string(
    const RepricingStrategy strategy
) noexcept {
    switch (strategy) {
        case RepricingStrategy::Skip:
            return "SKIP";

        case RepricingStrategy::Selective:
            return "SELECTIVE";

        case RepricingStrategy::Full:
            return "FULL";
    }

    return "UNKNOWN";
}

}  // namespace mercator::pricing
