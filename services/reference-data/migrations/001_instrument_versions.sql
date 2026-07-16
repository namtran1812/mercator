CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS instrument_versions (
    version_id BIGSERIAL PRIMARY KEY,
    instrument_id BIGINT NOT NULL,
    instrument_type TEXT NOT NULL
        CHECK (instrument_type IN ('CORPORATE_BOND', 'FIXED_INCOME_ETF')),

    cusip TEXT,
    isin TEXT,
    ticker TEXT,

    issuer_name TEXT NOT NULL,
    coupon_rate NUMERIC(10, 6),
    maturity_date DATE,
    rating TEXT,
    sector TEXT,
    currency CHAR(3) NOT NULL DEFAULT 'USD',

    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,

    recorded_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    recorded_to TIMESTAMPTZ,

    source TEXT NOT NULL,
    source_priority INTEGER NOT NULL DEFAULT 100,
    source_event_id UUID NOT NULL DEFAULT gen_random_uuid(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (source_event_id),

    CHECK (valid_to IS NULL OR valid_to > valid_from),
    CHECK (recorded_to IS NULL OR recorded_to > recorded_from)
);

CREATE INDEX IF NOT EXISTS idx_instrument_versions_instrument
ON instrument_versions (instrument_id);

CREATE INDEX IF NOT EXISTS idx_instrument_versions_cusip
ON instrument_versions (cusip)
WHERE cusip IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_instrument_versions_isin
ON instrument_versions (isin)
WHERE isin IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_instrument_versions_temporal
ON instrument_versions (
    instrument_id,
    valid_from,
    valid_to,
    recorded_from,
    recorded_to
);
