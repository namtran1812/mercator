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

[[nodiscard]]
std::vector<CurvePoint> replay_curve_updates(
    std::vector<CurvePoint> initial_points,
    std::uint64_t initial_version,
    const std::vector<CurveUpdateEvent>& events,
    std::uint64_t target_version
);

}  // namespace mercator::pricing
