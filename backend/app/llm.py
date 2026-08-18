"""Hybrid-grounded Q&A orchestration.

Stat/ranking questions get answered via the Tool Runner (app/tools.py) --
Claude calls a real pandas-backed function and the numbers can't be
invented. Interpretive/judgment questions get no tool call, so the answer
is Claude's own reasoning -- callers must label those as opinion, not fact.
We detect which happened by checking whether any tool_use block appeared
in the turn.
"""

from __future__ import annotations

import os

from anthropic import Anthropic

from app.tools import compare_creators, get_creator_stats, rank_creators


class LLMConfigError(RuntimeError):
    """Raised when the LLM client can't be configured (e.g. missing API key)."""

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are a research assistant helping a talent agency evaluate TikTok creators "
    "from a fixed historical dataset (Sep-Dec 2020, not live data). "
    "For questions about rankings, totals, or specific creators' stats, use the provided "
    "tools -- never estimate or invent numbers. "
    "For subjective questions (e.g. brand fit, content style), answer directly using your "
    "own judgment; do not call a tool for these."
)

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            raise LLMConfigError(
                "ANTHROPIC_API_KEY is not set. Copy backend/.env.example to backend/.env "
                "and add your key, or export ANTHROPIC_API_KEY before starting the server."
            )
        _client = Anthropic()
    return _client


def ask(question: str, client: Anthropic | None = None) -> dict:
    """Answer a question, returning {"answer": str, "kind": "computed" | "opinion"}."""
    client = client or get_client()

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[rank_creators, get_creator_stats, compare_creators],
        messages=[{"role": "user", "content": question}],
    )

    used_tool = False
    final_message = None
    for message in runner:
        final_message = message
        if any(block.type == "tool_use" for block in message.content):
            used_tool = True

    answer_text = ""
    if final_message is not None:
        answer_text = "".join(
            block.text for block in final_message.content if block.type == "text"
        )

    return {"answer": answer_text, "kind": "computed" if used_tool else "opinion"}
