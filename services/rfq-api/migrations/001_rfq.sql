CREATE TABLE IF NOT EXISTS rfqs
(
    id UUID PRIMARY KEY,

    instrument_id BIGINT NOT NULL,

    side TEXT NOT NULL,

    quantity DOUBLE PRECISION NOT NULL,

    client TEXT NOT NULL,

    requested_at TIMESTAMPTZ NOT NULL,

    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dealer_quotes
(
    id UUID PRIMARY KEY,

    rfq_id UUID NOT NULL,

    dealer TEXT NOT NULL,

    price DOUBLE PRECISION NOT NULL,

    spread_bps DOUBLE PRECISION NOT NULL,

    latency_ms INTEGER NOT NULL,

    quoted_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS executions
(
    id UUID PRIMARY KEY,

    rfq_id UUID NOT NULL,

    dealer TEXT NOT NULL,

    price DOUBLE PRECISION NOT NULL,

    quantity DOUBLE PRECISION NOT NULL,

    executed_at TIMESTAMPTZ NOT NULL
);
