#!/usr/bin/env python3
"""
智能地名匹配器
支持精确匹配、模糊匹配、拼音匹配、层级匹配等多种策略
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from city_coordinate_db import CityCoordinateDB, PlaceInfo


@dataclass
class MatchResult:
    """匹配结果数据类"""
    place_info: PlaceInfo
    score: float  # 匹配分数 0-1
    match_type: str  # 匹配类型：exact, fuzzy, pinyin, contains, hierarchical
    confidence: str  # 置信度：high, medium, low


class PlaceNameMatcher:
    """智能地名匹配器"""

    def __init__(self, coordinate_db: CityCoordinateDB):
        """
        初始化地名匹配器

        Args:
            coordinate_db: 坐标数据库实例
        """
        self.db = coordinate_db
        self.cache = {}  # 简单的内存缓存

        # 常见地名别名映射
        self.alias_map = {
            # 省级别名
            "北京": "北京市",
            "上海": "上海市",
            "天津": "天津市",
            "重庆": "重庆市",
            "广东": "广东省",
            "浙江": "浙江省",
            "四川": "四川省",
            "陕西": "陕西省",
            "湖北": "湖北省",
            "江苏": "江苏省",
            "山东": "山东省",
            "辽宁": "辽宁省",
            "福建": "福建省",
            "湖南": "湖南省",
            "河南": "河南省",
            "安徽": "安徽省",
            "江西": "江西省",
            "贵州": "贵州省",
            "云南": "云南省",

            # 市级别名
            "广州": "广州市",
            "深圳": "深圳市",
            "杭州": "杭州市",
            "成都": "成都市",
            "西安": "西安市",
            "武汉": "武汉市",
            "南京": "南京市",
            "济南": "济南市",
            "青岛": "青岛市",
            "沈阳": "沈阳市",
            "大连": "大连市",
            "福州": "福州市",
            "厦门": "厦门市",
            "长沙": "长沙市",
            "郑州": "郑州市",
            "合肥": "合肥市",
            "南昌": "南昌市",
            "贵阳": "贵阳市",
            "昆明": "昆明市",
        }

        # 行政区划后缀
        self.admin_suffixes = [
            "省", "市", "县", "区", "镇", "乡", "村",
            "自治区", "自治州", "自治县", "特别行政区",
            "地区", "盟", "旗"
        ]

    def match_place(self, place_name: str) -> Optional[MatchResult]:
        """
        智能匹配地名，支持多种匹配策略

        Args:
            place_name: 要匹配的地名

        Returns:
            匹配结果或None
        """
        if not place_name or not place_name.strip():
            return None

        # 预处理
        normalized_name = self._normalize_place_name(place_name)

        # 检查缓存
        cache_key = f"match:{normalized_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 多策略匹配
        match_result = None

        # 1. 精确匹配（最高优先级）
        match_result = self._exact_match(normalized_name)
        if match_result and match_result.score >= 0.95:
            self.cache[cache_key] = match_result
            return match_result

        # 2. 别名匹配
        match_result = self._alias_match(normalized_name)
        if match_result and match_result.score >= 0.9:
            self.cache[cache_key] = match_result
            return match_result

        # 3. 层级匹配
        match_result = self._hierarchical_match(normalized_name)
        if match_result and match_result.score >= 0.85:
            self.cache[cache_key] = match_result
            return match_result

        # 4. 拼音匹配
        match_result = self._pinyin_match(normalized_name)
        if match_result and match_result.score >= 0.8:
            self.cache[cache_key] = match_result
            return match_result

        # 5. 模糊匹配
        match_result = self._fuzzy_match(normalized_name)
        if match_result and match_result.score >= 0.7:
            self.cache[cache_key] = match_result
            return match_result

        # 6. 包含匹配
        match_result = self._contains_match(normalized_name)
        if match_result and match_result.score >= 0.6:
            self.cache[cache_key] = match_result
            return match_result

        # 缓存未匹配结果
        self.cache[cache_key] = None
        return None

    def _normalize_place_name(self, place_name: str) -> str:
        """标准化地名"""
        # 去除前后空格
        name = place_name.strip()

        # 去除常见的修饰词
        name = re.sub(r'^(.+?)(省|市|县|区|镇|乡|村)$', r'\1', name)

        # 去除"省、市、县、区"等后缀进行匹配，但保留原名用于精确匹配
        for suffix in self.admin_suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        return name

    def _exact_match(self, place_name: str) -> Optional[MatchResult]:
        """精确匹配"""
        # 尝试各种可能的名称变体
        name_variants = [
            place_name,  # 原名
            place_name + "市",  # 加市
            place_name + "省",  # 加省
            place_name + "县",  # 加县
            place_name + "区",  # 加区
        ]

        for variant in name_variants:
            places = self.db.search_place(variant, limit=1)
            if places:
                return MatchResult(
                    place_info=places[0],
                    score=1.0 if variant == place_name else 0.95,
                    match_type="exact",
                    confidence="high"
                )

        return None

    def _alias_match(self, place_name: str) -> Optional[MatchResult]:
        """别名匹配"""
        # 检查别名映射
        if place_name in self.alias_map:
            canonical_name = self.alias_map[place_name]
            places = self.db.search_place(canonical_name, limit=1)
            if places:
                return MatchResult(
                    place_info=places[0],
                    score=0.9,
                    match_type="alias",
                    confidence="high"
                )

        # 检查数据库中的别名
        query = """
            SELECT code, name, parent_code, level, longitude, latitude, pinyin, aliases
            FROM regions
            WHERE aliases LIKE ?
            ORDER BY level DESC
            LIMIT 1
        """
        try:
            cursor = self.db.connection.execute(query, (f'%"{place_name}"%',))
            row = cursor.fetchone()
            if row:
                place_info = self.db._row_to_place_info(row)
                return MatchResult(
                    place_info=place_info,
                    score=0.9,
                    match_type="alias",
                    confidence="high"
                )
        except Exception:
            pass

        return None

    def _hierarchical_match(self, place_name: str) -> Optional[MatchResult]:
        """层级匹配"""
        # 尝试解析层级地名（如：广东省广州市天河区）
        if "省" in place_name or "市" in place_name:
            parts = re.split(r'[省市区县]', place_name)
            parts = [p.strip() for p in parts if p.strip()]

            if len(parts) >= 2:
                # 逐级匹配
                current_level = None
                for part in parts:
                    places = self.db.search_place(part, limit=5)
                    if places:
                        # 选择最合适的匹配
                        best_match = self._select_best_match(places, part, current_level)
                        if best_match:
                            current_level = best_match
                        else:
                            break
                    else:
                        break

                if current_level:
                    return MatchResult(
                        place_info=current_level,
                        score=0.85,
                        match_type="hierarchical",
                        confidence="medium"
                    )

        return None

    def _pinyin_match(self, place_name: str) -> Optional[MatchResult]:
        """拼音匹配"""
        # 简单的拼音匹配（基于数据库中的pinyin字段）
        query = """
            SELECT code, name, parent_code, level, longitude, latitude, pinyin, aliases
            FROM regions
            WHERE pinyin LIKE ? OR pinyin = ?
            ORDER BY level DESC, length(name) ASC
            LIMIT 3
        """
        try:
            cursor = self.db.connection.execute(query, (f'%{place_name}%', place_name.lower()))
            rows = cursor.fetchall()

            if rows:
                # 选择最佳匹配
                places = [self.db._row_to_place_info(row) for row in rows]
                best_match = self._select_best_match(places, place_name)

                if best_match:
                    # 计算拼音匹配分数
                    pinyin_score = self._calculate_pinyin_similarity(place_name, best_match.pinyin or "")

                    return MatchResult(
                        place_info=best_match,
                        score=0.8 * pinyin_score,
                        match_type="pinyin",
                        confidence="medium"
                    )
        except Exception:
            pass

        return None

    def _fuzzy_match(self, place_name: str) -> Optional[MatchResult]:
        """模糊匹配（使用编辑距离）"""
        # 搜索相似的地名
        places = self.db.search_place(place_name, limit=10)

        if not places:
            return None

        # 计算相似度分数
        best_match = None
        best_score = 0.0

        for place in places:
            similarity = self._calculate_similarity(place_name, place.name)
            if similarity > best_score:
                best_score = similarity
                best_match = place

        if best_match and best_score >= 0.7:
            return MatchResult(
                place_info=best_match,
                score=best_score * 0.8,  # 模糊匹配权重
                match_type="fuzzy",
                confidence="medium" if best_score >= 0.8 else "low"
            )

        return None

    def _contains_match(self, place_name: str) -> Optional[MatchResult]:
        """包含匹配"""
        query = """
            SELECT code, name, parent_code, level, longitude, latitude, pinyin, aliases
            FROM regions
            WHERE ? LIKE '%' || name || '%'
            ORDER BY level DESC, length(name) DESC
            LIMIT 5
        """
        try:
            cursor = self.db.connection.execute(query, (place_name,))
            rows = cursor.fetchall()

            if rows:
                places = [self.db._row_to_place_info(row) for row in rows]
                best_match = self._select_best_match(places, place_name)

                if best_match:
                    # 计算包含匹配分数
                    contain_score = len(best_match.name) / len(place_name) if place_name else 0

                    return MatchResult(
                        place_info=best_match,
                        score=0.6 * contain_score,
                        match_type="contains",
                        confidence="low"
                    )
        except Exception:
            pass

        return None

    def _select_best_match(self, places: List[PlaceInfo], query: str, parent_info: Optional[PlaceInfo] = None) -> Optional[PlaceInfo]:
        """从多个候选中选择最佳匹配"""
        if not places:
            return None

        # 如果只有一个候选，直接返回
        if len(places) == 1:
            return places[0]

        # 多候选选择策略
        best_match = None
        best_score = 0.0

        for place in places:
            score = 0.0

            # 1. 名称相似度
            similarity = self._calculate_similarity(query, place.name)
            score += similarity * 0.6

            # 2. 级别权重（省级 > 地级 > 县级）
            level_weight = {1: 0.3, 2: 0.2, 3: 0.1}.get(place.level, 0.0)
            score += level_weight

            # 3. 名称长度匹配（更接近查询长度的优先）
            length_diff = abs(len(place.name) - len(query))
            length_score = max(0, 1 - length_diff / 10)
            score += length_score * 0.1

            # 4. 父级匹配（如果有父级信息）
            if parent_info and place.parent_code == parent_info.code:
                score += 0.2

            if score > best_score:
                best_score = score
                best_match = place

        return best_match

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _calculate_pinyin_similarity(self, query: str, pinyin: str) -> float:
        """计算拼音相似度"""
        if not pinyin:
            return 0.0

        # 简单的拼音相似度计算
        query_lower = query.lower()
        pinyin_lower = pinyin.lower()

        if query_lower == pinyin_lower:
            return 1.0
        elif query_lower in pinyin_lower or pinyin_lower in query_lower:
            return 0.8
        else:
            return self._calculate_similarity(query_lower, pinyin_lower)

    def batch_match(self, place_names: List[str]) -> List[Optional[MatchResult]]:
        """批量匹配地名"""
        return [self.match_place(name) for name in place_names]

    def clear_cache(self) -> None:
        """清理缓存"""
        self.cache.clear()

    def get_statistics(self) -> Dict[str, int]:
        """获取匹配器统计信息"""
        stats = {
            "cache_size": len(self.cache),
            "alias_map_size": len(self.alias_map),
            "admin_suffixes_count": len(self.admin_suffixes)
        }
        return stats


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 PlaceNameMatcher")
    print("=" * 50)

    # 初始化
    db = CityCoordinateDB()
    matcher = PlaceNameMatcher(db)

    # 测试匹配
    test_places = [
        "北京",  # 别名匹配
        "上海",  # 别名匹配
        "天河区",  # 精确匹配
        "朝阳区",  # 不存在
        "广州",  # 别名匹配
        "西湖区",  # 精确匹配
        "杭州西湖",  # 包含匹配
        "广东广州",  # 层级匹配
        "beijing",  # 拼音匹配
        "guangzhou",  # 拼音匹配
        "湖",  # 模糊匹配
    ]

    print("🔍 测试地名匹配:")
    for place in test_places:
        result = matcher.match_place(place)
        if result:
            print(f"   ✅ {place} -> {result.place_info.name} "
                  f"(分数: {result.score:.3f}, 类型: {result.match_type}, 置信度: {result.confidence})")
        else:
            print(f"   ❌ {place} -> 未匹配")

    # 获取统计信息
    stats = matcher.get_statistics()
    print(f"\n📊 匹配器统计:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # 清理
    db.close()
    print("\n✅ 测试完成！")