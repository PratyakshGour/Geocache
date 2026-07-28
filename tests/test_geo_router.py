from app.core.geo_router import geo_router
from app.core.config import settings


def test_haversine_distance():
    # Test distance between New York (40.7128, -74.0060) and London (51.5074, -0.1278)
    # Expected approximate great-circle distance is ~5570 km
    dist = geo_router.haversine_distance(40.7128, -74.0060, 51.5074, -0.1278)
    assert 5500 < dist < 5650


def test_resolve_location():
    lat, lon, label = geo_router.resolve_location(city="Tokyo, Japan")
    assert label == "Tokyo, Japan"
    assert lat == 35.6762
    assert lon == 139.6503


def test_optimal_region_selection():
    # Request from London should choose eu-west (Frankfurt)
    route = geo_router.get_optimal_region(city="London, UK")
    assert route.optimal_region_id == "eu-west"
    assert route.optimal_region_name == "EU West"
    
    # Request from Mumbai should choose ap-south
    route_mumbai = geo_router.get_optimal_region(city="Delhi, India")
    assert route_mumbai.optimal_region_id == "ap-south"
