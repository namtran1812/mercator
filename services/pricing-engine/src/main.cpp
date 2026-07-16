#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <chrono>
#include <iomanip>
#include <iostream>
#include <vector>

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const Date valuation_date{
        year{2026},
        month{7},
        day{15}
    };

    const Date maturity_date{
        year{2031},
        month{7},
        day{15}
    };

    const auto cashflows = generate_fixed_rate_cashflows(
        1000.0,
        0.055,
        2,
        valuation_date,
        maturity_date
    );

    const YieldCurve treasury_curve{
        1,
        valuation_date,
        std::vector<CurvePoint>{
            {0.25, 0.0430},
            {0.50, 0.0420},
            {1.00, 0.0410},
            {2.00, 0.0400},
            {3.00, 0.0410},
            {5.00, 0.0430},
            {7.00, 0.0450},
            {10.00, 0.0460},
            {30.00, 0.0470},
        }
    };

    const double treasury_price =
        present_value_from_curve(
            cashflows,
            valuation_date,
            treasury_curve
        );

    const double credit_price =
        present_value_from_curve(
            cashflows,
            valuation_date,
            treasury_curve,
            150.0
        );

    std::cout << std::fixed << std::setprecision(6);

    std::cout
        << "Curve version: "
        << treasury_curve.version()
        << "\n";

    std::cout
        << "3.5Y interpolated zero rate: "
        << treasury_curve.zero_rate(3.5) * 100.0
        << "%\n";

    std::cout
        << "Treasury-discounted price: "
        << treasury_price
        << "\n";

    std::cout
        << "Price with 150 bp credit spread: "
        << credit_price
        << "\n";

    return 0;
}
