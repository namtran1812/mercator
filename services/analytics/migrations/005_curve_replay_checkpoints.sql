ALTER TABLE mercator.curve_events
    ADD COLUMN IF NOT EXISTS
        previous_version UInt64
        DEFAULT 0;

ALTER TABLE mercator.curve_events
    ADD COLUMN IF NOT EXISTS
        node_id UInt64
        DEFAULT 0;

ALTER TABLE mercator.curve_events
    ADD COLUMN IF NOT EXISTS
        maturity_years Float64
        DEFAULT 0.0;


CREATE TABLE IF NOT EXISTS mercator.curve_checkpoints
(
    curve_name LowCardinality(String),

    curve_version UInt64,

    valuation_date Date,

    maturity_years Array(Float64),

    zero_rates Array(Float64),

    source LowCardinality(String),

    source_event_id String,

    recorded_at DateTime64(6, 'UTC')
        DEFAULT now64(6),

    CONSTRAINT matching_curve_nodes
        CHECK length(maturity_years)
            = length(zero_rates)
)
ENGINE = MergeTree
ORDER BY (
    curve_name,
    curve_version
);
