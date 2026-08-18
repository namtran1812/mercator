#pragma once

#include "mercator/pricing/curve_update.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace mercator::pricing {

class CurveReplaySink {
public:
    CurveReplaySink(
        std::string base_url,
        std::string database,
        std::string username,
        std::string password
    );

    void insert_event(
        const CurveUpdateEvent& event
    ) const;

    void insert_checkpoint(
        const CurveUpdateEvent& event,
        Date valuation_date,
        const std::vector<CurvePoint>& curve_points
    ) const;

    [[nodiscard]]
    bool should_checkpoint(
        std::uint64_t version,
        std::uint64_t interval
    ) const noexcept;

private:
    void execute_insert(
        const std::string& query,
        const std::string& payload
    ) const;

    std::string base_url_;
    std::string database_;
    std::string username_;
    std::string password_;
};

}  // namespace mercator::pricing
