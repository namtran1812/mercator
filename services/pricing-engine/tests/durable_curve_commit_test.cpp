#include "mercator/pricing/durable_curve_commit.hpp"

#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using mercator::pricing::DurableCurveCommitHooks;
using mercator::pricing::execute_durable_curve_commit;


void expect_equal(
    const std::vector<std::string>& actual,
    const std::vector<std::string>& expected,
    const char* message
) {
    if (actual != expected) {
        throw std::runtime_error(
            message
        );
    }
}


void test_success_order() {
    std::vector<std::string> calls;

    execute_durable_curve_commit(
        DurableCurveCommitHooks{
            .persist_curve_event =
                [&] {
                    calls.push_back("event");
                },

            .persist_prices =
                [&] {
                    calls.push_back("prices");
                },

            .persist_checkpoint =
                [&] {
                    calls.push_back("checkpoint");
                },

            .publish_latest_state =
                [&] {
                    calls.push_back("redis");
                },

            .commit_curve_version =
                [&] {
                    calls.push_back("version");
                },

            .install_curve_state =
                [&] {
                    calls.push_back("curve_state");
                },

            .commit_kafka_offset =
                [&] {
                    calls.push_back("kafka");
                },
        }
    );

    expect_equal(
        calls,
        {
            "event",
            "prices",
            "checkpoint",
            "redis",
            "version",
            "curve_state",
            "kafka",
        },
        "durable commit ordering changed"
    );
}


void test_event_failure_blocks_everything() {
    std::vector<std::string> calls;

    bool failed = false;

    try {
        execute_durable_curve_commit(
            DurableCurveCommitHooks{
                .persist_curve_event =
                    [&] {
                        calls.push_back("event");

                        throw std::runtime_error(
                            "injected event failure"
                        );
                    },

                .persist_prices =
                    [&] {
                        calls.push_back("prices");
                    },

                .persist_checkpoint =
                    [&] {
                        calls.push_back("checkpoint");
                    },

                .publish_latest_state =
                    [&] {
                        calls.push_back("redis");
                    },

                .commit_curve_version =
                    [&] {
                        calls.push_back("version");
                    },

                .install_curve_state =
                    [&] {
                        calls.push_back("curve_state");
                    },

                .commit_kafka_offset =
                    [&] {
                        calls.push_back("kafka");
                    },
            }
        );
    }
    catch (const std::runtime_error&) {
        failed = true;
    }

    if (!failed) {
        throw std::runtime_error(
            "expected event persistence failure"
        );
    }

    expect_equal(
        calls,
        {"event"},
        "event failure allowed downstream side effects"
    );
}


void test_price_failure_never_commits_state() {
    std::vector<std::string> calls;

    bool failed = false;

    try {
        execute_durable_curve_commit(
            DurableCurveCommitHooks{
                .persist_curve_event =
                    [&] {
                        calls.push_back("event");
                    },

                .persist_prices =
                    [&] {
                        calls.push_back("prices");

                        throw std::runtime_error(
                            "injected price failure"
                        );
                    },

                .persist_checkpoint =
                    [&] {
                        calls.push_back("checkpoint");
                    },

                .publish_latest_state =
                    [&] {
                        calls.push_back("redis");
                    },

                .commit_curve_version =
                    [&] {
                        calls.push_back("version");
                    },

                .install_curve_state =
                    [&] {
                        calls.push_back("curve_state");
                    },

                .commit_kafka_offset =
                    [&] {
                        calls.push_back("kafka");
                    },
            }
        );
    }
    catch (const std::runtime_error&) {
        failed = true;
    }

    if (!failed) {
        throw std::runtime_error(
            "expected price persistence failure"
        );
    }

    expect_equal(
        calls,
        {
            "event",
            "prices",
        },
        "price failure advanced local or Kafka state"
    );
}


void test_checkpoint_failure_never_commits_state() {
    std::vector<std::string> calls;

    bool failed = false;

    try {
        execute_durable_curve_commit(
            DurableCurveCommitHooks{
                .persist_curve_event =
                    [&] {
                        calls.push_back("event");
                    },

                .persist_prices =
                    [&] {
                        calls.push_back("prices");
                    },

                .persist_checkpoint =
                    [&] {
                        calls.push_back("checkpoint");

                        throw std::runtime_error(
                            "injected checkpoint failure"
                        );
                    },

                .publish_latest_state =
                    [&] {
                        calls.push_back("redis");
                    },

                .commit_curve_version =
                    [&] {
                        calls.push_back("version");
                    },

                .install_curve_state =
                    [&] {
                        calls.push_back("curve_state");
                    },

                .commit_kafka_offset =
                    [&] {
                        calls.push_back("kafka");
                    },
            }
        );
    }
    catch (const std::runtime_error&) {
        failed = true;
    }

    if (!failed) {
        throw std::runtime_error(
            "expected checkpoint failure"
        );
    }

    expect_equal(
        calls,
        {
            "event",
            "prices",
            "checkpoint",
        },
        "checkpoint failure advanced state"
    );
}

}  // namespace


int main() {
    test_success_order();
    test_event_failure_blocks_everything();
    test_price_failure_never_commits_state();
    test_checkpoint_failure_never_commits_state();

    std::cout
        << "All durable curve commit tests passed.\n";

    return 0;
}
