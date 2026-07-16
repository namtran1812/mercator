#include "mercator/pricing/quote_reconciliation.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace mercator::pricing {

namespace {

double midpoint(const MarketQuote& quote) {
    return (quote.bid + quote.ask) / 2.0;
}

double median(std::vector<double> values) {
    if (values.empty()) {
        throw std::invalid_argument(
            "cannot calculate median of empty values"
        );
    }

    std::sort(values.begin(), values.end());

    const std::size_t middle = values.size() / 2;

    if (values.size() % 2 == 0) {
        return (
            values[middle - 1] +
            values[middle]
        ) / 2.0;
    }

    return values[middle];
}

}  // namespace

QuoteReconciler::QuoteReconciler(
    const double maximum_quote_age_seconds,
    const double outlier_threshold_bps
)
    : maximum_quote_age_seconds_(
          maximum_quote_age_seconds
      ),
      outlier_threshold_bps_(
          outlier_threshold_bps
      ) {
    if (maximum_quote_age_seconds_ <= 0.0) {
        throw std::invalid_argument(
            "maximum quote age must be positive"
        );
    }

    if (outlier_threshold_bps_ <= 0.0) {
        throw std::invalid_argument(
            "outlier threshold must be positive"
        );
    }
}

ReconciledQuote QuoteReconciler::reconcile(
    const std::uint64_t instrument_id,
    const std::vector<MarketQuote>& quotes,
    const std::chrono::system_clock::time_point evaluation_time
) const {
    std::vector<const MarketQuote*> eligible;
    std::size_t rejected = 0;

    for (const auto& quote : quotes) {
        if (
            quote.instrument_id != instrument_id ||
            quote.bid <= 0.0 ||
            quote.ask <= 0.0 ||
            quote.bid > quote.ask ||
            quote.source_reliability <= 0.0
        ) {
            ++rejected;
            continue;
        }

        const double age_seconds =
            std::chrono::duration<double>(
                evaluation_time -
                quote.event_time
            ).count();

        if (
            age_seconds < 0.0 ||
            age_seconds > maximum_quote_age_seconds_
        ) {
            ++rejected;
            continue;
        }

        eligible.push_back(&quote);
    }

    if (eligible.empty()) {
        throw std::runtime_error(
            "no eligible quotes available"
        );
    }

    std::vector<double> mids;
    mids.reserve(eligible.size());

    for (const auto* quote : eligible) {
        mids.push_back(midpoint(*quote));
    }

    const double median_mid = median(mids);

    std::vector<const MarketQuote*> accepted;
    accepted.reserve(eligible.size());

    for (const auto* quote : eligible) {
        const double quote_mid = midpoint(*quote);

        const double deviation_bps =
            std::abs(quote_mid - median_mid) /
            median_mid *
            10'000.0;

        if (deviation_bps > outlier_threshold_bps_) {
            ++rejected;
            continue;
        }

        accepted.push_back(quote);
    }

    if (accepted.empty()) {
        throw std::runtime_error(
            "all eligible quotes were rejected as outliers"
        );
    }

    double weighted_bid = 0.0;
    double weighted_ask = 0.0;
    double total_weight = 0.0;

    std::vector<std::string> quote_ids;
    std::vector<double> accepted_mids;

    for (const auto* quote : accepted) {
        const double age_seconds =
            std::chrono::duration<double>(
                evaluation_time -
                quote->event_time
            ).count();

        const double freshness_weight =
            std::max(
                0.0,
                1.0 -
                age_seconds /
                maximum_quote_age_seconds_
            );

        const double spread =
            quote->ask - quote->bid;

        const double liquidity_weight =
            1.0 / std::max(spread, 0.0001);

        const double weight =
            quote->source_reliability *
            freshness_weight *
            liquidity_weight;

        weighted_bid += quote->bid * weight;
        weighted_ask += quote->ask * weight;
        total_weight += weight;

        quote_ids.push_back(quote->quote_id);
        accepted_mids.push_back(midpoint(*quote));
    }

    if (total_weight <= 0.0) {
        throw std::runtime_error(
            "quote weights summed to zero"
        );
    }

    const double evaluated_bid =
        weighted_bid / total_weight;

    const double evaluated_ask =
        weighted_ask / total_weight;

    const double evaluated_mid =
        (evaluated_bid + evaluated_ask) / 2.0;

    double squared_error_sum = 0.0;

    for (const double accepted_mid : accepted_mids) {
        const double deviation_bps =
            (accepted_mid - evaluated_mid) /
            evaluated_mid *
            10'000.0;

        squared_error_sum +=
            deviation_bps * deviation_bps;
    }

    const double dispersion_bps =
        std::sqrt(
            squared_error_sum /
            static_cast<double>(accepted_mids.size())
        );

    const double source_coverage =
        std::min(
            1.0,
            static_cast<double>(accepted.size()) / 4.0
        );

    const double dispersion_score =
        std::max(
            0.0,
            1.0 -
            dispersion_bps /
            outlier_threshold_bps_
        );

    const double confidence_score =
        0.6 * source_coverage +
        0.4 * dispersion_score;

    return ReconciledQuote{
        .instrument_id = instrument_id,
        .evaluated_bid = evaluated_bid,
        .evaluated_ask = evaluated_ask,
        .evaluated_mid = evaluated_mid,
        .confidence_score = confidence_score,
        .source_dispersion_bps = dispersion_bps,
        .accepted_sources = accepted.size(),
        .rejected_sources = rejected,
        .contributing_quote_ids = std::move(quote_ids),
    };
}

}  // namespace mercator::pricing
