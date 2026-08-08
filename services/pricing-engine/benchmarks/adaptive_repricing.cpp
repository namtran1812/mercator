#include "mercator/pricing/analytics.hpp"
#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>


namespace {

using mercator::pricing::CashFlow;
using mercator::pricing::CurveNode;
using mercator::pricing::CurveNodeId;
using mercator::pricing::Date;
using mercator::pricing::InstrumentId;


struct Instrument {
    InstrumentId id;

    std::vector<CashFlow>
        cashflows;

    double spread_bps;
};


double percentile(
    std::vector<double> values,
    const double percentile_value
) {
    if (values.empty()) {
        return 0.0;
    }

    std::sort(
        values.begin(),
        values.end()
    );

    const auto index =
        static_cast<std::size_t>(
            percentile_value
            * static_cast<double>(
                values.size() - 1
            )
        );

    return values[index];
}


}  // namespace


int main(
    int argc,
    char** argv
) {
    using namespace std::chrono;
    using namespace mercator::pricing;


    constexpr std::uint64_t instrument_count =
        10'000;

    constexpr int benchmark_runs =
        20;

    /*
     * 1 bp bump used to measure key-rate sensitivity.
     */
    constexpr double key_rate_bump =
        0.0001;

    /*
     * Actual scenario evaluated by the benchmark:
     * +10 bp to the selected curve node.
     */
    constexpr double scenario_shock =
        0.0010;


    double error_budget_bps =
        0.25;

    double full_reprice_fraction =
        0.70;

    if (argc >= 2) {
        error_budget_bps =
            std::stod(
                argv[1]
            );
    }

    if (
        error_budget_bps
        < 0.0
    ) {
        throw std::invalid_argument(
            "error budget cannot be negative"
        );
    }

    double selected_maturity_years =
        2.0;

    if (argc >= 3) {
        selected_maturity_years =
            std::stod(
                argv[2]
            );
    }


    if (argc >= 4) {
        full_reprice_fraction =
            std::stod(
                argv[3]
            );
    }

    if (
        full_reprice_fraction < 0.0
        || full_reprice_fraction > 1.0
    ) {
        throw std::invalid_argument(
            "full-reprice fraction must "
            "be between 0 and 1"
        );
    }


    const Date valuation_date{
        year{2026},
        month{7},
        day{15},
    };


    const std::vector<CurveNode> nodes{
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


    const YieldCurve base_curve{
        1,
        valuation_date,
        base_points,
    };


    std::mt19937 generator{42};


    std::uniform_int_distribution<int>
        maturity_distribution{
            1,
            30,
        };


    std::uniform_real_distribution<double>
        coupon_distribution{
            0.02,
            0.08,
        };


    std::uniform_real_distribution<double>
        spread_distribution{
            50.0,
            400.0,
        };


    std::vector<Instrument>
        instruments;

    instruments.reserve(
        instrument_count
    );


    for (
        InstrumentId instrument_id = 1;
        instrument_id <= instrument_count;
        ++instrument_id
    ) {
        const int maturity_years =
            maturity_distribution(
                generator
            );


        const double coupon_rate =
            coupon_distribution(
                generator
            );


        const double spread_bps =
            spread_distribution(
                generator
            );


        const Date maturity_date{
            valuation_date.year()
                + years{maturity_years},

            valuation_date.month(),
            valuation_date.day(),
        };


        instruments.push_back(
            Instrument{
                .id =
                    instrument_id,

                .cashflows =
                    generate_fixed_rate_cashflows(
                        1000.0,
                        coupon_rate,
                        2,
                        valuation_date,
                        maturity_date
                    ),

                .spread_bps =
                    spread_bps,
            }
        );
    }


    std::vector<double>
        baseline_prices(
            instrument_count
        );


    for (
        std::size_t index = 0;
        index < instruments.size();
        ++index
    ) {
        baseline_prices[index] =
            present_value_from_curve(
                instruments[index]
                    .cashflows,

                valuation_date,

                base_curve,

                instruments[index]
                    .spread_bps
            );
    }


    /*
     * Build the MATERIAL dependency graph.
     *
     * A curve node is retained when a 1 bp bump
     * moves the instrument's price by at least
     * materiality_threshold_bps relative-price bp.
     */

    PricingDependencyGraph material_graph;


    std::uint64_t material_edges =
        0;


    for (
        std::size_t instrument_index = 0;
        instrument_index < instruments.size();
        ++instrument_index
    ) {
        const auto& instrument =
            instruments[instrument_index];


        const double baseline_price =
            baseline_prices[
                instrument_index
            ];


        std::vector<CurveNodeId>
            material_nodes;


        for (
            std::size_t node_index = 0;
            node_index < nodes.size();
            ++node_index
        ) {
            auto bumped_points =
                base_points;


            bumped_points[node_index]
                .zero_rate +=
                    key_rate_bump;


            const YieldCurve bumped_curve{
                2,
                valuation_date,
                bumped_points,
            };


            const double bumped_price =
                present_value_from_curve(
                    instrument.cashflows,
                    valuation_date,
                    bumped_curve,
                    instrument.spread_bps
                );


            const double absolute_change =
                std::abs(
                    bumped_price
                    - baseline_price
                );


            const double relative_impact_bps =
                baseline_price != 0.0
                    ? (
                        absolute_change
                        / std::abs(
                            baseline_price
                        )
                        * 10'000.0
                    )
                    : 0.0;


            const double shock_bps =
                std::abs(
                    scenario_shock
                )
                * 10'000.0;

            const double estimated_scenario_impact_bps =
                relative_impact_bps
                * shock_bps;

            if (
                estimated_scenario_impact_bps
                >= error_budget_bps
            ) {
                material_nodes.push_back(
                    nodes[node_index].id
                );
            }
        }


        material_edges +=
            material_nodes.size();


        material_graph.register_instrument(
            instrument.id,
            material_nodes
        );
    }


    /*
     * Find and shock the selected curve node.
     */

    std::size_t changed_node_index =
        nodes.size();

    for (
        std::size_t index = 0;
        index < nodes.size();
        ++index
    ) {
        if (
            std::abs(
                nodes[index].maturity_years
                - selected_maturity_years
            )
            < 1e-12
        ) {
            changed_node_index =
                index;

            break;
        }
    }

    if (
        changed_node_index
        == nodes.size()
    ) {
        throw std::invalid_argument(
            "selected maturity does not "
            "match a curve node"
        );
    }


    const CurveNodeId changed_node =
        nodes[
            changed_node_index
        ].id;


    auto shocked_points =
        base_points;


    shocked_points[
        changed_node_index
    ].zero_rate +=
        scenario_shock;


    const YieldCurve shocked_curve{
        3,
        valuation_date,
        shocked_points,
    };


    const auto affected =
        material_graph
            .affected_instruments(
                {
                    changed_node,
                }
            );


    const double affected_fraction =
        static_cast<double>(
            affected.size()
        )
        / static_cast<double>(
            instrument_count
        );

    enum class Strategy {
        Skip,
        Selective,
        Full,
    };

    Strategy strategy;

    if (affected.empty()) {
        strategy =
            Strategy::Skip;
    }
    else if (
        affected_fraction
        >= full_reprice_fraction
    ) {
        strategy =
            Strategy::Full;
    }
    else {
        strategy =
            Strategy::Selective;
    }


    std::unordered_map<
        InstrumentId,
        std::size_t
    > instrument_index;


    instrument_index.reserve(
        instrument_count
    );


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


    std::vector<double>
        full_prices(
            instrument_count
        );


    std::vector<double>
        material_prices(
            instrument_count
        );


    std::vector<double>
        full_latencies_us;


    std::vector<double>
        material_latencies_us;


    full_latencies_us.reserve(
        benchmark_runs
    );


    material_latencies_us.reserve(
        benchmark_runs
    );


    for (
        int run = 0;
        run < benchmark_runs;
        ++run
    ) {
        const auto full_start =
            steady_clock::now();


        for (
            std::size_t index = 0;
            index < instruments.size();
            ++index
        ) {
            full_prices[index] =
                present_value_from_curve(
                    instruments[index]
                        .cashflows,

                    valuation_date,

                    shocked_curve,

                    instruments[index]
                        .spread_bps
                );
        }


        const auto full_end =
            steady_clock::now();


        material_prices =
            baseline_prices;


        const auto material_start =
            steady_clock::now();


        if (
            strategy == Strategy::Full
        ) {
            for (
                std::size_t index = 0;
                index < instruments.size();
                ++index
            ) {
                material_prices[index] =
                    present_value_from_curve(
                        instruments[index]
                            .cashflows,

                        valuation_date,

                        shocked_curve,

                        instruments[index]
                            .spread_bps
                    );
            }
        }
        else if (
            strategy == Strategy::Selective
        ) {
            for (
                const InstrumentId instrument_id :
                affected
            ) {
                const auto iterator =
                    instrument_index.find(
                        instrument_id
                    );

                if (
                    iterator
                    == instrument_index.end()
                ) {
                    throw std::runtime_error(
                        "material dependency referenced "
                        "unknown instrument"
                    );
                }

                const std::size_t index =
                    iterator->second;

                material_prices[index] =
                    present_value_from_curve(
                        instruments[index]
                            .cashflows,

                        valuation_date,

                        shocked_curve,

                        instruments[index]
                            .spread_bps
                    );
            }
        }


        const auto material_end =
            steady_clock::now();


        full_latencies_us.push_back(
            duration<
                double,
                std::micro
            >(
                full_end
                - full_start
            ).count()
        );


        material_latencies_us.push_back(
            duration<
                double,
                std::micro
            >(
                material_end
                - material_start
            ).count()
        );
    }


    std::vector<double>
        relative_errors_bps;


    relative_errors_bps.reserve(
        instrument_count
    );


    double maximum_relative_error_bps =
        0.0;


    double maximum_absolute_error =
        0.0;


    for (
        std::size_t index = 0;
        index < instrument_count;
        ++index
    ) {
        const double absolute_error =
            std::abs(
                full_prices[index]
                - material_prices[index]
            );


        const double relative_error_bps =
            full_prices[index] != 0.0
                ? (
                    absolute_error
                    / std::abs(
                        full_prices[index]
                    )
                    * 10'000.0
                )
                : 0.0;


        relative_errors_bps.push_back(
            relative_error_bps
        );


        maximum_relative_error_bps =
            std::max(
                maximum_relative_error_bps,
                relative_error_bps
            );


        maximum_absolute_error =
            std::max(
                maximum_absolute_error,
                absolute_error
            );
    }


    const double full_median =
        percentile(
            full_latencies_us,
            0.50
        );


    const double material_median =
        percentile(
            material_latencies_us,
            0.50
        );


    const double p95_error_bps =
        percentile(
            relative_errors_bps,
            0.95
        );


    const double p99_error_bps =
        percentile(
            relative_errors_bps,
            0.99
        );


    const double latency_reduction =
        100.0
        * (
            full_median
            - material_median
        )
        / full_median;


    const double work_avoided =
        100.0
        * static_cast<double>(
            instrument_count
            - affected.size()
        )
        / static_cast<double>(
            instrument_count
        );


    std::cout
        << std::fixed
        << std::setprecision(3);


    std::cout
        << "Policy: adaptive repricing\n";


    std::cout
        << "Scenario error budget: "
        << error_budget_bps
        << " bp\n";

    std::cout
        << "Full-reprice crossover: "
        << (
            full_reprice_fraction
            * 100.0
        )
        << "%\n";

    std::cout
        << "Strategy: "
        << (
            strategy == Strategy::Skip
                ? "SKIP"
                : (
                    strategy == Strategy::Full
                        ? "FULL"
                        : "SELECTIVE"
                )
        )
        << "\n";


    std::cout
        << "Changed node: "
        << selected_maturity_years
        << "Y\n";


    std::cout
        << "Shock: +10 bp\n";


    std::cout
        << "Total instruments: "
        << instrument_count
        << "\n";


    std::cout
        << "Material dependency edges: "
        << material_edges
        << "\n";


    std::cout
        << "Average material dependencies/instrument: "
        << (
            static_cast<double>(
                material_edges
            )
            / static_cast<double>(
                instrument_count
            )
        )
        << "\n";


    std::cout
        << "Affected instruments: "
        << affected.size()
        << "\n";


    std::cout
        << "Avoided repricing: "
        << (
            instrument_count
            - affected.size()
        )
        << "\n";


    std::cout
        << "Work avoided: "
        << work_avoided
        << "%\n";


    std::cout
        << "Full repricing median: "
        << full_median
        << " us\n";


    std::cout
        << "Material repricing median: "
        << material_median
        << " us\n";


    std::cout
        << "Latency reduction: "
        << latency_reduction
        << "%\n";


    std::cout
        << "p95 relative price error: "
        << p95_error_bps
        << " bp\n";


    std::cout
        << "p99 relative price error: "
        << p99_error_bps
        << " bp\n";


    std::cout
        << "Maximum relative price error: "
        << maximum_relative_error_bps
        << " bp\n";


    std::cout
        << "Maximum absolute price error: "
        << maximum_absolute_error
        << "\n";


    return 0;
}
