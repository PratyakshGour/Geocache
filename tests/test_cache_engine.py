import time
import pytest
from app.core.cache_engine import CacheEngine


def test_cache_set_and_get():
    cache = CacheEngine(region_id="test-region", max_size=10, default_ttl=60)
    cache.set("key1", "value1")
    
    assert cache.get("key1") == "value1"
    assert cache.hits == 1
    assert cache.misses == 0


def test_cache_miss_and_expiration():
    cache = CacheEngine(region_id="test-region", max_size=10, default_ttl=1)
    cache.set("short_key", "short_val", ttl=1)
    
    # Verify present immediately
    assert cache.get("short_key") == "short_val"
    
    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("short_key") is None
    assert cache.misses == 1


def test_lru_eviction():
    cache = CacheEngine(region_id="test-region", max_size=2, default_ttl=60, eviction_policy="LRU")
    cache.set("k1", "v1")
    time.sleep(0.01)
    cache.set("k2", "v2")
    time.sleep(0.01)
    
    # Access k1 so k2 becomes least recently used
    cache.get("k1")
    time.sleep(0.01)
    
    # Add k3, which should trigger eviction of k2
    cache.set("k3", "v3")
    
    assert cache.get("k1") == "v1"
    assert cache.get("k3") == "v3"
    assert cache.get("k2") is None
    assert cache.evictions == 1


def test_cache_stats():
    cache = CacheEngine(region_id="us-east", max_size=100, default_ttl=60)
    cache.set("a", 1)
    cache.get("a")  # Hit
    cache.get("b")  # Miss
    
    stats = cache.get_stats()
    assert stats.region_id == "us-east"
    assert stats.total_items == 1
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.hit_ratio == 50.0
