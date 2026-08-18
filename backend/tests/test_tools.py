import json

from app.tools import compare_creators, get_creator_stats, rank_creators


def test_rank_creators_matches_promising_pool_top5():
    from app.data import compute_promising_pool

    result = json.loads(rank_creators.func(sort_by="engagement_rate", min_views=250_000, max_views=10_000_000, limit=5))
    expected = compute_promising_pool()[:5]
    assert [c["handle"] for c in result] == [c["handle"] for c in expected]


def test_get_creator_stats_known_handle():
    result = json.loads(get_creator_stats.func(handle="reus.fx"))
    assert result["total_views"] == 465_900
    assert result["engagement_rate_pct"] == 40.07


def test_get_creator_stats_unknown_handle_returns_not_found_message():
    result = get_creator_stats.func(handle="definitely_not_a_real_handle")
    assert "No creator found" in result


def test_compare_creators_returns_both():
    result = json.loads(compare_creators.func(handles=["reus.fx", "immaculatebae"]))
    handles = {c["handle"] for c in result}
    assert handles == {"reus.fx", "immaculatebae"}


def test_compare_creators_handles_unknown_handle_gracefully():
    result = json.loads(compare_creators.func(handles=["reus.fx", "not_a_real_handle"]))
    unknown = next(c for c in result if c["handle"] == "not_a_real_handle")
    assert unknown["error"] == "not found"


def test_rank_creators_empty_result_returns_clear_message():
    result = rank_creators.func(min_views=999_999_999, max_views=999_999_999_999, limit=5)
    assert "No creators matched" in result
