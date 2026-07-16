ALTER TABLE executions
ADD COLUMN IF NOT EXISTS quote_id UUID;

ALTER TABLE executions
ADD COLUMN IF NOT EXISTS instrument_id BIGINT;

ALTER TABLE executions
ADD COLUMN IF NOT EXISTS side TEXT;

ALTER TABLE executions
ADD COLUMN IF NOT EXISTS client TEXT;

ALTER TABLE executions
ADD COLUMN IF NOT EXISTS execution_status TEXT
NOT NULL DEFAULT 'EXECUTED';

ALTER TABLE executions
ADD CONSTRAINT executions_quote_id_unique
UNIQUE (quote_id);

CREATE INDEX IF NOT EXISTS idx_executions_rfq
ON executions (
    rfq_id,
    executed_at DESC
);

CREATE INDEX IF NOT EXISTS idx_executions_instrument
ON executions (
    instrument_id,
    executed_at DESC
);
