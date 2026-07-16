from __future__ import annotations

import argparse

from mercator_ingestion.extractors.credit_signals import (
    extract_credit_signals,
)
from mercator_ingestion.extractors.filing_chunks import (
    create_filing_chunks,
)
from mercator_ingestion.storage.credit_postgres import (
    CreditSignalStore,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cik",
        required=True,
    )

    parser.add_argument(
        "--section-limit",
        type=int,
        default=20,
    )

    arguments = parser.parse_args()

    store = CreditSignalStore()

    sections = store.extracted_sections(
        cik=arguments.cik,
        limit=arguments.section_limit,
    )

    total_chunks = 0
    total_signals = 0

    for section in sections:
        chunks = create_filing_chunks(
            section["normalized_text"],
            section_name=section["section_name"],
            maximum_characters=1_800,
            overlap_sentences=2,
        )

        signals_by_chunk = [
            extract_credit_signals(chunk.text)
            for chunk in chunks
        ]

        chunk_count, signal_count = (
            store.replace_chunks_and_signals(
                filing_id=section["filing_id"],
                section_id=section["section_id"],
                chunks=chunks,
                signals_by_chunk=signals_by_chunk,
            )
        )

        total_chunks += chunk_count
        total_signals += signal_count

        print(
            f"{section['form_type']} "
            f"{section['filing_date']} "
            f"{section['section_name']}: "
            f"{chunk_count} chunks, "
            f"{signal_count} signals"
        )

    print(f"Total chunks:  {total_chunks}")
    print(f"Total signals: {total_signals}")


if __name__ == "__main__":
    main()
