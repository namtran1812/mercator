#pragma once

#include "mercator/pricing/curve_update.hpp"
#include "mercator/pricing/evaluated_price.hpp"

#include <string>
#include <vector>

namespace mercator::pricing {

class RedisPriceSink {
public:
    RedisPriceSink(
        std::string host,
        int port,
        std::string channel
    );

    void publish(
        const std::vector<EvaluatedPrice>& prices,
        const CurveUpdateEvent& event
    ) const;

private:
    std::string host_;
    int port_;
    std::string channel_;
};

}  // namespace mercator::pricing
