#!/usr/bin/env python3
"""
批量修复地区层级关系
主要修复地级市的province字段和县级地区的层级字段
"""

import sqlite3
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_hierarchy_relationships():
    """批量修复层级关系"""
    db_path = "data/admin_divisions.db"

    if not Path(db_path).exists():
        logger.error("❌ 数据库文件不存在")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("🔧 开始批量修复地区层级关系...")

    # 1. 首先修复地级市的province字段
    logger.info("📊 1. 修复地级市的province字段...")

    # 根据地级市代码前缀确定省份
    province_mapping = {
        '11': '北京市',
        '12': '天津市',
        '13': '河北省',
        '14': '山西省',
        '15': '内蒙古自治区',
        '21': '辽宁省',
        '22': '吉林省',
        '23': '黑龙江省',
        '31': '上海市',
        '32': '江苏省',
        '33': '浙江省',
        '34': '安徽省',
        '35': '福建省',
        '36': '江西省',
        '37': '山东省',
        '41': '河南省',
        '42': '湖北省',
        '43': '湖南省',
        '44': '广东省',
        '45': '广西壮族自治区',
        '46': '海南省',
        '50': '重庆市',
        '51': '四川省',
        '52': '贵州省',
        '53': '云南省',
        '54': '西藏自治区',
        '61': '陕西省',
        '62': '甘肃省',
        '63': '青海省',
        '64': '宁夏回族自治区',
        '65': '新疆维吾尔自治区',
    }

    city_fixes = 0
    cursor.execute('SELECT code, name FROM regions WHERE level = 2 AND province IS NULL')
    cities_to_fix = cursor.fetchall()

    for code, name in cities_to_fix:
        if len(code) >= 2:
            province_code = code[:2]
            province_name = province_mapping.get(province_code)

            if province_name:
                cursor.execute('''
                    UPDATE regions
                    SET province = ?, city = ?
                    WHERE code = ? AND name = ?
                ''', (province_name, name, code, name))

                city_fixes += 1
                logger.info(f"✅ 修复地级市: {name} -> {province_name}")

    conn.commit()
    logger.info(f"📊 修复了 {city_fixes} 个地级市的province字段")

    # 2. 修复县级地区的层级字段
    logger.info("📊 2. 修复县级地区的层级字段...")

    county_fixes = 0
    cursor.execute('SELECT code, name, parent_code FROM regions WHERE level = 3 AND (province IS NULL OR city IS NULL)')
    counties_to_fix = cursor.fetchall()

    for code, name, parent_code in counties_to_fix:
        if parent_code and len(parent_code) >= 2:
            province_code = parent_code[:2]
            province_name = province_mapping.get(province_code)

            if province_name:
                # 获取上级地级市信息
                cursor.execute('SELECT name FROM regions WHERE code = ?', (parent_code,))
                parent_result = cursor.fetchone()

                if parent_result:
                    city_name = parent_result[0]

                    cursor.execute('''
                        UPDATE regions
                        SET province = ?, city = ?, district = ?
                        WHERE code = ? AND name = ?
                    ''', (province_name, city_name, name, code, name))

                    county_fixes += 1
                    logger.info(f"✅ 修复县级: {name} -> {province_name}-{city_name}")

    conn.commit()
    logger.info(f"📊 修复了 {county_fixes} 个县级地区的层级字段")

    # 3. 修复特殊情况的层级关系
    logger.info("📊 3. 修复特殊情况...")

    # 根据区县名称推断上级城市
    special_fixes = 0

    # 处理一些特殊的区县
    special_counties = [
        # 北京的区县
        ('110101', '东城区', '北京市', '北京市'),
        ('110102', '西城区', '北京市', '北京市'),
        ('110105', '朝阳区', '北京市', '北京市'),
        ('110106', '丰台区', '北京市', '北京市'),
        ('110107', '石景山区', '北京市', '北京市'),
        ('110108', '海淀区', '北京市', '北京市'),
        ('110109', '门头沟区', '北京市', '北京市'),
        ('110111', '房山区', '北京市', '北京市'),
        ('110112', '通州区', '北京市', '北京市'),
        ('110113', '顺义区', '北京市', '北京市'),
        ('110114', '昌平区', '北京市', '北京市'),
        ('110115', '大兴区', '北京市', '北京市'),
        ('110116', '怀柔区', '北京市', '北京市'),
        ('110117', '平谷区', '北京市', '北京市'),
        ('110118', '密云区', '北京市', '北京市'),
        ('110119', '延庆区', '北京市', '北京市'),

        # 上海的区县
        ('310101', '黄浦区', '上海市', '上海市'),
        ('310104', '徐汇区', '上海市', '上海市'),
        ('310105', '长宁区', '上海市', '上海市'),
        ('310106', '静安区', '上海市', '上海市'),
        ('310107', '普陀区', '上海市', '上海市'),
        ('310109', '虹口区', '上海市', '上海市'),
        ('310110', '杨浦区', '上海市', '上海市'),
        ('310112', '闵行区', '上海市', '上海市'),
        ('310113', '宝山区', '上海市', '上海市'),
        ('310114', '嘉定区', '上海市', '上海市'),
        ('310115', '浦东新区', '上海市', '上海市'),
        ('310116', '金山区', '上海市', '上海市'),
        ('310117', '松江区', '上海市', '上海市'),
        ('310118', '青浦区', '上海市', '上海市'),
        ('310120', '奉贤区', '上海市', '上海市'),
        ('310151', '崇明区', '上海市', '上海市'),
    ]

    for code, name, province, city in special_counties:
        cursor.execute('''
            UPDATE regions
            SET province = ?, city = ?, district = ?
            WHERE code = ? AND name = ?
        ''', (province, city, name, code, name))

        special_fixes += 1
        logger.info(f"✅ 修复特殊地区: {name} -> {province}-{city}")

    conn.commit()
    logger.info(f"📊 修复了 {special_fixes} 个特殊地区的层级字段")

    # 4. 验证修复结果
    logger.info("📊 4. 验证修复结果...")

    # 检查还有多少地区缺少层级字段
    cursor.execute('''
        SELECT COUNT(*) FROM regions
        WHERE (level = 2 AND province IS NULL)
        OR (level = 3 AND (province IS NULL OR city IS NULL))
    ''')
    remaining_issues = cursor.fetchone()[0]

    # 统计各层级数量
    cursor.execute('SELECT level, COUNT(*) FROM regions GROUP BY level ORDER BY level')
    level_stats = cursor.fetchall()

    logger.info("📊 修复后统计:")
    for level, count in level_stats:
        level_name = {1: "省级", 2: "地级", 3: "县级", 4: "乡镇级", 5: "村级"}.get(level, f"级别{level}")
        logger.info(f"   {level_name}: {count}个")

    logger.info(f"📊 剩余问题: {remaining_issues}个地区仍有层级问题")

    # 5. 测试一些典型地区的层级关系
    logger.info("📊 5. 测试典型地区的层级关系...")

    test_cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '武汉', '南京', '重庆']

    for city in test_cities:
        cursor.execute('''
            SELECT code, name, level, province, city, district
            FROM regions
            WHERE name LIKE ? OR name LIKE ?
            ORDER BY level
            LIMIT 3
        ''', (city, f'%{city}%'))

        results = cursor.fetchall()
        if results:
            for row in results:
                level_name = {1: "省级", 2: "地级", 3: "县级"}.get(row[2], f"级别{row[2]}")
                logger.info(f"✅ {row[1]} ({level_name}): {row[3]}-{row[4]}-{row[5]}")

    conn.close()

    total_fixes = city_fixes + county_fixes + special_fixes
    logger.info(f"\\n🎉 层级关系修复完成!")
    logger.info(f"📊 总共修复: {total_fixes} 个地区")
    logger.info(f"📊 地级市修复: {city_fixes} 个")
    logger.info(f"📊 县级修复: {county_fixes} 个")
    logger.info(f"📊 特殊修复: {special_fixes} 个")
    logger.info(f"📊 剩余问题: {remaining_issues} 个")

if __name__ == "__main__":
    fix_hierarchy_relationships()