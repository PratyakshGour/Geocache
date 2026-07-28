from fastapi.testclient import TestClient
from app.main import app
from app.services.data_service import geo_cache_service

client = TestClient(app)


def setup_function():
    geo_cache_service.clear_cluster()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "GeoCache"


def test_set_and_get_cache_endpoint():
    # Store item from New York (routes to us-east)
    set_payload = {
        "key": "test_session",
        "value": {"user_id": 42, "role": "admin"},
        "city": "New York, USA",
        "ttl": 3600
    }
    res_set = client.post("/api/v1/cache/set", json=set_payload)
    assert res_set.status_code == 200
    data_set = res_set.json()
    assert data_set["served_by_region"] == "us-east"
    assert "eu-west" in data_set["replicated_to"]

    # Fetch item from London (routes to eu-west, should hit via replication!)
    res_get = client.get("/api/v1/cache/get/test_session?city=London,%20UK")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["hit"] is True
    assert data_get["served_by_region"] == "eu-west"
    assert data_get["value"] == {"user_id": 42, "role": "admin"}


def test_cluster_status_and_clear():
    client.post("/api/v1/cache/set", json={"key": "k1", "value": "v1", "city": "Tokyo, Japan"})
    
    res_status = client.get("/api/v1/cluster/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total_cluster_items"] > 0
    
    res_clear = client.post("/api/v1/cluster/clear")
    assert res_clear.status_code == 200
    
    res_status2 = client.get("/api/v1/cluster/status")
    assert res_status2.json()["total_cluster_items"] == 0
