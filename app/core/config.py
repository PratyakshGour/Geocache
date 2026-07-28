from typing import Dict, Any, List
from pydantic import BaseModel


class RegionConfig(BaseModel):
    id: str
    name: str
    location: str
    lat: float
    lon: float
    status: str = "active"


class CityPreset(BaseModel):
    name: str
    lat: float
    lon: float


class Settings:
    PROJECT_NAME: str = "GeoCache"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Geo-distributed in-memory caching system with location-based routing and replication."

    # Cache configurations
    DEFAULT_TTL: int = 3600  # 1 hour in seconds
    MAX_CACHE_SIZE: int = 1000  # Max items per region
    DEFAULT_EVICTION_POLICY: str = "LRU"  # LRU or LFU

    # Simulated regional servers (Distributed Nodes)
    REGIONS: Dict[str, RegionConfig] = {
        "us-east": RegionConfig(
            id="us-east",
            name="US East",
            location="N. Virginia, USA",
            lat=38.0336,
            lon=-78.5080,
        ),
        "eu-west": RegionConfig(
            id="eu-west",
            name="EU West",
            location="Frankfurt, Germany",
            lat=50.1109,
            lon=8.6821,
        ),
        "ap-south": RegionConfig(
            id="ap-south",
            name="Asia Pacific South",
            location="Mumbai, India",
            lat=19.0760,
            lon=72.8777,
        ),
        "ap-southeast": RegionConfig(
            id="ap-southeast",
            name="Asia Pacific Southeast",
            location="Singapore",
            lat=1.3521,
            lon=103.8198,
        ),
        "sa-east": RegionConfig(
            id="sa-east",
            name="South America East",
            location="São Paulo, Brazil",
            lat=-23.5505,
            lon=-46.6333,
        ),
    }

    # Preset client cities for testing and UI demonstrations
    CITY_PRESETS: List[CityPreset] = [
        CityPreset(name="New York, USA", lat=40.7128, lon=-74.0060),
        CityPreset(name="London, UK", lat=51.5074, lon=-0.1278),
        CityPreset(name="Tokyo, Japan", lat=35.6762, lon=139.6503),
        CityPreset(name="Sydney, Australia", lat=-33.8688, lon=151.2093),
        CityPreset(name="Delhi, India", lat=28.6139, lon=77.2090),
        CityPreset(name="Paris, France", lat=48.8566, lon=2.3522),
        CityPreset(name="San Francisco, USA", lat=37.7749, lon=-122.4194),
        CityPreset(name="Cairo, Egypt", lat=30.0444, lon=31.2357),
    ]


settings = Settings()
