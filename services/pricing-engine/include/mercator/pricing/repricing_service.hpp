#pragma once

#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/curve_update.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/evaluated_price.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <cstdint>
#include <unordered_map>
#include <vector>

namespace mercator::pricing {

struct PricingInstrument {
    InstrumentId instrument_id;
    CouponSchedule schedule;
    double spread_bps;
    double market_confidence;
    std::uint64_t reference_version;
};

class RepricingService {
public:
    RepricingService(
        Date valuation_date,
        PricingDependencyGraph dependency_graph,
        std::unordered_map<InstrumentId, PricingInstrument> instruments,
        std::size_t pricing_workers = 0
    );

    [[nodiscard]] std::vector<EvaluatedPrice> reprice(
        const CurveUpdateEvent& event,
        const YieldCurve& updated_curve
    ) const;

    [[nodiscard]] std::vector<InstrumentId>
    affected_instruments(
        const CurveUpdateEvent& event
    ) const;

    [[nodiscard]] std::vector<EvaluatedPrice>
    reprice_all(
        const CurveUpdateEvent& event,
        const YieldCurve& updated_curve
    ) const;

    [[nodiscard]] std::size_t
    instrument_count() const noexcept;

private:
    Date valuation_date_;
    PricingDependencyGraph dependency_graph_;
    std::unordered_map<InstrumentId, PricingInstrument> instruments_;
    std::size_t pricing_workers_;
};

}  // namespace mercator::pricing
