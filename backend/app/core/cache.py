import time
from typing import Dict, Any, Optional


class SimpleMemoryCache:
    """
    In-memory cache with dataset-specific TTL policies.
    DO NOT use for high-frequency dynamic AIS positions or live weather.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds,
        }

    def clear(self):
        self._cache.clear()


# Global cache instance
cache = SimpleMemoryCache()

# Dataset-specific TTL presets (in seconds)
PORT_CONSTRAINTS_TTL = 86400   # 24 hours (regulatory tariffs rarely change mid-voyage)
VESSEL_PARTICULARS_TTL = 3600  # 1 hour
MODEL_METADATA_TTL = 43200     # 12 hours
