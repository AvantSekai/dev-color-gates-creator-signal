"""Hybrid-grounded Q&A orchestration.

Every answer is one of three kinds, and the caller always gets the raw
`sources` (tool name, input, output) that backed it -- not just a badge:

- "computed"        -- one or more tools ran and the answer just reports
                        what they returned. No interpretation layered on.
- "grounded_opinion" -- one or more tools ran, but the answer also adds
                        judgment beyond the raw numbers (e.g. "would this
                        creator fit a skincare brand?" answered using their
                        real stats plus the model's read on content fit).
- "opinion"          -- no tool ran at all; pure model reasoning.

Which of "computed" vs "grounded_opinion" applies isn't detectable from a
simple heuristic (an answer that starts with real stats and ends with a
recommendation is common and reasonable) -- so after tool use we ask the
model to self-classify its own answer in a second, cheap, tool-free call.
"""

from __future__ import annotations

import os

from anthropic import Anthropic

from app.tools import (
    compare_creators,
    get_call_log,
    get_creator_stats,
    rank_creators,
    start_call_log,
)


class LLMConfigError(RuntimeError):
    """Raised when the LLM client can't be configured (e.g. missing API key)."""


MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "You are a research assistant helping a talent agency evaluate TikTok creators "
    "from a fixed historical dataset (Sep-Dec 2020, not live data). "
    "For questions about rankings, totals, or specific creators' stats, use the provided "
    "tools -- never estimate or invent numbers. "
    "For subjective questions (e.g. brand fit, content style), you may look up a creator's "
    "real stats first if it would ground your answer, then give your own judgment on top -- "
    "just be clear in your answer which parts are data and which are your read."
)

CLASSIFY_PROMPT = (
    "Question: {question}\n\nAnswer: {answer}\n\n"
    "Does this answer state ONLY facts/numbers that were computed from data, with no added "
    "judgment or interpretation, or does it also include the model's own opinion, "
    "recommendation, or interpretation beyond the raw data? "
    "Reply with exactly one word: FACT or OPINION."
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


def _classify_computed_vs_grounded_opinion(client: Anthropic, question: str, answer: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=8,
        messages=[
            {"role": "user", "content": CLASSIFY_PROMPT.format(question=question, answer=answer)}
        ],
    )
    verdict = "".join(block.text for block in response.content if block.type == "text").strip().upper()
    return "grounded_opinion" if "OPINION" in verdict else "computed"


def ask(question: str, client: Anthropic | None = None) -> dict:
    """Answer a question, returning {"answer", "kind", "sources"}.

    kind is "computed" | "grounded_opinion" | "opinion". sources is a list of
    {"tool", "input", "output"} for every tool call made while answering --
    empty when kind is "opinion".
    """
    client = client or get_client()
    start_call_log()

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

    sources = get_call_log()

    if not used_tool:
        kind = "opinion"
    else:
        kind = _classify_computed_vs_grounded_opinion(client, question, answer_text)

    return {"answer": answer_text, "kind": kind, "sources": sources}
