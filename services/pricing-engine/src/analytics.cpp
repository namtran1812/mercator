#include "mercator/pricing/analytics.hpp"

#include <cmath>
#include <stdexcept>

namespace mercator::pricing {

double year_fraction_actual_365(
    const Date start_date,
    const Date end_date
) {
    const auto start = std::chrono::sys_days{start_date};
    const auto end = std::chrono::sys_days{end_date};

    if (end < start) {
        throw std::invalid_argument(
            "end_date must not be before start_date"
        );
    }

    const auto days =
        std::chrono::duration_cast<std::chrono::days>(end - start).count();

    return static_cast<double>(days) / 365.0;
}

double present_value(
    const std::vector<CashFlow>& cashflows,
    const Date valuation_date,
    const double annual_yield,
    const int payments_per_year
) {
    if (payments_per_year <= 0) {
        throw std::invalid_argument(
            "payments_per_year must be positive"
        );
    }

    const double periodic_yield =
        annual_yield / static_cast<double>(payments_per_year);

    if (1.0 + periodic_yield <= 0.0) {
        throw std::invalid_argument(
            "yield produces a non-positive discount base"
        );
    }

    double price = 0.0;

    for (const auto& cashflow : cashflows) {
        if (std::chrono::sys_days{cashflow.payment_date} <=
            std::chrono::sys_days{valuation_date}) {
            continue;
        }

        const double years =
            year_fraction_actual_365(
                valuation_date,
                cashflow.payment_date
            );

        const double periods =
            years * static_cast<double>(payments_per_year);

        const double discount_factor =
            std::pow(1.0 + periodic_yield, periods);

        price += cashflow.amount / discount_factor;
    }

    return price;
}

double solve_yield_to_maturity(
    const std::vector<CashFlow>& cashflows,
    const Date valuation_date,
    const double target_price,
    const int payments_per_year,
    double lower_bound,
    double upper_bound,
    const double tolerance,
    const int max_iterations
) {
    if (target_price <= 0.0) {
        throw std::invalid_argument(
            "target_price must be positive"
        );
    }

    double lower_price = present_value(
        cashflows,
        valuation_date,
        lower_bound,
        payments_per_year
    );

    double upper_price = present_value(
        cashflows,
        valuation_date,
        upper_bound,
        payments_per_year
    );

    if (!(lower_price >= target_price &&
          upper_price <= target_price)) {
        throw std::runtime_error(
            "yield bounds do not bracket the target price"
        );
    }

    for (int iteration = 0;
         iteration < max_iterations;
         ++iteration) {
        const double midpoint =
            (lower_bound + upper_bound) / 2.0;

        const double midpoint_price = present_value(
            cashflows,
            valuation_date,
            midpoint,
            payments_per_year
        );

        if (std::abs(midpoint_price - target_price) < tolerance) {
            return midpoint;
        }

        if (midpoint_price > target_price) {
            lower_bound = midpoint;
        } else {
            upper_bound = midpoint;
        }
    }

    return (lower_bound + upper_bound) / 2.0;
}

BondAnalytics calculate_bond_analytics(
    const std::vector<CashFlow>& cashflows,
    const Date valuation_date,
    const double market_price,
    const int payments_per_year
) {
    const double ytm = solve_yield_to_maturity(
        cashflows,
        valuation_date,
        market_price,
        payments_per_year
    );

    const double periodic_yield =
        ytm / static_cast<double>(payments_per_year);

    double weighted_time = 0.0;
    double convexity_numerator = 0.0;
    double calculated_price = 0.0;

    for (const auto& cashflow : cashflows) {
        if (std::chrono::sys_days{cashflow.payment_date} <=
            std::chrono::sys_days{valuation_date}) {
            continue;
        }

        const double years =
            year_fraction_actual_365(
                valuation_date,
                cashflow.payment_date
            );

        const double periods =
            years * static_cast<double>(payments_per_year);

        const double discount_factor =
            std::pow(1.0 + periodic_yield, periods);

        const double pv =
            cashflow.amount / discount_factor;

        calculated_price += pv;
        weighted_time += years * pv;

        convexity_numerator +=
            cashflow.amount *
            periods *
            (periods + 1.0) /
            std::pow(
                1.0 + periodic_yield,
                periods + 2.0
            );
    }

    const double macaulay_duration =
        weighted_time / calculated_price;

    const double modified_duration =
        macaulay_duration /
        (1.0 + periodic_yield);

    const double convexity =
        convexity_numerator /
        (
            calculated_price *
            static_cast<double>(
                payments_per_year * payments_per_year
            )
        );

    return BondAnalytics{
        .dirty_price = calculated_price,
        .yield_to_maturity = ytm,
        .macaulay_duration = macaulay_duration,
        .modified_duration = modified_duration,
        .convexity = convexity,
    };
}

}  // namespace mercator::pricing
