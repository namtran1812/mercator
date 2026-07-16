#pragma once

#include "mercator/pricing/cashflow.hpp"

#include <cstdint>
#include <vector>

namespace mercator::pricing {

struct CurvePoint {
    double maturity_years;
    double zero_rate;
};

class YieldCurve {
public:
    YieldCurve(
        std::uint64_t version,
        Date as_of_date,
        std::vector<CurvePoint> points
    );

    [[nodiscard]] std::uint64_t version() const noexcept;
    [[nodiscard]] Date as_of_date() const noexcept;

    [[nodiscard]] double zero_rate(double maturity_years) const;
    [[nodiscard]] double discount_factor(double maturity_years) const;

private:
    std::uint64_t version_;
    Date as_of_date_;
    std::vector<CurvePoint> points_;
};

}  // namespace mercator::pricing
