#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/evaluated_price.hpp"
#include "mercator/pricing/repricing_service.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(
            message
        );
    }
}

void require_close(
    const double left,
    const double right,
    const double tolerance,
    const char* message
) {
    if (
        std::abs(
            left - right
        )
        > tolerance
    ) {
        throw std::runtime_error(
            message
        );
    }
}

void compare_price(
    const mercator::pricing::EvaluatedPrice& left,
    const mercator::pricing::EvaluatedPrice& right
) {
    constexpr double tolerance =
        1e-12;

    require(
        left.instrument_id
            == right.instrument_id,
        "instrument_id mismatch"
    );

    require_close(
        left.clean_price,
        right.clean_price,
        tolerance,
        "clean_price mismatch"
    );

    require_close(
        left.dirty_price,
        right.dirty_price,
        tolerance,
        "dirty_price mismatch"
    );

    require_close(
        left.yield_to_maturity,
        right.yield_to_maturity,
        tolerance,
        "yield_to_maturity mismatch"
    );

    require_close(
        left.g_spread_bps,
        right.g_spread_bps,
        tolerance,
        "g_spread_bps mismatch"
    );

    require_close(
        left.modified_duration,
        right.modified_duration,
        tolerance,
        "modified_duration mismatch"
    );

    require_close(
        left.convexity,
        right.convexity,
        tolerance,
        "convexity mismatch"
    );

    require(
        left.curve_version
            == right.curve_version,
        "curve_version mismatch"
    );

    require(
        left.reference_version
            == right.reference_version,
        "reference_version mismatch"
    );

    require_close(
        left.quality_score,
        right.quality_score,
        tolerance,
        "quality_score mismatch"
    );

    require(
        left.quality_status
            == right.quality_status,
        "quality_status mismatch"
    );

    require(
        left.model_version
            == right.model_version,
        "model_version mismatch"
    );

    require(
        left.calculation_trace_id
            == right.calculation_trace_id,
        "calculation_trace_id mismatch"
    );

    require(
        left.source_event_id
            == right.source_event_id,
        "source_event_id mismatch"
    );

    /*
     * event_time is intentionally excluded.
     *
     * Each result is timestamped when the individual
     * valuation completes, so thread scheduling can
     * legitimately produce different wall-clock times.
     */
}

}  // namespace


int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;


    const Date valuation_date{
        year{2026},
        month{7},
        day{15},
    };


    const std::vector<CurvePoint>
        curve_points{
            {0.25, 0.0380},
            {0.50, 0.0385},
            {1.00, 0.0390},
            {2.00, 0.0400},
            {3.00, 0.0410},
            {5.00, 0.0430},
            {7.00, 0.0440},
            {10.00, 0.0460},
            {30.00, 0.0495},
        };


    const YieldCurve curve{
        43,
        valuation_date,
        curve_points,
    };


    std::unordered_map<
        InstrumentId,
        PricingInstrument
    > instruments;


    PricingDependencyGraph dependency_graph;


    constexpr std::size_t instrument_count =
        2'000;


    for (
        std::size_t index = 0;
        index < instrument_count;
        ++index
    ) {
        const InstrumentId instrument_id =
            static_cast<InstrumentId>(
                index + 1
            );


        const int maturity_years =
            2
            + static_cast<int>(
                index % 14
            );


        const double coupon =
            0.03
            + static_cast<double>(
                index % 20
            )
            * 0.001;


        const Date maturity_date{
            year{
                2026
                + maturity_years
            },
            month{7},
            day{15},
        };


        auto schedule =
            generate_fixed_rate_schedule(
                1000.0,
                coupon,
                2,
                valuation_date,
                maturity_date
            );


        instruments.emplace(
            instrument_id,
            PricingInstrument{
                .instrument_id =
                    instrument_id,

                .schedule =
                    std::move(
                        schedule
                    ),

                .spread_bps =
                    50.0
                    + static_cast<double>(
                        index % 150
                    ),

                .market_confidence =
                    0.85,

                .reference_version =
                    7,
            }
        );


        dependency_graph.register_instrument(
            instrument_id,
            {
                4,
                6,
                8,
                9,
            }
        );
    }


    const CurveUpdateEvent event{
        .event_id =
            "11111111-2222-5333-8444-555555555555",

        .previous_version =
            42,

        .new_version =
            43,

        .updates =
            {
                CurveNodeUpdate{
                    .node_id = 9,
                    .maturity_years = 30.0,
                    .old_rate = 0.0494,
                    .new_rate = 0.0495,
                },
            },
    };


    RepricingService sequential{
        valuation_date,
        dependency_graph,
        instruments,
        1
    };


    RepricingService parallel{
        valuation_date,
        dependency_graph,
        instruments,
        8
    };


    const auto sequential_results =
        sequential.reprice_all(
            event,
            curve
        );


    const auto parallel_results =
        parallel.reprice_all(
            event,
            curve
        );


    require(
        sequential_results.size()
            == instrument_count,
        "unexpected sequential result count"
    );

    require(
        parallel_results.size()
            == instrument_count,
        "unexpected parallel result count"
    );


    require(
        sequential_results.size()
            == parallel_results.size(),
        "result sizes differ"
    );


    for (
        std::size_t index = 0;
        index < sequential_results.size();
        ++index
    ) {
        compare_price(
            sequential_results[index],
            parallel_results[index]
        );
    }


    std::cout
        << "Parallel repricing matches "
        << "sequential repricing for "
        << sequential_results.size()
        << " instruments.\n";


    return 0;
}
