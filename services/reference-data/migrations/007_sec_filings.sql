CREATE TABLE IF NOT EXISTS sec_issuers (
    cik TEXT PRIMARY KEY,
    entity_name TEXT NOT NULL,
    tickers TEXT[] NOT NULL DEFAULT '{}',
    exchanges TEXT[] NOT NULL DEFAULT '{}',
    sic TEXT,
    sic_description TEXT,
    fiscal_year_end TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sec_filings (
    filing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    cik TEXT NOT NULL
        REFERENCES sec_issuers(cik)
        ON DELETE CASCADE,

    accession_number TEXT NOT NULL,
    form_type TEXT NOT NULL,

    filing_date DATE NOT NULL,
    report_date DATE,
    acceptance_datetime TIMESTAMPTZ,

    primary_document TEXT,
    primary_document_description TEXT,

    filing_url TEXT NOT NULL,
    index_url TEXT NOT NULL,

    source_name TEXT NOT NULL DEFAULT 'sec-edgar',
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    UNIQUE (cik, accession_number)
);

CREATE INDEX IF NOT EXISTS idx_sec_filings_issuer_date
ON sec_filings (
    cik,
    filing_date DESC
);

CREATE INDEX IF NOT EXISTS idx_sec_filings_form
ON sec_filings (
    form_type,
    filing_date DESC
);
