"""Loads the TikTok CSV once and computes the promising-creator pool.

Promising = per-creator total views in [FLOOR, CEILING], ranked by average
per-video engagement rate. See docs/brainstorms/2026-08-17-creator-signal-
prototype-requirements.md for why this floor/ceiling/rate combination was
chosen over reach-alone or rate-alone ranking.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "2026datathon_interview_data.csv"

FLOOR_VIEWS = 250_000
CEILING_VIEWS = 10_000_000


@lru_cache(maxsize=1)
def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["engagement_count"] = df["likes"] + df["comments"] + df["shares"]
    df["engagement_rate"] = df["engagement_count"] / df["views"].replace(0, pd.NA)
    return df


@lru_cache(maxsize=1)
def _aggregate_all_creators() -> pd.DataFrame:
    """Per-creator aggregates across the full dataset, no floor/ceiling filter applied."""
    df = load_dataset()
    return df.groupby("author_name").agg(
        total_views=("views", "sum"),
        avg_engagement_rate=("engagement_rate", "mean"),
        video_count=("video_id", "count"),
        verified=("author_verified", "any"),
        sample_caption=("caption", "first"),
    )


def _row_to_dict(handle: str, row: pd.Series) -> dict:
    return {
        "handle": handle,
        "total_views": int(row["total_views"]),
        "engagement_rate": round(float(row["avg_engagement_rate"]), 4),
        "video_count": int(row["video_count"]),
        "verified": bool(row["verified"]),
        "sample_caption": None if pd.isna(row["sample_caption"]) else row["sample_caption"],
    }


@lru_cache(maxsize=1)
def compute_promising_pool() -> list[dict]:
    grouped = _aggregate_all_creators()

    pool = grouped[
        (grouped["total_views"] >= FLOOR_VIEWS) & (grouped["total_views"] <= CEILING_VIEWS)
    ].sort_values("avg_engagement_rate", ascending=False)

    return [_row_to_dict(handle, row) for handle, row in pool.iterrows()]


def rank_all_creators(
    sort_by: str = "engagement_rate",
    min_views: int | None = None,
    max_views: int | None = None,
    limit: int = 10,
) -> list[dict]:
    """Rank creators across the *full* dataset (not just the promising pool) by views or engagement rate."""
    grouped = _aggregate_all_creators()

    if min_views is not None:
        grouped = grouped[grouped["total_views"] >= min_views]
    if max_views is not None:
        grouped = grouped[grouped["total_views"] <= max_views]

    sort_col = "total_views" if sort_by == "total_views" else "avg_engagement_rate"
    grouped = grouped.sort_values(sort_col, ascending=False).head(limit)

    return [_row_to_dict(handle, row) for handle, row in grouped.iterrows()]


def get_creator(handle: str) -> dict | None:
    """Look up a single creator's aggregated stats, from the full dataset (not just the promising pool)."""
    grouped = _aggregate_all_creators()
    if handle not in grouped.index:
        return None
    return _row_to_dict(handle, grouped.loc[handle])


@lru_cache(maxsize=1)
def get_dataset_meta() -> dict:
    df = load_dataset()
    pool = compute_promising_pool()
    dates = pd.to_datetime(df["upload_date"])
    return {
        "total_creators": int(df["author_name"].nunique()),
        "promising_count": len(pool),
        "date_range": [dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d")],
    }
