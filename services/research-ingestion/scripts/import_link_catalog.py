from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from mercator_ingestion.models.document import DocumentReference
from mercator_ingestion.storage.postgres import ResearchDocumentStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog")
    arguments = parser.parse_args()

    records = json.loads(Path(arguments.catalog).read_text())
    store = ResearchDocumentStore()

    for record in records:
        url = record["url"]

        reference = DocumentReference(
            source_name="citadel-securities-link-catalog",
            source_document_id=hashlib.sha256(
                url.encode("utf-8")
            ).hexdigest(),
            canonical_url=url,
            title=record["title"],
            category=record.get("category"),
            published_at=(
                datetime.fromisoformat(
                    record["published_at"].replace(
                        "Z",
                        "+00:00",
                    )
                )
                if record.get("published_at")
                else None
            ),
            metadata={
                "storage_policy": "link_and_metadata_only",
                "full_text_fetched": False,
                "automated_access_status": "HTTP_403",
            },
        )

        store.upsert_discovered(reference)
        print(f"Catalogued: {reference.title}")


if __name__ == "__main__":
    main()
