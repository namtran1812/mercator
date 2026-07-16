#pragma once

#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <vector>

namespace mercator::pricing {


struct PriceBreakdown {
    double clean_price;
    double dirty_price;
    double accrued_interest;
};

double accrued_interest_actual_actual(
    const CouponSchedule& schedule,
    Date settlement_date
);

PriceBreakdown price_from_curve(
    const CouponSchedule& schedule,
    Date settlement_date,
    const YieldCurve& curve,
    double spread_bps = 0.0
);

double solve_g_spread_bps(
    const CouponSchedule& schedule,
    Date settlement_date,
    const YieldCurve& curve,
    double target_dirty_price,
    double lower_bound_bps = -1000.0,
    double upper_bound_bps = 5000.0,
    double tolerance = 1e-10,
    int max_iterations = 200
);

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
