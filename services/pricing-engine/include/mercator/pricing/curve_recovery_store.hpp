#pragma once

#include "mercator/pricing/curve_update.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace mercator::pricing {

struct RecoveredCurve {
    std::uint64_t version;
    std::vector<CurvePoint> points;
};

class CurveRecoveryStore {
public:
    CurveRecoveryStore(
        std::string base_url,
        std::string database,
        std::string username,
        std::string password
    );

    [[nodiscard]]
    std::optional<RecoveredCurve> recover_latest(
        const std::string& curve_name
    ) const;

    [[nodiscard]]
    std::vector<CurveUpdateEvent> recover_events_after(
        const std::string& curve_name,
        std::uint64_t version
    ) const;

private:
    std::string execute_query(
        const std::string& query
    ) const;

    std::string base_url_;
    std::string database_;
    std::string username_;
    std::string password_;
};

}  // namespace mercator::pricing
