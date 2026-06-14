"""景点推荐服务

优化策略：
1. 一次有界 Dijkstra 获取起点到所有可达节点的距离（O(E log V)）
2. POI 通过 snapped_node_id 直接查表匹配（O(N)）
3. Redis 热度 + DB fallback

相比逐点 Dijkstra（O(N × E log V)），加载时间从数十秒降至 1 秒以内。
"""

from __future__ import annotations

import heapq

from database.config import get_session
from database.models import POI
from backend.services.graph_service import get_graph
from backend.services.snap_service import get_snap_service
from backend.services.redis_service import get_all_heats

INF = float("inf")
_MAX_DIST = 5000.0  # 有界 Dijkstra 搜索半径（米）


def _snap_node(lat: float, lng: float):
    """吸附坐标到图节点 ID。"""
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
    """有界 Dijkstra，一次遍历获得起点到所有可达节点的距离。

    Returns:
        {node_id: distance_meters}，node_id 类型与图中一致。
    """
    G = get_graph()
    dist: dict = {origin_node: 0.0}
    heap = [(0.0, origin_node)]

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
    """从一次 Dijkstra 结果中获取 POI 的路网距离。"""
    if poi.snapped_node_id is None:
        return INF
    G = get_graph()
    snap = (poi.snapped_node_id
            if poi.snapped_node_id in reachable
            else str(poi.snapped_node_id))
    if snap not in reachable:
        # int/str 类型兼容
        alt = str(snap) if isinstance(snap, int) else int(snap) if isinstance(snap, str) else None
        if alt is not None and alt in reachable:
            return reachable[alt]
        return INF
    return reachable[snap]


def _format_item(poi, dist: float, heat: float) -> dict:
    return {
        "id": poi.id,
        "name": poi.name,
        "category": poi.category,
        "sub_category": poi.sub_category or "",
        "lat": poi.lat,
        "lng": poi.lng,
        "address": poi.address or "",
        "rating": poi.rating or 0.0,
        "heat": round(heat, 1),
        "distance": round(dist, 1),
    }


def list_attractions(origin_lat: float, origin_lng: float,
                     sub_category: str = "", sort_by: str = "heat",
                     limit: int = 20) -> list[dict]:
    """景点列表查询。

    一次有界 Dijkstra 覆盖所有 POI，避免逐点计算。
    """
    origin_node = _snap_node(origin_lat, origin_lng)
    if origin_node is None:
        return []

    # Step 1: 一次有界 Dijkstra，获得等时圈内所有节点距离
    reachable = _bounded_dijkstra(origin_node, _MAX_DIST)

    # Step 2: 从 DB 加载景点 POI
    session = get_session()
    try:
        q = session.query(POI).filter(POI.category == "景点")
        if sub_category:
            q = q.filter(POI.sub_category == sub_category)
        pois = q.all()
    finally:
        session.close()

    if not pois:
        return []

    # Step 3: 批量匹配 — 直接从 reachable 查表，不再逐点 Dijkstra
    heats = get_all_heats("attraction")
    results: list[tuple[POI, float, float]] = []

    for poi in pois:
        dist = _resolve_dist(reachable, poi)
        if dist < INF:
            heat = float(heats.get(str(poi.id), poi.heat or 0))
            results.append((poi, dist, heat))

    if not results:
        return []

    if sort_by == "distance":
        results.sort(key=lambda x: x[1])
    else:
        results.sort(key=lambda x: (-x[2], x[1]))

    return [_format_item(poi, dist, heat) for poi, dist, heat in results[:limit]]


def search_attractions(origin_lat: float, origin_lng: float,
                       q: str, limit: int = 20) -> list[dict]:
    """按名称搜索景点。

    一次有界 Dijkstra 覆盖所有搜索结果。
    """
    origin_node = _snap_node(origin_lat, origin_lng)
    if origin_node is None:
        return []

    # Step 1: 一次有界 Dijkstra
    reachable = _bounded_dijkstra(origin_node, _MAX_DIST)

    # Step 2: 按名称搜索
    session = get_session()
    try:
        pois = (session.query(POI)
                .filter(POI.category == "景点")
                .filter(POI.name.like(f"%{q}%"))
                .all())
    finally:
        session.close()

    if not pois:
        return []

    # Step 3: 批量匹配
    heats = get_all_heats("attraction")
    results: list[tuple[POI, float, float]] = []

    for poi in pois:
        dist = _resolve_dist(reachable, poi)
        heat = float(heats.get(str(poi.id), poi.heat or 0))
        results.append((poi, dist, heat))

    results.sort(key=lambda x: (x[1] if x[1] < INF else float('inf'), -x[2]))

    return [_format_item(poi, dist, heat) for poi, dist, heat in results[:limit]]
