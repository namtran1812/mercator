#include "mercator/pricing/repricing_service.hpp"

#include "mercator/pricing/analytics.hpp"

#include <algorithm>
#include <chrono>
#include <future>
#include <iomanip>
#include <sstream>
#include <thread>
#include <stdexcept>

namespace mercator::pricing {

namespace {

std::uint64_t fnv1a(
    const std::string& value,
    std::uint64_t seed
) {
    std::uint64_t hash = seed;

    for (const unsigned char byte : value) {
        hash ^= byte;
        hash *= 1099511628211ULL;
    }

    return hash;
}


std::string deterministic_uuid(
    const std::string& value
) {
    std::uint64_t high =
        fnv1a(
            value,
            14695981039346656037ULL
        );

    std::uint64_t low =
        fnv1a(
            value,
            1099511628211ULL
        );

    /*
     * Set RFC-4122-style version/variant bits.
     */
    high &= 0xffffffffffff0fffULL;
    high |= 0x0000000000005000ULL;

    low &= 0x3fffffffffffffffULL;
    low |= 0x8000000000000000ULL;

    std::ostringstream stream;

    stream
        << std::hex
        << std::setfill('0')
        << std::setw(8)
        << static_cast<std::uint32_t>(
            high >> 32
        )
        << "-"
        << std::setw(4)
        << static_cast<std::uint16_t>(
            high >> 16
        )
        << "-"
        << std::setw(4)
        << static_cast<std::uint16_t>(
            high
        )
        << "-"
        << std::setw(4)
        << static_cast<std::uint16_t>(
            low >> 48
        )
        << "-"
        << std::setw(12)
        << (
            low
            & 0x0000ffffffffffffULL
        );

    return stream.str();
}


std::string make_trace_id(
    const std::string& event_id,
    const InstrumentId instrument_id
) {
    return deterministic_uuid(
        event_id
        + ":"
        + std::to_string(
            instrument_id
        )
    );
}

}  // namespace

RepricingService::RepricingService(
    const Date valuation_date,
    PricingDependencyGraph dependency_graph,
    std::unordered_map<InstrumentId, PricingInstrument> instruments,
    const std::size_t pricing_workers
)
    : valuation_date_(valuation_date),
      dependency_graph_(std::move(dependency_graph)),
      instruments_(std::move(instruments)),
      pricing_workers_(pricing_workers) {}

std::vector<InstrumentId>
RepricingService::affected_instruments(
    const CurveUpdateEvent& event
) const {
    std::vector<CurveNodeId> changed_nodes;

    changed_nodes.reserve(
        event.updates.size()
    );

    for (const auto& update : event.updates) {
        changed_nodes.push_back(
            update.node_id
        );
    }

    return dependency_graph_
        .affected_instruments(
            changed_nodes
        );
}


namespace {

std::vector<EvaluatedPrice>
price_instrument_range(
    const Date valuation_date,
    const std::unordered_map<
        InstrumentId,
        PricingInstrument
    >& instruments,
    const std::vector<InstrumentId>& instrument_ids,
    const std::size_t begin,
    const std::size_t end,
    const CurveUpdateEvent& event,
    const YieldCurve& updated_curve,
    const std::chrono::system_clock::time_point received_time
) {
    std::vector<EvaluatedPrice> results;

    results.reserve(
        end - begin
    );


    for (
        std::size_t index = begin;
        index < end;
        ++index
    ) {
        const InstrumentId instrument_id =
            instrument_ids[index];


        const auto iterator =
            instruments.find(
                instrument_id
            );

        if (
            iterator
            == instruments.end()
        ) {
            throw std::runtime_error(
                "dependency graph referenced "
                "unknown instrument"
            );
        }


        const PricingInstrument& instrument =
            iterator->second;


        const PriceBreakdown prices =
            price_from_curve(
                instrument.schedule,
                valuation_date,
                updated_curve,
                instrument.spread_bps
            );


        const double solved_g_spread_bps =
            solve_g_spread_bps(
                instrument.schedule,
                valuation_date,
                updated_curve,
                prices.dirty_price
            );


        const BondAnalytics analytics =
            calculate_bond_analytics(
                instrument.schedule.cashflows,
                valuation_date,
                prices.dirty_price,
                instrument.schedule.payments_per_year
            );


        results.push_back(
            EvaluatedPrice{
                .instrument_id =
                    instrument.instrument_id,

                .clean_price =
                    prices.clean_price,

                .dirty_price =
                    prices.dirty_price,

                .yield_to_maturity =
                    analytics.yield_to_maturity,

                .g_spread_bps =
                    solved_g_spread_bps,

                .modified_duration =
                    analytics.modified_duration,

                .convexity =
                    analytics.convexity,

                .curve_version =
                    updated_curve.version(),

                .reference_version =
                    instrument.reference_version,

                .quality_score =
                    instrument.market_confidence,

                .quality_status =
                    instrument.market_confidence
                        >= 0.80
                        ? "VALID"
                        : "LOW_CONFIDENCE",

                .model_version =
                    "mercator-pricer-0.1.0",

                .calculation_trace_id =
                    make_trace_id(
                        event.event_id,
                        instrument_id
                    ),

                .source_event_id =
                    event.event_id,

                .event_time =
                    std::chrono::system_clock::now(),

                .received_time =
                    received_time,
            }
        );
    }


    return results;
}


std::vector<EvaluatedPrice>
price_instruments(
    const Date valuation_date,
    const std::unordered_map<
        InstrumentId,
        PricingInstrument
    >& instruments,
    const std::vector<InstrumentId>& instrument_ids,
    const CurveUpdateEvent& event,
    const YieldCurve& updated_curve,
    const std::size_t requested_workers
) {
    if (instrument_ids.empty()) {
        return {};
    }


    const auto received_time =
        std::chrono::system_clock::now();


    /*
     * Instrument valuation is independent across the
     * requested universe.
     *
     * Keep the output deterministic by assigning
     * contiguous input ranges to workers and merging
     * futures in range order.
     */
    const unsigned int hardware_threads =
        std::thread::hardware_concurrency();


    const std::size_t automatic_workers =
        hardware_threads == 0
            ? 4
            : hardware_threads;


    const std::size_t configured_workers =
        requested_workers == 0
            ? automatic_workers
            : requested_workers;


    const std::size_t worker_count =
        std::min<std::size_t>(
            instrument_ids.size(),
            std::max<std::size_t>(
                1,
                configured_workers
            )
        );


    /*
     * Avoid parallel overhead for very small updates.
     */
    constexpr std::size_t minimum_parallel_size =
        512;


    if (
        worker_count == 1
        || instrument_ids.size()
            < minimum_parallel_size
    ) {
        return price_instrument_range(
            valuation_date,
            instruments,
            instrument_ids,
            0,
            instrument_ids.size(),
            event,
            updated_curve,
            received_time
        );
    }


    const std::size_t chunk_size =
        (
            instrument_ids.size()
            + worker_count
            - 1
        )
        / worker_count;


    std::vector<
        std::future<
            std::vector<EvaluatedPrice>
        >
    > futures;

    futures.reserve(
        worker_count
    );


    for (
        std::size_t begin = 0;
        begin < instrument_ids.size();
        begin += chunk_size
    ) {
        const std::size_t end =
            std::min(
                begin + chunk_size,
                instrument_ids.size()
            );


        futures.push_back(
            std::async(
                std::launch::async,
                [
                    valuation_date,
                    &instruments,
                    &instrument_ids,
                    begin,
                    end,
                    &event,
                    &updated_curve,
                    received_time
                ]() {
                    return price_instrument_range(
                        valuation_date,
                        instruments,
                        instrument_ids,
                        begin,
                        end,
                        event,
                        updated_curve,
                        received_time
                    );
                }
            )
        );
    }


    std::vector<EvaluatedPrice> results;

    results.reserve(
        instrument_ids.size()
    );


    /*
     * Futures are consumed in submission order, so
     * result ordering remains identical to the input
     * instrument ordering.
     */
    for (auto& future : futures) {
        auto chunk =
            future.get();

        results.insert(
            results.end(),
            std::make_move_iterator(
                chunk.begin()
            ),
            std::make_move_iterator(
                chunk.end()
            )
        );
    }


    return results;
}

}  // namespace


std::vector<EvaluatedPrice>
RepricingService::reprice(
    const CurveUpdateEvent& event,
    const YieldCurve& updated_curve
) const {
    return price_instruments(
        valuation_date_,
        instruments_,
        affected_instruments(event),
        event,
        updated_curve,
        pricing_workers_
    );
}


std::vector<EvaluatedPrice>
RepricingService::reprice_all(
    const CurveUpdateEvent& event,
    const YieldCurve& updated_curve
) const {
    std::vector<InstrumentId> instrument_ids;

    instrument_ids.reserve(
        instruments_.size()
    );

    for (const auto& entry : instruments_) {
        instrument_ids.push_back(
            entry.first
        );
    }

    std::sort(
        instrument_ids.begin(),
        instrument_ids.end()
    );

    return price_instruments(
        valuation_date_,
        instruments_,
        instrument_ids,
        event,
        updated_curve,
        pricing_workers_
    );
}


std::size_t
RepricingService::instrument_count() const noexcept {
    return instruments_.size();
}


}  // namespace mercator::pricing
