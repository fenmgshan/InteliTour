"""旅游日记服务

- zlib 无损压缩存储正文（LZ77 + Huffman）
- Whoosh 全文检索（倒排索引，TF-IDF/BM25）
- MySQL B+树索引精确查找（title/destination）
- Redis 热度计数
- Min-Heap Top-N 推荐
"""

import zlib
import os
from datetime import datetime
from typing import List, Optional

from whoosh import index as whoosh_index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.writing import AsyncWriter

from database.config import get_session
from database.models import Diary
from backend.services.redis_service import (
    incr_heat, get_heat, get_all_heats, get_all_ratings, set_rating
)
from backend.services.heap_service import top_n

# ── Whoosh 索引目录 ───────────────────────────────────────
_INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "whoosh_diary")
_SCHEMA = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    destination=TEXT(stored=True),
    content=TEXT(stored=False),   # 正文只索引不存储（已压缩存 DB）
)

_ix = None  # Whoosh index 单例


def _get_index():
    global _ix
    if _ix is not None:
        return _ix
    os.makedirs(_INDEX_DIR, exist_ok=True)
    if whoosh_index.exists_in(_INDEX_DIR):
        _ix = whoosh_index.open_dir(_INDEX_DIR)
    else:
        _ix = whoosh_index.create_in(_INDEX_DIR, _SCHEMA)
    return _ix


# ── 压缩/解压 ─────────────────────────────────────────────

def _compress(text: str) -> bytes:
    return zlib.compress(text.encode("utf-8"), level=6)


def _decompress(data: bytes) -> str:
    return zlib.decompress(data).decode("utf-8")


# ── CRUD ─────────────────────────────────────────────────

def create_diary(title: str, author: str, destination: str,
                 content: str, rating: float) -> int:
    """创建日记，返回新记录 id。"""
    compressed = _compress(content)
    session = get_session()
    try:
        diary = Diary(
            title=title,
            author=author,
            destination=destination,
            content_compressed=compressed,
            rating=rating,
            created_at=datetime.utcnow(),
        )
        session.add(diary)
        session.commit()
        session.refresh(diary)
        diary_id = diary.id

        # 写入 Redis 初始评分
        if rating > 0:
            set_rating("diary", diary_id, rating)

        # 写入 Whoosh 索引
        ix = _get_index()
        writer = AsyncWriter(ix)
        writer.add_document(
            id=str(diary_id),
            title=title,
            destination=destination,
            content=content,
        )
        writer.commit()

        return diary_id
    finally:
        session.close()


def get_diary(diary_id: int) -> Optional[dict]:
    """获取单篇日记（解压正文），同时热度 +1。"""
    session = get_session()
    try:
        diary = session.get(Diary, diary_id)
        if diary is None:
            return None
        heat = incr_heat("diary", diary_id)
        return _to_dict(diary, _decompress(diary.content_compressed), heat)
    finally:
        session.close()


def delete_diary(diary_id: int) -> bool:
    """删除日记，同时从 Whoosh 索引移除。"""
    session = get_session()
    try:
        diary = session.get(Diary, diary_id)
        if diary is None:
            return False
        session.delete(diary)
        session.commit()

        ix = _get_index()
        writer = AsyncWriter(ix)
        writer.delete_by_term("id", str(diary_id))
        writer.commit()
        return True
    finally:
        session.close()


# ── 搜索 ─────────────────────────────────────────────────

def search_diaries(mode: str, q: str) -> List[dict]:
    """三种搜索模式。

    - title: MySQL B+树索引精确/前缀匹配
    - destination: MySQL 索引过滤
    - fulltext: Whoosh 全文检索（BM25）
    """
    if mode == "title":
        return _search_by_title(q)
    elif mode == "destination":
        return _search_by_destination(q)
    elif mode == "fulltext":
        return _fulltext_search(q)
    else:
        raise ValueError(f"不支持的搜索模式: {mode}")


def _search_by_title(q: str) -> List[dict]:
    session = get_session()
    try:
        # 利用 MySQL title 索引（B+树）精确匹配
        rows = session.query(Diary).filter(Diary.title == q).all()
        return [_brief_dict(r) for r in rows]
    finally:
        session.close()


def _search_by_destination(q: str) -> List[dict]:
    session = get_session()
    try:
        rows = (session.query(Diary)
                .filter(Diary.destination.like(f"%{q}%"))
                .order_by(Diary.created_at.desc())
                .limit(50)
                .all())
        return [_brief_dict(r) for r in rows]
    finally:
        session.close()


def _fulltext_search(q: str) -> List[dict]:
    """Whoosh BM25 全文检索，返回匹配日记的摘要列表。"""
    ix = _get_index()
    parser = MultifieldParser(["title", "destination", "content"], ix.schema)
    query = parser.parse(q)

    matched_ids = []
    with ix.searcher() as searcher:
        results = searcher.search(query, limit=50)
        matched_ids = [int(r["id"]) for r in results]

    if not matched_ids:
        return []

    session = get_session()
    try:
        rows = session.query(Diary).filter(Diary.id.in_(matched_ids)).all()
        id_order = {mid: i for i, mid in enumerate(matched_ids)}
        rows.sort(key=lambda r: id_order.get(r.id, 999))
        return [_brief_dict(r) for r in rows]
    finally:
        session.close()


# ── 推荐（Min-Heap Top-N）────────────────────────────────

def recommend_diaries(n: int = 10) -> List[dict]:
    """基于热度+评分的 Min-Heap Top-N 推荐。

    综合分 = 0.6 * heat_normalized + 0.4 * rating_normalized
    """
    session = get_session()
    try:
        rows = session.query(Diary).all()
        if not rows:
            return []

        heats = get_all_heats("diary")
        ratings = get_all_ratings("diary")

        # 归一化用最大值
        max_heat = max((float(v) for v in heats.values()), default=1.0) or 1.0
        max_rating = 5.0

        def score(diary: Diary) -> float:
            h = heats.get(str(diary.id), 0.0)
            r = ratings.get(str(diary.id), diary.rating or 0.0)
            return 0.6 * (h / max_heat) + 0.4 * (r / max_rating)

        top = top_n(rows, score, n)
        return [_brief_dict(r) for r in top]
    finally:
        session.close()


# ── 工具函数 ──────────────────────────────────────────────

def _brief_dict_by_id(diary_id: int) -> dict:
    session = get_session()
    try:
        diary = session.get(Diary, diary_id)
        return _brief_dict(diary)
    finally:
        session.close()


def _to_dict(diary: Diary, content: str, heat: float) -> dict:
    return {
        "id": diary.id,
        "title": diary.title,
        "author": diary.author,
        "destination": diary.destination,
        "content": content,
        "rating": diary.rating,
        "heat": heat,
        "created_at": diary.created_at,
    }


def _brief_dict(diary: Diary) -> dict:
    heat = get_heat("diary", diary.id)
    return {
        "id": diary.id,
        "title": diary.title,
        "author": diary.author,
        "destination": diary.destination,
        "rating": diary.rating,
        "heat": heat,
        "created_at": diary.created_at,
    }
