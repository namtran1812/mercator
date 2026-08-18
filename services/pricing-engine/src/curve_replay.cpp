#include "mercator/pricing/curve_replay.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>
#include <utility>

namespace mercator::pricing {

void apply_curve_update(
    std::vector<CurvePoint>& points,
    const CurveUpdateEvent& event
) {
    for (const auto& update : event.updates) {
        bool found = false;

        for (auto& point : points) {
            if (
                std::abs(
                    point.maturity_years
                    - update.maturity_years
                ) < 1e-12
            ) {
                if (
                    std::abs(
                        point.zero_rate
                        - update.old_rate
                    ) > 1e-10
                ) {
                    throw std::runtime_error(
                        "curve replay old-rate mismatch "
                        "at maturity "
                        + std::to_string(
                            update.maturity_years
                        )
                    );
                }

                point.zero_rate =
                    update.new_rate;

                found = true;
                break;
            }
        }

        if (!found) {
            throw std::runtime_error(
                "curve update referenced "
                "unknown maturity"
            );
        }
    }
}


std::vector<CurvePoint> replay_curve_updates(
    std::vector<CurvePoint> initial_points,
    const std::uint64_t initial_version,
    const std::vector<CurveUpdateEvent>& events,
    const std::uint64_t target_version
) {
    if (target_version < initial_version) {
        throw std::runtime_error(
            "target curve version precedes "
            "initial curve version"
        );
    }

    auto ordered_events = events;

    std::sort(
        ordered_events.begin(),
        ordered_events.end(),
        [](
            const CurveUpdateEvent& left,
            const CurveUpdateEvent& right
        ) {
            return left.new_version
                < right.new_version;
        }
    );

    std::uint64_t current_version =
        initial_version;

    for (const auto& event : ordered_events) {
        if (event.new_version <= current_version) {
            continue;
        }

        if (event.new_version > target_version) {
            break;
        }

        if (
            event.previous_version
            != current_version
        ) {
            throw std::runtime_error(
                "curve replay version gap: "
                "expected previous version "
                + std::to_string(current_version)
                + ", received "
                + std::to_string(
                    event.previous_version
                )
            );
        }

        apply_curve_update(
            initial_points,
            event
        );

        current_version =
            event.new_version;
    }

    if (current_version != target_version) {
        throw std::runtime_error(
            "curve replay did not reach target "
            "version "
            + std::to_string(target_version)
        );
    }

    return initial_points;
}

}  // namespace mercator::pricing
