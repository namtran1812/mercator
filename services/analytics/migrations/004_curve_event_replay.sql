CREATE TABLE IF NOT EXISTS mercator.curve_events
(
    event_time DateTime64(6, 'UTC'),
    event_id UUID,
    curve_version UInt64,
    curve_name LowCardinality(String),
    tenor LowCardinality(String),
    old_rate Float64,
    new_rate Float64,
    source LowCardinality(String),
    scenario_name LowCardinality(String),
    recorded_at DateTime64(6, 'UTC')
        DEFAULT now64(6)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (
    scenario_name,
    event_time,
    curve_version
);
