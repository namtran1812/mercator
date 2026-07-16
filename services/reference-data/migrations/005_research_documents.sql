CREATE TABLE IF NOT EXISTS research_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_name TEXT NOT NULL,
    source_document_id TEXT NOT NULL,

    canonical_url TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    series TEXT,
    category TEXT,

    published_at TIMESTAMPTZ,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    fetched_at TIMESTAMPTZ,

    summary TEXT,
    normalized_text TEXT,

    content_hash TEXT,
    extraction_status TEXT NOT NULL DEFAULT 'DISCOVERED',
    extraction_error TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    UNIQUE (source_name, source_document_id),
    UNIQUE (canonical_url)
);

CREATE INDEX IF NOT EXISTS idx_research_documents_published
ON research_documents (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_documents_series
ON research_documents (series);

CREATE INDEX IF NOT EXISTS idx_research_documents_content_hash
ON research_documents (content_hash)
WHERE content_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS research_document_spans (
    span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL
        REFERENCES research_documents(document_id)
        ON DELETE CASCADE,

    span_index INTEGER NOT NULL,
    section_heading TEXT,
    span_text TEXT NOT NULL,

    start_character INTEGER NOT NULL,
    end_character INTEGER NOT NULL,

    content_hash TEXT NOT NULL,

    UNIQUE (document_id, span_index)
);

CREATE INDEX IF NOT EXISTS idx_research_spans_document
ON research_document_spans (document_id, span_index);
