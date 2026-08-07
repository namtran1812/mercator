CREATE TABLE IF NOT EXISTS fixed_income_etf_versions (
    version_id BIGSERIAL PRIMARY KEY,

    instrument_id BIGINT NOT NULL,

    fund_name TEXT NOT NULL,

    benchmark_name TEXT,

    expense_ratio NUMERIC(10, 8),

    shares_outstanding NUMERIC(24, 6),

    nav NUMERIC(20, 8),

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,

    recorded_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_to TIMESTAMPTZ,

    source TEXT NOT NULL,
    source_event_id UUID NOT NULL
);

CREATE INDEX IF NOT EXISTS
    idx_fixed_income_etf_versions_current
ON fixed_income_etf_versions (
    instrument_id,
    valid_to,
    recorded_to
);


CREATE TABLE IF NOT EXISTS fixed_income_etf_constituents (
    etf_instrument_id BIGINT NOT NULL,
    constituent_instrument_id BIGINT NOT NULL,

    weight NUMERIC(14, 10) NOT NULL
        CHECK (
            weight >= 0
            AND weight <= 1
        ),

    face_value NUMERIC(24, 6),

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,

    recorded_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_to TIMESTAMPTZ,

    source TEXT NOT NULL,
    source_event_id UUID NOT NULL,

    PRIMARY KEY (
        etf_instrument_id,
        constituent_instrument_id,
        recorded_from
    )
);

CREATE INDEX IF NOT EXISTS
    idx_etf_constituents_current
ON fixed_income_etf_constituents (
    etf_instrument_id,
    valid_to,
    recorded_to
);
