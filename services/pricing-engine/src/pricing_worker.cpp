#include "mercator/pricing/adaptive_repricing.hpp"
#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/clickhouse_price_sink.hpp"
#include "mercator/pricing/curve_event_parser.hpp"
#include "mercator/pricing/curve_replay_sink.hpp"
#include "mercator/pricing/durable_curve_commit.hpp"
#include "mercator/pricing/dependency_graph.hpp"
#include "mercator/pricing/dependency_resolver.hpp"
#include "mercator/pricing/repricing_service.hpp"
#include "mercator/pricing/redis_price_sink.hpp"
#include "mercator/pricing/postgres_instrument_loader.hpp"
#include "mercator/pricing/version_guard.hpp"
#include "mercator/pricing/yield_curve.hpp"

#include <librdkafka/rdkafka.h>

#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>


namespace {

std::atomic_bool running{true};


void handle_signal(int) {
    running.store(false);
}


std::string environment(
    const char* name,
    const char* fallback
) {
    const char* value =
        std::getenv(name);

    return value != nullptr
        ? std::string{value}
        : std::string{fallback};
}


std::uint64_t environment_uint64(
    const char* name,
    const std::uint64_t fallback
) {
    const char* value =
        std::getenv(name);

    if (value == nullptr) {
        return fallback;
    }

    return std::stoull(value);
}


double environment_double(
    const char* name,
    const double fallback
) {
    const char* value =
        std::getenv(name);

    if (value == nullptr) {
        return fallback;
    }

    return std::stod(value);
}




std::vector<mercator::pricing::CurvePoint>
initial_curve_points() {
    using namespace mercator::pricing;

    return {
        {0.25, 0.0430},
        {0.50, 0.0420},
        {1.00, 0.0410},
        {2.00, 0.0400},
        {3.00, 0.0410},
        {5.00, 0.0430},
        {7.00, 0.0450},
        {10.00, 0.0460},
        {30.00, 0.0470},
    };
}





void apply_curve_event(
    std::vector<
        mercator::pricing::CurvePoint
    >& points,
    const mercator::pricing::CurveUpdateEvent& event
) {
    for (const auto& update : event.updates) {
        bool found = false;

        for (auto& point : points) {
            if (
                std::abs(
                    point.maturity_years
                    - update.maturity_years
                )
                < 1e-12
            ) {
                point.zero_rate =
                    update.new_rate;

                found = true;
                break;
            }
        }

        if (!found) {
            throw std::runtime_error(
                "curve update referenced "
                "unknown maturity"
            );
        }
    }
}


struct KafkaConsumerDeleter {
    void operator()(
        rd_kafka_t* consumer
    ) const noexcept {
        if (consumer != nullptr) {
            rd_kafka_consumer_close(
                consumer
            );

            rd_kafka_destroy(
                consumer
            );
        }
    }
};


std::unique_ptr<
    rd_kafka_t,
    KafkaConsumerDeleter
>
create_consumer(
    const std::string& brokers,
    const std::string& group_id
) {
    char error_buffer[
        512
    ]{};

    rd_kafka_conf_t* configuration =
        rd_kafka_conf_new();

    auto configure =
        [
            configuration,
            &error_buffer
        ](
            const char* key,
            const std::string& value
        ) {
            if (
                rd_kafka_conf_set(
                    configuration,
                    key,
                    value.c_str(),
                    error_buffer,
                    sizeof(error_buffer)
                )
                != RD_KAFKA_CONF_OK
            ) {
                throw std::runtime_error(
                    std::string{
                        "Kafka config error for "
                    }
                    + key
                    + ": "
                    + error_buffer
                );
            }
        };

    configure(
        "bootstrap.servers",
        brokers
    );

    configure(
        "group.id",
        group_id
    );

    configure(
        "enable.auto.commit",
        "false"
    );

    configure(
        "enable.auto.offset.store",
        "false"
    );

    configure(
        "auto.offset.reset",
        "earliest"
    );

    rd_kafka_t* consumer =
        rd_kafka_new(
            RD_KAFKA_CONSUMER,
            configuration,
            error_buffer,
            sizeof(error_buffer)
        );

    if (consumer == nullptr) {
        throw std::runtime_error(
            std::string{
                "Unable to create Kafka consumer: "
            }
            + error_buffer
        );
    }

    rd_kafka_poll_set_consumer(
        consumer
    );

    return {
        consumer,
        KafkaConsumerDeleter{},
    };
}


void subscribe(
    rd_kafka_t* consumer,
    const std::string& topic
) {
    rd_kafka_topic_partition_list_t* topics =
        rd_kafka_topic_partition_list_new(
            1
        );

    rd_kafka_topic_partition_list_add(
        topics,
        topic.c_str(),
        RD_KAFKA_PARTITION_UA
    );

    const rd_kafka_resp_err_t error =
        rd_kafka_subscribe(
            consumer,
            topics
        );

    rd_kafka_topic_partition_list_destroy(
        topics
    );

    if (error != RD_KAFKA_RESP_ERR_NO_ERROR) {
        throw std::runtime_error(
            std::string{
                "Kafka subscribe failed: "
            }
            + rd_kafka_err2str(error)
        );
    }
}


void commit_message(
    rd_kafka_t* consumer,
    rd_kafka_message_t* message
) {
    const rd_kafka_resp_err_t error =
        rd_kafka_commit_message(
            consumer,
            message,
            0
        );

    if (
        error
        != RD_KAFKA_RESP_ERR_NO_ERROR
    ) {
        throw std::runtime_error(
            std::string{
                "Kafka commit failed: "
            }
            + rd_kafka_err2str(
                error
            )
        );
    }
}


}  // namespace


int main() {
    using namespace std::chrono;
    using namespace mercator::pricing;

    /*
     * Flush worker diagnostics immediately.
     *
     * This matters when stdout is piped through tee during
     * production/load benchmarks.
     */
    std::cout.setf(
        std::ios::unitbuf
    );

    std::cerr.setf(
        std::ios::unitbuf
    );

    std::signal(
        SIGINT,
        handle_signal
    );

    std::signal(
        SIGTERM,
        handle_signal
    );


    const std::string brokers =
        environment(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        );

    const std::string topic =
        environment(
            "CURVE_TOPIC",
            "market.curves.v1"
        );

    const std::string group_id =
        environment(
            "PRICING_WORKER_GROUP_ID",
            "mercator-pricing-worker-v1"
        );


    const std::uint64_t initial_version =
        environment_uint64(
            "INITIAL_CURVE_VERSION",
            2
        );


    const std::string clickhouse_url =
        environment(
            "CLICKHOUSE_URL",
            "http://127.0.0.1:8123"
        );

    const std::string clickhouse_database =
        environment(
            "CLICKHOUSE_DATABASE",
            "mercator"
        );

    const std::string clickhouse_username =
        environment(
            "CLICKHOUSE_USERNAME",
            "mercator"
        );

    const std::string clickhouse_password =
        environment(
            "CLICKHOUSE_PASSWORD",
            "mercator"
        );


    const ClickHousePriceSink price_sink{
        clickhouse_url,
        clickhouse_database,
        clickhouse_username,
        clickhouse_password,
    };


    const CurveReplaySink replay_sink{
        clickhouse_url,
        clickhouse_database,
        clickhouse_username,
        clickhouse_password,
    };


    const std::string redis_host =
        environment(
            "REDIS_HOST",
            "127.0.0.1"
        );

    const int redis_port =
        static_cast<int>(
            environment_uint64(
                "REDIS_PORT",
                6380
            )
        );

    const std::string redis_channel =
        environment(
            "REDIS_PRICE_CHANNEL",
            "mercator:price-updates"
        );


    const RedisPriceSink redis_sink{
        redis_host,
        redis_port,
        redis_channel,
    };


    const std::size_t pricing_workers =
        static_cast<std::size_t>(
            environment_uint64(
                "PRICING_WORKERS",
                8
            )
        );


    const std::uint64_t checkpoint_interval =
        environment_uint64(
            "MERCATOR_CURVE_CHECKPOINT_INTERVAL",
            100
        );


    const bool fail_after_curve_event =
        environment_uint64(
            "MERCATOR_FAIL_AFTER_CURVE_EVENT",
            0
        ) != 0;


    const AdaptiveRepricingPolicy policy{
        .error_budget_bps =
            environment_double(
                "PRICING_ERROR_BUDGET_BPS",
                0.25
            ),

        .full_reprice_fraction =
            environment_double(
                "FULL_REPRICE_FRACTION",
                0.70
            ),
    };


    const Date valuation_date{
        year{2026},
        month{7},
        day{15},
    };


    auto curve_points =
        initial_curve_points();


    CurveVersionGuard version_guard{
        initial_version
    };


    const std::string postgres_dsn =
        environment(
            "POSTGRES_DSN",
            ""
        );

    if (postgres_dsn.empty()) {
        throw std::runtime_error(
            "POSTGRES_DSN is required"
        );
    }


    auto universe =
        load_instruments_from_postgres(
            postgres_dsn,
            valuation_date
        );


    RepricingService repricing_service{
        valuation_date,
        std::move(
            universe.dependency_graph
        ),
        std::move(
            universe.instruments
        ),
        pricing_workers,
    };


    auto consumer =
        create_consumer(
            brokers,
            group_id
        );


    subscribe(
        consumer.get(),
        topic
    );


    std::cout
        << "Mercator C++ pricing worker started\n"
        << "topic="
        << topic
        << "\n"
        << "brokers="
        << brokers
        << "\n"
        << "instruments="
        << repricing_service.instrument_count()
        << "\n"
        << "curve_version="
        << initial_version
        << "\n"
        << "full_reprice_fraction="
        << policy.full_reprice_fraction
        << "\n"
        << "pricing_workers="
        << (
            pricing_workers == 0
                ? std::string{"auto"}
                : std::to_string(
                    pricing_workers
                )
        )
        << "\n"
        << "fail_after_curve_event="
        << (
            fail_after_curve_event
                ? "true"
                : "false"
        )
        << "\n";


    while (running.load()) {
        rd_kafka_message_t* message =
            rd_kafka_consumer_poll(
                consumer.get(),
                500
            );

        if (message == nullptr) {
            continue;
        }


        if (
            message->err
            != RD_KAFKA_RESP_ERR_NO_ERROR
        ) {
            if (
                message->err
                != RD_KAFKA_RESP_ERR__PARTITION_EOF
            ) {
                std::cerr
                    << "Kafka error: "
                    << rd_kafka_message_errstr(
                        message
                    )
                    << "\n";
            }

            rd_kafka_message_destroy(
                message
            );

            continue;
        }


        try {
            const std::string payload{
                static_cast<const char*>(
                    message->payload
                ),
                message->len
            };


            const CurveUpdateEvent event =
                parse_curve_update_event(
                    payload
                );


            const auto disposition =
                version_guard.classify(
                    event
                );


            if (
                disposition
                != CurveEventDisposition::Accept
            ) {
                std::cout
                    << "event="
                    << event.event_id
                    << " disposition="
                    << to_string(
                        disposition
                    )
                    << " current_version="
                    << version_guard.current_version()
                    << "\n";


                /*
                 * Duplicate and stale events are safe
                 * to acknowledge.
                 *
                 * GAP is not: leave its offset uncommitted
                 * so recovery can resolve missing versions.
                 */
                if (
                    disposition
                    == CurveEventDisposition::Duplicate
                    || disposition
                    == CurveEventDisposition::Stale
                ) {
                    commit_message(
                        consumer.get(),
                        message
                    );
                }


                rd_kafka_message_destroy(
                    message
                );

                continue;
            }


            auto next_curve_points =
                curve_points;


            apply_curve_event(
                next_curve_points,
                event
            );


            const YieldCurve updated_curve{
                event.new_version,
                valuation_date,
                next_curve_points,
            };


            const auto affected =
                repricing_service
                    .affected_instruments(
                        event
                    );


            /*
             * This first worker uses the exact
             * dependency graph, so omitted error is
             * zero for the affected-set decision.
             *
             * Material sensitivity routing will be
             * wired into the worker after the native
             * event path is stable.
             */
            const RepricingDecision decision =
                choose_repricing_strategy(
                    affected.size(),
                    repricing_service
                        .instrument_count(),
                    0.0,
                    policy
                );


            const auto processing_start =
                steady_clock::now();

            const auto pricing_start =
                processing_start;


            std::vector<EvaluatedPrice>
                prices;


            switch (decision.strategy) {
                case RepricingStrategy::Skip:
                    break;

                case RepricingStrategy::Selective:
                    prices =
                        repricing_service.reprice(
                            event,
                            updated_curve
                        );
                    break;

                case RepricingStrategy::Full:
                    prices =
                        repricing_service.reprice_all(
                            event,
                            updated_curve
                        );
                    break;
            }


            const auto pricing_end =
                steady_clock::now();


            const double pricing_ms =
                duration<
                    double,
                    std::milli
                >(
                    pricing_end - pricing_start
                ).count();


            /*
             * Durable boundary:
             *
             * Persist the causal curve transition before
             * evaluated prices. Do not advance local curve
             * state or commit Kafka until all durable writes
             * have succeeded.
             */
            const auto clickhouse_start =
                steady_clock::now();

            double clickhouse_ms = 0.0;
            double redis_ms = 0.0;
            double kafka_commit_ms = 0.0;


            execute_durable_curve_commit(
                DurableCurveCommitHooks{
                    .persist_curve_event =
                        [&] {
                            const auto start =
                                std::chrono::steady_clock::now();

                            replay_sink.insert_event(
                                event
                            );

                            const auto end =
                                std::chrono::steady_clock::now();

                            clickhouse_ms +=
                                std::chrono::duration<
                                    double,
                                    std::milli
                                >(
                                    end - start
                                ).count();

                            /*
                             * Test-only crash-window injection.
                             *
                             * The causal curve event is durable,
                             * but no evaluated prices, checkpoint,
                             * Redis state, local version advance,
                             * or Kafka offset commit may occur.
                             */
                            if (fail_after_curve_event) {
                                throw std::runtime_error(
                                    "injected failure after "
                                    "curve-event persistence"
                                );
                            }
                        },

                    .persist_prices =
                        [&] {
                            const auto start =
                                std::chrono::steady_clock::now();

                            price_sink.insert(
                                prices
                            );

                            const auto end =
                                std::chrono::steady_clock::now();

                            clickhouse_ms +=
                                std::chrono::duration<
                                    double,
                                    std::milli
                                >(
                                    end - start
                                ).count();
                        },

                    .persist_checkpoint =
                        [&] {
                            const auto start =
                                std::chrono::steady_clock::now();

                            if (
                                replay_sink.should_checkpoint(
                                    event.new_version,
                                    checkpoint_interval
                                )
                            ) {
                                replay_sink.insert_checkpoint(
                                    event,
                                    valuation_date,
                                    next_curve_points
                                );
                            }

                            const auto end =
                                std::chrono::steady_clock::now();

                            clickhouse_ms +=
                                std::chrono::duration<
                                    double,
                                    std::milli
                                >(
                                    end - start
                                ).count();
                        },

                    .publish_latest_state =
                        [&] {
                            const auto start =
                                std::chrono::steady_clock::now();

                            redis_sink.publish(
                                prices,
                                event
                            );

                            const auto end =
                                std::chrono::steady_clock::now();

                            redis_ms =
                                std::chrono::duration<
                                    double,
                                    std::milli
                                >(
                                    end - start
                                ).count();
                        },

                    .commit_curve_version =
                        [&] {
                            version_guard.commit(
                                event
                            );
                        },

                    .install_curve_state =
                        [&] {
                            curve_points =
                                next_curve_points;
                        },

                    .commit_kafka_offset =
                        [&] {
                            const auto start =
                                std::chrono::steady_clock::now();

                            commit_message(
                                consumer.get(),
                                message
                            );

                            const auto end =
                                std::chrono::steady_clock::now();

                            kafka_commit_ms =
                                std::chrono::duration<
                                    double,
                                    std::milli
                                >(
                                    end - start
                                ).count();
                        },
                }
            );

            const auto processing_end =
                steady_clock::now();

            const double e2e_ms =
                duration<
                    double,
                    std::milli
                >(
                    processing_end
                    - processing_start
                ).count();


            std::cout
                << std::fixed
                << std::setprecision(3)
                << "event="
                << event.event_id
                << " version="
                << event.new_version
                << " strategy="
                << to_string(
                    decision.strategy
                )
                << " affected="
                << affected.size()
                << "/"
                << repricing_service
                    .instrument_count()
                << " repriced="
                << prices.size()
                << " pricing_ms="
                << pricing_ms
                << " clickhouse_ms="
                << clickhouse_ms
                << " redis_ms="
                << redis_ms
                << " kafka_commit_ms="
                << kafka_commit_ms
                << " e2e_ms="
                << e2e_ms
                << "\n";
        }
        catch (const std::exception& error) {
            std::cerr
                << "Processing failed: "
                << error.what()
                << "\n";

            /*
             * Intentionally do not commit.
             */
        }


        rd_kafka_message_destroy(
            message
        );
    }


    std::cout
        << "Mercator pricing worker stopped.\n";


    return 0;
}
