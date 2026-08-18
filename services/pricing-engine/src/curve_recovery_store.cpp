#include "mercator/pricing/curve_recovery_store.hpp"

#include <curl/curl.h>
#include <nlohmann/json.hpp>

#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>

namespace mercator::pricing {

namespace {

std::uint64_t json_uint64(
    const nlohmann::json& value
) {
    if (value.is_number_unsigned()) {
        return value.get<std::uint64_t>();
    }

    if (value.is_number_integer()) {
        return static_cast<std::uint64_t>(
            value.get<std::int64_t>()
        );
    }

    if (value.is_string()) {
        return std::stoull(
            value.get<std::string>()
        );
    }

    throw std::runtime_error(
        "expected unsigned integer JSON value"
    );
}


double json_double(
    const nlohmann::json& value
) {
    if (value.is_number()) {
        return value.get<double>();
    }

    if (value.is_string()) {
        return std::stod(
            value.get<std::string>()
        );
    }

    throw std::runtime_error(
        "expected floating-point JSON value"
    );
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


CurveRecoveryStore::CurveRecoveryStore(
    std::string base_url,
    std::string database,
    std::string username,
    std::string password
)
    : base_url_(std::move(base_url)),
      database_(std::move(database)),
      username_(std::move(username)),
      password_(std::move(password)) {}


std::string CurveRecoveryStore::execute_query(
    const std::string& query
) const {
    CURL* raw =
        curl_easy_init();

    if (raw == nullptr) {
        throw std::runtime_error(
            "curl_easy_init failed"
        );
    }

    char* escaped =
        curl_easy_escape(
            raw,
            query.c_str(),
            static_cast<int>(
                query.size()
            )
        );

    if (escaped == nullptr) {
        curl_easy_cleanup(raw);

        throw std::runtime_error(
            "unable to encode ClickHouse recovery query"
        );
    }

    const std::string url =
        base_url_
        + "/?database="
        + database_
        + "&query="
        + escaped;

    curl_free(escaped);

    std::string response;

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
        &response
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
            "ClickHouse recovery query failed: "
            + message
        );
    }

    long status = 0;

    curl_easy_getinfo(
        raw,
        CURLINFO_RESPONSE_CODE,
        &status
    );

    curl_easy_cleanup(raw);

    if (
        status < 200
        || status >= 300
    ) {
        throw std::runtime_error(
            "ClickHouse recovery query returned HTTP "
            + std::to_string(status)
            + ": "
            + response
        );
    }

    return response;
}


std::optional<RecoveredCurve>
CurveRecoveryStore::recover_latest(
    const std::string& curve_name
) const {
    /*
     * curve_name is currently an internal configuration
     * value. Keep the query deliberately simple until the
     * recovery API needs arbitrary user-provided names.
     */
    if (curve_name.find('\'') != std::string::npos) {
        throw std::runtime_error(
            "invalid curve name"
        );
    }

    const std::string query =
        "SELECT "
        "curve_version, "
        "maturity_years, "
        "zero_rates "
        "FROM curve_checkpoints "
        "WHERE curve_name = '"
        + curve_name
        + "' "
        "ORDER BY curve_version DESC, recorded_at DESC "
        "LIMIT 1 "
        "FORMAT JSONEachRow";

    const std::string body =
        execute_query(query);

    if (body.empty()) {
        return std::nullopt;
    }

    const auto row =
        nlohmann::json::parse(body);

    const auto maturities =
        row.at("maturity_years")
            .get<std::vector<double>>();

    const auto rates =
        row.at("zero_rates")
            .get<std::vector<double>>();

    if (maturities.size() != rates.size()) {
        throw std::runtime_error(
            "recovered curve checkpoint has "
            "mismatched node arrays"
        );
    }

    if (maturities.empty()) {
        throw std::runtime_error(
            "recovered curve checkpoint is empty"
        );
    }

    std::vector<CurvePoint> points;

    points.reserve(
        maturities.size()
    );

    for (
        std::size_t index = 0;
        index < maturities.size();
        ++index
    ) {
        points.push_back(
            CurvePoint{
                maturities[index],
                rates[index],
            }
        );
    }

    return RecoveredCurve{
        json_uint64(
            row.at("curve_version")
        ),
        std::move(points),
    };
}

}  // namespace mercator::pricing


namespace mercator::pricing {

std::vector<CurveUpdateEvent>
CurveRecoveryStore::recover_events_after(
    const std::string& curve_name,
    const std::uint64_t version
) const {
    if (curve_name.find('\'') != std::string::npos) {
        throw std::runtime_error(
            "invalid curve name"
        );
    }

    /*
     * Redelivery can create duplicate physical ClickHouse rows.
     *
     * We collapse them by logical node transition:
     *
     *   event_id + node_id
     *
     * and retain the latest physical row by recorded_at.
     */
    const std::string query =
        "SELECT "
        "event_id, "
        "previous_version, "
        "curve_version, "
        "event_time, "
        "curve_name, "
        "source, "
        "scenario_name, "
        "node_id, "
        "maturity_years, "
        "old_rate, "
        "new_rate "
        "FROM ("
            "SELECT "
            "argMax(ce.event_id, ce.recorded_at) AS event_id, "
            "argMax(ce.previous_version, ce.recorded_at) "
                "AS previous_version, "
            "argMax(ce.curve_version, ce.recorded_at) "
                "AS curve_version, "
            "argMax(ce.event_time, ce.recorded_at) "
                "AS event_time, "
            "argMax(ce.curve_name, ce.recorded_at) "
                "AS curve_name, "
            "argMax(ce.source, ce.recorded_at) "
                "AS source, "
            "argMax(ce.scenario_name, ce.recorded_at) "
                "AS scenario_name, "
            "node_id, "
            "argMax(ce.maturity_years, ce.recorded_at) "
                "AS maturity_years, "
            "argMax(ce.old_rate, ce.recorded_at) "
                "AS old_rate, "
            "argMax(ce.new_rate, ce.recorded_at) "
                "AS new_rate "
            "FROM curve_events AS ce "
            "WHERE ce.curve_name = '"
            + curve_name
            + "' "
            "AND ce.curve_version > "
            + std::to_string(version)
            + " "
            "GROUP BY ce.event_id, ce.node_id"
        ") "
        "ORDER BY curve_version ASC, event_id ASC, node_id ASC "
        "FORMAT JSONEachRow";

    const std::string body =
        execute_query(query);

    if (body.empty()) {
        return {};
    }

    std::vector<CurveUpdateEvent> events;

    CurveUpdateEvent current;
    bool have_current = false;

    std::size_t start = 0;

    while (start < body.size()) {
        const std::size_t end =
            body.find(
                '\n',
                start
            );

        const std::string line =
            body.substr(
                start,
                end == std::string::npos
                    ? std::string::npos
                    : end - start
            );

        if (!line.empty()) {
            const auto row =
                nlohmann::json::parse(
                    line
                );

            const std::string event_id =
                row.at("event_id")
                    .get<std::string>();

            if (
                !have_current
                || current.event_id != event_id
            ) {
                if (have_current) {
                    events.push_back(
                        std::move(current)
                    );
                }

                current =
                    CurveUpdateEvent{
                        .event_id =
                            event_id,

                        .event_time =
                            row.at("event_time")
                                .get<std::string>(),

                        .curve_name =
                            row.at("curve_name")
                                .get<std::string>(),

                        .source =
                            row.at("source")
                                .get<std::string>(),

                        .scenario_name =
                            row.at("scenario_name")
                                .get<std::string>(),

                        .previous_version =
                            json_uint64(
                                row.at(
                                    "previous_version"
                                )
                            ),

                        .new_version =
                            json_uint64(
                                row.at(
                                    "curve_version"
                                )
                            ),

                        .updates = {},
                    };

                have_current = true;
            }

            if (
                current.previous_version
                != json_uint64(
                    row.at(
                        "previous_version"
                    )
                )
                || current.new_version
                != json_uint64(
                    row.at(
                        "curve_version"
                    )
                )
            ) {
                throw std::runtime_error(
                    "recovery event rows disagree "
                    "on version metadata"
                );
            }

            current.updates.push_back(
                CurveNodeUpdate{
                    .node_id =
                        static_cast<CurveNodeId>(
                            json_uint64(
                                row.at(
                                    "node_id"
                                )
                            )
                        ),

                    .maturity_years =
                        json_double(
                            row.at(
                                "maturity_years"
                            )
                        ),

                    .old_rate =
                        json_double(
                            row.at(
                                "old_rate"
                            )
                        ),

                    .new_rate =
                        json_double(
                            row.at(
                                "new_rate"
                            )
                        ),
                }
            );
        }

        if (end == std::string::npos) {
            break;
        }

        start = end + 1;
    }

    if (have_current) {
        events.push_back(
            std::move(current)
        );
    }

    return events;
}

}  // namespace mercator::pricing
