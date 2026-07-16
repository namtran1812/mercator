#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"

#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>

namespace {

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

    const auto cashflows = generate_fixed_rate_cashflows(
        1000.0,
        0.05,
        2,
        issue_date,
        maturity_date
    );

    const double par_price = present_value(
        cashflows,
        issue_date,
        0.05,
        2
    );

    expect_near(
        par_price,
        1000.0,
        1.0,
        "coupon rate equal to yield should price near par"
    );

    const double solved_yield = solve_yield_to_maturity(
        cashflows,
        issue_date,
        par_price,
        2
    );

    expect_near(
        solved_yield,
        0.05,
        1e-8,
        "yield solver should recover original yield"
    );

    const auto analytics = calculate_bond_analytics(
        cashflows,
        issue_date,
        par_price,
        2
    );

    if (analytics.modified_duration <= 0.0) {
        throw std::runtime_error(
            "modified duration must be positive"
        );
    }

    if (analytics.convexity <= 0.0) {
        throw std::runtime_error(
            "convexity must be positive"
        );
    }

    std::cout << "All analytics tests passed.\n";
    return 0;
}
