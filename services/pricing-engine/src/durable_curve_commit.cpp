#include "mercator/pricing/durable_curve_commit.hpp"

#include <stdexcept>
#include <string>

namespace mercator::pricing {

namespace {

void require_hook(
    const std::function<void()>& hook,
    const char* name
) {
    if (!hook) {
        throw std::invalid_argument(
            std::string{
                "missing durable commit hook: "
            }
            + name
        );
    }
}

}  // namespace


void execute_durable_curve_commit(
    const DurableCurveCommitHooks& hooks
) {
    require_hook(
        hooks.persist_curve_event,
        "persist_curve_event"
    );

    require_hook(
        hooks.persist_prices,
        "persist_prices"
    );

    require_hook(
        hooks.persist_checkpoint,
        "persist_checkpoint"
    );

    require_hook(
        hooks.publish_latest_state,
        "publish_latest_state"
    );

    require_hook(
        hooks.commit_curve_version,
        "commit_curve_version"
    );

    require_hook(
        hooks.install_curve_state,
        "install_curve_state"
    );

    require_hook(
        hooks.commit_kafka_offset,
        "commit_kafka_offset"
    );

    /*
     * The ordering here is a correctness invariant.
     *
     * In particular:
     *
     * 1. The causal curve event must become durable before
     *    any evaluated prices derived from it.
     *
     * 2. Kafka must not be acknowledged until all durable
     *    writes, latest-state publication, and local state
     *    advancement have succeeded.
     */
    hooks.persist_curve_event();
    hooks.persist_prices();
    hooks.persist_checkpoint();
    hooks.publish_latest_state();
    hooks.commit_curve_version();
    hooks.install_curve_state();
    hooks.commit_kafka_offset();
}

}  // namespace mercator::pricing
