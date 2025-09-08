# tests/test_app.py
import pytest

from recovery_agent.ui.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_healthz_endpoint(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"OK"


def test_status_endpoint(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "status" in data
    assert data["status"] == "idle"
    assert "details" in data


def test_non_existent_route_returns_404(client):
    """Negative test to ensure an unknown route returns a 404 error."""
    resp = client.get("/this-route-does-not-exist")
    assert resp.status_code == 404
