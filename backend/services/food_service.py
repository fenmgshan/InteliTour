"""美食推荐服务

算法：
1. Trie 前缀树：快速前缀匹配候选集
2. Levenshtein 编辑距离 DP：容错模糊匹配
3. 路网 Dijkstra 距离：实际可达距离
4. Min-Heap Top-N：综合评分不完全排序
"""

from __future__ import annotations

import heapq
from typing import Optional

from database.config import get_session
from database.models import POI
from backend.services.graph_service import get_graph, WALK_SPEED
from backend.services.snap_service import get_snap_service
from backend.services.redis_service import get_heat, get_all_heats, get_all_avg_ratings
from backend.services.heap_service import top_n

# 餐饮相关的 category/sub_category 关键词
_FOOD_CATEGORIES = {"restaurant", "cafe", "fast_food", "food", "餐厅", "咖啡", "美食"}

INF = float("inf")


# ══════════════════════════════════════════════════════════
# Trie 字典树
# ══════════════════════════════════════════════════════════

class _TrieNode:
    __slots__ = ("children", "ids")

    def __init__(self):
        self.children: dict[str, _TrieNode] = {}
        self.ids: list[int] = []  # 以该节点为前缀终止的 POI id 列表


class Trie:
    def __init__(self):
        self.root = _TrieNode()

    def insert(self, word: str, poi_id: int) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
            node.ids.append(poi_id)  # 每个前缀节点都记录，方便前缀搜索

    def prefix_search(self, prefix: str) -> list[int]:
        """返回所有以 prefix 开头的 POI id 列表。"""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        return list(node.ids)


# ══════════════════════════════════════════════════════════
# Levenshtein 编辑距离（DP）
# ══════════════════════════════════════════════════════════

def levenshtein(s: str, t: str) -> int:
    """计算字符串 s 和 t 的编辑距离。O(|s|*|t|) 时间，O(|t|) 空间。"""
    m, n = len(s), len(t)
    if m < n:
        s, t, m, n = t, s, n, m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[n]


# ══════════════════════════════════════════════════════════
# 全局 Trie 单例（按需构建）
# ══════════════════════════════════════════════════════════

_trie: Trie | None = None
_trie_id_to_name: dict[int, str] = {}


def _get_trie() -> tuple[Trie, dict[int, str]]:
    global _trie, _trie_id_to_name
    if _trie is not None:
        return _trie, _trie_id_to_name

    session = get_session()
    try:
        rows = session.query(POI.id, POI.name).filter(POI.name != "").all()
        trie = Trie()
        id_to_name: dict[int, str] = {}
        for poi_id, name in rows:
            if name:
                trie.insert(name, poi_id)
                id_to_name[poi_id] = name
        _trie = trie
        _trie_id_to_name = id_to_name
        return _trie, _trie_id_to_name
    finally:
        session.close()


# ══════════════════════════════════════════════════════════
# 路网距离计算
# ══════════════════════════════════════════════════════════

_MAX_DIST = 5000.0  # 有界 Dijkstra 搜索半径（米）


def _snap_node(lat: float, lng: float):
    """吸附坐标到图节点 ID（处理 int/str 类型差异）。"""
    service = get_snap_service()
    node_id, _, _, _ = service.snap_point(lat, lng)
    G = get_graph()
    if node_id in G:
        return node_id
    str_id = str(node_id)
    if str_id in G:
        return str_id
    return None


def _bounded_dijkstra(origin_node, max_dist: float) -> dict:
    """一次有界 Dijkstra，返回 {node_id: distance_meters}。"""
    G = get_graph()
    dist: dict = {origin_node: 0.0}
    heap = [(0.0, origin_node)]
    INF = float("inf")

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, INF):
            continue
        if d > max_dist:
            break
        for v, edge_data in G[u].items():
            nd = d + edge_data["length"]
            if nd <= max_dist and nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def _resolve_dist(reachable: dict, poi) -> float:
    """从一次 Dijkstra 结果中查表获取 POI 路网距离。"""
    if poi.snapped_node_id is None:
        return INF
    snap = poi.snapped_node_id
    if snap in reachable:
        return reachable[snap]
    str_snap = str(snap)
    if str_snap in reachable:
        return reachable[str_snap]
    return INF


# ══════════════════════════════════════════════════════════
# 查询餐饮 POI
# ══════════════════════════════════════════════════════════

def _load_food_pois(cuisine: str = "") -> list[POI]:
    """从 DB 加载餐饮类 POI，可按 sub_category 过滤。"""
    session = get_session()
    try:
        q = session.query(POI).filter(
            POI.category.in_(["餐厅", "restaurant", "cafe", "fast_food", "food"])
        )
        if cuisine:
            q = q.filter(POI.sub_category.like(f"%{cuisine}%"))
        return q.all()
    finally:
        session.close()


def _poi_to_dict(poi: POI, distance: float, score: float) -> dict:
    heat = get_heat("food", poi.id)
    return {
        "id": poi.id,
        "name": poi.name,
        "category": poi.category,
        "sub_category": poi.sub_category,
        "lat": poi.lat,
        "lng": poi.lng,
        "address": poi.address or "",
        "rating": poi.rating or 0.0,
        "heat": heat,
        "distance": round(distance, 1),
        "score": round(score, 4),
    }


# ══════════════════════════════════════════════════════════
# 公开接口
# ══════════════════════════════════════════════════════════

def recommend_food(origin_lat: float, origin_lng: float,
                   cuisine: str = "", n: int = 10) -> list[dict]:
    """附近美食 Top-N 推荐。

    综合分 = α*heat + β*rating - γ*distance_normalized
    α=0.3, β=0.4, γ=0.3
    """
    origin_node = _snap_node(origin_lat, origin_lng)
    if origin_node is None:
        return []

    # 一次有界 Dijkstra，获得起点到所有可达节点的距离（O(E log V)）
    reachable = _bounded_dijkstra(origin_node, _MAX_DIST)

    pois = _load_food_pois(cuisine)
    if not pois:
        return []

    heats = get_all_heats("food")
    ratings = get_all_avg_ratings("food")

    # 从一次 Dijkstra 结果中 O(1) 查表，不再逐点 Dijkstra
    dist_cache: dict[int, float] = {}
    for poi in pois:
        dist_cache[poi.id] = _resolve_dist(reachable, poi)

    # 过滤不可达
    reachable = [p for p in pois if dist_cache[p.id] < INF]
    if not reachable:
        return []

    max_dist = max(dist_cache[p.id] for p in reachable) or 1.0
    max_heat = max(float(heats.get(str(p.id), p.heat or 0)) for p in reachable) or 1.0
    max_rating = 5.0

    def score(poi: POI) -> float:
        h = float(heats.get(str(poi.id), poi.heat or 0))
        r = float(ratings.get(str(poi.id), poi.rating or 0))
        d = dist_cache[poi.id]
        return (0.3 * h / max_heat
                + 0.4 * r / max_rating
                - 0.3 * d / max_dist)

    top = top_n(reachable, score, n)
    return [_poi_to_dict(p, dist_cache[p.id], score(p)) for p in top]


def search_food(q: str, origin_lat: Optional[float], origin_lng: Optional[float],
                max_edit_distance: int = 2, n: int = 10) -> list[dict]:
    """模糊搜索美食。

    1. Trie 前缀匹配召回候选
    2. Levenshtein 编辑距离过滤容错
    3. 若有起点则按路网距离排序，否则按评分排序
    """
    trie, id_to_name = _get_trie()

    # Step 1: Trie 前缀匹配
    candidate_ids = set(trie.prefix_search(q))

    # Step 2: Levenshtein 容错补充（遍历所有名称，找编辑距离 <= max_edit_distance 的）
    for poi_id, name in id_to_name.items():
        if poi_id in candidate_ids:
            continue
        # 只对长度相近的名称计算编辑距离，剪枝加速
        if abs(len(name) - len(q)) <= max_edit_distance:
            if levenshtein(q, name) <= max_edit_distance:
                candidate_ids.add(poi_id)

    if not candidate_ids:
        return []

    session = get_session()
    try:
        pois = (session.query(POI)
                .filter(POI.id.in_(list(candidate_ids)))
                .filter(POI.category.in_(["restaurant", "cafe", "fast_food", "food"]))
                .all())
    finally:
        session.close()

    if not pois:
        return []

    # Step 3: 一次有界 Dijkstra + O(1) 查表计算距离
    origin_node = _snap_node(origin_lat, origin_lng) if origin_lat is not None else None
    reachable = _bounded_dijkstra(origin_node, _MAX_DIST) if origin_node is not None else {}

    results = []
    for poi in pois:
        d = _resolve_dist(reachable, poi) if origin_node is not None else INF
        results.append((poi, d))

    if origin_node is not None:
        results.sort(key=lambda x: x[1])
    else:
        results.sort(key=lambda x: -(x[0].rating or 0))

    return [_poi_to_dict(p, d, 0.0) for p, d in results[:n]]
