from app import data


def test_load_dataset_row_count():
    assert len(data.load_dataset()) == 1000


def test_promising_pool_size():
    assert len(data.compute_promising_pool()) == 205


def test_promising_pool_excludes_mega_reach_creators():
    handles = {c["handle"] for c in data.compute_promising_pool()}
    assert "billieeilish" not in handles


def test_promising_pool_sorted_by_engagement_rate_desc():
    pool = data.compute_promising_pool()
    rates = [c["engagement_rate"] for c in pool]
    assert rates == sorted(rates, reverse=True)


def test_promising_pool_top_creator_is_known_high_rate_account():
    pool = data.compute_promising_pool()
    assert pool[0]["handle"] == "reus.fx"


def test_get_creator_known_handle():
    creator = data.get_creator("reus.fx")
    assert creator is not None
    assert creator["total_views"] == 465_900


def test_get_creator_unknown_handle_returns_none():
    assert data.get_creator("definitely_not_a_real_handle") is None


def test_dataset_meta():
    meta = data.get_dataset_meta()
    assert meta["total_creators"] == 802
    assert meta["promising_count"] == 205
    assert meta["date_range"] == ["2020-09-22", "2020-12-21"]
