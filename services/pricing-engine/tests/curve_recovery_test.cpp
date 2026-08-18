#include "mercator/pricing/curve_replay.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace mercator::pricing;


namespace {

void require(
    const bool condition,
    const std::string& message
) {
    if (!condition) {
        throw std::runtime_error(
            message
        );
    }
}


void require_near(
    const double actual,
    const double expected,
    const double tolerance,
    const std::string& message
) {
    if (
        std::abs(
            actual - expected
        ) > tolerance
    ) {
        throw std::runtime_error(
            message
        );
    }
}


std::vector<CurvePoint>
checkpoint_v163() {
    return {
        {0.25, 0.0430},
        {0.50, 0.0420},
        {1.00, 0.0410},
        {2.00, 0.0400},
        {3.00, 0.0410},
        {5.00, 0.0430},
        {7.00, 0.0450},
        {10.00, 0.0460},
        {30.00, 0.0471},
    };
}


CurveUpdateEvent event_163_to_164() {
    return CurveUpdateEvent{
        .event_id =
            "c61a75a6-8a2a-4321-922f-076771c60872",

        .event_time =
            "2026-08-18T05:17:47Z",

        .curve_name =
            "UST",

        .source =
            "recovery-test",

        .scenario_name =
            "live",

        .previous_version =
            163,

        .new_version =
            164,

        .updates = {
            CurveNodeUpdate{
                .node_id = 9,
                .maturity_years = 30.0,
                .old_rate = 0.0471,
                .new_rate = 0.0472,
            },
        },
    };
}


void test_recovers_checkpoint_without_deltas() {
    const auto state =
        recover_curve_state(
            checkpoint_v163(),
            163,
            {}
        );

    require(
        state.version == 163,
        "checkpoint-only recovery version mismatch"
    );

    require(
        state.points.size() == 9,
        "checkpoint-only recovery node count mismatch"
    );

    require_near(
        recovered_curve_rate(
            state,
            30.0
        ),
        0.0471,
        1e-12,
        "checkpoint-only 30Y rate mismatch"
    );
}


void test_recovers_contiguous_delta() {
    const auto state =
        recover_curve_state(
            checkpoint_v163(),
            163,
            {
                event_163_to_164(),
            }
        );

    require(
        state.version == 164,
        "delta recovery did not reach v164"
    );

    require(
        state.points.size() == 9,
        "delta recovery changed curve node count"
    );

    require_near(
        recovered_curve_rate(
            state,
            30.0
        ),
        0.0472,
        1e-12,
        "delta recovery 30Y rate mismatch"
    );

    require_near(
        recovered_curve_rate(
            state,
            10.0
        ),
        0.0460,
        1e-12,
        "unchanged node moved during recovery"
    );
}


void test_version_gap_is_rejected() {
    auto bad =
        event_163_to_164();

    bad.previous_version = 162;
    bad.new_version = 164;

    bool failed = false;

    try {
        (void) recover_curve_state(
            checkpoint_v163(),
            163,
            {bad}
        );
    }
    catch (const std::runtime_error&) {
        failed = true;
    }

    require(
        failed,
        "version gap was not rejected"
    );
}


void test_old_rate_mismatch_is_rejected() {
    auto bad =
        event_163_to_164();

    bad.updates[0].old_rate =
        0.0999;

    bool failed = false;

    try {
        (void) recover_curve_state(
            checkpoint_v163(),
            163,
            {bad}
        );
    }
    catch (const std::runtime_error&) {
        failed = true;
    }

    require(
        failed,
        "old-rate mismatch was not rejected"
    );
}


void test_duplicate_logical_event_is_ignored() {
    const auto event =
        event_163_to_164();

    const auto state =
        recover_curve_state(
            checkpoint_v163(),
            163,
            {
                event,
                event,
            }
        );

    require(
        state.version == 164,
        "duplicate event changed final version"
    );

    require_near(
        recovered_curve_rate(
            state,
            30.0
        ),
        0.0472,
        1e-12,
        "duplicate event changed final rate"
    );
}

}  // namespace


int main() {
    test_recovers_checkpoint_without_deltas();
    test_recovers_contiguous_delta();
    test_version_gap_is_rejected();
    test_old_rate_mismatch_is_rejected();
    test_duplicate_logical_event_is_ignored();

    std::cout
        << "All curve recovery tests passed.\n";

    return 0;
}
