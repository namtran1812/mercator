ALTER TABLE sec_filings
ADD COLUMN IF NOT EXISTS fetch_status TEXT
NOT NULL DEFAULT 'DISCOVERED';

ALTER TABLE sec_filings
ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ;

ALTER TABLE sec_filings
ADD COLUMN IF NOT EXISTS content_hash TEXT;

ALTER TABLE sec_filings
ADD COLUMN IF NOT EXISTS normalized_text TEXT;

ALTER TABLE sec_filings
ADD COLUMN IF NOT EXISTS fetch_error TEXT;

CREATE TABLE IF NOT EXISTS sec_filing_sections (
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    filing_id UUID NOT NULL
        REFERENCES sec_filings(filing_id)
        ON DELETE CASCADE,

    section_name TEXT NOT NULL,
    section_order INTEGER NOT NULL,

    normalized_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,

    start_character INTEGER NOT NULL,
    end_character INTEGER NOT NULL,

    extraction_method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (
        filing_id,
        section_name,
        section_order
    )
);

CREATE INDEX IF NOT EXISTS idx_sec_filing_sections_filing
ON sec_filing_sections (
    filing_id,
    section_order
);

CREATE INDEX IF NOT EXISTS idx_sec_filing_sections_name
ON sec_filing_sections (
    section_name
);
