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

namespace mercator::pricing {

double present_value_from_curve(
    const std::vector<CashFlow>& cashflows,
    const Date valuation_date,
    const YieldCurve& curve,
    const double spread_bps
) {
    const double spread =
        spread_bps / 10'000.0;

    double price = 0.0;

    for (const auto& cashflow : cashflows) {
        if (
            std::chrono::sys_days{cashflow.payment_date} <=
            std::chrono::sys_days{valuation_date}
        ) {
            continue;
        }

        const double years =
            year_fraction_actual_365(
                valuation_date,
                cashflow.payment_date
            );

        const double rate =
            curve.zero_rate(years) + spread;

        const double discount_factor =
            std::exp(-rate * years);

        price += cashflow.amount * discount_factor;
    }

    return price;
}

}  // namespace mercator::pricing

namespace mercator::pricing {

namespace {

Date previous_coupon_date(
    const CouponSchedule& schedule,
    const Date settlement_date
) {
    Date previous = schedule.issue_date;

    for (const auto& cashflow : schedule.cashflows) {
        if (
            std::chrono::sys_days{cashflow.payment_date} >
            std::chrono::sys_days{settlement_date}
        ) {
            break;
        }

        previous = cashflow.payment_date;
    }

    return previous;
}

Date next_coupon_date(
    const CouponSchedule& schedule,
    const Date settlement_date
) {
    for (const auto& cashflow : schedule.cashflows) {
        if (
            std::chrono::sys_days{cashflow.payment_date} >
            std::chrono::sys_days{settlement_date}
        ) {
            return cashflow.payment_date;
        }
    }

    return schedule.maturity_date;
}

}  // namespace

double accrued_interest_actual_actual(
    const CouponSchedule& schedule,
    const Date settlement_date
) {
    if (
        std::chrono::sys_days{settlement_date} <=
        std::chrono::sys_days{schedule.issue_date}
    ) {
        return 0.0;
    }

    if (
        std::chrono::sys_days{settlement_date} >=
        std::chrono::sys_days{schedule.maturity_date}
    ) {
        return 0.0;
    }

    const Date previous =
        previous_coupon_date(
            schedule,
            settlement_date
        );

    const Date next =
        next_coupon_date(
            schedule,
            settlement_date
        );

    const auto elapsed_days =
        (
            std::chrono::sys_days{settlement_date} -
            std::chrono::sys_days{previous}
        ).count();

    const auto period_days =
        (
            std::chrono::sys_days{next} -
            std::chrono::sys_days{previous}
        ).count();

    if (period_days <= 0) {
        throw std::runtime_error(
            "invalid coupon period"
        );
    }

    const double coupon_amount =
        schedule.face_value *
        schedule.annual_coupon_rate /
        static_cast<double>(
            schedule.payments_per_year
        );

    return coupon_amount *
        static_cast<double>(elapsed_days) /
        static_cast<double>(period_days);
}

PriceBreakdown price_from_curve(
    const CouponSchedule& schedule,
    const Date settlement_date,
    const YieldCurve& curve,
    const double spread_bps
) {
    const double dirty_price =
        present_value_from_curve(
            schedule.cashflows,
            settlement_date,
            curve,
            spread_bps
        );

    const double accrued_interest =
        accrued_interest_actual_actual(
            schedule,
            settlement_date
        );

    return PriceBreakdown{
        .clean_price =
            dirty_price - accrued_interest,
        .dirty_price = dirty_price,
        .accrued_interest = accrued_interest,
    };
}

double solve_g_spread_bps(
    const CouponSchedule& schedule,
    const Date settlement_date,
    const YieldCurve& curve,
    const double target_dirty_price,
    double lower_bound_bps,
    double upper_bound_bps,
    const double tolerance,
    const int max_iterations
) {
    if (target_dirty_price <= 0.0) {
        throw std::invalid_argument(
            "target_dirty_price must be positive"
        );
    }

    const double lower_price =
        price_from_curve(
            schedule,
            settlement_date,
            curve,
            lower_bound_bps
        ).dirty_price;

    const double upper_price =
        price_from_curve(
            schedule,
            settlement_date,
            curve,
            upper_bound_bps
        ).dirty_price;

    if (
        lower_price < target_dirty_price ||
        upper_price > target_dirty_price
    ) {
        throw std::runtime_error(
            "G-spread bounds do not bracket target price"
        );
    }

    for (
        int iteration = 0;
        iteration < max_iterations;
        ++iteration
    ) {
        const double midpoint =
            (lower_bound_bps + upper_bound_bps) /
            2.0;

        const double midpoint_price =
            price_from_curve(
                schedule,
                settlement_date,
                curve,
                midpoint
            ).dirty_price;

        if (
            std::abs(
                midpoint_price -
                target_dirty_price
            ) < tolerance
        ) {
            return midpoint;
        }

        if (midpoint_price > target_dirty_price) {
            lower_bound_bps = midpoint;
        } else {
            upper_bound_bps = midpoint;
        }
    }

    return (
        lower_bound_bps +
        upper_bound_bps
    ) / 2.0;
}

}  // namespace mercator::pricing
