#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

void expect_near(
    const double actual,
    const double expected,
    const double tolerance,
    const char* message
) {
    if (std::abs(actual - expected) > tolerance) {
        throw std::runtime_error(message);
    }
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const Date valuation_date{
        year{2026},
        month{7},
        day{15}
    };

    const YieldCurve curve{
        42,
        valuation_date,
        std::vector<CurvePoint>{
            {1.0, 0.04},
            {3.0, 0.05},
            {5.0, 0.06},
        }
    };

    expect_near(
        curve.zero_rate(2.0),
        0.045,
        1e-12,
        "linear interpolation failed"
    );

    expect_near(
        curve.zero_rate(0.5),
        0.04,
        1e-12,
        "short-end extrapolation failed"
    );

    expect_near(
        curve.zero_rate(10.0),
        0.06,
        1e-12,
        "long-end extrapolation failed"
    );

    const Date maturity_date{
        year{2031},
        month{7},
        day{15}
    };

    const auto cashflows = generate_fixed_rate_cashflows(
        1000.0,
        0.05,
        2,
        valuation_date,
        maturity_date
    );

    const double base_price =
        present_value_from_curve(
            cashflows,
            valuation_date,
            curve,
            0.0
        );

    const double wider_spread_price =
        present_value_from_curve(
            cashflows,
            valuation_date,
            curve,
            200.0
        );

    if (wider_spread_price >= base_price) {
        throw std::runtime_error(
            "higher spread should reduce bond price"
        );
    }

    std::cout << "All yield curve tests passed.\n";
    return 0;
}
