CREATE TABLE IF NOT EXISTS mercator.evaluated_prices
(
    event_time DateTime64(6, 'UTC'),
    received_time DateTime64(6, 'UTC'),
    instrument_id UInt64,

    clean_price Float64,
    dirty_price Float64,
    yield_to_maturity Float64,
    g_spread_bps Float64,
    modified_duration Float64,
    convexity Float64,

    reference_version UInt64,
    curve_version UInt64,

    model_version LowCardinality(String),
    quality_status LowCardinality(String),
    quality_score Float32,

    calculation_trace_id UUID,
    source_event_id UUID
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (instrument_id, event_time);
