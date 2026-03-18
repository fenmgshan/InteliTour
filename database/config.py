"""数据库连接配置"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "mysql+pymysql://intelitour_user:mypassword@localhost:3306/intelitour?charset=utf8mb4"

# 不指定数据库的连接，用于创建数据库
SERVER_URL = "mysql+pymysql://intelitour_user:mypassword@localhost:3306/?charset=utf8mb4"

_engine = None


def get_engine():
    """获取数据库引擎（单例）"""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)
    return _engine


def get_session() -> Session:
    """获取数据库会话"""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
