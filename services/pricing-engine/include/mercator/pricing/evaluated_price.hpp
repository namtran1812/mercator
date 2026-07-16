#pragma once

#include <chrono>
#include <cstdint>
#include <string>

namespace mercator::pricing {

struct EvaluatedPrice {
    std::uint64_t instrument_id;

    double clean_price;
    double dirty_price;
    double yield_to_maturity;
    double g_spread_bps;
    double modified_duration;
    double convexity;

    std::uint64_t curve_version;
    std::uint64_t reference_version;

    double quality_score;
    std::string quality_status;
    std::string model_version;
    std::string calculation_trace_id;
    std::string source_event_id;

    std::chrono::system_clock::time_point event_time;
    std::chrono::system_clock::time_point received_time;
};

}  // namespace mercator::pricing
