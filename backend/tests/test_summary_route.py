from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_summary_returns_200_with_expected_shape():
    response = client.get("/api/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["promising_count"] == 205
    assert len(body["creators"]) == 205


def test_summary_creators_sorted_by_engagement_rate_desc():
    response = client.get("/api/summary")
    rates = [c["engagement_rate"] for c in response.json()["creators"]]
    assert rates == sorted(rates, reverse=True)


def test_summary_includes_date_range():
    response = client.get("/api/summary")
    assert response.json()["meta"]["date_range"] == ["2020-09-22", "2020-12-21"]
