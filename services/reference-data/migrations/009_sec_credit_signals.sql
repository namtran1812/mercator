CREATE TABLE IF NOT EXISTS sec_filing_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    filing_id UUID NOT NULL
        REFERENCES sec_filings(filing_id)
        ON DELETE CASCADE,

    section_id UUID
        REFERENCES sec_filing_sections(section_id)
        ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    section_name TEXT,

    chunk_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,

    start_character INTEGER NOT NULL,
    end_character INTEGER NOT NULL,

    token_estimate INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (filing_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS sec_credit_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    filing_id UUID NOT NULL
        REFERENCES sec_filings(filing_id)
        ON DELETE CASCADE,

    chunk_id UUID NOT NULL
        REFERENCES sec_filing_chunks(chunk_id)
        ON DELETE CASCADE,

    signal_type TEXT NOT NULL,
    signal_value TEXT NOT NULL,

    confidence_score NUMERIC(5,4) NOT NULL
        CHECK (
            confidence_score >= 0
            AND confidence_score <= 1
        ),

    evidence_text TEXT NOT NULL,

    extraction_method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (
        chunk_id,
        signal_type,
        signal_value
    )
);

CREATE INDEX IF NOT EXISTS idx_sec_chunks_filing
ON sec_filing_chunks (
    filing_id,
    chunk_index
);

CREATE INDEX IF NOT EXISTS idx_sec_chunks_section
ON sec_filing_chunks (
    section_name
);

CREATE INDEX IF NOT EXISTS idx_sec_credit_signals_type
ON sec_credit_signals (
    signal_type,
    confidence_score DESC
);
