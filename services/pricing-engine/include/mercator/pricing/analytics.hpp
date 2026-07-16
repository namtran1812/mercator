#pragma once

#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <vector>

namespace mercator::pricing {

struct BondAnalytics {
    double dirty_price;
    double yield_to_maturity;
    double macaulay_duration;
    double modified_duration;
    double convexity;
};

double year_fraction_actual_365(
    Date start_date,
    Date end_date
);


double present_value_from_curve(
    const std::vector<CashFlow>& cashflows,
    Date valuation_date,
    const YieldCurve& curve,
    double spread_bps = 0.0
);

double present_value(
    const std::vector<CashFlow>& cashflows,
    Date valuation_date,
    double annual_yield,
    int payments_per_year
);

double solve_yield_to_maturity(
    const std::vector<CashFlow>& cashflows,
    Date valuation_date,
    double target_price,
    int payments_per_year,
    double lower_bound = -0.95,
    double upper_bound = 1.00,
    double tolerance = 1e-10,
    int max_iterations = 200
);

BondAnalytics calculate_bond_analytics(
    const std::vector<CashFlow>& cashflows,
    Date valuation_date,
    double market_price,
    int payments_per_year
);

}  // namespace mercator::pricing
