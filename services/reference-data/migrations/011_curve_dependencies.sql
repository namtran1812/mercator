CREATE TABLE IF NOT EXISTS instrument_curve_dependencies (
    instrument_id BIGINT NOT NULL,
    curve_name TEXT NOT NULL DEFAULT 'UST',
    tenor TEXT NOT NULL,
    dependency_weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (
        instrument_id,
        curve_name,
        tenor
    )
);

CREATE INDEX IF NOT EXISTS idx_curve_dependencies_tenor
ON instrument_curve_dependencies (
    curve_name,
    tenor,
    instrument_id
);
