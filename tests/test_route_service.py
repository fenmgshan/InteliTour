"""核心算法单元测试

构造已知结构的小图，验证 Dijkstra 和 Bitmask DP TSP 的正确性。
不依赖数据库和 GraphML 文件。

运行: cd InteliTour && python3 -m pytest tests/test_route_service.py -v
"""

import math
from unittest.mock import patch

import networkx as nx
import pytest

from backend.services.graph_service import WALK_SPEED, _precompute_weights
from backend.services.route_service import (
    dijkstra_shortest_path,
    solve_tsp,
    _path_distance,
    _path_weight,
    _dijkstra_path_between,
    INF,
)


def _build_test_graph():
    """构造一个 5 节点的测试图，边权已知，方便手算验证。

    拓扑结构（有向图，双向边）:

        A ---500m--- B ---300m--- C
        |                        |
       400m                    200m
        |                        |
        D ----------700m-------- E

    congestion 全部为 1.0，highway_type = "residential"
    节点坐标使用北京附近的虚拟经纬度（仅用于坐标输出验证）。
    """
    G = nx.DiGraph()

    nodes = {
        "A": {"lat": 39.900, "lng": 116.390},
        "B": {"lat": 39.900, "lng": 116.395},
        "C": {"lat": 39.900, "lng": 116.400},
        "D": {"lat": 39.896, "lng": 116.390},
        "E": {"lat": 39.896, "lng": 116.400},
    }
    for nid, attrs in nodes.items():
        G.add_node(nid, **attrs)

    edges = [
        ("A", "B", 500), ("B", "A", 500),
        ("B", "C", 300), ("C", "B", 300),
        ("A", "D", 400), ("D", "A", 400),
        ("C", "E", 200), ("E", "C", 200),
        ("D", "E", 700), ("E", "D", 700),
    ]
    for src, dst, length in edges:
        G.add_edge(src, dst, length=float(length), congestion=1.0,
                   highway_type="residential", max_speed=0.0)

    _precompute_weights(G)
    return G


# ── 全局 mock ─────────────────────────────────────────────
# 用 patch 替换 get_graph()，使算法使用我们构造的测试图

TEST_GRAPH = _build_test_graph()


@pytest.fixture(autouse=True)
def mock_graph():
    with patch("backend.services.route_service.get_graph", return_value=TEST_GRAPH):
        yield


# ══════════════════════════════════════════════════════════
# Dijkstra 测试
# ══════════════════════════════════════════════════════════

class TestDijkstra:
    def test_same_node(self):
        """起点终点相同 → 路径只含一个点，距离为 0。"""
        coords, dist, time = dijkstra_shortest_path("A", "A", "distance")
        assert len(coords) == 1
        assert dist == 0.0
        assert time == 0.0

    def test_direct_neighbor(self):
        """A→B 直连 500m。"""
        coords, dist, time = dijkstra_shortest_path("A", "B", "distance")
        assert dist == 500.0
        assert len(coords) == 2
        assert coords[0].lat == 39.900
        assert time == pytest.approx(500.0 / WALK_SPEED, rel=1e-6)

    def test_shortest_path_A_to_E(self):
        """A→E 最短路径应为 A→B→C→E = 500+300+200 = 1000m,
        而非 A→D→E = 400+700 = 1100m。
        """
        coords, dist, _ = dijkstra_shortest_path("A", "E", "distance")
        assert dist == 1000.0
        # 验证路径经过 4 个节点
        assert len(coords) == 4

    def test_shortest_path_D_to_C(self):
        """D→C: D→A→B→C = 400+500+300 = 1200m
              D→E→C = 700+200 = 900m  ← 最短
        """
        coords, dist, _ = dijkstra_shortest_path("D", "C", "distance")
        assert dist == 900.0
        assert len(coords) == 3  # D, E, C

    def test_time_strategy(self):
        """time 策略下，权重 = length / (WALK_SPEED * congestion)。
        congestion=1.0，所以最短 time 路径和最短 distance 路径一致。
        """
        _, dist_d, _ = dijkstra_shortest_path("A", "E", "distance")
        _, dist_t, _ = dijkstra_shortest_path("A", "E", "time")
        assert dist_d == dist_t

    def test_unreachable(self):
        """不可达节点应抛出异常。"""
        # 添加一个孤立节点
        TEST_GRAPH.add_node("Z", lat=40.0, lng=117.0)
        try:
            with pytest.raises(nx.NetworkXNoPath):
                dijkstra_shortest_path("A", "Z", "distance")
        finally:
            TEST_GRAPH.remove_node("Z")


# ══════════════════════════════════════════════════════════
# TSP 测试
# ══════════════════════════════════════════════════════════

class TestTSP:
    def test_single_waypoint(self):
        """只有 1 个途经点 = 普通最短路径。
        A → B = 500m
        """
        order, segments, cost = solve_tsp("A", ["B"], "distance", round_trip=False)
        assert order == [0]
        assert len(segments) == 1
        _, seg_dist, _ = segments[0]
        assert seg_dist == 500.0

    def test_single_waypoint_round_trip(self):
        """1 个途经点 + 回程: A→B→A = 500+500 = 1000m。"""
        order, segments, cost = solve_tsp("A", ["B"], "distance", round_trip=True)
        assert order == [0]
        assert len(segments) == 2  # A→B, B→A
        total = sum(s[1] for s in segments)
        assert total == 1000.0

    def test_two_waypoints_optimal_order(self):
        """A 出发, 途经 D 和 E, 不回程。
        A→D→E = 400+700 = 1100m
        A→E→D = 1000+700 = 1700m  (A→E=1000 via B,C)
        最优: A→D→E, order=[0,1] (D=index0, E=index1)
        """
        order, segments, _ = solve_tsp("A", ["D", "E"], "distance", round_trip=False)
        assert order == [0, 1]  # 先 D 再 E
        total = sum(s[1] for s in segments)
        assert total == 1100.0

    def test_three_waypoints(self):
        """A 出发, 途经 B, C, E, 不回程。
        最优: A→B→C→E = 500+300+200 = 1000m
        """
        order, segments, _ = solve_tsp(
            "A", ["B", "C", "E"], "distance", round_trip=False
        )
        total = sum(s[1] for s in segments)
        assert total == 1000.0
        # 验证顺序: B=0, C=1, E=2
        assert order == [0, 1, 2]

    def test_round_trip_returns_to_origin(self):
        """回程时最后一段应返回起点。"""
        order, segments, _ = solve_tsp(
            "A", ["B", "C"], "distance", round_trip=True
        )
        # 最后一段的路径终点应是 A
        last_path = segments[-1][0]
        assert last_path[-1] == "A"

    def test_segments_path_continuity(self):
        """各段路径首尾衔接。"""
        _, segments, _ = solve_tsp(
            "A", ["B", "D", "E"], "distance", round_trip=True
        )
        for i in range(len(segments) - 1):
            prev_end = segments[i][0][-1]
            next_start = segments[i + 1][0][0]
            assert prev_end == next_start, (
                f"段 {i} 终点 {prev_end} != 段 {i+1} 起点 {next_start}"
            )

    def test_empty_waypoints(self):
        """没有途经点 → 返回空。"""
        order, segments, cost = solve_tsp("A", [], "distance")
        assert order == []
        assert segments == []
        assert cost == 0.0


# ══════════════════════════════════════════════════════════
# 内部函数测试
# ══════════════════════════════════════════════════════════

class TestHelpers:
    def test_path_distance(self):
        assert _path_distance(TEST_GRAPH, ["A", "B", "C"]) == 800.0

    def test_path_weight_time(self):
        expected = 800.0 / (WALK_SPEED * 1.0)
        assert _path_weight(TEST_GRAPH, ["A", "B", "C"], "time") == pytest.approx(
            expected, rel=1e-6
        )

    def test_dijkstra_path_between_no_path(self):
        TEST_GRAPH.add_node("Z", lat=40.0, lng=117.0)
        try:
            path, cost = _dijkstra_path_between(TEST_GRAPH, "A", "Z", "length")
            assert path == []
            assert cost == INF
        finally:
            TEST_GRAPH.remove_node("Z")
