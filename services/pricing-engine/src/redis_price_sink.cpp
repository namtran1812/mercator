#include "mercator/pricing/redis_price_sink.hpp"

#include <hiredis/hiredis.h>
#include <nlohmann/json.hpp>

#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

namespace mercator::pricing {

namespace {

struct RedisContextDeleter {
    void operator()(
        redisContext* context
    ) const noexcept {
        if (context != nullptr) {
            redisFree(context);
        }
    }
};

struct RedisReplyDeleter {
    void operator()(
        redisReply* reply
    ) const noexcept {
        if (reply != nullptr) {
            freeReplyObject(reply);
        }
    }
};

using RedisContextPtr =
    std::unique_ptr<
        redisContext,
        RedisContextDeleter
    >;

using RedisReplyPtr =
    std::unique_ptr<
        redisReply,
        RedisReplyDeleter
    >;


std::string iso8601(
    const std::chrono::system_clock::time_point time
) {
    const auto micros =
        std::chrono::duration_cast<
            std::chrono::microseconds
        >(
            time.time_since_epoch()
        );

    const std::int64_t total_micros =
        micros.count();

    const std::time_t seconds =
        static_cast<std::time_t>(
            total_micros / 1'000'000
        );

    const std::int64_t fractional =
        total_micros % 1'000'000;

    std::tm utc{};

#if defined(_WIN32)
    gmtime_s(
        &utc,
        &seconds
    );
#else
    gmtime_r(
        &seconds,
        &utc
    );
#endif

    std::ostringstream output;

    output
        << std::put_time(
            &utc,
            "%Y-%m-%dT%H:%M:%S"
        )
        << "."
        << std::setw(6)
        << std::setfill('0')
        << fractional
        << "Z";

    return output.str();
}


std::string dependency_tenor(
    const CurveUpdateEvent& event
) {
    if (event.updates.empty()) {
        return "";
    }

    const double maturity =
        event.updates.front()
            .maturity_years;

    if (
        std::abs(maturity - 0.25)
        < 1e-12
    ) {
        return "3M";
    }

    if (
        std::abs(maturity - 0.50)
        < 1e-12
    ) {
        return "6M";
    }

    if (
        std::abs(maturity - 1.0)
        < 1e-12
    ) {
        return "1Y";
    }

    if (
        std::abs(maturity - 2.0)
        < 1e-12
    ) {
        return "2Y";
    }

    if (
        std::abs(maturity - 3.0)
        < 1e-12
    ) {
        return "3Y";
    }

    if (
        std::abs(maturity - 5.0)
        < 1e-12
    ) {
        return "5Y";
    }

    if (
        std::abs(maturity - 7.0)
        < 1e-12
    ) {
        return "7Y";
    }

    if (
        std::abs(maturity - 10.0)
        < 1e-12
    ) {
        return "10Y";
    }

    if (
        std::abs(maturity - 30.0)
        < 1e-12
    ) {
        return "30Y";
    }

    std::ostringstream output;

    output
        << maturity
        << "Y";

    return output.str();
}


std::string make_payload(
    const EvaluatedPrice& price,
    const CurveUpdateEvent& event,
    const double price_change
) {
    using json =
        nlohmann::json;

    const json payload{
        {
            "instrument_id",
            price.instrument_id
        },
        {
            "clean_price",
            price.clean_price
        },
        {
            "dirty_price",
            price.dirty_price
        },
        {
            "yield_to_maturity",
            price.yield_to_maturity
        },
        {
            "g_spread_bps",
            price.g_spread_bps
        },
        {
            "modified_duration",
            price.modified_duration
        },
        {
            "convexity",
            price.convexity
        },
        {
            "curve_version",
            price.curve_version
        },
        {
            "reference_version",
            price.reference_version
        },
        {
            "quality_score",
            price.quality_score
        },
        {
            "quality_status",
            price.quality_status
        },
        {
            "model_version",
            price.model_version
        },
        {
            "calculation_trace_id",
            price.calculation_trace_id
        },
        {
            "event_time",
            iso8601(
                price.event_time
            )
        },

        /*
         * Stream-compatibility metadata.
         *
         * The C++ pricing engine applies the actual
         * updated curve, so dependency_weight is not
         * used as a pricing approximation.
         */
        {
            "price_change",
            price_change
        },
        {
            "source_event_id",
            price.source_event_id
        },
        {
            "dependency_tenor",
            dependency_tenor(
                event
            )
        },
        {
            "dependency_weight",
            1.0
        },
    };

    return payload.dump();
}


void require_ok(
    redisReply* reply,
    const std::string& operation
) {
    if (reply == nullptr) {
        throw std::runtime_error(
            "Redis "
            + operation
            + " returned null reply"
        );
    }

    if (
        reply->type
        == REDIS_REPLY_ERROR
    ) {
        const std::string message =
            reply->str != nullptr
                ? std::string{
                    reply->str,
                    reply->len
                }
                : "unknown Redis error";

        throw std::runtime_error(
            "Redis "
            + operation
            + " failed: "
            + message
        );
    }
}

}  // namespace


RedisPriceSink::RedisPriceSink(
    std::string host,
    const int port,
    std::string channel
)
    : host_(
        std::move(host)
    ),
      port_(port),
      channel_(
        std::move(channel)
    ) {}


void RedisPriceSink::publish(
    const std::vector<EvaluatedPrice>& prices,
    const CurveUpdateEvent& event
) const {
    if (prices.empty()) {
        return;
    }


    RedisContextPtr context{
        redisConnect(
            host_.c_str(),
            port_
        )
    };


    if (
        context == nullptr
        || context->err != 0
    ) {
        const std::string message =
            context != nullptr
                ? context->errstr
                : "unable to allocate Redis context";

        throw std::runtime_error(
            "Redis connection failed: "
            + message
        );
    }


    /*
     * Phase 1:
     * pipeline reads of previous cached prices.
     */

    for (const auto& price : prices) {
        const std::string key =
            "mercator:price:"
            + std::to_string(
                price.instrument_id
            );

        if (
            redisAppendCommand(
                context.get(),
                "GET %b",
                key.data(),
                key.size()
            )
            != REDIS_OK
        ) {
            throw std::runtime_error(
                "Redis GET pipeline failed"
            );
        }
    }


    std::vector<double>
        price_changes;

    price_changes.reserve(
        prices.size()
    );


    for (std::size_t index = 0;
         index < prices.size();
         ++index) {
        void* raw_reply = nullptr;

        if (
            redisGetReply(
                context.get(),
                &raw_reply
            )
            != REDIS_OK
        ) {
            throw std::runtime_error(
                "Redis GET reply failed"
            );
        }


        RedisReplyPtr reply{
            static_cast<redisReply*>(
                raw_reply
            )
        };


        require_ok(
            reply.get(),
            "GET"
        );


        double previous_clean_price =
            prices[index].clean_price;


        if (
            reply->type
            == REDIS_REPLY_STRING
            && reply->str != nullptr
        ) {
            try {
                const auto previous =
                    nlohmann::json::parse(
                        std::string{
                            reply->str,
                            reply->len
                        }
                    );

                if (
                    previous.contains(
                        "clean_price"
                    )
                ) {
                    previous_clean_price =
                        previous.at(
                            "clean_price"
                        ).get<double>();
                }
            }
            catch (
                const nlohmann::json::exception&
            ) {
                /*
                 * Corrupt/missing previous cache state
                 * should not block authoritative pricing.
                 *
                 * Treat this as the first observation.
                 */
                previous_clean_price =
                    prices[index].clean_price;
            }
        }


        price_changes.push_back(
            prices[index].clean_price
            - previous_clean_price
        );
    }


    /*
     * Phase 2:
     * pipeline latest-state writes and publications.
     */

    for (std::size_t index = 0;
         index < prices.size();
         ++index) {
        const auto& price =
            prices[index];


        const std::string key =
            "mercator:price:"
            + std::to_string(
                price.instrument_id
            );


        const std::string payload =
            make_payload(
                price,
                event,
                price_changes[index]
            );


        if (
            redisAppendCommand(
                context.get(),
                "SET %b %b",
                key.data(),
                key.size(),
                payload.data(),
                payload.size()
            )
            != REDIS_OK
        ) {
            throw std::runtime_error(
                "Redis SET pipeline failed"
            );
        }


        if (
            redisAppendCommand(
                context.get(),
                "PUBLISH %b %b",
                channel_.data(),
                channel_.size(),
                payload.data(),
                payload.size()
            )
            != REDIS_OK
        ) {
            throw std::runtime_error(
                "Redis PUBLISH pipeline failed"
            );
        }
    }


    /*
     * Drain SET + PUBLISH replies.
     */

    for (std::size_t index = 0;
         index < prices.size();
         ++index) {
        void* raw_reply = nullptr;

        if (
            redisGetReply(
                context.get(),
                &raw_reply
            )
            != REDIS_OK
        ) {
            throw std::runtime_error(
                "Redis SET reply failed"
            );
        }

        RedisReplyPtr set_reply{
            static_cast<redisReply*>(
                raw_reply
            )
        };

        require_ok(
            set_reply.get(),
            "SET"
        );


        raw_reply = nullptr;

        if (
            redisGetReply(
                context.get(),
                &raw_reply
            )
            != REDIS_OK
        ) {
            throw std::runtime_error(
                "Redis PUBLISH reply failed"
            );
        }

        RedisReplyPtr publish_reply{
            static_cast<redisReply*>(
                raw_reply
            )
        };

        require_ok(
            publish_reply.get(),
            "PUBLISH"
        );
    }
}

}  // namespace mercator::pricing
