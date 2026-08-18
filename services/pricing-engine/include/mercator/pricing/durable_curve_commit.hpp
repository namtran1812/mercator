#pragma once

#include <functional>

namespace mercator::pricing {

struct DurableCurveCommitHooks {
    std::function<void()> persist_curve_event;
    std::function<void()> persist_prices;
    std::function<void()> persist_checkpoint;
    std::function<void()> publish_latest_state;
    std::function<void()> commit_curve_version;
    std::function<void()> install_curve_state;
    std::function<void()> commit_kafka_offset;
};

void execute_durable_curve_commit(
    const DurableCurveCommitHooks& hooks
);

}  // namespace mercator::pricing
