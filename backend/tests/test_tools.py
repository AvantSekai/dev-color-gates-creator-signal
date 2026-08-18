import json

from app.tools import (
    compare_creators,
    get_call_log,
    get_creator_stats,
    rank_creators,
    start_call_log,
)


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


def test_call_log_records_tool_invocations_for_provenance():
    start_call_log()
    get_creator_stats.func(handle="reus.fx")
    rank_creators.func(sort_by="engagement_rate", limit=3)

    log = get_call_log()
    assert [entry["tool"] for entry in log] == ["get_creator_stats", "rank_creators"]
    assert log[0]["input"] == {"handle": "reus.fx"}
    assert log[0]["output"]["handle"] == "reus.fx"


def test_call_log_is_empty_before_start_call_log_is_invoked():
    # No start_call_log() call in this test -- the module-level contextvar default
    # is None, so recording should be a no-op rather than erroring.
    from app.tools import _call_log

    _call_log.set(None)
    get_creator_stats.func(handle="reus.fx")
    assert get_call_log() == []
