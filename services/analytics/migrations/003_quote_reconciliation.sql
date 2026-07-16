CREATE TABLE IF NOT EXISTS mercator.market_quotes
(
    event_time DateTime64(6, 'UTC'),
    quote_id String,
    source LowCardinality(String),
    instrument_id UInt64,

    bid Float64,
    ask Float64,
    mid Float64,

    source_reliability Float32,
    accepted Bool,
    rejection_reason LowCardinality(String),

    evaluation_id UUID
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (
    instrument_id,
    event_time,
    source
);

CREATE TABLE IF NOT EXISTS mercator.reconciled_quotes
(
    evaluation_time DateTime64(6, 'UTC'),
    evaluation_id UUID,
    instrument_id UInt64,

    evaluated_bid Float64,
    evaluated_ask Float64,
    evaluated_mid Float64,

    confidence_score Float32,
    source_dispersion_bps Float64,

    accepted_sources UInt16,
    rejected_sources UInt16
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(evaluation_time)
ORDER BY (
    instrument_id,
    evaluation_time
);
