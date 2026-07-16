ALTER TABLE dealer_quotes
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

ALTER TABLE dealer_quotes
ADD COLUMN IF NOT EXISTS quote_status TEXT
NOT NULL DEFAULT 'ACTIVE';

ALTER TABLE dealer_quotes
ADD COLUMN IF NOT EXISTS inventory_adjustment_bps
DOUBLE PRECISION NOT NULL DEFAULT 0.0;

ALTER TABLE dealer_quotes
ADD COLUMN IF NOT EXISTS size_adjustment_bps
DOUBLE PRECISION NOT NULL DEFAULT 0.0;

CREATE UNIQUE INDEX IF NOT EXISTS idx_dealer_quotes_rfq_dealer
ON dealer_quotes (
    rfq_id,
    dealer
);

CREATE INDEX IF NOT EXISTS idx_dealer_quotes_active
ON dealer_quotes (
    rfq_id,
    quote_status,
    expires_at
);
