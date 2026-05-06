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

def add_rating(namespace: str, item_id: int, score: float) -> float:
    """累加评分，返回新平均分。"""
    r = get_redis()
    r.hincrbyfloat(f"{namespace}:rating_sum", str(item_id), score)
    r.hincrby(f"{namespace}:rating_count", str(item_id), 1)
    total = float(r.hget(f"{namespace}:rating_sum", str(item_id)) or 0)
    count = int(r.hget(f"{namespace}:rating_count", str(item_id)) or 1)
    return round(total / count, 2)


def get_avg_rating(namespace: str, item_id: int) -> float:
    r = get_redis()
    total = float(r.hget(f"{namespace}:rating_sum", str(item_id)) or 0)
    count = int(r.hget(f"{namespace}:rating_count", str(item_id)) or 0)
    return round(total / count, 2) if count > 0 else 0.0


def get_all_avg_ratings(namespace: str) -> dict[str, float]:
    r = get_redis()
    sums = r.hgetall(f"{namespace}:rating_sum")
    counts = r.hgetall(f"{namespace}:rating_count")
    result = {}
    for k, s in sums.items():
        c = int(counts.get(k, 1))
        result[k] = round(float(s) / c, 2) if c > 0 else 0.0
    return result


