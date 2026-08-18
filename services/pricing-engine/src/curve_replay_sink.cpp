#include "mercator/pricing/curve_replay_sink.hpp"

#include <curl/curl.h>
#include <nlohmann/json.hpp>

#include <chrono>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

namespace mercator::pricing {

namespace {

std::string clickhouse_datetime64(
    std::string value
) {
    /*
     * Accept producer ISO-8601 timestamps like:
     *
     *   2026-08-18T04:50:12Z
     *
     * and convert them to ClickHouse DateTime64 text:
     *
     *   2026-08-18 04:50:12.000000
     */
    if (value.empty()) {
        return "1970-01-01 00:00:00.000000";
    }

    if (
        value.size() >= 20
        && value[10] == 'T'
        && value.back() == 'Z'
    ) {
        value[10] = ' ';
        value.pop_back();

        if (
            value.find('.') == std::string::npos
        ) {
            value += ".000000";
        }

        return value;
    }

    /*
     * Already ClickHouse-compatible.
     */
    return value;
}


std::string json_payload(
    const nlohmann::json& row
) {
    return row.dump() + "\n";
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


CurveReplaySink::CurveReplaySink(
    std::string base_url,
    std::string database,
    std::string username,
    std::string password
)
    : base_url_(std::move(base_url)),
      database_(std::move(database)),
      username_(std::move(username)),
      password_(std::move(password)) {}


void CurveReplaySink::execute_insert(
    const std::string& query,
    const std::string& payload
) const {
    CURL* raw =
        curl_easy_init();

    if (raw == nullptr) {
        throw std::runtime_error(
            "curl_easy_init failed"
        );
    }

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
            "unable to encode ClickHouse replay query"
        );
    }

    const std::string url =
        base_url_
        + "/?query="
        + escaped_query;

    curl_free(escaped_query);

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
        10'000L
    );

    const CURLcode result =
        curl_easy_perform(raw);

    if (result != CURLE_OK) {
        const std::string message =
            curl_easy_strerror(result);

        curl_easy_cleanup(raw);

        throw std::runtime_error(
            "ClickHouse curve replay insert failed: "
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
            "ClickHouse curve replay insert returned HTTP "
            + std::to_string(status_code)
            + ": "
            + response_body
        );
    }
}


void CurveReplaySink::insert_event(
    const CurveUpdateEvent& event
) const {
    if (event.updates.empty()) {
        return;
    }

    std::ostringstream payload;

    for (const auto& update : event.updates) {
        nlohmann::json row{
            {
                "event_id",
                event.event_id
            },
            {
                "previous_version",
                event.previous_version
            },
            {
                "curve_version",
                event.new_version
            },
            {
                "event_time",
                clickhouse_datetime64(
                    event.event_time
                )
            },
            {
                "curve_name",
                event.curve_name.empty()
                    ? "UST"
                    : event.curve_name
            },
            {
                "source",
                event.source.empty()
                    ? "curve-stream"
                    : event.source
            },
            {
                "scenario_name",
                event.scenario_name.empty()
                    ? "live"
                    : event.scenario_name
            },
            {
                "node_id",
                update.node_id
            },
            {
                "maturity_years",
                update.maturity_years
            },
            {
                "tenor",
                std::to_string(
                    update.node_id
                )
            },
            {
                "old_rate",
                update.old_rate
            },
            {
                "new_rate",
                update.new_rate
            },
        };

        payload
            << row.dump()
            << "\n";
    }

    /*
     * Deterministic token:
     *
     * Kafka may redeliver an event when the process
     * crashes after ClickHouse persistence but before
     * committing the Kafka offset.
     */
    const std::string query =
        "INSERT INTO "
        + database_
        + ".curve_events "
        + "SETTINGS insert_deduplication_token = 'curve-event:"
        + event.event_id
        + "' "
        + "FORMAT JSONEachRow";

    execute_insert(
        query,
        payload.str()
    );
}


void CurveReplaySink::insert_checkpoint(
    const CurveUpdateEvent& event,
    const Date valuation_date,
    const std::vector<CurvePoint>& curve_points
) const {
    const auto year =
        static_cast<int>(
            valuation_date.year()
        );

    const auto month =
        static_cast<unsigned>(
            valuation_date.month()
        );

    const auto day =
        static_cast<unsigned>(
            valuation_date.day()
        );

    std::ostringstream valuation_date_text;

    valuation_date_text
        << std::setfill('0')
        << std::setw(4)
        << year
        << "-"
        << std::setw(2)
        << month
        << "-"
        << std::setw(2)
        << day;


    nlohmann::json maturities =
        nlohmann::json::array();

    nlohmann::json zero_rates =
        nlohmann::json::array();

    for (const auto& point : curve_points) {
        maturities.push_back(
            point.maturity_years
        );

        zero_rates.push_back(
            point.zero_rate
        );
    }

    nlohmann::json row{
        {
            "source_event_id",
            event.event_id
        },
        {
            "curve_version",
            event.new_version
        },
        {
            "curve_name",
            event.curve_name.empty()
                ? "UST"
                : event.curve_name
        },
        {
            "valuation_date",
            valuation_date_text.str()
        },
        {
            "source",
            event.source.empty()
                ? "pricing-worker"
                : event.source
        },
        {
            "maturity_years",
            std::move(maturities)
        },
        {
            "zero_rates",
            std::move(zero_rates)
        },
    };

    const std::string query =
        "INSERT INTO "
        + database_
        + ".curve_checkpoints "
        + "SETTINGS insert_deduplication_token = 'curve-checkpoint:"
        + std::to_string(event.new_version)
        + "' "
        + "FORMAT JSONEachRow";

    execute_insert(
        query,
        json_payload(row)
    );
}


bool CurveReplaySink::should_checkpoint(
    const std::uint64_t version,
    const std::uint64_t interval
) const noexcept {
    return (
        interval != 0
        && version % interval == 0
    );
}

}  // namespace mercator::pricing
