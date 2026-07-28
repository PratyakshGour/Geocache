from typing import Dict, Optional, List
from app.core.cache_engine import CacheEngine
from app.core.config import settings
from app.schemas.data import ClusterStatusResponse, RegionStats


class ClusterRepository:
    # Manages all regional in-memory cache nodes for the cluster
    def __init__(self):
        self.nodes: Dict[str, CacheEngine] = {}
        for region_id in settings.REGIONS.keys():
            self.nodes[region_id] = CacheEngine(region_id=region_id)

    def get_node(self, region_id: str) -> Optional[CacheEngine]:
        return self.nodes.get(region_id)

    def get_all_nodes(self) -> Dict[str, CacheEngine]:
        return self.nodes

    def clear_all(self):
        # Clear all cache nodes and reset metrics
        for node in self.nodes.values():
            node.clear()

    def get_cluster_status(self) -> ClusterStatusResponse:
        # Collect stats across all regions in the cluster
        region_stats_list: List[RegionStats] = []
        total_items = 0
        total_hits = 0
        total_misses = 0

        for region_id, node in self.nodes.items():
            stats = node.get_stats()
            region_stats_list.append(stats)
            total_items += stats.total_items
            total_hits += stats.hits
            total_misses += stats.misses

        total_requests = total_hits + total_misses
        cluster_hit_ratio = round((total_hits / total_requests) * 100, 2) if total_requests > 0 else 0.0

        return ClusterStatusResponse(
            project=settings.PROJECT_NAME,
            version=settings.VERSION,
            status="running",
            total_cluster_items=total_items,
            total_cluster_hits=total_hits,
            total_cluster_misses=total_misses,
            cluster_hit_ratio=cluster_hit_ratio,
            regions=region_stats_list
        )


cluster_repository = ClusterRepository()