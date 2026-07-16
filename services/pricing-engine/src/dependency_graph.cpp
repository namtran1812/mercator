#include "mercator/pricing/dependency_graph.hpp"

#include <algorithm>

namespace mercator::pricing {

void PricingDependencyGraph::register_instrument(
    const InstrumentId instrument_id,
    const std::vector<CurveNodeId>& curve_nodes
) {
    unregister_instrument(instrument_id);

    auto& dependencies =
        instrument_dependencies_[instrument_id];

    for (const CurveNodeId node_id : curve_nodes) {
        dependencies.insert(node_id);
        reverse_dependencies_[node_id].insert(instrument_id);
    }
}

void PricingDependencyGraph::unregister_instrument(
    const InstrumentId instrument_id
) {
    const auto instrument_iterator =
        instrument_dependencies_.find(instrument_id);

    if (instrument_iterator == instrument_dependencies_.end()) {
        return;
    }

    for (const CurveNodeId node_id :
         instrument_iterator->second) {
        auto reverse_iterator =
            reverse_dependencies_.find(node_id);

        if (reverse_iterator == reverse_dependencies_.end()) {
            continue;
        }

        reverse_iterator->second.erase(instrument_id);

        if (reverse_iterator->second.empty()) {
            reverse_dependencies_.erase(reverse_iterator);
        }
    }

    instrument_dependencies_.erase(instrument_iterator);
}

std::vector<InstrumentId>
PricingDependencyGraph::affected_instruments(
    const std::vector<CurveNodeId>& changed_nodes
) const {
    std::unordered_set<InstrumentId> affected;

    for (const CurveNodeId node_id : changed_nodes) {
        const auto iterator =
            reverse_dependencies_.find(node_id);

        if (iterator == reverse_dependencies_.end()) {
            continue;
        }

        affected.insert(
            iterator->second.begin(),
            iterator->second.end()
        );
    }

    std::vector<InstrumentId> result{
        affected.begin(),
        affected.end()
    };

    std::sort(result.begin(), result.end());
    return result;
}

std::vector<CurveNodeId>
PricingDependencyGraph::dependencies_for(
    const InstrumentId instrument_id
) const {
    const auto iterator =
        instrument_dependencies_.find(instrument_id);

    if (iterator == instrument_dependencies_.end()) {
        return {};
    }

    std::vector<CurveNodeId> result{
        iterator->second.begin(),
        iterator->second.end()
    };

    std::sort(result.begin(), result.end());
    return result;
}

std::size_t
PricingDependencyGraph::instrument_count() const noexcept {
    return instrument_dependencies_.size();
}

}  // namespace mercator::pricing
