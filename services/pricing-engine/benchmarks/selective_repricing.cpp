#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/dependency_resolver.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace {

using mercator::pricing::CashFlow;
using mercator::pricing::InstrumentId;

struct Instrument {
    InstrumentId id;
    std::vector<CashFlow> cashflows;
    double spread_bps;
};

double percentile(
    std::vector<double> values,
    const double percentile_value
) {
    if (values.empty()) {
        return 0.0;
    }

    std::sort(values.begin(), values.end());

    const auto index = static_cast<std::size_t>(
        percentile_value *
        static_cast<double>(values.size() - 1)
    );

    return values[index];
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    constexpr std::uint64_t instrument_count = 10'000;
    constexpr int benchmark_runs = 20;

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

    const std::vector<CurvePoint> base_points{
        {0.25, 0.0430},
        {0.50, 0.0420},
        {1.00, 0.0410},
        {2.00, 0.0400},
        {3.00, 0.0410},
        {5.00, 0.0430},
        {7.00, 0.0450},
        {10.00, 0.0460},
        {30.00, 0.0470},
    };

    auto shocked_points = base_points;

    for (auto& point : shocked_points) {
        if (std::abs(point.maturity_years - 2.0) < 1e-12) {
            point.zero_rate += 0.0010;
        }
    }

    const YieldCurve base_curve{
        1,
        valuation_date,
        base_points
    };

    const YieldCurve shocked_curve{
        2,
        valuation_date,
        shocked_points
    };

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

    std::vector<Instrument> instruments;
    instruments.reserve(instrument_count);

    PricingDependencyGraph graph;

    for (
        InstrumentId instrument_id = 1;
        instrument_id <= instrument_count;
        ++instrument_id
    ) {
        const int maturity_years =
            maturity_distribution(generator);

        const double coupon_rate =
            coupon_distribution(generator);

        const double spread_bps =
            spread_distribution(generator);

        const Date maturity_date{
            valuation_date.year() +
                years{maturity_years},
            valuation_date.month(),
            valuation_date.day()
        };

        auto cashflows = generate_fixed_rate_cashflows(
            1000.0,
            coupon_rate,
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

        instruments.push_back({
            .id = instrument_id,
            .cashflows = std::move(cashflows),
            .spread_bps = spread_bps,
        });
    }

    std::unordered_map<InstrumentId, std::size_t>
        instrument_index;

    instrument_index.reserve(instruments.size());

    for (
        std::size_t index = 0;
        index < instruments.size();
        ++index
    ) {
        instrument_index.emplace(
            instruments[index].id,
            index
        );
    }

    std::vector<double> baseline_prices(
        instrument_count
    );

    for (
        std::size_t index = 0;
        index < instruments.size();
        ++index
    ) {
        baseline_prices[index] =
            present_value_from_curve(
                instruments[index].cashflows,
                valuation_date,
                base_curve,
                instruments[index].spread_bps
            );
    }

    const CurveNodeId changed_node = 4;

    const auto affected =
        graph.affected_instruments({changed_node});

    std::vector<double> full_latencies_us;
    std::vector<double> incremental_latencies_us;

    full_latencies_us.reserve(benchmark_runs);
    incremental_latencies_us.reserve(benchmark_runs);

    std::vector<double> full_prices(instrument_count);
    std::vector<double> incremental_prices(instrument_count);

    for (int run = 0; run < benchmark_runs; ++run) {
        const auto full_start = steady_clock::now();

        for (
            std::size_t index = 0;
            index < instruments.size();
            ++index
        ) {
            full_prices[index] =
                present_value_from_curve(
                    instruments[index].cashflows,
                    valuation_date,
                    shocked_curve,
                    instruments[index].spread_bps
                );
        }

        const auto full_end = steady_clock::now();

        incremental_prices = baseline_prices;

        const auto incremental_start =
            steady_clock::now();

        for (const InstrumentId instrument_id : affected) {
            const auto iterator =
                instrument_index.find(instrument_id);

            if (iterator == instrument_index.end()) {
                throw std::runtime_error(
                    "affected instrument was not indexed"
                );
            }

            const std::size_t index = iterator->second;

            incremental_prices[index] =
                present_value_from_curve(
                    instruments[index].cashflows,
                    valuation_date,
                    shocked_curve,
                    instruments[index].spread_bps
                );
        }

        const auto incremental_end =
            steady_clock::now();

        full_latencies_us.push_back(
            duration<double, std::micro>(
                full_end - full_start
            ).count()
        );

        incremental_latencies_us.push_back(
            duration<double, std::micro>(
                incremental_end - incremental_start
            ).count()
        );
    }

    double maximum_difference = 0.0;

    for (
        std::size_t index = 0;
        index < full_prices.size();
        ++index
    ) {
        maximum_difference = std::max(
            maximum_difference,
            std::abs(
                full_prices[index] -
                incremental_prices[index]
            )
        );
    }

    const double full_median =
        percentile(full_latencies_us, 0.50);

    const double incremental_median =
        percentile(incremental_latencies_us, 0.50);

    const double reduction_percent =
        100.0 *
        (full_median - incremental_median) /
        full_median;

    std::cout << std::fixed << std::setprecision(3);

    std::cout
        << "Changed node: 2Y\n";

    std::cout
        << "Total instruments: "
        << instrument_count
        << "\n";

    std::cout
        << "Affected instruments: "
        << affected.size()
        << "\n";

    std::cout
        << "Avoided repricing: "
        << instrument_count - affected.size()
        << "\n";

    std::cout
        << "Full repricing median: "
        << full_median
        << " us\n";

    std::cout
        << "Incremental median: "
        << incremental_median
        << " us\n";

    std::cout
        << "Latency reduction: "
        << reduction_percent
        << "%\n";

    std::cout
        << "Maximum price difference: "
        << maximum_difference
        << "\n";

    if (maximum_difference > 1e-9) {
        throw std::runtime_error(
            "incremental repricing differs from full repricing"
        );
    }

    return 0;
}
