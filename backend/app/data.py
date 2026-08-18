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
def compute_promising_pool() -> list[dict]:
    df = load_dataset()

    grouped = df.groupby("author_name").agg(
        total_views=("views", "sum"),
        avg_engagement_rate=("engagement_rate", "mean"),
        video_count=("video_id", "count"),
        verified=("author_verified", "any"),
        sample_caption=("caption", "first"),
    )

    pool = grouped[
        (grouped["total_views"] >= FLOOR_VIEWS) & (grouped["total_views"] <= CEILING_VIEWS)
    ].sort_values("avg_engagement_rate", ascending=False)

    return [
        {
            "handle": handle,
            "total_views": int(row["total_views"]),
            "engagement_rate": round(float(row["avg_engagement_rate"]), 4),
            "video_count": int(row["video_count"]),
            "verified": bool(row["verified"]),
            "sample_caption": None if pd.isna(row["sample_caption"]) else row["sample_caption"],
        }
        for handle, row in pool.iterrows()
    ]


def get_creator(handle: str) -> dict | None:
    """Look up a single creator's aggregated stats, from the full dataset (not just the promising pool)."""
    df = load_dataset()
    rows = df[df["author_name"] == handle]
    if rows.empty:
        return None
    return {
        "handle": handle,
        "total_views": int(rows["views"].sum()),
        "engagement_rate": round(float(rows["engagement_rate"].mean()), 4),
        "video_count": int(len(rows)),
        "verified": bool(rows["author_verified"].any()),
    }


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
