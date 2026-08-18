#include "mercator/pricing/curve_replay.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

void expect_near(
    const double actual,
    const double expected
) {
    if (
        std::abs(actual - expected)
        > 1e-12
    ) {
        throw std::runtime_error(
            "unexpected curve value"
        );
    }
}


void expect_failure(
    const auto& operation
) {
    bool failed = false;

    try {
        operation();
    }
    catch (const std::runtime_error&) {
        failed = true;
    }

    if (!failed) {
        throw std::runtime_error(
            "expected replay failure"
        );
    }
}

}  // namespace


int main() {
    using namespace mercator::pricing;

    const std::vector<CurvePoint> initial{
        {1.0, 0.0400},
        {2.0, 0.0410},
        {5.0, 0.0430},
    };

    const CurveUpdateEvent version_2{
        .event_id = "v2",
        .previous_version = 1,
        .new_version = 2,
        .updates = {
            CurveNodeUpdate{
                .node_id = 2,
                .maturity_years = 2.0,
                .old_rate = 0.0410,
                .new_rate = 0.0420,
            },
        },
    };

    const CurveUpdateEvent version_3{
        .event_id = "v3",
        .previous_version = 2,
        .new_version = 3,
        .updates = {
            CurveNodeUpdate{
                .node_id = 3,
                .maturity_years = 5.0,
                .old_rate = 0.0430,
                .new_rate = 0.0440,
            },
        },
    };

    /*
     * Intentionally pass events out of order.
     * Replay must establish deterministic
     * version ordering itself.
     */
    const auto replayed =
        replay_curve_updates(
            initial,
            1,
            {
                version_3,
                version_2,
            },
            3
        );

    expect_near(
        replayed[0].zero_rate,
        0.0400
    );

    expect_near(
        replayed[1].zero_rate,
        0.0420
    );

    expect_near(
        replayed[2].zero_rate,
        0.0440
    );

    /*
     * Version gap.
     */
    expect_failure(
        [&]() {
            const CurveUpdateEvent gap{
                .event_id = "gap",
                .previous_version = 7,
                .new_version = 8,
                .updates = {},
            };

            (void) replay_curve_updates(
                initial,
                1,
                {gap},
                8
            );
        }
    );

    /*
     * Corrupt provenance: event says the old
     * rate was something other than the state
     * reconstructed by replay.
     */
    expect_failure(
        [&]() {
            auto corrupt = version_2;

            corrupt.updates[0].old_rate =
                0.0999;

            (void) replay_curve_updates(
                initial,
                1,
                {corrupt},
                2
            );
        }
    );

    /*
     * Missing target version.
     */
    expect_failure(
        [&]() {
            (void) replay_curve_updates(
                initial,
                1,
                {version_2},
                3
            );
        }
    );

    std::cout
        << "All curve replay tests passed.\n";

    return 0;
}
