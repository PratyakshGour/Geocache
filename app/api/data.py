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


@router.post("/cache/set", summary="Store item in nearest cache server")
def set_cache(request: CacheSetRequest):
    # Store key-value in closest node and replicate across other regions
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


@router.get("/cache/get/{key}", response_model=CacheGetResponse, summary="Get item from nearest server")
def get_cache(
    key: str,
    lat: Optional[float] = Query(None, description="Client latitude"),
    lon: Optional[float] = Query(None, description="Client longitude"),
    city: Optional[str] = Query(None, description="City name (e.g. London, Tokyo)"),
):
    # Retrieve item from closest node; fallback to other regions if missed locally
    try:
        return geo_cache_service.get_data(key=key, lat=lat, lon=lon, city=city)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cache/{key}", summary="Delete key across cluster")
def delete_cache(key: str):
    result = geo_cache_service.delete_data(key)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Key not found in cache")
    return result


@router.post("/cluster/simulate-route", response_model=GeoRouteResponse, summary="Check nearest server distance")
def simulate_route(request: GeoRouteRequest):
    return geo_router.get_optimal_region(lat=request.lat, lon=request.lon, city=request.city)


@router.get("/cluster/status", response_model=ClusterStatusResponse, summary="Get cluster health and stats")
def get_cluster_status():
    return geo_cache_service.get_cluster_status()


@router.post("/cluster/clear", summary="Clear all cache nodes")
def clear_cluster():
    return geo_cache_service.clear_cluster()


@router.get("/cluster/cities", summary="Get test city coordinates")
def get_cities():
    return {"cities": [c.model_dump() for c in settings.CITY_PRESETS]}