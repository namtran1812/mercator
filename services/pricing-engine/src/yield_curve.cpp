#include "mercator/pricing/yield_curve.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace mercator::pricing {

YieldCurve::YieldCurve(
    const std::uint64_t version,
    const Date as_of_date,
    std::vector<CurvePoint> points
)
    : version_(version),
      as_of_date_(as_of_date),
      points_(std::move(points)) {
    if (points_.empty()) {
        throw std::invalid_argument(
            "yield curve must contain at least one point"
        );
    }

    std::sort(
        points_.begin(),
        points_.end(),
        [](const CurvePoint& left, const CurvePoint& right) {
            return left.maturity_years < right.maturity_years;
        }
    );

    for (std::size_t index = 0; index < points_.size(); ++index) {
        if (points_[index].maturity_years <= 0.0) {
            throw std::invalid_argument(
                "curve maturities must be positive"
            );
        }

        if (points_[index].zero_rate <= -1.0) {
            throw std::invalid_argument(
                "zero rates must exceed -100%"
            );
        }

        if (
            index > 0 &&
            points_[index - 1].maturity_years ==
                points_[index].maturity_years
        ) {
            throw std::invalid_argument(
                "curve maturities must be unique"
            );
        }
    }
}

std::uint64_t YieldCurve::version() const noexcept {
    return version_;
}

Date YieldCurve::as_of_date() const noexcept {
    return as_of_date_;
}

double YieldCurve::zero_rate(
    const double maturity_years
) const {
    if (maturity_years <= 0.0) {
        throw std::invalid_argument(
            "maturity_years must be positive"
        );
    }

    if (maturity_years <= points_.front().maturity_years) {
        return points_.front().zero_rate;
    }

    if (maturity_years >= points_.back().maturity_years) {
        return points_.back().zero_rate;
    }

    const auto upper = std::lower_bound(
        points_.begin(),
        points_.end(),
        maturity_years,
        [](const CurvePoint& point, const double maturity) {
            return point.maturity_years < maturity;
        }
    );

    const auto lower = upper - 1;

    const double width =
        upper->maturity_years - lower->maturity_years;

    const double weight =
        (maturity_years - lower->maturity_years) / width;

    return lower->zero_rate +
        weight * (upper->zero_rate - lower->zero_rate);
}

double YieldCurve::discount_factor(
    const double maturity_years
) const {
    const double rate = zero_rate(maturity_years);

    return std::exp(-rate * maturity_years);
}

}  // namespace mercator::pricing
