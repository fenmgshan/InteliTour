"""景点推荐服务

1. 查询 category="景点" 的 POI，按子类别过滤
2. 有界 Dijkstra 计算路网距离
3. Redis 热度 + DB fallback
4. 按热度 / 距离排序
"""

from __future__ import annotations

import heapq
from typing import Optional

from database.config import get_session
from database.models import POI
from backend.services.graph_service import get_graph
from backend.services.snap_service import get_snap_service
from backend.services.redis_service import get_all_heats

INF = float("inf")

# 默认有界 Dijkstra 最大搜索距离（米）
_DEFAULT_MAX_DIST = 3000.0


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
    """有界 Dijkstra，返回 {node_id: distance_meters}。"""
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


def _road_distance(origin_node, dest_node) -> float:
    """路网最短距离（米），不可达返回 INF。"""
    if origin_node is None or dest_node is None:
        return INF
    if origin_node == dest_node:
        return 0.0
    G = get_graph()
    try:
        import networkx as nx
        length = nx.dijkstra_path_length(G, origin_node, dest_node, weight="length")
        return float(length)
    except nx.NetworkXNoPath:
        return INF


def list_attractions(origin_lat: float, origin_lng: float,
                     sub_category: str = "", sort_by: str = "heat",
                     limit: int = 20) -> list[dict]:
    """景点列表查询。

    Args:
        origin_lat/lng: 起点坐标
        sub_category: OSM 子类别过滤，空=全部
        sort_by: "heat" 按热度降序，"distance" 按距离升序
        limit: 返回数量上限
    """
    origin_node = _snap_node(origin_lat, origin_lng)

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

    heats = get_all_heats("attraction")

    results: list[tuple[POI, float, float]] = []
    for poi in pois:
        heat = float(heats.get(str(poi.id), poi.heat or 0))

        if poi.snapped_node_id is None:
            dist = INF
        else:
            G = get_graph()
            dest_node = (poi.snapped_node_id
                         if poi.snapped_node_id in G
                         else str(poi.snapped_node_id))
            dist = _road_distance(origin_node, dest_node)

        if dist < INF:
            results.append((poi, dist, heat))

    if not results:
        return []

    if sort_by == "distance":
        results.sort(key=lambda x: x[1])
    else:
        results.sort(key=lambda x: (-x[2], x[1]))

    return [
        {
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
        for poi, dist, heat in results[:limit]
    ]


def search_attractions(origin_lat: float, origin_lng: float,
                       q: str, limit: int = 20) -> list[dict]:
    """按名称搜索景点。

    Args:
        origin_lat/lng: 起点坐标
        q: 名称搜索关键词
        limit: 返回数量上限
    """
    origin_node = _snap_node(origin_lat, origin_lng)

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

    heats = get_all_heats("attraction")

    results: list[tuple[POI, float, float]] = []
    for poi in pois:
        heat = float(heats.get(str(poi.id), poi.heat or 0))

        if poi.snapped_node_id is None:
            dist = INF
        else:
            G = get_graph()
            dest_node = (poi.snapped_node_id
                         if poi.snapped_node_id in G
                         else str(poi.snapped_node_id))
            dist = _road_distance(origin_node, dest_node)

        if dist < INF:
            results.append((poi, dist, heat))
        else:
            results.append((poi, INF, heat))

    results.sort(key=lambda x: (x[1] if x[1] < INF else float('inf'), -x[2]))

    return [
        {
            "id": poi.id,
            "name": poi.name,
            "category": poi.category,
            "sub_category": poi.sub_category or "",
            "lat": poi.lat,
            "lng": poi.lng,
            "address": poi.address or "",
            "rating": poi.rating or 0.0,
            "heat": round(heat, 1),
            "distance": round(dist, 1) if dist < INF else -1,
        }
        for poi, dist, heat in results[:limit]
    ]
