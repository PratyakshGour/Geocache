import time
from typing import Dict, Any, Optional, List
from app.repositories.data_repository import ClusterRepository, cluster_repository
from app.core.geo_router import geo_router
from app.schemas.data import CacheGetResponse, ClusterStatusResponse


class GeoCacheService:
    # Service layer for routing read/write operations and handling replication
    def __init__(self, repository: ClusterRepository = cluster_repository):
        self.repository = repository

    def set_data(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city: Optional[str] = None,
        replicate: bool = True
    ) -> Dict[str, Any]:
        # Find closest server and write data there
        route = geo_router.get_optimal_region(lat, lon, city)
        primary_region_id = route.optimal_region_id
        
        primary_node = self.repository.get_node(primary_region_id)
        if not primary_node:
            raise ValueError(f"Region node {primary_region_id} not found")

        item = primary_node.set(key, value, ttl)

        # Replicate to other nodes in background/sync
        replicated_regions = []
        if replicate:
            for region_id, node in self.repository.get_all_nodes().items():
                if region_id != primary_region_id:
                    node.set(key, value, ttl)
                    replicated_regions.append(region_id)

        return {
            "key": key,
            "value": value,
            "status": "stored",
            "served_by_region": primary_region_id,
            "region_name": route.optimal_region_name,
            "distance_km": route.distance_km,
            "simulated_latency_ms": route.simulated_latency_ms,
            "replicated_to": replicated_regions,
            "expires_at": item.expires_at
        }

    def get_data(
        self,
        key: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        city: Optional[str] = None
    ) -> CacheGetResponse:
        # Route get request to nearest server
        route = geo_router.get_optimal_region(lat, lon, city)
        optimal_region_id = route.optimal_region_id
        optimal_node = self.repository.get_node(optimal_region_id)
        
        if not optimal_node:
            raise ValueError(f"Region node {optimal_region_id} not found")

        item = optimal_node.get_item(key)
        hit = item is not None
        served_by_region = optimal_region_id
        region_name = route.optimal_region_name
        distance_km = route.distance_km
        latency_ms = route.simulated_latency_ms

        # If missed locally, check other regions and copy it over (WAN fallback)
        if not hit:
            for route_comp in route.all_regions[1:]:
                fallback_node = self.repository.get_node(route_comp.region_id)
                if fallback_node:
                    fallback_item = fallback_node.get_item(key)
                    if fallback_item:
                        remaining_ttl = int(fallback_item.expires_at - time.time()) if fallback_item.expires_at else None
                        item = optimal_node.set(key, fallback_item.value, remaining_ttl)
                        hit = True
                        served_by_region = route_comp.region_id
                        region_name = route_comp.region_name
                        distance_km = route_comp.distance_km
                        latency_ms = route_comp.simulated_latency_ms + 15.0
                        break

        ttl_remaining = None
        if item and item.expires_at:
            ttl_remaining = max(0, int(item.expires_at - time.time()))

        return CacheGetResponse(
            key=key,
            value=item.value if item else None,
            hit=hit,
            served_by_region=served_by_region,
            region_name=region_name,
            distance_km=distance_km,
            simulated_latency_ms=round(latency_ms, 2),
            ttl_remaining=ttl_remaining,
            replicated_regions=[rid for rid in self.repository.get_all_nodes().keys() if rid != served_by_region] if hit else []
        )

    def delete_data(self, key: str) -> Dict[str, Any]:
        # Remove key from all cluster nodes
        invalidated_regions = []
        for region_id, node in self.repository.get_all_nodes().items():
            if node.delete(key):
                invalidated_regions.append(region_id)

        return {
            "key": key,
            "status": "deleted" if invalidated_regions else "not_found",
            "invalidated_regions": invalidated_regions,
            "nodes_count": len(invalidated_regions)
        }

    def clear_cluster(self):
        self.repository.clear_all()
        return {"status": "cluster_cleared", "message": "All regional caches emptied."}

    def get_cluster_status(self) -> ClusterStatusResponse:
        return self.repository.get_cluster_status()


geo_cache_service = GeoCacheService()