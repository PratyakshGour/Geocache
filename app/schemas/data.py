from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import time


class CacheItem(BaseModel):
    key: str
    value: Any
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None
    region_id: str
    access_count: int = 1
    last_accessed: float = Field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CacheSetRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None


class CacheGetResponse(BaseModel):
    key: str
    value: Optional[Any] = None
    hit: bool
    served_by_region: str
    region_name: str
    distance_km: float
    simulated_latency_ms: float
    ttl_remaining: Optional[int] = None
    replicated_regions: List[str] = []


class GeoRouteRequest(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None


class RouteComparison(BaseModel):
    region_id: str
    region_name: str
    distance_km: float
    simulated_latency_ms: float
    is_closest: bool


class GeoRouteResponse(BaseModel):
    client_location: str
    optimal_region_id: str
    optimal_region_name: str
    distance_km: float
    simulated_latency_ms: float
    all_regions: List[RouteComparison]


class RegionStats(BaseModel):
    region_id: str
    name: str
    location: str
    lat: float
    lon: float
    status: str
    total_items: int
    max_capacity: int
    hits: int
    misses: int
    hit_ratio: float
    evictions: int


class ClusterStatusResponse(BaseModel):
    project: str
    version: str
    status: str
    total_cluster_items: int
    total_cluster_hits: int
    total_cluster_misses: int
    cluster_hit_ratio: float
    regions: List[RegionStats]