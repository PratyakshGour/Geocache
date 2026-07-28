import time
import threading
from typing import Dict, Any, Optional, List
from app.schemas.data import CacheItem, RegionStats
from app.core.config import settings


class CacheEngine:
    # Thread-safe in-memory cache store with TTL and LRU/LFU eviction support.
    def __init__(
        self,
        region_id: str,
        max_size: int = settings.MAX_CACHE_SIZE,
        default_ttl: int = settings.DEFAULT_TTL,
        eviction_policy: str = settings.DEFAULT_EVICTION_POLICY,
    ):
        self.region_id = region_id
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy.upper()
        self.store: Dict[str, CacheItem] = {}
        self.lock = threading.Lock()

        # Cache stats
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get_item(self, key: str) -> Optional[CacheItem]:
        with self.lock:
            if key not in self.store:
                self.misses += 1
                return None

            item = self.store[key]
            if item.is_expired:
                del self.store[key]
                self.misses += 1
                return None

            item.access_count += 1
            item.last_accessed = time.time()
            self.hits += 1
            return item

    def get(self, key: str) -> Optional[Any]:
        item = self.get_item(key)
        return item.value if item else None

    def _evict_item(self) -> str:
        """Internal helper to evict an item when cache is full."""
        if not self.store:
            return ""

        if self.eviction_policy == "LFU":
            # Least Frequently Used: minimum access_count, tie-break by last_accessed
            eviction_key = min(
                self.store.keys(),
                key=lambda k: (self.store[k].access_count, self.store[k].last_accessed)
            )
        else:
            # LRU (Default): Least Recently Used: minimum last_accessed
            eviction_key = min(
                self.store.keys(),
                key=lambda k: self.store[k].last_accessed
            )

        del self.store[eviction_key]
        self.evictions += 1
        return eviction_key

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> CacheItem:
        with self.lock:
            effective_ttl = ttl if ttl is not None else self.default_ttl
            expires_at = time.time() + effective_ttl if effective_ttl > 0 else None

            if key not in self.store and len(self.store) >= self.max_size:
                self._evict_item()

            item = CacheItem(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                region_id=self.region_id,
                access_count=1 if key not in self.store else self.store[key].access_count + 1,
                last_accessed=time.time(),
            )
            self.store[key] = item
            return item

    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.store:
                del self.store[key]
                return True
            return False

    def get_all_keys(self) -> List[str]:
        with self.lock:
            # Clean expired items while listing
            current_time = time.time()
            expired_keys = [k for k, v in self.store.items() if v.expires_at and current_time > v.expires_at]
            for k in expired_keys:
                del self.store[k]
            return list(self.store.keys())

    def clear(self):
        with self.lock:
            self.store.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def get_stats(self) -> RegionStats:
        with self.lock:
            total_requests = self.hits + self.misses
            hit_ratio = round((self.hits / total_requests) * 100, 2) if total_requests > 0 else 0.0
            region_info = settings.REGIONS.get(self.region_id)
            
            return RegionStats(
                region_id=self.region_id,
                name=region_info.name if region_info else self.region_id,
                location=region_info.location if region_info else "Unknown",
                lat=region_info.lat if region_info else 0.0,
                lon=region_info.lon if region_info else 0.0,
                status="active",
                total_items=len(self.store),
                max_capacity=self.max_size,
                hits=self.hits,
                misses=self.misses,
                hit_ratio=hit_ratio,
                evictions=self.evictions,
            )
