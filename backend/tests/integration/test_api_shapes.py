from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_markets_endpoint_shape():
    response = client.get("/markets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "open" in first
    assert "assets" in first


def test_sessions_and_compare_endpoint_shapes():
    # Create session
    res = client.post("/sessions", json={"target": "GOLD", "asset": "XAUUSD", "scenario": "bull"})
    assert res.status_code == 200
    s = res.json()
    assert "id" in s
    assert "final_action" in s
    assert "messages" in s
    assert "equity" in s

    # Compare
    cmp_res = client.get("/compare")
    assert cmp_res.status_code == 200
    setups = cmp_res.json()
    assert len(setups) == 3
    assert setups[0]["name"] == "Single Agent"
