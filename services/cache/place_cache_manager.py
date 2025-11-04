#!/usr/bin/env python3
"""
地名查询缓存管理器
提供多级缓存策略，优化地名匹配性能
"""

import json
import time
import sqlite3
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import RLock
from collections import OrderedDict

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    ttl: int  # 生存时间（秒）
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl

class MemoryCache:
    """内存缓存 - LRU策略"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化内存缓存

        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._lock = RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired:
                    del self._cache[key]
                    self._stats['misses'] += 1
                    return None

                # 移到末尾（LRU更新）
                self._cache.move_to_end(key)
                entry.hit_count += 1
                self._stats['hits'] += 1
                return entry.value

            self._stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            # 如果已存在，更新并移动到末尾
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].timestamp = time.time()
                self._cache[key].ttl = ttl or self.default_ttl
                self._cache.move_to_end(key)
                return

            # 检查容量限制
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats['evictions'] += 1

            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl
            )
            self._cache[key] = entry

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self._stats['evictions']
            }

class DatabaseCache:
    """SQLite持久化缓存"""

    def __init__(self, db_path: str = "data/cache.db"):
        """
        初始化数据库缓存

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS place_cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        ttl INTEGER NOT NULL,
                        hit_count INTEGER DEFAULT 0
                    )
                """)

                # 创建索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON place_cache(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ttl ON place_cache(ttl)")

                conn.commit()
        except Exception as e:
            logger.error(f"初始化数据库缓存失败: {e}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, timestamp, ttl, hit_count FROM place_cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()

                if row:
                    value_json, timestamp, ttl, hit_count = row

                    # 检查是否过期
                    if time.time() - timestamp > ttl:
                        self.delete(key)
                        return None

                    # 更新命中次数
                    conn.execute(
                        "UPDATE place_cache SET hit_count = hit_count + 1 WHERE key = ?",
                        (key,)
                    )
                    conn.commit()

                    return json.loads(value_json)

        except Exception as e:
            logger.warning(f"数据库缓存查询失败: {e}")

        return None

    def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """设置缓存值"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO place_cache (key, value, timestamp, ttl)
                    VALUES (?, ?, ?, ?)
                """, (
                    key,
                    json.dumps(value, ensure_ascii=False),
                    time.time(),
                    ttl
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"数据库缓存写入失败: {e}")

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM place_cache WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.warning(f"数据库缓存删除失败: {e}")
            return False

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM place_cache
                    WHERE timestamp + ttl < ?
                """, (time.time(),))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.warning(f"数据库缓存清理失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总条目数
                total_result = conn.execute("SELECT COUNT(*) FROM place_cache").fetchone()
                total_count = total_result[0] if total_result else 0

                # 过期条目数
                expired_result = conn.execute("""
                    SELECT COUNT(*) FROM place_cache
                    WHERE timestamp + ttl < ?
                """, (time.time(),)).fetchone()
                expired_count = expired_result[0] if expired_result else 0

                # 总命中次数
                hits_result = conn.execute("SELECT SUM(hit_count) FROM place_cache").fetchone()
                total_hits = hits_result[0] if hits_result and hits_result[0] else 0

                return {
                    'total_entries': total_count,
                    'expired_entries': expired_count,
                    'valid_entries': total_count - expired_count,
                    'total_hits': total_hits
                }
        except Exception as e:
            logger.warning(f"数据库缓存统计获取失败: {e}")
            return {}

class PlaceCacheManager:
    """地名缓存管理器 - 多级缓存策略"""

    def __init__(self,
                 memory_size: int = 1000,
                 memory_ttl: int = 3600,
                 disk_ttl: int = 86400):
        """
        初始化缓存管理器

        Args:
            memory_size: 内存缓存最大条目数
            memory_ttl: 内存缓存TTL（秒）
            disk_ttl: 磁盘缓存TTL（秒）
        """
        self.memory_cache = MemoryCache(max_size=memory_size, default_ttl=memory_ttl)
        self.disk_cache = DatabaseCache()
        self.disk_ttl = disk_ttl

        # 定期清理
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5分钟

        logger.info("地名缓存管理器初始化完成")

    def _generate_cache_key(self, place_name: str, prefix: str = "place") -> str:
        """生成缓存键"""
        # 使用MD5确保键名的一致性和长度限制
        content = f"{prefix}:{place_name.lower().strip()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get(self, place_name: str) -> Optional[Any]:
        """
        获取地名缓存

        Args:
            place_name: 地名

        Returns:
            缓存的匹配结果或None
        """
        cache_key = self._generate_cache_key(place_name)

        # 1. 先查内存缓存
        result = self.memory_cache.get(cache_key)
        if result is not None:
            logger.debug(f"内存缓存命中: {place_name}")
            return result

        # 2. 查磁盘缓存
        result = self.disk_cache.get(cache_key)
        if result is not None:
            logger.debug(f"磁盘缓存命中: {place_name}")
            # 将结果提升到内存缓存
            self.memory_cache.set(cache_key, result)
            return result

        logger.debug(f"缓存未命中: {place_name}")
        return None

    def set(self, place_name: str, result: Any, ttl: Optional[int] = None) -> None:
        """
        设置地名缓存

        Args:
            place_name: 地名
            result: 匹配结果
            ttl: 自定义TTL（秒）
        """
        cache_key = self._generate_cache_key(place_name)

        # 设置内存缓存
        memory_ttl = ttl or self.memory_cache.default_ttl
        self.memory_cache.set(cache_key, result, memory_ttl)

        # 设置磁盘缓存
        disk_ttl = ttl or self.disk_ttl
        self.disk_cache.set(cache_key, result, disk_ttl)

        logger.debug(f"缓存已设置: {place_name} (TTL: {memory_ttl}s)")

    def delete(self, place_name: str) -> bool:
        """删除地名缓存"""
        cache_key = self._generate_cache_key(place_name)

        memory_deleted = self.memory_cache.delete(cache_key)
        disk_deleted = self.disk_cache.delete(cache_key)

        return memory_deleted or disk_deleted

    def cleanup(self) -> None:
        """清理过期缓存"""
        current_time = time.time()

        # 检查是否需要清理
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        # 清理内存缓存
        memory_cleaned = self.memory_cache.cleanup_expired()

        # 清理磁盘缓存
        disk_cleaned = self.disk_cache.cleanup_expired()

        self._last_cleanup = current_time

        if memory_cleaned > 0 or disk_cleaned > 0:
            logger.info(f"缓存清理完成: 内存{memory_cleaned}条, 磁盘{disk_cleaned}条")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        self.cleanup()  # 先清理过期数据

        memory_stats = self.memory_cache.get_stats()
        disk_stats = self.disk_cache.get_stats()

        return {
            'memory_cache': memory_stats,
            'disk_cache': disk_stats,
            'total_entries': memory_stats['size'] + disk_stats.get('valid_entries', 0)
        }

    def clear_all(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()

        # 清空磁盘缓存（重建数据库）
        try:
            self.disk_cache.db_path.unlink(missing_ok=True)
            self.disk_cache._init_database()
        except Exception as e:
            logger.warning(f"清空磁盘缓存失败: {e}")

        logger.info("所有缓存已清空")

def main():
    """测试缓存管理器"""
    print("🧪 测试地名缓存管理器")
    print("=" * 60)

    cache_manager = PlaceCacheManager()

    # 测试缓存操作
    test_places = [
        "河桥镇",
        "北京市朝阳区",
        "临安区",
        "杭州市",
        "上海市浦东新区"
    ]

    # 模拟匹配结果
    test_results = [
        {"matched": "临安区", "level": "县级", "approx": True},
        {"matched": "北京市朝阳区", "level": "县级", "approx": False},
        {"matched": "临安区", "level": "县级", "approx": False},
        {"matched": "杭州市", "level": "地级", "approx": False},
        {"matched": "上海市浦东新区", "level": "县级", "approx": False}
    ]

    print("1️⃣ 测试缓存写入:")
    for place, result in zip(test_places, test_results):
        cache_manager.set(place, result)
        print(f"   ✅ 缓存已设置: {place}")

    print("\n2️⃣ 测试缓存读取:")
    for place in test_places:
        result = cache_manager.get(place)
        if result:
            print(f"   ✅ 缓存命中: {place} -> {result['matched']}")
        else:
            print(f"   ❌ 缓存未命中: {place}")

    print("\n3️⃣ 测试新地名（缓存未命中）:")
    new_places = ["深圳市南山区", "广州市天河区"]
    for place in new_places:
        result = cache_manager.get(place)
        if result:
            print(f"   ✅ 缓存命中: {place} -> {result['matched']}")
        else:
            print(f"   ❌ 缓存未命中: {place} (预期行为)")

    print("\n4️⃣ 缓存统计:")
    stats = cache_manager.get_stats()
    print(f"   内存缓存:")
    for key, value in stats['memory_cache'].items():
        print(f"      {key}: {value}")

    print(f"   磁盘缓存:")
    for key, value in stats['disk_cache'].items():
        print(f"      {key}: {value}")

    print(f"   总计: {stats['total_entries']} 个缓存条目")

    print("\n5️⃣ 性能测试:")
    import time

    # 测试缓存命中性能
    start_time = time.time()
    for _ in range(1000):
        cache_manager.get("河桥镇")
    cache_time = time.time() - start_time

    print(f"   1000次缓存查询耗时: {cache_time:.4f}秒")
    print(f"   平均每次查询: {cache_time/1000*1000:.2f}毫秒")

    print(f"\n✅ 缓存管理器测试完成!")

if __name__ == "__main__":
    main()