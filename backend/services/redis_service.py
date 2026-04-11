"""Redis 热度/评分服务

供日记和美食推荐共用。
热度存储在 Redis Hash: {namespace}:heat  field=id  value=count
评分存储在 Redis Hash: {namespace}:rating field=id  value=score
"""

import redis

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    return _client


# ── 热度 ──────────────────────────────────────────────────

def incr_heat(namespace: str, item_id: int) -> int:
    """热度 +1，返回新热度值。"""
    return get_redis().hincrby(f"{namespace}:heat", str(item_id), 1)


def get_heat(namespace: str, item_id: int) -> float:
    val = get_redis().hget(f"{namespace}:heat", str(item_id))
    return float(val) if val else 0.0


def get_all_heats(namespace: str) -> dict[str, float]:
    """返回 {id_str: heat} 字典。"""
    raw = get_redis().hgetall(f"{namespace}:heat")
    return {k: float(v) for k, v in raw.items()}


# ── 评分 ──────────────────────────────────────────────────

def set_rating(namespace: str, item_id: int, score: float) -> None:
    get_redis().hset(f"{namespace}:rating", str(item_id), score)


def get_rating(namespace: str, item_id: int) -> float:
    val = get_redis().hget(f"{namespace}:rating", str(item_id))
    return float(val) if val else 0.0


def get_all_ratings(namespace: str) -> dict[str, float]:
    raw = get_redis().hgetall(f"{namespace}:rating")
    return {k: float(v) for k, v in raw.items()}
