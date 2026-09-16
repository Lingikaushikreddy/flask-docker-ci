"""Tests run in CI on every push. If these fail, nothing gets deployed."""

import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_index_returns_service_name(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.get_json()["service"] == "flask-docker-ci"


def test_health_is_healthy(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"


def test_greet_uses_the_name(client):
    res = client.get("/api/greet/Kaushik")
    assert res.status_code == 200
    assert res.get_json()["greeting"] == "Hello, Kaushik!"


def test_sum_adds_numbers(client):
    res = client.post("/api/sum", json={"numbers": [1, 2, 3, 4]})
    assert res.status_code == 200
    body = res.get_json()
    assert body["sum"] == 10
    assert body["count"] == 4


def test_sum_rejects_empty_list(client):
    res = client.post("/api/sum", json={"numbers": []})
    assert res.status_code == 400


def test_sum_rejects_non_numbers(client):
    res = client.post("/api/sum", json={"numbers": [1, "two", 3]})
    assert res.status_code == 400


def test_unknown_route_is_404_json(client):
    res = client.get("/nope")
    assert res.status_code == 404
    assert res.get_json()["error"] == "not found"
