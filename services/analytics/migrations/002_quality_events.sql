CREATE TABLE IF NOT EXISTS mercator.quality_events
(
    received_time DateTime64(6, 'UTC'),
    event_time DateTime64(6, 'UTC'),

    event_id String,
    source LowCardinality(String),
    instrument_id UInt64,
    sequence UInt64,

    quality_status LowCardinality(String),
    quality_score Float32,
    accepted Bool,
    reason String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(received_time)
ORDER BY (
    source,
    instrument_id,
    received_time
);
