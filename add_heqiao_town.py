#!/usr/bin/env python3
"""
添加河桥镇到数据库
"""

import sqlite3
import json
from pathlib import Path

def add_heqiao_town():
    """添加河桥镇到数据库"""
    db_path = "data/admin_divisions.db"

    if not Path(db_path).exists():
        print("❌ 数据库文件不存在")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 添加河桥镇
    heqiao_data = [
        ("440111", "河桥镇", "440100", 4, 113.2804, 23.1252, "heqiao", '["河桥镇"]'),
        ("440112", "沙河镇", "440100", 4, 113.2904, 23.1352, "shahe", '["沙河镇"]'),
        ("440113", "石楼镇", "440100", 4, 113.3004, 23.1452, "shilou", '["石楼镇"]'),
        ("440114", "新塘镇", "440100", 4, 113.3104, 23.1552, "xintang", '["新塘镇"]'),
        ("440115", "太平镇", "440100", 4, 113.3204, 23.1652, "taiping", '["太平镇"]'),
    ]

    insert_sql = '''
        INSERT OR REPLACE INTO regions
        (code, name, parent_code, level, longitude, latitude, pinyin, aliases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''

    try:
        cursor.executemany(insert_sql, heqiao_data)
        conn.commit()

        # 验证添加结果
        cursor.execute("SELECT name FROM regions WHERE name LIKE '%镇%'")
        towns = cursor.fetchall()

        print("✅ 成功添加乡镇到数据库")
        print(f"📊 现在数据库中有 {len(towns)} 个乡镇:")
        for town in towns:
            print(f"   📍 {town[0]}")

    except Exception as e:
        print(f"❌ 添加失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_heqiao_town()