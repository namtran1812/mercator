#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_near(
    const double actual,
    const double expected,
    const double tolerance,
    const char* message
) {
    if (std::abs(actual - expected) > tolerance) {
        std::cerr
            << message
            << ": expected "
            << expected
            << ", got "
            << actual
            << "\n";

        throw std::runtime_error(message);
    }
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const Date issue_date{
        year{2026},
        month{1},
        day{15}
    };

    const Date maturity_date{
        year{2031},
        month{1},
        day{15}
    };

    const Date settlement_date{
        year{2026},
        month{4},
        day{15}
    };

    const auto schedule =
        generate_fixed_rate_schedule(
            1000.0,
            0.06,
            2,
            issue_date,
            maturity_date
        );

    const YieldCurve curve{
        1,
        settlement_date,
        std::vector<CurvePoint>{
            {0.25, 0.04},
            {1.00, 0.04},
            {2.00, 0.04},
            {5.00, 0.04},
            {10.00, 0.04},
        }
    };

    const double accrued =
        accrued_interest_actual_actual(
            schedule,
            settlement_date
        );

    expect_near(
        accrued,
        15.0,
        0.25,
        "half-period accrued interest should be near 15"
    );

    const auto price =
        price_from_curve(
            schedule,
            settlement_date,
            curve,
            175.0
        );

    require(
        price.dirty_price > price.clean_price,
        "dirty price must exceed clean price between coupons"
    );

    expect_near(
        price.dirty_price - price.clean_price,
        accrued,
        1e-10,
        "clean/dirty difference must equal accrued interest"
    );

    const double solved_spread =
        solve_g_spread_bps(
            schedule,
            settlement_date,
            curve,
            price.dirty_price
        );

    expect_near(
        solved_spread,
        175.0,
        1e-6,
        "spread solver should recover input spread"
    );

    std::cout
        << "All clean price and G-spread tests passed.\n";

    return 0;
}
