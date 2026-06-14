"""图加载单例

启动时从数据库构建 NetworkX DiGraph 并预计算各策略权重。
"""

import networkx as nx
from scripts.export_graphml import build_graph_from_db

# ── 速度常量 (km/h → m/s) ────────────────────────────────
WALK_SPEED = 5 * 1000 / 3600      # ≈ 1.39 m/s
BIKE_SPEED = 15 * 1000 / 3600     # ≈ 4.17 m/s
EBIKE_SPEED = 25 * 1000 / 3600    # ≈ 6.94 m/s

# ── 单例 ─────────────────────────────────────────────────
_graph: nx.DiGraph | None = None


def _precompute_weights(G: nx.DiGraph) -> None:
    """为每条边预计算 time / bike / ebike 权重。"""
    for _, _, data in G.edges(data=True):
        length = float(data["length"])
        congestion = float(data.get("congestion", 1))
        if congestion <= 0:
            congestion = 1.0
        data["time"] = length / (WALK_SPEED * congestion)
        data["bike"] = length / (BIKE_SPEED * congestion)
        data["ebike"] = length / (EBIKE_SPEED * congestion)


def init_graph() -> None:
    """从数据库构建图并预处理权重（应用启动时调用一次）。"""
    global _graph
    G = build_graph_from_db()
    _precompute_weights(G)
    _graph = G
    print(f"[启动] 图加载完成: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")


def get_graph() -> nx.DiGraph:
    """获取全局图实例。"""
    if _graph is None:
        raise RuntimeError("图尚未加载，请先调用 init_graph()")
    return _graph
