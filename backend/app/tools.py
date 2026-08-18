"""Grounded computation tools for the Q&A chat.

Each function here is decorated with @beta_tool and handed to Claude's Tool
Runner in app/llm.py. When Claude calls one of these, the answer is computed
by pandas over the real CSV -- the model can phrase the result, but it
cannot invent the numbers.
"""

from __future__ import annotations

import json
from contextvars import ContextVar

from anthropic import beta_tool

from app.data import compute_promising_pool, get_creator, rank_all_creators

# Records every tool call made during the current request, so the API response
# can show the user exactly what data backed an answer -- not just a badge.
_call_log: ContextVar[list[dict] | None] = ContextVar("_call_log", default=None)


def start_call_log() -> None:
    _call_log.set([])


def get_call_log() -> list[dict]:
    return _call_log.get() or []


def _record(tool_name: str, tool_input: dict, output: object) -> None:
    log = _call_log.get()
    if log is not None:
        log.append({"tool": tool_name, "input": tool_input, "output": output})


def _format_creator(c: dict) -> dict:
    return {
        "handle": c["handle"],
        "total_views": c["total_views"],
        "engagement_rate_pct": round(c["engagement_rate"] * 100, 2),
        "video_count": c["video_count"],
        "verified": c["verified"],
    }


@beta_tool
def rank_creators(
    sort_by: str = "engagement_rate",
    min_views: int = 0,
    max_views: int = 0,
    limit: int = 10,
) -> str:
    """Rank creators from the dataset by total views or engagement rate.

    Args:
        sort_by: Either "engagement_rate" or "total_views".
        min_views: Minimum total views to include (0 = no minimum).
        max_views: Maximum total views to include (0 = no maximum).
        limit: Maximum number of creators to return.
    """
    results = rank_all_creators(
        sort_by=sort_by,
        min_views=min_views or None,
        max_views=max_views or None,
        limit=limit,
    )
    formatted = [_format_creator(c) for c in results]
    _record(
        "rank_creators",
        {"sort_by": sort_by, "min_views": min_views, "max_views": max_views, "limit": limit},
        formatted,
    )
    if not results:
        return "No creators matched those filters."
    return json.dumps(formatted)


@beta_tool
def get_promising_creators(limit: int = 10) -> str:
    """Get the agency's "promising" creators: total views between 250K and 10M,
    ranked by average engagement rate. This is the same pool and ranking shown
    on the summary dashboard -- use this tool (not rank_creators) whenever the
    question is about which creators are "promising" or worth pursuing.

    Args:
        limit: Maximum number of creators to return.
    """
    results = compute_promising_pool()[:limit]
    formatted = [_format_creator(c) for c in results]
    _record("get_promising_creators", {"limit": limit}, formatted)
    return json.dumps(formatted)


@beta_tool
def get_creator_stats(handle: str) -> str:
    """Get a single creator's aggregated stats (total views, engagement rate, video count).

    Args:
        handle: The creator's exact author_name/handle from the dataset.
    """
    creator = get_creator(handle)
    if creator is None:
        _record("get_creator_stats", {"handle": handle}, {"error": "not found"})
        return f'No creator found with handle "{handle}". It may be misspelled or not in this dataset.'
    formatted = _format_creator(creator)
    _record("get_creator_stats", {"handle": handle}, formatted)
    return json.dumps(formatted)


@beta_tool
def compare_creators(handles: list[str]) -> str:
    """Get side-by-side aggregated stats for two or more creators.

    Args:
        handles: List of creator handles to compare.
    """
    results = []
    for handle in handles:
        creator = get_creator(handle)
        results.append(_format_creator(creator) if creator else {"handle": handle, "error": "not found"})
    _record("compare_creators", {"handles": handles}, results)
    return json.dumps(results)
