#pragma once

#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_graph.hpp"

#include <vector>

namespace mercator::pricing {

std::vector<CurveNodeId> resolve_curve_dependencies(
    const std::vector<CashFlow>& cashflows,
    Date valuation_date,
    const std::vector<CurveNode>& curve_nodes
);

}  // namespace mercator::pricing
