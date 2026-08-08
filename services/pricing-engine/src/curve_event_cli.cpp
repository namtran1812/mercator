#include "mercator/pricing/curve_event_parser.hpp"

#include <iostream>
#include <iterator>
#include <string>

int main() {
    using namespace mercator::pricing;

    const std::string payload{
        std::istreambuf_iterator<char>{std::cin},
        std::istreambuf_iterator<char>{}
    };

    try {
        const auto event =
            parse_curve_update_event(
                payload
            );

        std::cout
            << "event_id="
            << event.event_id
            << "\n";

        std::cout
            << "previous_version="
            << event.previous_version
            << "\n";

        std::cout
            << "new_version="
            << event.new_version
            << "\n";

        std::cout
            << "updates="
            << event.updates.size()
            << "\n";

        for (const auto& update : event.updates) {
            std::cout
                << "node_id="
                << update.node_id
                << " maturity="
                << update.maturity_years
                << " old_rate="
                << update.old_rate
                << " new_rate="
                << update.new_rate
                << "\n";
        }

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "ERROR: "
            << error.what()
            << "\n";

        return 1;
    }
}
