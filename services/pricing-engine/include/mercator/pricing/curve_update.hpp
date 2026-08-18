#pragma once

#include "mercator/pricing/dependency_graph.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace mercator::pricing {

struct CurveNodeUpdate {
    CurveNodeId node_id;
    double maturity_years;
    double old_rate;
    double new_rate;
};

struct CurveUpdateEvent {
    std::string event_id;

    /*
     * Replay/audit metadata travels with the event rather
     * than being synthesized by persistence sinks.
     */
    std::string event_time;
    std::string curve_name;
    std::string source;
    std::string scenario_name;

    std::uint64_t previous_version;
    std::uint64_t new_version;

    std::vector<CurveNodeUpdate> updates;
};

}  // namespace mercator::pricing
