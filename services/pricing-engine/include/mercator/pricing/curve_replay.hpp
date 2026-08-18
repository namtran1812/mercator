#pragma once

#include "mercator/pricing/curve_update.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <cstdint>
#include <vector>

namespace mercator::pricing {

void apply_curve_update(
    std::vector<CurvePoint>& points,
    const CurveUpdateEvent& event
);


struct RecoveredCurveState {
    std::uint64_t version;
    std::vector<CurvePoint> points;
};

[[nodiscard]]
RecoveredCurveState recover_curve_state(
    std::vector<CurvePoint> checkpoint_points,
    std::uint64_t checkpoint_version,
    const std::vector<CurveUpdateEvent>& events
);

[[nodiscard]]
double recovered_curve_rate(
    const RecoveredCurveState& state,
    double maturity_years
);

[[nodiscard]]
std::vector<CurvePoint> replay_curve_updates(
    std::vector<CurvePoint> initial_points,
    std::uint64_t initial_version,
    const std::vector<CurveUpdateEvent>& events,
    std::uint64_t target_version
);

}  // namespace mercator::pricing
