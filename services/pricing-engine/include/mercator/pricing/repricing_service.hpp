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
        std::unordered_map<InstrumentId, PricingInstrument> instruments
    );

    [[nodiscard]] std::vector<EvaluatedPrice> reprice(
        const CurveUpdateEvent& event,
        const YieldCurve& updated_curve
    ) const;

private:
    Date valuation_date_;
    PricingDependencyGraph dependency_graph_;
    std::unordered_map<InstrumentId, PricingInstrument> instruments_;
};

}  // namespace mercator::pricing
