#include "mercator/pricing/cashflow.hpp"

#include <stdexcept>

namespace mercator::pricing {

CouponSchedule generate_fixed_rate_schedule(
    const double face_value,
    const double annual_coupon_rate,
    const int payments_per_year,
    const Date issue_date,
    const Date maturity_date
) {
    if (face_value <= 0.0) {
        throw std::invalid_argument(
            "face_value must be positive"
        );
    }

    if (annual_coupon_rate < 0.0) {
        throw std::invalid_argument(
            "annual_coupon_rate cannot be negative"
        );
    }

    if (
        payments_per_year != 1 &&
        payments_per_year != 2 &&
        payments_per_year != 4
    ) {
        throw std::invalid_argument(
            "payments_per_year must be 1, 2, or 4"
        );
    }

    if (
        std::chrono::sys_days{maturity_date} <=
        std::chrono::sys_days{issue_date}
    ) {
        throw std::invalid_argument(
            "maturity_date must be after issue_date"
        );
    }

    const unsigned months_per_period =
        static_cast<unsigned>(
            12 / payments_per_year
        );

    const double coupon_amount =
        face_value *
        annual_coupon_rate /
        static_cast<double>(payments_per_year);

    std::vector<CashFlow> cashflows;

    Date payment_date =
        issue_date +
        std::chrono::months{months_per_period};

    while (
        std::chrono::sys_days{payment_date} <
        std::chrono::sys_days{maturity_date}
    ) {
        cashflows.push_back({
            .payment_date = payment_date,
            .amount = coupon_amount,
        });

        payment_date =
            payment_date +
            std::chrono::months{months_per_period};
    }

    cashflows.push_back({
        .payment_date = maturity_date,
        .amount = coupon_amount + face_value,
    });

    return CouponSchedule{
        .cashflows = std::move(cashflows),
        .issue_date = issue_date,
        .maturity_date = maturity_date,
        .face_value = face_value,
        .annual_coupon_rate = annual_coupon_rate,
        .payments_per_year = payments_per_year,
    };
}

std::vector<CashFlow> generate_fixed_rate_cashflows(
    const double face_value,
    const double annual_coupon_rate,
    const int payments_per_year,
    const Date issue_date,
    const Date maturity_date
) {
    return generate_fixed_rate_schedule(
        face_value,
        annual_coupon_rate,
        payments_per_year,
        issue_date,
        maturity_date
    ).cashflows;
}

}  // namespace mercator::pricing
