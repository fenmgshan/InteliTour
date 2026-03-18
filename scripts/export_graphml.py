"""从 MySQL 重建 NetworkX 图并导出 GraphML

提供 load_graph() 函数供后端路由规划模块直接调用。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import networkx as nx
from database.config import get_session
from database.models import RoadNode, RoadEdge

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GRAPHML_PATH = os.path.join(DATA_DIR, "beijing_walk.graphml")


def build_graph_from_db():
    """从数据库读取路网数据，重建 NetworkX 图"""
    session = get_session()
    try:
        G = nx.DiGraph()

        # 添加节点
        nodes = session.query(RoadNode).all()
        for n in nodes:
            G.add_node(n.id, lat=n.lat, lng=n.lng, node_type=n.node_type)

        # 添加边
        edges = session.query(RoadEdge).all()
        for e in edges:
            G.add_edge(
                e.source_node_id,
                e.target_node_id,
                length=e.length,
                congestion=e.congestion,
                highway_type=e.highway_type,
                max_speed=e.max_speed,
            )

        print(f"[OK] 重建图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
        return G
    finally:
        session.close()


def export_graphml(G=None):
    """导出 GraphML 文件"""
    if G is None:
        G = build_graph_from_db()
    os.makedirs(DATA_DIR, exist_ok=True)
    nx.write_graphml(G, GRAPHML_PATH)
    print(f"[OK] 已导出 {GRAPHML_PATH}")


def load_graph():
    """加载 GraphML 文件为 NetworkX 图

    供后端路由规划模块直接调用:
        from scripts.export_graphml import load_graph
        G = load_graph()
    """
    if not os.path.exists(GRAPHML_PATH):
        print("GraphML 文件不存在，正在从数据库重建...")
        G = build_graph_from_db()
        export_graphml(G)
        return G
    G = nx.read_graphml(GRAPHML_PATH)
    print(f"[OK] 加载图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
    return G


def main():
    G = build_graph_from_db()
    export_graphml(G)
    print("[OK] GraphML 导出完成")


if __name__ == "__main__":
    main()
