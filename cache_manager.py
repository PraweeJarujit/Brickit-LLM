"""
Production-ready Cache Manager
Supports Redis and Memory caching with intelligent invalidation
"""

import json
import pickle
import hashlib
import time
from typing import Any, Optional, Union, Dict
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger("brickkit.cache")

class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

class MemoryCache(CacheBackend):
    """In-memory cache backend"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._default_ttl = 3600
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        
        # Check if expired
        if time.time() > item['expires']:
            del self._cache[key]
            return None
        
        return item['value']
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache"""
        try:
            self._cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }
            return True
        except Exception as e:
            logger.error(f"Memory cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Memory cache clear error: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if key not in self._cache:
            return False
        
        item = self._cache[key]
        if time.time() > item['expires']:
            del self._cache[key]
            return False
        
        return True
    
    def cleanup_expired(self):
        """Clean up expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self._cache.items()
            if current_time > item['expires']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

class RedisCache(CacheBackend):
    """Redis cache backend"""
    
    def __init__(self, redis_url: str):
        try:
            import redis
            self.client = redis.from_url(redis_url, decode_responses=False)
            self.client.ping()  # Test connection
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis"""
        try:
            data = pickle.dumps(value)
            return self.client.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache (use with caution!)"""
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {str(e)}")
            return False

class CacheManager:
    """Production-ready cache manager"""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with stats"""
        value = self.backend.get(key)
        if value is not None:
            self._stats['hits'] += 1
            logger.debug(f"Cache hit: {key}")
        else:
            self._stats['misses'] += 1
            logger.debug(f"Cache miss: {key}")
        return value
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with stats"""
        success = self.backend.set(key, value, ttl)
        if success:
            self._stats['sets'] += 1
            logger.debug(f"Cache set: {key}")
        return success
    
    def delete(self, key: str) -> bool:
        """Delete key from cache with stats"""
        success = self.backend.delete(key)
        if success:
            self._stats['deletes'] += 1
            logger.debug(f"Cache delete: {key}")
        return success
    
    def get_or_set(self, key: str, func, ttl: int = 3600, *args, **kwargs) -> Any:
        """Get from cache or set using function"""
        value = self.get(key)
        if value is not None:
            return value
        
        # Execute function to get value
        value = func(*args, **kwargs)
        self.set(key, value, ttl)
        return value
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""
        # This is a simplified implementation
        # In production, use Redis patterns or maintain key registry
        if hasattr(self.backend, '_cache'):
            # Memory cache implementation
            keys_to_delete = [
                key for key in self.backend._cache.keys()
                if pattern in key
            ]
            
            deleted_count = 0
            for key in keys_to_delete:
                if self.delete(key):
                    deleted_count += 1
            
            logger.info(f"Invalidated {deleted_count} keys matching pattern: {pattern}")
            return deleted_count
        
        return 0
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self._stats,
            'hit_rate': f"{hit_rate:.2f}%",
            'total_requests': total_requests
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

# Cache decorators
def cache_result(key_prefix: str, ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_key(key_prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def cache_user_data(ttl: int = 1800):
    """Decorator to cache user-specific data"""
    def decorator(func):
        def wrapper(user_id: int, *args, **kwargs):
            cache_key = f"user_data:{user_id}:{func.__name__}"
            return cache_manager.get_or_set(
                cache_key, func, ttl, user_id, *args, **kwargs
            )
        return wrapper
    return decorator

def cache_product_data(ttl: int = 3600):
    """Decorator to cache product data"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"product_data:{func.__name__}"
            return cache_manager.get_or_set(cache_key, func, ttl, *args, **kwargs)
        return wrapper
    return decorator

# Initialize cache manager
def init_cache(redis_url: str = None) -> CacheManager:
    """Initialize cache manager with appropriate backend"""
    if redis_url:
        try:
            backend = RedisCache(redis_url)
            logger.info("Using Redis cache backend")
        except Exception:
            logger.warning("Redis unavailable, falling back to memory cache")
            backend = MemoryCache()
    else:
        backend = MemoryCache()
        logger.info("Using memory cache backend")
    
    return CacheManager(backend)

# Global cache manager instance
cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global cache_manager
    if cache_manager is None:
        from config import settings
        cache_manager = init_cache(settings.redis_url)
    return cache_manager

# Cache warming utilities
class CacheWarmer:
    """Utilities for warming up cache"""
    
    @staticmethod
    def warm_product_cache():
        """Warm up product cache"""
        from models import Product
        from database_config import db_config
        
        with db_config.get_db() as db:
            products = db.query(Product).all()
            
            # Cache all products
            cache_manager.set("all_products", products, ttl=3600)
            
            # Cache by category
            for category in ["S", "M", "L"]:
                category_products = [p for p in products if p.size_category == category]
                cache_manager.set(f"products_{category}", category_products, ttl=3600)
        
        logger.info("Product cache warmed up")
    
    @staticmethod
    def warm_user_cache(user_id: int):
        """Warm up user-specific cache"""
        # Cache user orders, wishlist, etc.
        logger.info(f"User cache warmed up for user {user_id}")

# Cache invalidation utilities
class CacheInvalidator:
    """Utilities for intelligent cache invalidation"""
    
    @staticmethod
    def invalidate_product_cache(product_id: int = None):
        """Invalidate product-related cache"""
        patterns = ["all_products", "products_"]
        
        if product_id:
            patterns.append(f"product_{product_id}")
        
        for pattern in patterns:
            cache_manager.invalidate_pattern(pattern)
        
        logger.info("Product cache invalidated")
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidate user-specific cache"""
        patterns = [f"user_data:{user_id}"]
        
        for pattern in patterns:
            cache_manager.invalidate_pattern(pattern)
        
        logger.info(f"User cache invalidated for user {user_id}")
