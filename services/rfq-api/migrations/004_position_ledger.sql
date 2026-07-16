CREATE TABLE IF NOT EXISTS trading_accounts
(
    account_id UUID PRIMARY KEY,
    account_name TEXT NOT NULL UNIQUE,
    base_currency TEXT NOT NULL DEFAULT 'USD',
    cash_balance DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS positions
(
    account_id UUID NOT NULL
        REFERENCES trading_accounts(account_id)
        ON DELETE CASCADE,

    instrument_id BIGINT NOT NULL,

    face_value DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    average_cost DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    realized_pnl DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (
        account_id,
        instrument_id
    )
);

CREATE TABLE IF NOT EXISTS position_ledger_entries
(
    ledger_entry_id UUID PRIMARY KEY,

    account_id UUID NOT NULL
        REFERENCES trading_accounts(account_id)
        ON DELETE CASCADE,

    execution_id UUID NOT NULL
        REFERENCES executions(id)
        ON DELETE RESTRICT,

    instrument_id BIGINT NOT NULL,
    side TEXT NOT NULL,

    quantity DOUBLE PRECISION NOT NULL,
    execution_price DOUBLE PRECISION NOT NULL,

    cash_change DOUBLE PRECISION NOT NULL,
    face_value_change DOUBLE PRECISION NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,

    UNIQUE (execution_id)
);

CREATE INDEX IF NOT EXISTS idx_positions_account
ON positions (
    account_id,
    instrument_id
);

CREATE INDEX IF NOT EXISTS idx_position_ledger_account_time
ON position_ledger_entries (
    account_id,
    created_at DESC
);
