"""Grounded computation tools for the Q&A chat.

Each function here is decorated with @beta_tool and handed to Claude's Tool
Runner in app/llm.py. When Claude calls one of these, the answer is computed
by pandas over the real CSV -- the model can phrase the result, but it
cannot invent the numbers.
"""

from __future__ import annotations

import json

from anthropic import beta_tool

from app.data import get_creator, rank_all_creators


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
    if not results:
        return "No creators matched those filters."
    return json.dumps([_format_creator(c) for c in results])


@beta_tool
def get_creator_stats(handle: str) -> str:
    """Get a single creator's aggregated stats (total views, engagement rate, video count).

    Args:
        handle: The creator's exact author_name/handle from the dataset.
    """
    creator = get_creator(handle)
    if creator is None:
        return f'No creator found with handle "{handle}". It may be misspelled or not in this dataset.'
    return json.dumps(_format_creator(creator))


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
    return json.dumps(results)
