#include "mercator/pricing/version_guard.hpp"

#include <stdexcept>

namespace mercator::pricing {

CurveVersionGuard::CurveVersionGuard(
    const std::uint64_t current_version
) noexcept
    : current_version_(current_version) {}


CurveEventDisposition
CurveVersionGuard::classify(
    const CurveUpdateEvent& event
) const noexcept {
    if (
        event.new_version
        == current_version_
    ) {
        return CurveEventDisposition::Duplicate;
    }

    if (
        event.new_version
        < current_version_
    ) {
        return CurveEventDisposition::Stale;
    }

    if (
        event.previous_version
            != current_version_
        || event.new_version
            != current_version_ + 1
    ) {
        return CurveEventDisposition::Gap;
    }

    return CurveEventDisposition::Accept;
}


void CurveVersionGuard::commit(
    const CurveUpdateEvent& event
) {
    if (
        classify(event)
        != CurveEventDisposition::Accept
    ) {
        throw std::invalid_argument(
            "cannot commit non-accepted curve event"
        );
    }

    current_version_ =
        event.new_version;
}


std::uint64_t
CurveVersionGuard::current_version() const noexcept {
    return current_version_;
}


std::string_view to_string(
    const CurveEventDisposition disposition
) noexcept {
    switch (disposition) {
        case CurveEventDisposition::Accept:
            return "ACCEPT";

        case CurveEventDisposition::Duplicate:
            return "DUPLICATE";

        case CurveEventDisposition::Stale:
            return "STALE";

        case CurveEventDisposition::Gap:
            return "GAP";
    }

    return "UNKNOWN";
}

}  // namespace mercator::pricing
