#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/price_replay.hpp"
#include "mercator/pricing/repricing_service.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <nlohmann/json.hpp>

#include <chrono>
#include <cstdint>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using namespace mercator::pricing;
using json = nlohmann::json;

Date parse_date(const std::string& value) {
    if (
        value.size() != 10
        || value[4] != '-'
        || value[7] != '-'
    ) {
        throw std::invalid_argument(
            "date must use YYYY-MM-DD format"
        );
    }

    const int year_value =
        std::stoi(value.substr(0, 4));

    const unsigned month_value =
        static_cast<unsigned>(
            std::stoul(value.substr(5, 2))
        );

    const unsigned day_value =
        static_cast<unsigned>(
            std::stoul(value.substr(8, 2))
        );

    const Date date{
        std::chrono::year{year_value},
        std::chrono::month{month_value},
        std::chrono::day{day_value}
    };

    if (!date.ok()) {
        throw std::invalid_argument(
            "date is not a valid calendar date"
        );
    }

    return date;
}

const char* status_name(
    const ReplayVerificationStatus status
) {
    switch (status) {
        case ReplayVerificationStatus::Verified:
            return "REPLAY_VERIFIED";

        case ReplayVerificationStatus::Mismatch:
            return "REPLAY_MISMATCH";
    }

    throw std::runtime_error(
        "unknown replay verification status"
    );
}

}  // namespace

int main() {
    using namespace mercator::pricing;

    const std::string payload{
        std::istreambuf_iterator<char>{std::cin},
        std::istreambuf_iterator<char>{}
    };

    try {
        const json request =
            json::parse(payload);

        const auto valuation_date =
            parse_date(
                request.at(
                    "valuation_date"
                ).get<std::string>()
            );

        const auto maturity_date =
            parse_date(
                request.at(
                    "maturity_date"
                ).get<std::string>()
            );

        const auto instrument_id =
            request.at(
                "instrument_id"
            ).get<std::uint64_t>();

        const auto reference_version =
            request.at(
                "reference_version"
            ).get<std::uint64_t>();

        const auto curve_version =
            request.at(
                "curve_version"
            ).get<std::uint64_t>();

        const double coupon_rate =
            request.at(
                "coupon_rate"
            ).get<double>();

        const double spread_bps =
            request.at(
                "spread_bps"
            ).get<double>();

        const double persisted_clean =
            request.at(
                "clean_price"
            ).get<double>();

        const double persisted_dirty =
            request.at(
                "dirty_price"
            ).get<double>();

        const double tolerance =
            request.value(
                "absolute_tolerance",
                1e-10
            );

        /*
         * Match the production PostgreSQL loader.
         */
        const Date issue_date{
            valuation_date.year()
                - std::chrono::years{1},
            valuation_date.month(),
            std::chrono::day{1}
        };

        auto schedule =
            generate_fixed_rate_schedule(
                1000.0,
                coupon_rate,
                2,
                issue_date,
                maturity_date
            );

        const PricingInstrument instrument{
            .instrument_id =
                instrument_id,

            .schedule =
                std::move(schedule),

            .spread_bps =
                spread_bps,

            .market_confidence =
                1.0,

            .reference_version =
                reference_version,
        };

        std::vector<CurvePoint> curve_points;

        for (
            const auto& point :
            request.at("curve_points")
        ) {
            curve_points.push_back(
                CurvePoint{
                    .maturity_years =
                        point.at(
                            "maturity_years"
                        ).get<double>(),

                    .zero_rate =
                        point.at(
                            "zero_rate"
                        ).get<double>(),
                }
            );
        }

        if (curve_points.empty()) {
            throw std::invalid_argument(
                "curve_points must not be empty"
            );
        }

        const YieldCurve curve{
            curve_version,
            valuation_date,
            std::move(curve_points)
        };

        const PersistedPriceSnapshot persisted{
            .clean_price =
                persisted_clean,

            .dirty_price =
                persisted_dirty,

            .curve_version =
                curve_version,

            .reference_version =
                reference_version,
        };

        const auto result =
            verify_historical_price(
                instrument,
                valuation_date,
                curve,
                persisted,
                tolerance
            );

        const json response{
            {
                "status",
                status_name(result.status)
            },
            {
                "instrument_id",
                instrument_id
            },
            {
                "curve_version",
                result.curve_version
            },
            {
                "reference_version",
                result.reference_version
            },
            {
                "persisted_clean_price",
                persisted_clean
            },
            {
                "persisted_dirty_price",
                persisted_dirty
            },
            {
                "replayed_clean_price",
                result.replayed.clean_price
            },
            {
                "replayed_dirty_price",
                result.replayed.dirty_price
            },
            {
                "clean_price_error",
                result.clean_price_error
            },
            {
                "dirty_price_error",
                result.dirty_price_error
            },
            {
                "absolute_tolerance",
                tolerance
            }
        };

        std::cout
            << response.dump()
            << "\n";

        return 0;
    }
    catch (const std::exception& error) {
        const json response{
            {
                "status",
                "REPLAY_ERROR"
            },
            {
                "error",
                error.what()
            }
        };

        std::cout
            << response.dump()
            << "\n";

        return 1;
    }
}
