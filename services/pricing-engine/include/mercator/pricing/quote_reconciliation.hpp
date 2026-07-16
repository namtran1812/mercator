#pragma once

#include <chrono>
#include <cstdint>
#include <string>
#include <vector>

namespace mercator::pricing {

struct MarketQuote {
    std::string quote_id;
    std::string source;
    std::uint64_t instrument_id;

    double bid;
    double ask;

    std::chrono::system_clock::time_point event_time;
    double source_reliability;
};

struct ReconciledQuote {
    std::uint64_t instrument_id;

    double evaluated_bid;
    double evaluated_ask;
    double evaluated_mid;

    double confidence_score;
    double source_dispersion_bps;

    std::size_t accepted_sources;
    std::size_t rejected_sources;

    std::vector<std::string> contributing_quote_ids;
};

class QuoteReconciler {
public:
    QuoteReconciler(
        double maximum_quote_age_seconds,
        double outlier_threshold_bps
    );

    [[nodiscard]] ReconciledQuote reconcile(
        std::uint64_t instrument_id,
        const std::vector<MarketQuote>& quotes,
        std::chrono::system_clock::time_point evaluation_time
    ) const;

private:
    double maximum_quote_age_seconds_;
    double outlier_threshold_bps_;
};

}  // namespace mercator::pricing
