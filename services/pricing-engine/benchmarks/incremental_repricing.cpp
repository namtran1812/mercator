#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/dependency_resolver.hpp"

#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    constexpr std::uint64_t instrument_count = 10'000;

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

    PricingDependencyGraph graph;

    std::mt19937 generator{42};
    std::uniform_int_distribution<int> maturity_years{
        1,
        30
    };

    for (
        std::uint64_t instrument_id = 1;
        instrument_id <= instrument_count;
        ++instrument_id
    ) {
        const int years_to_maturity =
            maturity_years(generator);

        const Date maturity_date{
            valuation_date.year() +
                std::chrono::years{years_to_maturity},
            valuation_date.month(),
            valuation_date.day()
        };

        const auto cashflows =
            generate_fixed_rate_cashflows(
                1000.0,
                0.05,
                2,
                valuation_date,
                maturity_date
            );

        graph.register_instrument(
            instrument_id,
            resolve_curve_dependencies(
                cashflows,
                valuation_date,
                nodes
            )
        );
    }

    const auto start = steady_clock::now();

    const auto affected =
        graph.affected_instruments({6});

    const auto end = steady_clock::now();

    const auto elapsed =
        duration_cast<microseconds>(end - start);

    std::cout
        << "Total instruments: "
        << instrument_count
        << "\n";

    std::cout
        << "Affected by 5Y node: "
        << affected.size()
        << "\n";

    std::cout
        << "Avoided repricing: "
        << instrument_count - affected.size()
        << "\n";

    std::cout
        << "Dependency lookup: "
        << elapsed.count()
        << " microseconds\n";

    return 0;
}
