#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/dependency_resolver.hpp"

#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <vector>

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    constexpr std::uint64_t instrument_count =
        10'000;

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

    PricingDependencyGraph graph;

    std::uint64_t total_dependencies = 0;

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

        const Date maturity_date{
            valuation_date.year()
                + years{maturity_years},

            valuation_date.month(),
            valuation_date.day(),
        };

        const auto cashflows =
            generate_fixed_rate_cashflows(
                1000.0,
                coupon_rate,
                2,
                valuation_date,
                maturity_date
            );

        const auto dependencies =
            resolve_curve_dependencies(
                cashflows,
                valuation_date,
                nodes
            );

        total_dependencies +=
            dependencies.size();

        graph.register_instrument(
            instrument_id,
            dependencies
        );
    }

    std::cout
        << std::fixed
        << std::setprecision(2);

    std::cout
        << "Total instruments: "
        << instrument_count
        << "\n";

    std::cout
        << "Total dependency edges: "
        << total_dependencies
        << "\n";

    std::cout
        << "Average dependencies/instrument: "
        << (
            static_cast<double>(
                total_dependencies
            )
            / static_cast<double>(
                instrument_count
            )
        )
        << "\n\n";

    std::cout
        << "NODE FANOUT\n";

    std::cout
        << "----------------------------------------\n";

    for (const auto& node : nodes) {
        const auto affected =
            graph.affected_instruments(
                {
                    node.id,
                }
            );

        const double percentage =
            100.0
            * static_cast<double>(
                affected.size()
            )
            / static_cast<double>(
                instrument_count
            );

        std::cout
            << std::setw(5)
            << node.maturity_years
            << "Y"
            << "  affected="
            << std::setw(5)
            << affected.size()
            << "  "
            << std::setw(6)
            << percentage
            << "%\n";
    }

    return 0;
}
