#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/curve_update.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/dependency_resolver.hpp"
#include "mercator/pricing/repricing_service.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <unordered_map>
#include <vector>

namespace {

std::int64_t epoch_microseconds(
    const std::chrono::system_clock::time_point time
) {
    return std::chrono::duration_cast<std::chrono::microseconds>(
        time.time_since_epoch()
    ).count();
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    constexpr std::uint64_t instrument_count = 10'000;

    const Date valuation_date{
        year{2026},
        month{7},
        day{15}
    };

    const std::vector<CurveNode> dependency_nodes{
        {1, 0.25},
        {2, 0.50},
        {3, 1.00},
        {4, 2.00},
        {5, 3.00},
        {6, 5.00},
        {7, 7.00},
        {8, 10.00},
        {9, 30.00},
    };

    const std::vector<CurvePoint> updated_points{
        {0.25, 0.0430},
        {0.50, 0.0420},
        {1.00, 0.0410},
        {2.00, 0.0410},
        {3.00, 0.0410},
        {5.00, 0.0430},
        {7.00, 0.0450},
        {10.00, 0.0460},
        {30.00, 0.0470},
    };

    const YieldCurve updated_curve{
        2,
        valuation_date,
        updated_points
    };

    PricingDependencyGraph graph;

    std::unordered_map<InstrumentId, PricingInstrument>
        instruments;

    instruments.reserve(instrument_count);

    std::mt19937 generator{42};

    std::uniform_int_distribution<int> maturity_distribution{
        1,
        30
    };

    std::uniform_real_distribution<double> coupon_distribution{
        0.02,
        0.08
    };

    std::uniform_real_distribution<double> spread_distribution{
        50.0,
        400.0
    };

    for (
        InstrumentId instrument_id = 1;
        instrument_id <= instrument_count;
        ++instrument_id
    ) {
        const int maturity_years =
            maturity_distribution(generator);

        const Date maturity_date{
            valuation_date.year() + years{maturity_years},
            valuation_date.month(),
            valuation_date.day()
        };

        auto cashflows = generate_fixed_rate_cashflows(
            1000.0,
            coupon_distribution(generator),
            2,
            valuation_date,
            maturity_date
        );

        graph.register_instrument(
            instrument_id,
            resolve_curve_dependencies(
                cashflows,
                valuation_date,
                dependency_nodes
            )
        );

        instruments.emplace(
            instrument_id,
            PricingInstrument{
                .instrument_id = instrument_id,
                .cashflows = std::move(cashflows),
                .spread_bps = spread_distribution(generator),
                .reference_version = 1,
            }
        );
    }

    const CurveUpdateEvent event{
        .event_id = "curve-update-000002",
        .previous_version = 1,
        .new_version = 2,
        .updates = {
            CurveNodeUpdate{
                .node_id = 4,
                .maturity_years = 2.0,
                .old_rate = 0.0400,
                .new_rate = 0.0410,
            }
        },
    };

    const RepricingService service{
        valuation_date,
        std::move(graph),
        std::move(instruments)
    };

    const auto start = steady_clock::now();

    const auto prices =
        service.reprice(event, updated_curve);

    const auto end = steady_clock::now();

    std::ofstream output{
        "artifacts/evaluated-prices.jsonl"
    };

    if (!output) {
        std::cerr << "Unable to open output file.\n";
        return 1;
    }

    output << std::fixed << std::setprecision(10);

    for (const auto& price : prices) {
        output
            << "{"
            << "\"event_time_us\":"
            << epoch_microseconds(price.event_time) << ","
            << "\"received_time_us\":"
            << epoch_microseconds(price.received_time) << ","
            << "\"instrument_id\":"
            << price.instrument_id << ","
            << "\"clean_price\":"
            << price.clean_price << ","
            << "\"dirty_price\":"
            << price.dirty_price << ","
            << "\"yield_to_maturity\":"
            << price.yield_to_maturity << ","
            << "\"g_spread_bps\":"
            << price.g_spread_bps << ","
            << "\"modified_duration\":"
            << price.modified_duration << ","
            << "\"convexity\":"
            << price.convexity << ","
            << "\"reference_version\":"
            << price.reference_version << ","
            << "\"curve_version\":"
            << price.curve_version << ","
            << "\"model_version\":\""
            << price.model_version << "\","
            << "\"quality_status\":\""
            << price.quality_status << "\","
            << "\"quality_score\":"
            << price.quality_score << ","
            << "\"calculation_trace_id\":\""
            << price.calculation_trace_id << "\","
            << "\"source_event_id\":\""
            << price.source_event_id << "\""
            << "}\n";
    }

    const double elapsed_ms =
        duration<double, std::milli>(end - start).count();

    std::cout
        << "Curve version: "
        << updated_curve.version()
        << "\n";

    std::cout
        << "Repriced instruments: "
        << prices.size()
        << "\n";

    std::cout
        << "Selective repricing latency: "
        << elapsed_ms
        << " ms\n";

    std::cout
        << "Output: artifacts/evaluated-prices.jsonl\n";

    return 0;
}
