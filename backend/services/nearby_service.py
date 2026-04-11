"""周边设施查询服务

核心算法：
1. 有界 Dijkstra（距离限制等时圈搜索）：从起点沿路网扩散，
   超过 max_dist 立即停止，避免全图搜索。
2. 快速排序（Quick Sort）：对收集到的设施按路网距离升序排列。
"""

from __future__ import annotations

import heapq
from typing import Optional

from database.config import get_session
from database.models import POI
from backend.services.graph_service import get_graph
from backend.services.snap_service import get_snap_service

INF = float("inf")


# ══════════════════════════════════════════════════════════
# 有界 Dijkstra（等时圈搜索）
# ══════════════════════════════════════════════════════════

def _bounded_dijkstra(origin_node, max_dist: float) -> dict:
    """从 origin_node 出发，沿路网扩散，返回所有路网距离 <= max_dist 的节点。

    Returns:
        {node_id: distance_meters}
    """
    G = get_graph()
    dist: dict = {origin_node: 0.0}
    heap = [(0.0, origin_node)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, INF):
            continue
        if d > max_dist:
            break  # 堆顶已超出范围，后续只会更远
        for v, edge_data in G[u].items():
            nd = d + edge_data["length"]
            if nd <= max_dist and nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist


# ══════════════════════════════════════════════════════════
# 快速排序（原地，按距离升序）
# ══════════════════════════════════════════════════════════

def _quicksort(items: list, key) -> list:
    """快速排序，返回新列表（升序）。"""
    if len(items) <= 1:
        return items
    pivot_key = key(items[len(items) // 2])
    left = [x for x in items if key(x) < pivot_key]
    mid = [x for x in items if key(x) == pivot_key]
    right = [x for x in items if key(x) > pivot_key]
    return _quicksort(left, key) + mid + _quicksort(right, key)


# ══════════════════════════════════════════════════════════
# 公开接口
# ══════════════════════════════════════════════════════════

def find_nearby(origin_lat: float, origin_lng: float,
                category: str, max_dist: float, limit: int) -> list[dict]:
    """周边设施查询。

    Args:
        origin_lat/lng: 起点坐标
        category: 设施类别（对应 POI.category）
        max_dist: 最大路网距离（米）
        limit: 最多返回数量

    Returns:
        按路网距离升序排列的设施列表
    """
    # 1. 吸附起点
    service = get_snap_service()
    node_id, _, _, _ = service.snap_point(origin_lat, origin_lng)
    G = get_graph()
    origin_node = node_id if node_id in G else str(node_id)

    # 2. 有界 Dijkstra，获取等时圈内所有节点及距离
    reachable = _bounded_dijkstra(origin_node, max_dist)

    if not reachable:
        return []

    # 3. 从 DB 查询目标类别的 POI，过滤出 snapped_node_id 在等时圈内的
    session = get_session()
    try:
        pois = (session.query(POI)
                .filter(POI.category == category)
                .filter(POI.snapped_node_id.isnot(None))
                .all())
    finally:
        session.close()

    # 4. 匹配路网节点，收集可达设施
    results: list[tuple[POI, float]] = []
    for poi in pois:
        snap_node = (poi.snapped_node_id
                     if poi.snapped_node_id in reachable
                     else str(poi.snapped_node_id))
        dist = reachable.get(snap_node, INF)
        if dist < INF:
            results.append((poi, dist))

    # 5. 快速排序按距离升序
    sorted_results = _quicksort(results, key=lambda x: x[1])

    # 6. 截取并格式化
    return [
        {
            "id": poi.id,
            "name": poi.name,
            "category": poi.category,
            "sub_category": poi.sub_category or "",
            "lat": poi.lat,
            "lng": poi.lng,
            "address": poi.address or "",
            "distance": round(dist, 1),
        }
        for poi, dist in sorted_results[:limit]
    ]
