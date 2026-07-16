from __future__ import annotations

from app.repository import ResearchRepository
from app.semantic_index import SemanticIndex


def main() -> None:
    repository = ResearchRepository()
    semantic_index = SemanticIndex()

    count = semantic_index.build(repository)

    print(
        f"Indexed {count:,} SEC filing chunks."
    )


if __name__ == "__main__":
    main()
