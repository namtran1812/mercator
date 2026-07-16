CREATE TABLE IF NOT EXISTS reference_sources (
    source_name TEXT PRIMARY KEY,
    source_priority INTEGER NOT NULL,
    trust_score NUMERIC(5,4) NOT NULL
        CHECK (trust_score >= 0 AND trust_score <= 1),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_observations (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id BIGINT NOT NULL,
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL,

    source_name TEXT NOT NULL
        REFERENCES reference_sources(source_name),

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_event_id UUID NOT NULL UNIQUE,

    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE TABLE IF NOT EXISTS reconciled_reference_values (
    reconciliation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id BIGINT NOT NULL,
    field_name TEXT NOT NULL,
    selected_value TEXT NOT NULL,

    selected_source TEXT NOT NULL,
    confidence_score NUMERIC(5,4) NOT NULL
        CHECK (confidence_score >= 0 AND confidence_score <= 1),

    contributing_observations UUID[] NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,

    recorded_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_to TIMESTAMPTZ,

    CHECK (valid_to IS NULL OR valid_to > valid_from),
    CHECK (recorded_to IS NULL OR recorded_to > recorded_from)
);

CREATE INDEX IF NOT EXISTS idx_reference_observations_lookup
ON reference_observations (
    instrument_id,
    field_name,
    valid_from,
    valid_to
);

CREATE INDEX IF NOT EXISTS idx_reconciled_reference_lookup
ON reconciled_reference_values (
    instrument_id,
    field_name,
    valid_from,
    valid_to,
    recorded_from,
    recorded_to
);
