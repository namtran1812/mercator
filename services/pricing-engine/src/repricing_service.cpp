#include "mercator/pricing/repricing_service.hpp"

#include "mercator/pricing/analytics.hpp"

#include <algorithm>
#include <chrono>
#include <sstream>
#include <stdexcept>

namespace mercator::pricing {

namespace {

std::string make_trace_id(
    const std::string& event_id,
    const InstrumentId instrument_id
) {
    std::ostringstream stream;
    stream << event_id << "-" << instrument_id;
    return stream.str();
}

}  // namespace

RepricingService::RepricingService(
    const Date valuation_date,
    PricingDependencyGraph dependency_graph,
    std::unordered_map<InstrumentId, PricingInstrument> instruments
)
    : valuation_date_(valuation_date),
      dependency_graph_(std::move(dependency_graph)),
      instruments_(std::move(instruments)) {}

std::vector<EvaluatedPrice> RepricingService::reprice(
    const CurveUpdateEvent& event,
    const YieldCurve& updated_curve
) const {
    std::vector<CurveNodeId> changed_nodes;
    changed_nodes.reserve(event.updates.size());

    for (const auto& update : event.updates) {
        changed_nodes.push_back(update.node_id);
    }

    const auto affected =
        dependency_graph_.affected_instruments(changed_nodes);

    std::vector<EvaluatedPrice> results;
    results.reserve(affected.size());

    const auto received_time =
        std::chrono::system_clock::now();

    for (const InstrumentId instrument_id : affected) {
        const auto iterator = instruments_.find(instrument_id);

        if (iterator == instruments_.end()) {
            throw std::runtime_error(
                "dependency graph referenced unknown instrument"
            );
        }

        const PricingInstrument& instrument =
            iterator->second;

        const PriceBreakdown prices =
            price_from_curve(
                instrument.schedule,
                valuation_date_,
                updated_curve,
                instrument.spread_bps
            );

        const double solved_g_spread_bps =
            solve_g_spread_bps(
                instrument.schedule,
                valuation_date_,
                updated_curve,
                prices.dirty_price
            );

        const BondAnalytics analytics =
            calculate_bond_analytics(
                instrument.schedule.cashflows,
                valuation_date_,
                prices.dirty_price,
                instrument.schedule.payments_per_year
            );

        results.push_back(EvaluatedPrice{
            .instrument_id = instrument.instrument_id,
            .clean_price = prices.clean_price,
            .dirty_price = prices.dirty_price,
            .yield_to_maturity = analytics.yield_to_maturity,
            .g_spread_bps = solved_g_spread_bps,
            .modified_duration = analytics.modified_duration,
            .convexity = analytics.convexity,
            .curve_version = updated_curve.version(),
            .reference_version = instrument.reference_version,
            .quality_score = instrument.market_confidence,
            .quality_status =
                instrument.market_confidence >= 0.80
                    ? "VALID"
                    : "LOW_CONFIDENCE",
            .model_version = "mercator-pricer-0.1.0",
            .calculation_trace_id =
                make_trace_id(event.event_id, instrument_id),
            .source_event_id = event.event_id,
            .event_time = std::chrono::system_clock::now(),
            .received_time = received_time,
        });
    }

    return results;
}

}  // namespace mercator::pricing
