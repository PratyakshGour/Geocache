from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.schemas.data import (
    CacheSetRequest,
    CacheGetResponse,
    GeoRouteRequest,
    GeoRouteResponse,
    ClusterStatusResponse,
)
from app.services.data_service import geo_cache_service
from app.core.geo_router import geo_router
from app.core.config import settings


router = APIRouter(tags=["GeoCache API"])


@router.post("/cache/set", summary="Store value in nearest cache region with replication")
def set_cache(request: CacheSetRequest):
    """
    Store a key-value item in the closest regional cache node based on client coordinates or city name.
    Automatically replicates to all other regional servers in the cluster.
    """
    try:
        return geo_cache_service.set_data(
            key=request.key,
            value=request.value,
            ttl=request.ttl,
            lat=request.lat,
            lon=request.lon,
            city=request.city,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cache/get/{key}", response_model=CacheGetResponse, summary="Retrieve value from nearest regional server")
def get_cache(
    key: str,
    lat: Optional[float] = Query(None, description="Client latitude coordinate"),
    lon: Optional[float] = Query(None, description="Client longitude coordinate"),
    city: Optional[str] = Query(None, description="Preset city name (e.g. London, Tokyo, Mumbai)"),
):
    """
    Retrieve a cached item from the closest geographical server node.
    If missed in the nearest node, performs WAN fallback read-through from neighboring regions.
    """
    try:
        return geo_cache_service.get_data(key=key, lat=lat, lon=lon, city=city)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cache/{key}", summary="Evict key across entire cluster")
def delete_cache(key: str):
    """
    Delete a cached key across all regional nodes simultaneously.
    """
    result = geo_cache_service.delete_data(key)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Key not found in any regional cache")
    return result


@router.post("/cluster/simulate-route", response_model=GeoRouteResponse, summary="Simulate location routing and latency savings")
def simulate_route(request: GeoRouteRequest):
    """
    Calculate geographic distances and simulated network latencies from a client location
    to all available regional server nodes in the GeoCache cluster.
    """
    return geo_router.get_optimal_region(lat=request.lat, lon=request.lon, city=request.city)


@router.get("/cluster/status", response_model=ClusterStatusResponse, summary="Get live cluster telemetry and node health")
def get_cluster_status():
    """
    Return real-time metrics including hit ratios, evictions, item counts, and status for every regional node.
    """
    return geo_cache_service.get_cluster_status()


@router.post("/cluster/clear", summary="Clear all regional cache nodes")
def clear_cluster():
    """
    Empty all cache data and reset telemetry counters across all regional nodes.
    """
    return geo_cache_service.clear_cluster()


@router.get("/cluster/cities", summary="Get list of preset global cities for testing")
def get_cities():
    """
    Return available preset city coordinates for testing and UI demonstration.
    """
    return {"cities": [c.model_dump() for c in settings.CITY_PRESETS]}