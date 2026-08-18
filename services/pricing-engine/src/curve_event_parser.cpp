#include "mercator/pricing/curve_event_parser.hpp"

#include <nlohmann/json.hpp>

#include <stdexcept>
#include <string>

namespace mercator::pricing {

CurveUpdateEvent parse_curve_update_event(
    const std::string_view payload
) {
    using json = nlohmann::json;

    json document;

    try {
        document = json::parse(payload);
    } catch (const json::exception& error) {
        throw std::invalid_argument(
            std::string{
                "invalid curve update JSON: "
            }
            + error.what()
        );
    }

    try {
        CurveUpdateEvent event{
            .event_id =
                document.at("event_id").get<std::string>(),

            .event_time =
                document.value(
                    "event_time",
                    std::string{}
                ),

            .curve_name =
                document.value(
                    "curve_name",
                    std::string{"UST"}
                ),

            .source =
                document.value(
                    "source",
                    std::string{"curve-stream"}
                ),

            .scenario_name =
                document.value(
                    "scenario_name",
                    std::string{"live"}
                ),

            .previous_version =
                document.at("previous_version")
                    .get<std::uint64_t>(),

            .new_version =
                document.at("new_version")
                    .get<std::uint64_t>(),

            .updates = {},
        };

        if (event.event_id.empty()) {
            throw std::invalid_argument(
                "event_id cannot be empty"
            );
        }

        if (
            event.new_version
            <= event.previous_version
        ) {
            throw std::invalid_argument(
                "new_version must exceed previous_version"
            );
        }

        const auto& updates =
            document.at("updates");

        if (!updates.is_array()) {
            throw std::invalid_argument(
                "updates must be an array"
            );
        }

        if (updates.empty()) {
            throw std::invalid_argument(
                "curve update must contain updates"
            );
        }

        event.updates.reserve(updates.size());

        for (const auto& update : updates) {
            event.updates.push_back(
                CurveNodeUpdate{
                    .node_id =
                        update.at("node_id")
                            .get<CurveNodeId>(),

                    .maturity_years =
                        update.at("maturity_years")
                            .get<double>(),

                    .old_rate =
                        update.at("old_rate")
                            .get<double>(),

                    .new_rate =
                        update.at("new_rate")
                            .get<double>(),
                }
            );
        }

        return event;

    } catch (const json::exception& error) {
        throw std::invalid_argument(
            std::string{
                "invalid curve update schema: "
            }
            + error.what()
        );
    }
}

}  // namespace mercator::pricing
