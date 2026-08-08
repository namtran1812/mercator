#pragma once

#include "mercator/pricing/curve_update.hpp"

#include <cstdint>
#include <string_view>

namespace mercator::pricing {

enum class CurveEventDisposition {
    Accept,
    Duplicate,
    Stale,
    Gap,
};

class CurveVersionGuard {
public:
    explicit CurveVersionGuard(
        std::uint64_t current_version
    ) noexcept;

    [[nodiscard]]
    CurveEventDisposition classify(
        const CurveUpdateEvent& event
    ) const noexcept;

    void commit(
        const CurveUpdateEvent& event
    );

    [[nodiscard]]
    std::uint64_t current_version() const noexcept;

private:
    std::uint64_t current_version_;
};


[[nodiscard]]
std::string_view to_string(
    CurveEventDisposition disposition
) noexcept;

}  // namespace mercator::pricing
