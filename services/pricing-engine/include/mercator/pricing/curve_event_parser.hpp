#pragma once

#include "mercator/pricing/curve_update.hpp"

#include <string_view>

namespace mercator::pricing {

[[nodiscard]]
CurveUpdateEvent parse_curve_update_event(
    std::string_view payload
);

}  // namespace mercator::pricing
