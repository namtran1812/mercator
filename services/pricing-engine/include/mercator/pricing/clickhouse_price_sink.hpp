#pragma once

#include "mercator/pricing/evaluated_price.hpp"

#include <string>
#include <vector>

namespace mercator::pricing {

class ClickHousePriceSink {
public:
    ClickHousePriceSink(
        std::string base_url,
        std::string database,
        std::string username,
        std::string password
    );

    void insert(
        const std::vector<EvaluatedPrice>& prices
    ) const;

    [[nodiscard]]
    std::size_t event_row_count(
        const std::string& source_event_id
    ) const;

    [[nodiscard]]
    bool event_exists(
        const std::string& source_event_id
    ) const;

private:
    std::string base_url_;
    std::string database_;
    std::string username_;
    std::string password_;
};

}  // namespace mercator::pricing
