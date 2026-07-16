#pragma once

#include <chrono>
#include <vector>

namespace mercator::pricing {

using Date = std::chrono::year_month_day;

struct CashFlow {
    Date payment_date;
    double amount;
};

std::vector<CashFlow> generate_fixed_rate_cashflows(
    double face_value,
    double annual_coupon_rate,
    int payments_per_year,
    Date issue_date,
    Date maturity_date
);

}  // namespace mercator::pricing
