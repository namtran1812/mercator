from __future__ import annotations

from mercator_agent.llm import LLMClient


def main() -> None:
    client = LLMClient()

    response = client.generate(
        system_prompt=(
            "You are Mercator, a concise "
            "fixed-income research assistant."
        ),
        user_prompt=(
            "Explain G-spread in one sentence."
        ),
        think=False,
    )

    print(response)


if __name__ == "__main__":
    main()
