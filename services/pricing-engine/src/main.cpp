#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"

#include <chrono>
#include <iomanip>
#include <iostream>

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const Date issue_date{
        year{2026},
        month{1},
        day{15}
    };

    const Date valuation_date{
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

    const double market_price = 975.0;

    const BondAnalytics analytics =
        calculate_bond_analytics(
            cashflows,
            valuation_date,
            market_price,
            2
        );

    std::cout << std::fixed << std::setprecision(6);

    std::cout
        << "Dirty price: "
        << analytics.dirty_price
        << "\n";

    std::cout
        << "Yield to maturity: "
        << analytics.yield_to_maturity * 100.0
        << "%\n";

    std::cout
        << "Macaulay duration: "
        << analytics.macaulay_duration
        << "\n";

    std::cout
        << "Modified duration: "
        << analytics.modified_duration
        << "\n";

    std::cout
        << "Convexity: "
        << analytics.convexity
        << "\n";

    return 0;
}
