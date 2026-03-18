"""图加载单例

启动时加载 NetworkX DiGraph 并预计算各策略权重。
"""

import networkx as nx
from scripts.export_graphml import load_graph

# ── 速度常量 (km/h → m/s) ────────────────────────────────
WALK_SPEED = 5 * 1000 / 3600      # ≈ 1.39 m/s
BIKE_SPEED = 15 * 1000 / 3600     # ≈ 4.17 m/s
EBIKE_SPEED = 25 * 1000 / 3600    # ≈ 6.94 m/s

# ── 单例 ─────────────────────────────────────────────────
_graph: nx.DiGraph | None = None


def _ensure_numeric_attrs(G: nx.DiGraph) -> None:
    """GraphML 读取后属性都是字符串，统一转为浮点数。"""
    for _, _, data in G.edges(data=True):
        data["length"] = float(data.get("length", 0))
        data["congestion"] = float(data.get("congestion", 1))
        data["max_speed"] = float(data.get("max_speed", 0))
    for _, data in G.nodes(data=True):
        data["lat"] = float(data.get("lat", 0))
        data["lng"] = float(data.get("lng", 0))


def _precompute_weights(G: nx.DiGraph) -> None:
    """为每条边预计算 time / bike / ebike 权重。"""
    for _, _, data in G.edges(data=True):
        length = data["length"]
        congestion = data["congestion"] if data["congestion"] > 0 else 1.0
        data["time"] = length / (WALK_SPEED * congestion)
        data["bike"] = length / (BIKE_SPEED * congestion)
        data["ebike"] = length / (EBIKE_SPEED * congestion)


def init_graph() -> None:
    """加载图并预处理权重（应用启动时调用一次）。"""
    global _graph
    G = load_graph()
    _ensure_numeric_attrs(G)
    _precompute_weights(G)
    _graph = G


def get_graph() -> nx.DiGraph:
    """获取全局图实例。"""
    if _graph is None:
        raise RuntimeError("图尚未加载，请先调用 init_graph()")
    return _graph
