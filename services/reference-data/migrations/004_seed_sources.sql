INSERT INTO reference_sources (
    source_name,
    source_priority,
    trust_score
)
VALUES
    ('issuer-filing', 10, 0.99),
    ('rating-agency-a', 20, 0.97),
    ('rating-agency-b', 25, 0.95),
    ('exchange-reference', 30, 0.93),
    ('vendor-a', 40, 0.90),
    ('vendor-b', 50, 0.85),
    ('synthetic-generator', 100, 0.70)
ON CONFLICT (source_name) DO UPDATE
SET
    source_priority = EXCLUDED.source_priority,
    trust_score = EXCLUDED.trust_score;
