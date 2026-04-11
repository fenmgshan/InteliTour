"""周边设施查询服务单元测试

测试有界 Dijkstra 等时圈搜索和快速排序算法。
"""

import pytest
import networkx as nx

from backend.services.nearby_service import _bounded_dijkstra, _quicksort


# ══════════════════════════════════════════════════════════
# 测试图构造
# ══════════════════════════════════════════════════════════

def _build_test_graph():
    """构造测试路网图。

    拓扑结构（有向图，双向边）:

        A ---100m--- B ---200m--- C
        |                        |
       50m                     150m
        |                        |
        D ----------600m-------- E

    """
    G = nx.DiGraph()
    nodes = ["A", "B", "C", "D", "E"]
    for n in nodes:
        G.add_node(n)

    edges = [
        ("A", "B", 100), ("B", "A", 100),
        ("B", "C", 200), ("C", "B", 200),
        ("A", "D", 50), ("D", "A", 50),
        ("C", "E", 150), ("E", "C", 150),
        ("D", "E", 600), ("E", "D", 600),
    ]
    for src, dst, length in edges:
        G.add_edge(src, dst, length=float(length))

    return G


# ══════════════════════════════════════════════════════════
# 有界 Dijkstra 测试
# ══════════════════════════════════════════════════════════

class TestBoundedDijkstra:
    def test_basic_reachability(self):
        """测试基本可达性：从 A 出发，max_dist=300"""
        G = _build_test_graph()

        # Mock get_graph
        import backend.services.nearby_service as ns
        import backend.services.graph_service as gs
        gs._graph = G

        result = _bounded_dijkstra("A", 300)

        # A→A=0, A→B=100, A→B→C=300, A→D=50
        # A→D→E=650 超出范围
        assert result == {"A": 0.0, "B": 100.0, "C": 300.0, "D": 50.0}

    def test_small_radius(self):
        """测试小半径：只能到达直连邻居"""
        G = _build_test_graph()
        import backend.services.graph_service as gs
        gs._graph = G

        result = _bounded_dijkstra("A", 60)
        assert result == {"A": 0.0, "D": 50.0}

    def test_large_radius(self):
        """测试大半径：覆盖全图"""
        G = _build_test_graph()
        import backend.services.graph_service as gs
        gs._graph = G

        result = _bounded_dijkstra("A", 1000)
        assert len(result) == 5  # 所有节点可达

    def test_isolated_node(self):
        """测试孤立节点"""
        G = nx.DiGraph()
        G.add_node("A")
        G.add_node("B")
        import backend.services.graph_service as gs
        gs._graph = G

        result = _bounded_dijkstra("A", 100)
        assert result == {"A": 0.0}

    def test_zero_radius(self):
        """测试半径为 0：只有起点自己"""
        G = _build_test_graph()
        import backend.services.graph_service as gs
        gs._graph = G

        result = _bounded_dijkstra("A", 0)
        assert result == {"A": 0.0}


# ══════════════════════════════════════════════════════════
# 快速排序测试
# ══════════════════════════════════════════════════════════

class TestQuickSort:
    def test_basic_sort(self):
        items = [5, 2, 8, 1, 9, 3]
        result = _quicksort(items, key=lambda x: x)
        assert result == [1, 2, 3, 5, 8, 9]

    def test_already_sorted(self):
        items = [1, 2, 3, 4, 5]
        result = _quicksort(items, key=lambda x: x)
        assert result == [1, 2, 3, 4, 5]

    def test_reverse_sorted(self):
        items = [5, 4, 3, 2, 1]
        result = _quicksort(items, key=lambda x: x)
        assert result == [1, 2, 3, 4, 5]

    def test_duplicates(self):
        items = [3, 1, 4, 1, 5, 9, 2, 6, 5]
        result = _quicksort(items, key=lambda x: x)
        assert result == [1, 1, 2, 3, 4, 5, 5, 6, 9]

    def test_single_element(self):
        assert _quicksort([42], key=lambda x: x) == [42]

    def test_empty_list(self):
        assert _quicksort([], key=lambda x: x) == []

    def test_custom_key(self):
        items = [("a", 3), ("b", 1), ("c", 2)]
        result = _quicksort(items, key=lambda x: x[1])
        assert result == [("b", 1), ("c", 2), ("a", 3)]

    def test_negative_numbers(self):
        items = [-5, 3, -1, 0, 2, -3]
        result = _quicksort(items, key=lambda x: x)
        assert result == [-5, -3, -1, 0, 2, 3]

    def test_floats(self):
        items = [3.14, 2.71, 1.41, 1.73]
        result = _quicksort(items, key=lambda x: x)
        assert result == [1.41, 1.73, 2.71, 3.14]


# ══════════════════════════════════════════════════════════
# Pydantic Schema 验证测试
# ══════════════════════════════════════════════════════════

class TestNearbySchemas:
    def test_nearby_request_valid(self):
        from backend.schemas.nearby import NearbyRequest
        req = NearbyRequest(
            origin_lat=39.9042,
            origin_lng=116.3974,
            category="toilet",
            max_dist=500,
            limit=10,
        )
        assert req.category == "toilet"
        assert req.max_dist == 500

    def test_nearby_request_defaults(self):
        from backend.schemas.nearby import NearbyRequest
        req = NearbyRequest(
            origin_lat=39.9,
            origin_lng=116.4,
            category="supermarket",
        )
        assert req.max_dist == 1000.0
        assert req.limit == 20

    def test_nearby_request_max_dist_validation(self):
        from backend.schemas.nearby import NearbyRequest
        from pydantic import ValidationError

        # max_dist 必须 > 0
        with pytest.raises(ValidationError):
            NearbyRequest(
                origin_lat=39.9,
                origin_lng=116.4,
                category="toilet",
                max_dist=0,
            )

        # max_dist 不能超过 5000
        with pytest.raises(ValidationError):
            NearbyRequest(
                origin_lat=39.9,
                origin_lng=116.4,
                category="toilet",
                max_dist=6000,
            )

    def test_nearby_item_response(self):
        from backend.schemas.nearby import NearbyItem
        item = NearbyItem(
            id=1,
            name="公共卫生间",
            category="toilet",
            sub_category="",
            lat=39.9,
            lng=116.4,
            address="北京市东城区",
            distance=123.5,
        )
        assert item.name == "公共卫生间"
        assert item.distance == 123.5


# ══════════════════════════════════════════════════════════
# 集成场景测试
# ══════════════════════════════════════════════════════════

class TestIntegrationScenarios:
    def test_bounded_dijkstra_with_quicksort(self):
        """模拟完整查询流程：等时圈搜索 + 排序"""
        G = _build_test_graph()
        import backend.services.graph_service as gs
        gs._graph = G

        # 从 A 出发，半径 400m
        reachable = _bounded_dijkstra("A", 400)

        # 模拟 POI 数据（节点 B, C, D 各有一个设施）
        pois = [
            {"id": 1, "node": "B", "name": "卫生间1"},
            {"id": 2, "node": "C", "name": "卫生间2"},
            {"id": 3, "node": "D", "name": "卫生间3"},
        ]

        # 过滤可达 + 附加距离
        results = []
        for poi in pois:
            if poi["node"] in reachable:
                results.append((poi, reachable[poi["node"]]))

        # 快速排序按距离升序
        sorted_results = _quicksort(results, key=lambda x: x[1])

        # 验证顺序：D(50) < B(100) < C(300)
        assert [p["id"] for p, _ in sorted_results] == [3, 1, 2]
        assert [d for _, d in sorted_results] == [50.0, 100.0, 300.0]


# ══════════════════════════════════════════════════════════
# 运行测试
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
