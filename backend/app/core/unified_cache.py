"""统一缓存系统"""

import json
import pickle
import hashlib
import time
import asyncio
from typing import Any, Optional, Dict, List, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from functools import wraps
import threading
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheBackend(Enum):
    """缓存后端类型"""
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"
    HYBRID = "hybrid"

class SerializationMethod(Enum):
    """序列化方法"""
    JSON = "json"
    PICKLE = "pickle"
    STRING = "string"

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def touch(self) -> None:
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_size: int = 0
    entry_count: int = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class CacheBackendInterface(ABC):
    """缓存后端接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存条目"""
        pass

    @abstractmethod
    async def set(self, entry: CacheEntry) -> None:
        """设置缓存条目"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存条目"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

    @abstractmethod
    async def get_stats(self) -> CacheStats:
        """获取统计信息"""
        pass

class MemoryCacheBackend(CacheBackendInterface):
    """内存缓存后端"""

    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = threading.RLock()
        self._last_cleanup = time.time()

    async def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存条目"""
        await self._cleanup_if_needed()

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None

            entry.touch()
            self._stats.hits += 1
            return entry

    async def set(self, entry: CacheEntry) -> None:
        """设置缓存条目"""
        await self._cleanup_if_needed()

        with self._lock:
            # 检查是否需要驱逐
            if len(self._cache) >= self.max_size and entry.key not in self._cache:
                await self._evict_lru()

            self._cache[entry.key] = entry
            self._stats.sets += 1
            self._update_stats()

    async def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.deletes += 1
                self._update_stats()
                return True
            return False

    async def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                return True
            return False

    async def get_stats(self) -> CacheStats:
        """获取统计信息"""
        with self._lock:
            self._update_stats()
            return self._stats

    async def _cleanup_if_needed(self) -> None:
        """如果需要则清理过期条目"""
        current_time = time.time()
        if current_time - self._last_cleanup > self.cleanup_interval:
            await self._cleanup_expired()
            self._last_cleanup = current_time

    async def _cleanup_expired(self) -> None:
        """清理过期条目"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self._stats.evictions += 1

            self._update_stats()

    async def _evict_lru(self) -> None:
        """驱逐最近最少使用的条目"""
        if not self._cache:
            return

        # 找到最近最少访问的条目
        lru_key = min(self._cache.keys(),
                     key=lambda k: self._cache[k].last_accessed or self._cache[k].created_at)

        del self._cache[lru_key]
        self._stats.evictions += 1

    def _update_stats(self) -> None:
        """更新统计信息"""
        self._stats.entry_count = len(self._cache)
        # 估算总大小（简化实现）
        self._stats.total_size = sum(len(str(entry.value)) for entry in self._cache.values())

class RedisCacheBackend(CacheBackendInterface):
    """Redis缓存后端"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 key_prefix: str = "mcps:",
                 serialization: SerializationMethod = SerializationMethod.PICKLE):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.serialization = serialization
        self._redis = None
        self._stats = CacheStats()

    async def _get_redis(self):
        """获取Redis连接"""
        if self._redis is None:
            try:
                import aioredis
                self._redis = await aioredis.from_url(self.redis_url)
            except ImportError:
                raise ImportError("需要安装aioredis: pip install aioredis")
        return self._redis

    def _serialize(self, obj: Any) -> bytes:
        """序列化对象"""
        if self.serialization == SerializationMethod.JSON:
            return json.dumps(obj, default=str).encode('utf-8')
        elif self.serialization == SerializationMethod.PICKLE:
            return pickle.dumps(obj)
        else:
            return str(obj).encode('utf-8')

    def _deserialize(self, data: bytes) -> Any:
        """反序列化对象"""
        if self.serialization == SerializationMethod.JSON:
            return json.loads(data.decode('utf-8'))
        elif self.serialization == SerializationMethod.PICKLE:
            return pickle.loads(data)
        else:
            return data.decode('utf-8')

    def _make_key(self, key: str) -> str:
        """生成Redis键"""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存条目"""
        redis = await self._get_redis()
        redis_key = self._make_key(key)

        try:
            data = await redis.get(redis_key)
            if data is None:
                self._stats.misses += 1
                return None

            entry = self._deserialize(data)
            if isinstance(entry, CacheEntry):
                if entry.is_expired():
                    await redis.delete(redis_key)
                    self._stats.misses += 1
                    self._stats.evictions += 1
                    return None

                entry.touch()
                self._stats.hits += 1

                # 更新Redis中的访问信息
                await redis.set(redis_key, self._serialize(entry))
                return entry

            self._stats.misses += 1
            return None

        except Exception as e:
            logger.error(f"Redis获取缓存失败: {e}")
            self._stats.misses += 1
            return None

    async def set(self, entry: CacheEntry) -> None:
        """设置缓存条目"""
        redis = await self._get_redis()
        redis_key = self._make_key(entry.key)

        try:
            serialized_data = self._serialize(entry)

            if entry.expires_at:
                # 计算TTL
                ttl = int((entry.expires_at - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    await redis.setex(redis_key, ttl, serialized_data)
                else:
                    return  # 已过期，不设置
            else:
                await redis.set(redis_key, serialized_data)

            self._stats.sets += 1

        except Exception as e:
            logger.error(f"Redis设置缓存失败: {e}")

    async def delete(self, key: str) -> bool:
        """删除缓存条目"""
        redis = await self._get_redis()
        redis_key = self._make_key(key)

        try:
            result = await redis.delete(redis_key)
            if result > 0:
                self._stats.deletes += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Redis删除缓存失败: {e}")
            return False

    async def clear(self) -> None:
        """清空缓存"""
        redis = await self._get_redis()

        try:
            # 删除所有带前缀的键
            pattern = f"{self.key_prefix}*"
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)

            self._stats = CacheStats()

        except Exception as e:
            logger.error(f"Redis清空缓存失败: {e}")

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        redis = await self._get_redis()
        redis_key = self._make_key(key)

        try:
            return await redis.exists(redis_key) > 0
        except Exception as e:
            logger.error(f"Redis检查键存在失败: {e}")
            return False

    async def get_stats(self) -> CacheStats:
        """获取统计信息"""
        return self._stats

class UnifiedCacheManager:
    """统一缓存管理器"""

    def __init__(self,
                 backend: CacheBackendInterface,
                 default_ttl: Optional[int] = None,
                 key_prefix: str = "",
                 enable_compression: bool = False):
        self.backend = backend
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.enable_compression = enable_compression
        self._lock = asyncio.Lock()

    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        if self.key_prefix:
            return f"{self.key_prefix}:{key}"
        return key

    def _hash_key(self, key: str) -> str:
        """对键进行哈希处理"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        cache_key = self._make_key(key)
        entry = await self.backend.get(cache_key)

        if entry is None:
            return default

        return entry.value

    async def set(self,
                 key: str,
                 value: Any,
                 ttl: Optional[int] = None,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """设置缓存值"""
        cache_key = self._make_key(key)

        # 计算过期时间
        expires_at = None
        if ttl is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        elif self.default_ttl is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl)

        # 创建缓存条目
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            tags=tags or [],
            metadata=metadata or {}
        )

        await self.backend.set(entry)

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        cache_key = self._make_key(key)
        return await self.backend.delete(cache_key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        cache_key = self._make_key(key)
        return await self.backend.exists(cache_key)

    async def clear(self) -> None:
        """清空缓存"""
        await self.backend.clear()

    async def get_or_set(self,
                        key: str,
                        factory: Callable[[], Any],
                        ttl: Optional[int] = None,
                        tags: Optional[List[str]] = None) -> Any:
        """获取缓存值，如果不存在则通过工厂函数创建"""
        value = await self.get(key)
        if value is not None:
            return value

        # 使用锁防止缓存击穿
        async with self._lock:
            # 再次检查缓存
            value = await self.get(key)
            if value is not None:
                return value

            # 调用工厂函数
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()

            # 设置缓存
            await self.set(key, value, ttl, tags)
            return value

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存值"""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self,
                      mapping: Dict[str, Any],
                      ttl: Optional[int] = None,
                      tags: Optional[List[str]] = None) -> None:
        """批量设置缓存值"""
        for key, value in mapping.items():
            await self.set(key, value, ttl, tags)

    async def delete_many(self, keys: List[str]) -> int:
        """批量删除缓存值"""
        deleted_count = 0
        for key in keys:
            if await self.delete(key):
                deleted_count += 1
        return deleted_count

    async def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        return await self.backend.get_stats()

    def cache_result(self,
                    key_template: str = "{func_name}:{args_hash}",
                    ttl: Optional[int] = None,
                    tags: Optional[List[str]] = None):
        """缓存函数结果的装饰器"""
        def decorator(func):
            # 检查函数是否为异步函数
            is_async = asyncio.iscoroutinefunction(func)
            
            if is_async:
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    # 生成缓存键
                    args_str = str(args) + str(sorted(kwargs.items()))
                    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                    cache_key = key_template.format(
                        func_name=func.__name__,
                        args_hash=args_hash,
                        module=func.__module__
                    )

                    # 尝试从缓存获取
                    cached_result = await self.get(cache_key)
                    if cached_result is not None:
                        return cached_result

                    # 执行函数
                    result = await func(*args, **kwargs)

                    # 缓存结果
                    await self.set(cache_key, result, ttl, tags)
                    return result
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    # 对于同步函数，直接执行原函数，不使用缓存
                    # 因为同步函数无法安全地与异步缓存系统交互
                    return func(*args, **kwargs)
                return sync_wrapper
        return decorator

# 缓存工厂
class CacheFactory:
    """缓存工厂"""

    @staticmethod
    def create_memory_cache(max_size: int = 1000,
                           cleanup_interval: int = 300,
                           default_ttl: Optional[int] = None) -> UnifiedCacheManager:
        """创建内存缓存"""
        backend = MemoryCacheBackend(max_size, cleanup_interval)
        return UnifiedCacheManager(backend, default_ttl)

    @staticmethod
    def create_redis_cache(redis_url: str = "redis://localhost:6379",
                          key_prefix: str = "mcps:",
                          serialization: SerializationMethod = SerializationMethod.PICKLE,
                          default_ttl: Optional[int] = None) -> UnifiedCacheManager:
        """创建Redis缓存"""
        backend = RedisCacheBackend(redis_url, key_prefix, serialization)
        return UnifiedCacheManager(backend, default_ttl)

    @staticmethod
    def create_hybrid_cache(memory_max_size: int = 100,
                           redis_url: str = "redis://localhost:6379",
                           default_ttl: Optional[int] = None) -> UnifiedCacheManager:
        """创建混合缓存（内存+Redis）"""
        # 这里可以实现一个混合后端，优先使用内存，溢出到Redis
        # 简化实现，直接返回Redis缓存
        return CacheFactory.create_redis_cache(redis_url, default_ttl=default_ttl)

# 全局缓存管理器
_cache_manager: Optional[UnifiedCacheManager] = None

def get_cache_manager() -> UnifiedCacheManager:
    """获取全局缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheFactory.create_memory_cache()
    return _cache_manager

def init_cache(backend_type: CacheBackend = CacheBackend.MEMORY, **kwargs) -> UnifiedCacheManager:
    """初始化缓存系统"""
    global _cache_manager

    if backend_type == CacheBackend.MEMORY:
        _cache_manager = CacheFactory.create_memory_cache(**kwargs)
    elif backend_type == CacheBackend.REDIS:
        _cache_manager = CacheFactory.create_redis_cache(**kwargs)
    elif backend_type == CacheBackend.HYBRID:
        _cache_manager = CacheFactory.create_hybrid_cache(**kwargs)
    else:
        raise ValueError(f"不支持的缓存后端类型: {backend_type}")

    return _cache_manager

# 便捷函数
async def cache_get(key: str, default: Any = None) -> Any:
    """获取缓存值的便捷函数"""
    return await get_cache_manager().get(key, default)

async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """设置缓存值的便捷函数"""
    await get_cache_manager().set(key, value, ttl)

async def cache_delete(key: str) -> bool:
    """删除缓存值的便捷函数"""
    return await get_cache_manager().delete(key)

def cached(ttl: Optional[int] = None, key_template: str = "{func_name}:{args_hash}"):
    """缓存装饰器的便捷函数"""
    return get_cache_manager().cache_result(key_template, ttl)
