import time
from typing import Dict, Any, Optional, List
from app.repositories.data_repository import ClusterRepository, cluster_repository
from app.core.geo_router import geo_router
from app.schemas.data import CacheGetResponse, ClusterStatusResponse


class GeoCacheService:
    """
    High-level GeoCache orchestration service managing location-based routing,
    multi-region data replication, and WAN fallback read-through caching.
    """
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
        """
        Store a key/value pair in the closest regional cache node, and
        asynchronously replicate it across all other regional nodes.
        """
        route = geo_router.get_optimal_region(lat, lon, city)
        primary_region_id = route.optimal_region_id
        
        primary_node = self.repository.get_node(primary_region_id)
        if not primary_node:
            raise ValueError(f"Region node {primary_region_id} not found")

        # Store in primary region
        item = primary_node.set(key, value, ttl)

        # Multi-region replication
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
        """
        Retrieve data from the nearest available server node.
        If a cache miss occurs in the primary closest node, performs WAN fallback
        lookup in neighboring regions and backfills the local regional cache.
        """
        route = geo_router.get_optimal_region(lat, lon, city)
        optimal_region_id = route.optimal_region_id
        optimal_node = self.repository.get_node(optimal_region_id)
        
        if not optimal_node:
            raise ValueError(f"Region node {optimal_region_id} not found")

        # Attempt read from nearest region
        item = optimal_node.get_item(key)
        hit = item is not None
        served_by_region = optimal_region_id
        region_name = route.optimal_region_name
        distance_km = route.distance_km
        latency_ms = route.simulated_latency_ms

        # WAN Fallback Read-Through: If missed locally, search other regions in order of distance
        if not hit:
            for route_comp in route.all_regions[1:]:
                fallback_node = self.repository.get_node(route_comp.region_id)
                if fallback_node:
                    fallback_item = fallback_node.get_item(key)
                    if fallback_item:
                        # Found in fallback region! Backfill into local optimal cache
                        remaining_ttl = int(fallback_item.expires_at - time.time()) if fallback_item.expires_at else None
                        item = optimal_node.set(key, fallback_item.value, remaining_ttl)
                        hit = True
                        served_by_region = route_comp.region_id
                        region_name = route_comp.region_name
                        distance_km = route_comp.distance_km
                        latency_ms = route_comp.simulated_latency_ms + 15.0  # WAN cross-region penalty ~15ms
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
        """Evict a cache key across all regional nodes (cluster-wide invalidation)."""
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
        """Clear all cache data and telemetry across the entire cluster."""
        self.repository.clear_all()
        return {"status": "cluster_cleared", "message": "All regional caches emptied and metrics reset."}

    def get_cluster_status(self) -> ClusterStatusResponse:
        """Get live health and statistics for the cluster."""
        return self.repository.get_cluster_status()


geo_cache_service = GeoCacheService()