"""核心路线算法

包含 Dijkstra 单源最短路径和 Bitmask DP TSP 求解。
"""

import math
from typing import List, Tuple

import networkx as nx

from backend.services.graph_service import get_graph, WALK_SPEED, BIKE_SPEED, EBIKE_SPEED
from backend.schemas.route import LatLng

# ── 策略 → 边权重字段 ────────────────────────────────────
STRATEGY_WEIGHT = {
    "distance": "length",
    "time": "time",
    "bike": "bike",
    "ebike": "ebike",
}

# ── 策略 → 速度 (m/s)，用于估算时间 ─────────────────────
STRATEGY_SPEED = {
    "distance": WALK_SPEED,
    "time": WALK_SPEED,
    "bike": BIKE_SPEED,
    "ebike": EBIKE_SPEED,
}

INF = float("inf")


# ── 工具函数 ──────────────────────────────────────────────

def _node_coord(G: nx.DiGraph, node) -> LatLng:
    """从图中取节点的经纬度。"""
    data = G.nodes[node]
    return LatLng(lat=data["lat"], lng=data["lng"])


def _path_to_coords(G: nx.DiGraph, path: list) -> List[LatLng]:
    """将节点 ID 列表转为坐标列表。"""
    return [_node_coord(G, n) for n in path]


def _path_distance(G: nx.DiGraph, path: list) -> float:
    """计算路径的总 length（米）。"""
    total = 0.0
    for i in range(len(path) - 1):
        total += G[path[i]][path[i + 1]]["length"]
    return total


def _path_weight(G: nx.DiGraph, path: list, weight: str) -> float:
    """计算路径在指定权重下的总代价。"""
    total = 0.0
    for i in range(len(path) - 1):
        total += G[path[i]][path[i + 1]][weight]
    return total


# ── Dijkstra 最短路径 ────────────────────────────────────

def dijkstra_shortest_path(
    origin_node, dest_node, strategy: str = "distance"
) -> Tuple[List[LatLng], float, float]:
    """两点间 Dijkstra 最短路径。

    Returns:
        (path_coords, total_distance_m, total_time_s)
    """
    G = get_graph()
    weight_key = STRATEGY_WEIGHT[strategy]

    path = nx.dijkstra_path(G, origin_node, dest_node, weight=weight_key)
    total_distance = _path_distance(G, path)
    speed = STRATEGY_SPEED[strategy]
    total_time = total_distance / speed

    return _path_to_coords(G, path), total_distance, total_time


def _dijkstra_path_between(
    G: nx.DiGraph, src, dst, weight_key: str
) -> Tuple[list, float]:
    """返回 (node_id_path, weight_cost)。找不到路径时返回 ([], INF)。"""
    try:
        path = nx.dijkstra_path(G, src, dst, weight=weight_key)
        cost = _path_weight(G, path, weight_key)
        return path, cost
    except nx.NetworkXNoPath:
        return [], INF


# ── Bitmask DP TSP ───────────────────────────────────────

def solve_tsp(
    origin_node,
    waypoint_nodes: list,
    strategy: str = "distance",
    round_trip: bool = False,
) -> Tuple[List[int], list, float]:
    """多点 TSP 求解（状态压缩 DP）。

    Args:
        origin_node: 起点节点 ID
        waypoint_nodes: 途经点节点 ID 列表（最多 ~15 个）
        strategy: 权重策略
        round_trip: 是否回到起点

    Returns:
        (ordered_indices, segment_paths, total_cost)
        - ordered_indices: waypoint_nodes 的最优访问索引顺序
        - segment_paths: 各段的 (node_id_path, distance, time) 列表
        - total_cost: 加权总代价
    """
    G = get_graph()
    weight_key = STRATEGY_WEIGHT[strategy]
    speed = STRATEGY_SPEED[strategy]
    n = len(waypoint_nodes)

    if n == 0:
        return [], [], 0.0

    # 关键点列表：0 = origin, 1..n = waypoints
    key_nodes = [origin_node] + list(waypoint_nodes)
    k = len(key_nodes)  # k = n + 1

    # Step 1: 计算两两最短距离矩阵和路径
    dist_matrix = [[INF] * k for _ in range(k)]
    path_matrix = [[[] for _ in range(k)] for _ in range(k)]

    for i in range(k):
        for j in range(k):
            if i == j:
                dist_matrix[i][j] = 0.0
                continue
            path, cost = _dijkstra_path_between(
                G, key_nodes[i], key_nodes[j], weight_key
            )
            dist_matrix[i][j] = cost
            path_matrix[i][j] = path

    # Step 2: Bitmask DP
    # dp[S][i] = 从起点出发，经过集合 S 中的途经点，最后到达途经点 i 的最短代价
    # S 是位掩码，表示已访问的途经点（索引 0..n-1 对应 waypoint_nodes）
    full_mask = (1 << n) - 1
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    # 初始化：从起点直接到各途经点
    for i in range(n):
        dp[1 << i][i] = dist_matrix[0][i + 1]

    # 转移
    for S in range(1, 1 << n):
        for last in range(n):
            if not (S & (1 << last)):
                continue
            if dp[S][last] == INF:
                continue
            for nxt in range(n):
                if S & (1 << nxt):
                    continue
                new_S = S | (1 << nxt)
                new_cost = dp[S][last] + dist_matrix[last + 1][nxt + 1]
                if new_cost < dp[new_S][nxt]:
                    dp[new_S][nxt] = new_cost
                    parent[new_S][nxt] = last

    # Step 3: 找最优终点
    if round_trip:
        best_cost = INF
        best_last = -1
        for i in range(n):
            cost = dp[full_mask][i] + dist_matrix[i + 1][0]
            if cost < best_cost:
                best_cost = cost
                best_last = i
    else:
        best_cost = INF
        best_last = -1
        for i in range(n):
            if dp[full_mask][i] < best_cost:
                best_cost = dp[full_mask][i]
                best_last = i

    if best_cost == INF:
        raise ValueError("无法找到连通路径，部分途经点不可达")

    # Step 4: 回溯得到访问顺序
    order = []
    S = full_mask
    cur = best_last
    while cur != -1:
        order.append(cur)
        prev = parent[S][cur]
        S ^= (1 << cur)
        cur = prev
    order.reverse()

    # Step 5: 拼接各段路径
    segments = []
    prev_key = 0  # 起点在 key_nodes 中的索引
    for wp_idx in order:
        cur_key = wp_idx + 1
        seg_path = path_matrix[prev_key][cur_key]
        seg_dist = _path_distance(G, seg_path) if seg_path else 0.0
        seg_time = seg_dist / speed if speed > 0 else 0.0
        segments.append((seg_path, seg_dist, seg_time))
        prev_key = cur_key

    # 回程段
    if round_trip:
        seg_path = path_matrix[prev_key][0]
        seg_dist = _path_distance(G, seg_path) if seg_path else 0.0
        seg_time = seg_dist / speed if speed > 0 else 0.0
        segments.append((seg_path, seg_dist, seg_time))

    return order, segments, best_cost
