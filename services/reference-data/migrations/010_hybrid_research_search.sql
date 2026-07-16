ALTER TABLE sec_filing_chunks
ADD COLUMN IF NOT EXISTS search_vector tsvector;

UPDATE sec_filing_chunks
SET search_vector =
    setweight(
        to_tsvector(
            'english',
            COALESCE(section_name, '')
        ),
        'A'
    )
    ||
    setweight(
        to_tsvector(
            'english',
            COALESCE(chunk_text, '')
        ),
        'B'
    )
WHERE search_vector IS NULL;

CREATE INDEX IF NOT EXISTS idx_sec_filing_chunks_search
ON sec_filing_chunks
USING GIN (search_vector);

CREATE OR REPLACE FUNCTION update_sec_chunk_search_vector()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.search_vector :=
        setweight(
            to_tsvector(
                'english',
                COALESCE(NEW.section_name, '')
            ),
            'A'
        )
        ||
        setweight(
            to_tsvector(
                'english',
                COALESCE(NEW.chunk_text, '')
            ),
            'B'
        );

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS sec_chunk_search_vector_trigger
ON sec_filing_chunks;

CREATE TRIGGER sec_chunk_search_vector_trigger
BEFORE INSERT OR UPDATE OF chunk_text, section_name
ON sec_filing_chunks
FOR EACH ROW
EXECUTE FUNCTION update_sec_chunk_search_vector();
