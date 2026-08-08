#include "mercator/pricing/adaptive_repricing.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>

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
    using namespace mercator::pricing;

    const AdaptiveRepricingPolicy policy{
        .error_budget_bps = 0.25,
        .full_reprice_fraction = 0.70,
    };


    /*
     * No material instruments and error inside budget:
     * skip work entirely.
     */

    const auto skip =
        choose_repricing_strategy(
            0,
            10'000,
            0.20,
            policy
        );

    require(
        skip.strategy
            == RepricingStrategy::Skip,
        "expected SKIP strategy"
    );


    /*
     * 97% fan-out:
     * selective routing is not worthwhile.
     */

    const auto full =
        choose_repricing_strategy(
            9'686,
            10'000,
            0.0,
            policy
        );

    require(
        full.strategy
            == RepricingStrategy::Full,
        "expected FULL strategy"
    );


    /*
     * ~66% fan-out:
     * measured benchmarks show selective execution
     * provides a useful latency reduction.
     */

    const auto selective =
        choose_repricing_strategy(
            6'654,
            10'000,
            0.033,
            policy
        );

    require(
        selective.strategy
            == RepricingStrategy::Selective,
        "expected SELECTIVE strategy"
    );


    /*
     * Exactly at crossover -> FULL.
     */

    const auto boundary =
        choose_repricing_strategy(
            7'000,
            10'000,
            0.0,
            policy
        );

    require(
        boundary.strategy
            == RepricingStrategy::Full,
        "70 percent fanout should use FULL"
    );


    require(
        to_string(
            RepricingStrategy::Selective
        )
        == "SELECTIVE",
        "strategy string conversion failed"
    );


    std::cout
        << "All adaptive repricing tests passed.\n";

    return 0;
}
