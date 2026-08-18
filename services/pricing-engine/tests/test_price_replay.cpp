#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/price_replay.hpp"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace mercator::pricing;

int main() {
    const Date valuation_date{
        std::chrono::year{2026},
        std::chrono::month{8},
        std::chrono::day{18}
    };

    CouponSchedule schedule;

    schedule.face_value = 100.0;
    schedule.annual_coupon_rate = 0.05;
    schedule.payments_per_year = 2;

    /*
     * Keep the fixture intentionally small.
     *
     * The replay verifier itself must not contain an
     * alternative pricing implementation. The persisted
     * values below are generated with the production
     * price_from_curve path and then independently replayed.
     */

    schedule.cashflows = {
        CashFlow{
            .payment_date = Date{
            std::chrono::year{2027},
            std::chrono::month{2},
            std::chrono::day{18}
        },
            .amount = 2.5
        },
        CashFlow{
            .payment_date = Date{
            std::chrono::year{2027},
            std::chrono::month{8},
            std::chrono::day{18}
        },
            .amount = 102.5
        },
    };

    const YieldCurve curve{
        42,
        valuation_date,
        {
            CurvePoint{
                .maturity_years = 0.5,
                .zero_rate = 0.04
            },
            CurvePoint{
                .maturity_years = 1.0,
                .zero_rate = 0.045
            },
        }
    };

    const PricingInstrument instrument{
        .instrument_id = 1001,
        .schedule = schedule,
        .spread_bps = 125.0,
        .market_confidence = 1.0,
        .reference_version = 17,
    };

    const PriceBreakdown original =
        price_from_curve(
            schedule,
            valuation_date,
            curve,
            instrument.spread_bps
        );

    const PersistedPriceSnapshot persisted{
        .clean_price = original.clean_price,
        .dirty_price = original.dirty_price,
        .curve_version = 42,
        .reference_version = 17,
    };

    const PriceReplayResult result =
        verify_historical_price(
            instrument,
            valuation_date,
            curve,
            persisted
        );

    assert(
        result.status
        == ReplayVerificationStatus::Verified
    );

    assert(
        std::abs(
            result.clean_price_error
        ) <= 1e-10
    );

    assert(
        std::abs(
            result.dirty_price_error
        ) <= 1e-10
    );

    assert(result.curve_version == 42);
    assert(result.reference_version == 17);

    /*
     * A persisted observation that differs materially
     * must never be labelled verified.
     */
    const PersistedPriceSnapshot mismatch{
        .clean_price =
            original.clean_price + 0.01,

        .dirty_price =
            original.dirty_price + 0.01,

        .curve_version = 42,
        .reference_version = 17,
    };

    const PriceReplayResult mismatch_result =
        verify_historical_price(
            instrument,
            valuation_date,
            curve,
            mismatch
        );

    assert(
        mismatch_result.status
        == ReplayVerificationStatus::Mismatch
    );

    std::cout
        << "historical price replay verified\n";

    return 0;
}
