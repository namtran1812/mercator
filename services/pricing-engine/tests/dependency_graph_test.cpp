#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/dependency_resolver.hpp"

#include <chrono>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    const Date valuation_date{
        year{2026},
        month{7},
        day{15}
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

    const auto five_year_cashflows =
        generate_fixed_rate_cashflows(
            1000.0,
            0.05,
            2,
            valuation_date,
            Date{year{2031}, month{7}, day{15}}
        );

    const auto ten_year_cashflows =
        generate_fixed_rate_cashflows(
            1000.0,
            0.06,
            2,
            valuation_date,
            Date{year{2036}, month{7}, day{15}}
        );

    const auto five_year_dependencies =
        resolve_curve_dependencies(
            five_year_cashflows,
            valuation_date,
            nodes
        );

    const auto ten_year_dependencies =
        resolve_curve_dependencies(
            ten_year_cashflows,
            valuation_date,
            nodes
        );

    PricingDependencyGraph graph;

    graph.register_instrument(
        1001,
        five_year_dependencies
    );

    graph.register_instrument(
        1002,
        ten_year_dependencies
    );

    require(
        graph.instrument_count() == 2,
        "expected two registered instruments"
    );

    const auto affected_by_five_year =
        graph.affected_instruments({6});

    require(
        !affected_by_five_year.empty(),
        "five-year curve change should affect instruments"
    );

    const auto affected_by_thirty_year =
        graph.affected_instruments({9});

    require(
        affected_by_thirty_year.size() == 1,
        "thirty-year node should affect exactly one instrument"
    );

    require(
        affected_by_thirty_year.front() == 1002,
        "thirty-year node should affect only the ten-year bond"
    );

    graph.unregister_instrument(1001);

    require(
        graph.instrument_count() == 1,
        "unregister should remove instrument"
    );

    std::cout
        << "All dependency graph tests passed.\n";

    return 0;
}
