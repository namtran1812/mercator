#include "mercator/pricing/clickhouse_price_sink.hpp"

#include <curl/curl.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>

namespace mercator::pricing {

namespace {

std::int64_t epoch_microseconds(
    const std::chrono::system_clock::time_point time
) {
    return std::chrono::duration_cast<
        std::chrono::microseconds
    >(
        time.time_since_epoch()
    ).count();
}


std::string clickhouse_datetime64(
    const std::chrono::system_clock::time_point time
) {
    const std::int64_t micros =
        epoch_microseconds(time);

    const std::int64_t seconds =
        micros / 1'000'000;

    const std::int64_t fractional =
        micros % 1'000'000;

    const std::time_t timestamp =
        static_cast<std::time_t>(
            seconds
        );

    std::tm utc{};

#if defined(_WIN32)
    gmtime_s(
        &utc,
        &timestamp
    );
#else
    gmtime_r(
        &timestamp,
        &utc
    );
#endif

    std::ostringstream stream;

    stream
        << std::put_time(
            &utc,
            "%Y-%m-%d %H:%M:%S"
        )
        << "."
        << std::setw(6)
        << std::setfill('0')
        << fractional;

    return stream.str();
}


std::string make_payload(
    const std::vector<EvaluatedPrice>& prices
) {
    using json =
        nlohmann::json;

    std::ostringstream output;

    for (const auto& price : prices) {
        json row{
            {
                "event_time",
                clickhouse_datetime64(
                    price.event_time
                )
            },
            {
                "received_time",
                clickhouse_datetime64(
                    price.received_time
                )
            },
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
                "reference_version",
                price.reference_version
            },
            {
                "curve_version",
                price.curve_version
            },
            {
                "model_version",
                price.model_version
            },
            {
                "quality_status",
                price.quality_status
            },
            {
                "quality_score",
                price.quality_score
            },
            {
                "calculation_trace_id",
                price.calculation_trace_id
            },
            {
                "source_event_id",
                price.source_event_id
            },
        };

        output
            << row.dump()
            << "\n";
    }

    return output.str();
}


size_t capture_response(
    char* data,
    size_t size,
    size_t count,
    void* destination
) {
    const std::size_t bytes =
        size * count;

    auto* output =
        static_cast<std::string*>(
            destination
        );

    output->append(
        data,
        bytes
    );

    return bytes;
}

}  // namespace


ClickHousePriceSink::ClickHousePriceSink(
    std::string base_url,
    std::string database,
    std::string username,
    std::string password
)
    : base_url_(
        std::move(base_url)
    ),
      database_(
        std::move(database)
    ),
      username_(
        std::move(username)
    ),
      password_(
        std::move(password)
    ) {}


void ClickHousePriceSink::insert(
    const std::vector<EvaluatedPrice>& prices
) const {
    if (prices.empty()) {
        return;
    }


    const std::string source_event_id =
        prices.front().source_event_id;


    for (const auto& price : prices) {
        if (
            price.source_event_id
            != source_event_id
        ) {
            throw std::runtime_error(
                "ClickHouse batch contains multiple "
                "source_event_id values"
            );
        }
    }


    /*
     * Keep individual HTTP inserts small enough that
     * ClickHouse does not need to parse thousands of
     * JSON rows in one large block.
     *
     * Each chunk receives a deterministic deduplication
     * token. A retry can therefore safely replay already
     * successful chunks after a partial failure.
     */
    constexpr std::size_t chunk_size =
        1'000;


    for (
        std::size_t begin = 0,
                    chunk_index = 0;

        begin < prices.size();

        begin += chunk_size,
        ++chunk_index
    ) {
        const std::size_t end =
            std::min(
                begin + chunk_size,
                prices.size()
            );


        std::vector<EvaluatedPrice> chunk{
            prices.begin()
                + static_cast<
                    std::ptrdiff_t
                >(begin),

            prices.begin()
                + static_cast<
                    std::ptrdiff_t
                >(end),
        };


        CURL* raw =
            curl_easy_init();


        if (raw == nullptr) {
            throw std::runtime_error(
                "curl_easy_init failed"
            );
        }


        const std::string dedup_token =
            source_event_id
            + ":"
            + std::to_string(
                chunk_index
            );


        const std::string query =
            "INSERT INTO "
            + database_
            + ".evaluated_prices "
            + "SETTINGS "
            + "insert_deduplication_token = '"
            + dedup_token
            + "' "
            + "FORMAT JSONEachRow";


        char* escaped_query =
            curl_easy_escape(
                raw,
                query.c_str(),
                static_cast<int>(
                    query.size()
                )
            );


        if (escaped_query == nullptr) {
            curl_easy_cleanup(raw);

            throw std::runtime_error(
                "unable to encode ClickHouse query"
            );
        }


        const std::string url =
            base_url_
            + "/?query="
            + escaped_query;


        curl_free(
            escaped_query
        );


        const std::string payload =
            make_payload(
                chunk
            );


        std::string response_body;


        curl_easy_setopt(
            raw,
            CURLOPT_URL,
            url.c_str()
        );

        curl_easy_setopt(
            raw,
            CURLOPT_POST,
            1L
        );

        curl_easy_setopt(
            raw,
            CURLOPT_POSTFIELDS,
            payload.data()
        );

        curl_easy_setopt(
            raw,
            CURLOPT_POSTFIELDSIZE_LARGE,
            static_cast<curl_off_t>(
                payload.size()
            )
        );

        curl_easy_setopt(
            raw,
            CURLOPT_USERNAME,
            username_.c_str()
        );

        curl_easy_setopt(
            raw,
            CURLOPT_PASSWORD,
            password_.c_str()
        );

        curl_easy_setopt(
            raw,
            CURLOPT_WRITEFUNCTION,
            capture_response
        );

        curl_easy_setopt(
            raw,
            CURLOPT_WRITEDATA,
            &response_body
        );

        curl_easy_setopt(
            raw,
            CURLOPT_CONNECTTIMEOUT_MS,
            2'000L
        );

        curl_easy_setopt(
            raw,
            CURLOPT_TIMEOUT_MS,
            15'000L
        );


        const CURLcode result =
            curl_easy_perform(
                raw
            );


        if (result != CURLE_OK) {
            const std::string message =
                curl_easy_strerror(
                    result
                );

            curl_easy_cleanup(raw);

            throw std::runtime_error(
                "ClickHouse chunk insert failed: "
                + message
            );
        }


        long status_code = 0;

        curl_easy_getinfo(
            raw,
            CURLINFO_RESPONSE_CODE,
            &status_code
        );


        curl_easy_cleanup(raw);


        if (
            status_code < 200
            || status_code >= 300
        ) {
            throw std::runtime_error(
                "ClickHouse chunk "
                + std::to_string(
                    chunk_index
                )
                + " returned HTTP "
                + std::to_string(
                    status_code
                )
                + ": "
                + response_body
            );
        }
    }
}

std::size_t
ClickHousePriceSink::event_row_count(
    const std::string& source_event_id
) const {
    CURL* raw =
        curl_easy_init();

    if (raw == nullptr) {
        throw std::runtime_error(
            "curl_easy_init failed"
        );
    }

    const std::string query =
        "SELECT count() FROM "
        + database_
        + ".evaluated_prices "
        + "WHERE source_event_id = toUUID('"
        + source_event_id
        + "')";


    char* escaped_query =
        curl_easy_escape(
            raw,
            query.c_str(),
            static_cast<int>(
                query.size()
            )
        );

    if (escaped_query == nullptr) {
        curl_easy_cleanup(raw);

        throw std::runtime_error(
            "unable to encode ClickHouse query"
        );
    }


    const std::string url =
        base_url_
        + "/?query="
        + escaped_query;

    curl_free(
        escaped_query
    );


    std::string response_body;

    curl_easy_setopt(
        raw,
        CURLOPT_URL,
        url.c_str()
    );

    curl_easy_setopt(
        raw,
        CURLOPT_USERNAME,
        username_.c_str()
    );

    curl_easy_setopt(
        raw,
        CURLOPT_PASSWORD,
        password_.c_str()
    );

    curl_easy_setopt(
        raw,
        CURLOPT_WRITEFUNCTION,
        capture_response
    );

    curl_easy_setopt(
        raw,
        CURLOPT_WRITEDATA,
        &response_body
    );

    curl_easy_setopt(
        raw,
        CURLOPT_CONNECTTIMEOUT_MS,
        2'000L
    );

    curl_easy_setopt(
        raw,
        CURLOPT_TIMEOUT_MS,
        5'000L
    );


    const CURLcode result =
        curl_easy_perform(
            raw
        );

    if (result != CURLE_OK) {
        const std::string message =
            curl_easy_strerror(
                result
            );

        curl_easy_cleanup(raw);

        throw std::runtime_error(
            "ClickHouse idempotency query failed: "
            + message
        );
    }


    long status_code = 0;

    curl_easy_getinfo(
        raw,
        CURLINFO_RESPONSE_CODE,
        &status_code
    );

    curl_easy_cleanup(raw);


    if (
        status_code < 200
        || status_code >= 300
    ) {
        throw std::runtime_error(
            "ClickHouse idempotency query returned HTTP "
            + std::to_string(
                status_code
            )
            + ": "
            + response_body
        );
    }


    try {
        return static_cast<std::size_t>(
            std::stoull(
                response_body
            )
        );
    }
    catch (const std::exception&) {
        throw std::runtime_error(
            "invalid ClickHouse count response: "
            + response_body
        );
    }
}


bool
ClickHousePriceSink::event_exists(
    const std::string& source_event_id
) const {
    return (
        event_row_count(
            source_event_id
        )
        > 0
    );
}


}  // namespace mercator::pricing
