from cachetools import TTLCache

# Cache in-memory for fast catalog serving. Max 1000 items, TTL 4 hours (14400s)
catalog_cache = TTLCache(maxsize=1000, ttl=14400)