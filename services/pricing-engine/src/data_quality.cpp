#include "mercator/pricing/data_quality.hpp"

#include <functional>
#include <utility>

namespace mercator::pricing {

bool DataQualityControl::SourceInstrumentKey::operator==(
    const SourceInstrumentKey& other
) const noexcept {
    return source == other.source &&
        instrument_id == other.instrument_id;
}

std::size_t DataQualityControl::KeyHash::operator()(
    const SourceInstrumentKey& key
) const noexcept {
    const std::size_t source_hash =
        std::hash<std::string>{}(key.source);

    const std::size_t instrument_hash =
        std::hash<std::uint64_t>{}(key.instrument_id);

    return source_hash ^
        (instrument_hash + 0x9e3779b9 +
         (source_hash << 6U) +
         (source_hash >> 2U));
}

DataQualityControl::DataQualityControl(
    const std::chrono::milliseconds stale_threshold
)
    : stale_threshold_(stale_threshold) {}

QualityResult DataQualityControl::evaluate(
    const MarketEventMetadata& event
) {
    if (
        event.event_id.empty() ||
        event.source.empty() ||
        event.instrument_id == 0 ||
        event.sequence == 0
    ) {
        return {
            .status = QualityStatus::Invalid,
            .score = 0.0,
            .accepted = false,
            .reason = "missing required metadata",
        };
    }

    if (seen_event_ids_.contains(event.event_id)) {
        return {
            .status = QualityStatus::Duplicate,
            .score = 0.0,
            .accepted = false,
            .reason = "duplicate event ID",
        };
    }

    const auto age =
        std::chrono::duration_cast<std::chrono::milliseconds>(
            event.received_time - event.event_time
        );

    if (age > stale_threshold_) {
        return {
            .status = QualityStatus::Stale,
            .score = 0.25,
            .accepted = false,
            .reason = "event exceeded staleness threshold",
        };
    }

    const SourceInstrumentKey key{
        .source = event.source,
        .instrument_id = event.instrument_id,
    };

    const auto iterator = last_sequence_.find(key);

    if (iterator != last_sequence_.end()) {
        const std::uint64_t previous =
            iterator->second;

        if (event.sequence <= previous) {
            return {
                .status = QualityStatus::OutOfOrder,
                .score = 0.1,
                .accepted = false,
                .reason = "sequence is not greater than prior sequence",
            };
        }

        if (event.sequence != previous + 1) {
            seen_event_ids_.emplace(event.event_id, true);
            last_sequence_[key] = event.sequence;

            return {
                .status = QualityStatus::SequenceGap,
                .score = 0.6,
                .accepted = true,
                .reason = "sequence gap detected",
            };
        }
    }

    seen_event_ids_.emplace(event.event_id, true);
    last_sequence_[key] = event.sequence;

    return {
        .status = QualityStatus::Valid,
        .score = 1.0,
        .accepted = true,
        .reason = "event passed validation",
    };
}

std::string to_string(const QualityStatus status) {
    switch (status) {
        case QualityStatus::Valid:
            return "VALID";
        case QualityStatus::Duplicate:
            return "DUPLICATE";
        case QualityStatus::Stale:
            return "STALE";
        case QualityStatus::SequenceGap:
            return "SEQUENCE_GAP";
        case QualityStatus::OutOfOrder:
            return "OUT_OF_ORDER";
        case QualityStatus::Invalid:
            return "INVALID";
    }

    return "UNKNOWN";
}

}  // namespace mercator::pricing
