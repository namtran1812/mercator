#pragma once

#include <cstddef>
#include <string_view>

namespace mercator::pricing {

enum class RepricingStrategy {
    Skip,
    Selective,
    Full,
};

struct AdaptiveRepricingPolicy {
    double error_budget_bps{0.25};
    double full_reprice_fraction{0.70};
};

struct RepricingDecision {
    RepricingStrategy strategy;

    std::size_t affected_instruments;
    std::size_t total_instruments;

    double affected_fraction;

    double estimated_omitted_error_bps;
};

[[nodiscard]]
RepricingDecision choose_repricing_strategy(
    std::size_t affected_instruments,
    std::size_t total_instruments,
    double estimated_omitted_error_bps,
    const AdaptiveRepricingPolicy& policy
);

[[nodiscard]]
std::string_view to_string(
    RepricingStrategy strategy
) noexcept;

}  // namespace mercator::pricing
