CREATE OR REPLACE VIEW rfq_analytics AS
SELECT
    r.id AS rfq_id,
    r.instrument_id,
    r.side,
    r.quantity,
    r.client,
    r.requested_at,
    r.status,

    count(q.id) AS quote_count,

    min(q.latency_ms) AS minimum_latency_ms,
    avg(q.latency_ms) AS average_latency_ms,
    max(q.latency_ms) AS maximum_latency_ms,

    min(q.price) FILTER (
        WHERE r.side = 'BUY'
    ) AS best_buy_price,

    max(q.price) FILTER (
        WHERE r.side = 'SELL'
    ) AS best_sell_price,

    bool_or(
        q.quote_status = 'EXECUTED'
    ) AS was_executed,

    max(e.executed_at) AS executed_at,

    CASE
        WHEN max(e.executed_at) IS NULL
        THEN NULL
        ELSE
            EXTRACT(
                EPOCH FROM (
                    max(e.executed_at)
                    - r.requested_at
                )
            ) * 1000.0
    END AS execution_latency_ms

FROM rfqs r

LEFT JOIN dealer_quotes q
    ON q.rfq_id = r.id

LEFT JOIN executions e
    ON e.rfq_id = r.id

GROUP BY
    r.id,
    r.instrument_id,
    r.side,
    r.quantity,
    r.client,
    r.requested_at,
    r.status;
