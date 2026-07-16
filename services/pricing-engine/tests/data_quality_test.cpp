#include "mercator/pricing/data_quality.hpp"

#include <chrono>
#include <iostream>
#include <stdexcept>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

}  // namespace

int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    DataQualityControl control{
        milliseconds{500}
    };

    const auto now = system_clock::now();

    const MarketEventMetadata first{
        .event_id = "event-1",
        .source = "feed-a",
        .instrument_id = 101,
        .sequence = 1,
        .event_time = now,
        .received_time = now + milliseconds{10},
    };

    const QualityResult first_result =
        control.evaluate(first);

    require(
        first_result.accepted,
        "first valid event should be accepted"
    );

    const QualityResult duplicate_result =
        control.evaluate(first);

    require(
        duplicate_result.status ==
            QualityStatus::Duplicate,
        "duplicate should be detected"
    );

    const MarketEventMetadata gap{
        .event_id = "event-3",
        .source = "feed-a",
        .instrument_id = 101,
        .sequence = 3,
        .event_time = now,
        .received_time = now + milliseconds{20},
    };

    const QualityResult gap_result =
        control.evaluate(gap);

    require(
        gap_result.status ==
            QualityStatus::SequenceGap,
        "sequence gap should be detected"
    );

    const MarketEventMetadata out_of_order{
        .event_id = "event-2",
        .source = "feed-a",
        .instrument_id = 101,
        .sequence = 2,
        .event_time = now,
        .received_time = now + milliseconds{30},
    };

    const QualityResult out_of_order_result =
        control.evaluate(out_of_order);

    require(
        out_of_order_result.status ==
            QualityStatus::OutOfOrder,
        "out-of-order event should be rejected"
    );

    const MarketEventMetadata stale{
        .event_id = "event-stale",
        .source = "feed-b",
        .instrument_id = 202,
        .sequence = 1,
        .event_time = now,
        .received_time = now + seconds{2},
    };

    const QualityResult stale_result =
        control.evaluate(stale);

    require(
        stale_result.status ==
            QualityStatus::Stale,
        "stale event should be detected"
    );

    std::cout
        << "All data quality tests passed.\n";

    return 0;
}
