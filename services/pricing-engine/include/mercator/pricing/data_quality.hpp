#pragma once

#include <chrono>
#include <cstdint>
#include <string>
#include <unordered_map>

namespace mercator::pricing {

enum class QualityStatus {
    Valid,
    Duplicate,
    Stale,
    SequenceGap,
    OutOfOrder,
    Invalid
};

struct MarketEventMetadata {
    std::string event_id;
    std::string source;
    std::uint64_t instrument_id;
    std::uint64_t sequence;
    std::chrono::system_clock::time_point event_time;
    std::chrono::system_clock::time_point received_time;
};

struct QualityResult {
    QualityStatus status;
    double score;
    bool accepted;
    std::string reason;
};

class DataQualityControl {
public:
    explicit DataQualityControl(
        std::chrono::milliseconds stale_threshold
    );

    [[nodiscard]] QualityResult evaluate(
        const MarketEventMetadata& event
    );

private:
    struct SourceInstrumentKey {
        std::string source;
        std::uint64_t instrument_id;

        bool operator==(
            const SourceInstrumentKey& other
        ) const noexcept;
    };

    struct KeyHash {
        std::size_t operator()(
            const SourceInstrumentKey& key
        ) const noexcept;
    };

    std::chrono::milliseconds stale_threshold_;

    std::unordered_map<
        SourceInstrumentKey,
        std::uint64_t,
        KeyHash
    > last_sequence_;

    std::unordered_map<std::string, bool> seen_event_ids_;
};

[[nodiscard]] std::string to_string(QualityStatus status);

}  // namespace mercator::pricing
