"""数据库初始化脚本 — 创建数据库和所有表"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from database.config import SERVER_URL, DATABASE_URL
from database.models import Base


def create_database():
    """创建 intelitour 数据库（如不存在）"""
    engine = create_engine(SERVER_URL, echo=False)
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE DATABASE IF NOT EXISTS intelitour "
            "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
        conn.commit()
    engine.dispose()
    print("[OK] 数据库 intelitour 已创建/已存在")


def create_tables():
    """创建所有 ORM 定义的表"""
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    engine.dispose()
    print("[OK] 所有表已创建")


def main():
    create_database()
    create_tables()
    print("[OK] 数据库初始化完成")


if __name__ == "__main__":
    main()
