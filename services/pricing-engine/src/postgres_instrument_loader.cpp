#include "mercator/pricing/postgres_instrument_loader.hpp"

#include "mercator/pricing/cashflow.hpp"
#include "mercator/pricing/dependency_resolver.hpp"

#include <libpq-fe.h>

#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace mercator::pricing {

namespace {

struct ConnectionDeleter {
    void operator()(PGconn* connection) const noexcept {
        if (connection != nullptr) {
            PQfinish(connection);
        }
    }
};

struct ResultDeleter {
    void operator()(PGresult* result) const noexcept {
        if (result != nullptr) {
            PQclear(result);
        }
    }
};

using ConnectionPtr =
    std::unique_ptr<
        PGconn,
        ConnectionDeleter
    >;

using ResultPtr =
    std::unique_ptr<
        PGresult,
        ResultDeleter
    >;


Date parse_date(
    const std::string& value
) {
    if (value.size() != 10) {
        throw std::runtime_error(
            "invalid PostgreSQL DATE: "
            + value
        );
    }

    const int year_value =
        std::stoi(
            value.substr(0, 4)
        );

    const unsigned month_value =
        static_cast<unsigned>(
            std::stoul(
                value.substr(5, 2)
            )
        );

    const unsigned day_value =
        static_cast<unsigned>(
            std::stoul(
                value.substr(8, 2)
            )
        );

    return Date{
        std::chrono::year{
            year_value
        },
        std::chrono::month{
            month_value
        },
        std::chrono::day{
            day_value
        },
    };
}


std::vector<CurveNode>
curve_nodes() {
    return {
        {1, 0.25},
        {2, 0.50},
        {3, 1.00},
        {4, 2.00},
        {5, 3.00},
        {6, 5.00},
        {7, 7.00},
        {8, 10.00},
        {9, 30.00},
    };
}


/*
 * Reference data currently does not persist
 * a market spread field.
 *
 * Keep the fallback deterministic so the worker
 * universe is reproducible until a market-derived
 * spread source is wired in.
 */
double deterministic_spread_bps(
    const InstrumentId instrument_id
) {
    return (
        50.0
        + static_cast<double>(
            instrument_id % 351
        )
    );
}

}  // namespace


LoadedInstrumentUniverse
load_instruments_from_postgres(
    const std::string& postgres_dsn,
    const Date valuation_date
) {
    ConnectionPtr connection{
        PQconnectdb(
            postgres_dsn.c_str()
        )
    };

    if (
        connection == nullptr
        || PQstatus(
            connection.get()
        ) != CONNECTION_OK
    ) {
        const std::string message =
            connection != nullptr
                ? PQerrorMessage(
                    connection.get()
                )
                : "unknown connection error";

        throw std::runtime_error(
            "Postgres connection failed: "
            + message
        );
    }


    constexpr const char* query = R"SQL(
        SELECT
            instrument_id,
            coupon_rate,
            maturity_date,
            version_id
        FROM instrument_versions
        WHERE instrument_type = 'CORPORATE_BOND'
          AND valid_to IS NULL
          AND recorded_to IS NULL
          AND coupon_rate IS NOT NULL
          AND maturity_date IS NOT NULL
        ORDER BY instrument_id
    )SQL";


    ResultPtr result{
        PQexec(
            connection.get(),
            query
        )
    };


    if (
        result == nullptr
        || PQresultStatus(
            result.get()
        ) != PGRES_TUPLES_OK
    ) {
        throw std::runtime_error(
            std::string{
                "Postgres instrument query failed: "
            }
            + PQerrorMessage(
                connection.get()
            )
        );
    }


    const int row_count =
        PQntuples(
            result.get()
        );


    if (row_count == 0) {
        throw std::runtime_error(
            "Postgres returned zero corporate bonds"
        );
    }


    PricingDependencyGraph graph;

    std::unordered_map<
        InstrumentId,
        PricingInstrument
    > instruments;

    instruments.reserve(
        static_cast<std::size_t>(
            row_count
        )
    );


    const auto nodes =
        curve_nodes();


    for (
        int row = 0;
        row < row_count;
        ++row
    ) {
        const InstrumentId instrument_id =
            std::stoull(
                PQgetvalue(
                    result.get(),
                    row,
                    0
                )
            );


        /*
         * Stored coupon values are percentages
         * such as 5.2500, while pricing expects
         * decimal form 0.0525.
         */
        const double coupon_rate =
            std::stod(
                PQgetvalue(
                    result.get(),
                    row,
                    1
                )
            )
            / 100.0;


        const Date maturity_date =
            parse_date(
                PQgetvalue(
                    result.get(),
                    row,
                    2
                )
            );


        const std::uint64_t reference_version =
            std::stoull(
                PQgetvalue(
                    result.get(),
                    row,
                    3
                )
            );


        if (
            std::chrono::sys_days{
                maturity_date
            }
            <= std::chrono::sys_days{
                valuation_date
            }
        ) {
            continue;
        }


        const Date issue_date{
            valuation_date.year()
                - std::chrono::years{1},

            valuation_date.month(),

            std::chrono::day{1},
        };


        auto schedule =
            generate_fixed_rate_schedule(
                1000.0,
                coupon_rate,
                2,
                issue_date,
                maturity_date
            );


        graph.register_instrument(
            instrument_id,
            resolve_curve_dependencies(
                schedule.cashflows,
                valuation_date,
                nodes
            )
        );


        instruments.emplace(
            instrument_id,
            PricingInstrument{
                .instrument_id =
                    instrument_id,

                .schedule =
                    std::move(
                        schedule
                    ),

                .spread_bps =
                    deterministic_spread_bps(
                        instrument_id
                    ),

                .market_confidence =
                    0.95,

                .reference_version =
                    reference_version,
            }
        );
    }


    if (instruments.empty()) {
        throw std::runtime_error(
            "No active corporate bonds were loaded"
        );
    }


    return LoadedInstrumentUniverse{
        .dependency_graph =
            std::move(graph),

        .instruments =
            std::move(instruments),
    };
}

}  // namespace mercator::pricing
