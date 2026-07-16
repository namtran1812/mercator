#include "mercator/pricing/quote_reconciliation.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_near(
    const double actual,
    const double expected,
    const double tolerance,
    const char* message
) {
    if (std::abs(actual - expected) > tolerance) {
        throw std::runtime_error(message);
    }
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const auto now = system_clock::now();

    const std::vector<MarketQuote> quotes{
        {
            .quote_id = "q1",
            .source = "dealer-a",
            .instrument_id = 101,
            .bid = 99.80,
            .ask = 100.00,
            .event_time = now - seconds{1},
            .source_reliability = 1.0,
        },
        {
            .quote_id = "q2",
            .source = "dealer-b",
            .instrument_id = 101,
            .bid = 99.82,
            .ask = 100.02,
            .event_time = now - seconds{2},
            .source_reliability = 0.95,
        },
        {
            .quote_id = "q3",
            .source = "dealer-c",
            .instrument_id = 101,
            .bid = 99.78,
            .ask = 99.98,
            .event_time = now - seconds{3},
            .source_reliability = 0.90,
        },
        {
            .quote_id = "outlier",
            .source = "dealer-d",
            .instrument_id = 101,
            .bid = 89.00,
            .ask = 90.00,
            .event_time = now,
            .source_reliability = 1.0,
        },
        {
            .quote_id = "stale",
            .source = "dealer-e",
            .instrument_id = 101,
            .bid = 99.81,
            .ask = 100.01,
            .event_time = now - seconds{120},
            .source_reliability = 1.0,
        },
    };

    const QuoteReconciler reconciler{
        30.0,
        100.0
    };

    const auto result =
        reconciler.reconcile(
            101,
            quotes,
            now
        );

    require(
        result.accepted_sources == 3,
        "three valid sources should be accepted"
    );

    require(
        result.rejected_sources == 2,
        "outlier and stale quote should be rejected"
    );

    expect_near(
        result.evaluated_mid,
        99.90,
        0.05,
        "reconciled midpoint is incorrect"
    );

    require(
        result.confidence_score > 0.7,
        "consistent quotes should produce strong confidence"
    );

    require(
        result.source_dispersion_bps < 10.0,
        "accepted quote dispersion should be low"
    );

    std::cout
        << "All quote reconciliation tests passed.\n";

    return 0;
}
