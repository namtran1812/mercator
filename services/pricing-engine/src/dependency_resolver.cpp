#include "mercator/pricing/dependency_resolver.hpp"

#include "mercator/pricing/analytics.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <unordered_set>

namespace mercator::pricing {

std::vector<CurveNodeId> resolve_curve_dependencies(
    const std::vector<CashFlow>& cashflows,
    const Date valuation_date,
    const std::vector<CurveNode>& curve_nodes
) {
    if (curve_nodes.empty()) {
        throw std::invalid_argument(
            "curve_nodes cannot be empty"
        );
    }

    std::vector<CurveNode> sorted_nodes = curve_nodes;

    std::sort(
        sorted_nodes.begin(),
        sorted_nodes.end(),
        [](const CurveNode& left, const CurveNode& right) {
            return left.maturity_years < right.maturity_years;
        }
    );

    std::unordered_set<CurveNodeId> dependencies;

    for (const auto& cashflow : cashflows) {
        if (
            std::chrono::sys_days{cashflow.payment_date} <=
            std::chrono::sys_days{valuation_date}
        ) {
            continue;
        }

        const double maturity =
            year_fraction_actual_365(
                valuation_date,
                cashflow.payment_date
            );

        const auto upper = std::lower_bound(
            sorted_nodes.begin(),
            sorted_nodes.end(),
            maturity,
            [](const CurveNode& node, const double value) {
                return node.maturity_years < value;
            }
        );

        if (upper == sorted_nodes.begin()) {
            dependencies.insert(upper->id);
            continue;
        }

        if (upper == sorted_nodes.end()) {
            dependencies.insert(sorted_nodes.back().id);
            continue;
        }

        dependencies.insert(upper->id);
        dependencies.insert((upper - 1)->id);
    }

    std::vector<CurveNodeId> result{
        dependencies.begin(),
        dependencies.end()
    };

    std::sort(result.begin(), result.end());
    return result;
}

}  // namespace mercator::pricing
