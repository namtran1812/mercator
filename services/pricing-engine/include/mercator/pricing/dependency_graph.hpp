#pragma once

#include <cstdint>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace mercator::pricing {

using InstrumentId = std::uint64_t;
using CurveNodeId = std::uint32_t;

struct CurveNode {
    CurveNodeId id;
    double maturity_years;
};

class PricingDependencyGraph {
public:
    void register_instrument(
        InstrumentId instrument_id,
        const std::vector<CurveNodeId>& curve_nodes
    );

    void unregister_instrument(InstrumentId instrument_id);

    [[nodiscard]] std::vector<InstrumentId>
    affected_instruments(
        const std::vector<CurveNodeId>& changed_nodes
    ) const;

    [[nodiscard]] std::vector<CurveNodeId>
    dependencies_for(InstrumentId instrument_id) const;

    [[nodiscard]] std::size_t instrument_count() const noexcept;

private:
    std::unordered_map<
        InstrumentId,
        std::unordered_set<CurveNodeId>
    > instrument_dependencies_;

    std::unordered_map<
        CurveNodeId,
        std::unordered_set<InstrumentId>
    > reverse_dependencies_;
};

}  // namespace mercator::pricing
