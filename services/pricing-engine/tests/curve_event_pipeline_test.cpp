#include "mercator/pricing/curve_event_parser.hpp"
#include "mercator/pricing/version_guard.hpp"

#include <iostream>
#include <stdexcept>

namespace {

void require(
    const bool condition,
    const char* message
) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

}  // namespace


int main() {
    using namespace mercator::pricing;

    const auto event =
        parse_curve_update_event(
            R"({
                "event_id": "curve-update-000002",
                "previous_version": 1,
                "new_version": 2,
                "updates": [
                    {
                        "node_id": 4,
                        "maturity_years": 2.0,
                        "old_rate": 0.0400,
                        "new_rate": 0.0410
                    }
                ]
            })"
        );

    require(
        event.event_id
            == "curve-update-000002",
        "event id mismatch"
    );

    require(
        event.previous_version == 1,
        "previous version mismatch"
    );

    require(
        event.new_version == 2,
        "new version mismatch"
    );

    require(
        event.updates.size() == 1,
        "expected one update"
    );

    require(
        event.updates.front().node_id == 4,
        "node id mismatch"
    );


    CurveVersionGuard guard{1};

    require(
        guard.classify(event)
            == CurveEventDisposition::Accept,
        "expected ACCEPT"
    );

    guard.commit(event);

    require(
        guard.current_version() == 2,
        "guard should advance to version 2"
    );

    require(
        guard.classify(event)
            == CurveEventDisposition::Duplicate,
        "replayed event should be duplicate"
    );


    const CurveUpdateEvent stale{
        .event_id = "old-event",
        .previous_version = 0,
        .new_version = 1,
        .updates = event.updates,
    };

    require(
        guard.classify(stale)
            == CurveEventDisposition::Stale,
        "expected STALE"
    );


    const CurveUpdateEvent gap{
        .event_id = "future-event",
        .previous_version = 4,
        .new_version = 5,
        .updates = event.updates,
    };

    require(
        guard.classify(gap)
            == CurveEventDisposition::Gap,
        "expected GAP"
    );


    std::cout
        << "All curve event pipeline tests passed.\n";

    return 0;
}
