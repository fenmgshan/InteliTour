"""爬取北京核心景区路网数据

以天安门 (39.9042, 116.3974) 为中心，半径 5000m，
爬取可步行路网并写入 MySQL + 导出 GraphML。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString
from sqlalchemy import text
from database.config import get_engine, get_session
from database.models import RoadNode, RoadEdge

# 天安门坐标
CENTER_LAT = 39.9042
CENTER_LNG = 116.3974
RADIUS = 5000  # 米

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def crawl_walk_network():
    """爬取步行路网"""
    print(f"正在爬取以 ({CENTER_LAT}, {CENTER_LNG}) 为中心、半径 {RADIUS}m 的步行路网...")
    G = ox.graph_from_point(
        (CENTER_LAT, CENTER_LNG),
        dist=RADIUS,
        network_type="walk",
        simplify=True,
    )
    print(f"爬取完成: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")
    return G


def detect_node_type(G, node_id):
    """判断节点类型：度 >= 3 为交叉口，否则为普通"""
    degree = G.degree(node_id)
    return "交叉口" if degree >= 3 else "普通"


def save_to_mysql(G):
    """将路网数据写入 MySQL"""
    session = get_session()
    try:

        session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        session.execute(text("DELETE FROM road_edges"))
        session.execute(text("DELETE FROM road_nodes"))
        session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        session.commit()

        # 写入节点
        nodes_data = []
        for node_id, data in G.nodes(data=True):
            nodes_data.append(RoadNode(
                id=int(node_id),
                lat=data["y"],
                lng=data["x"],
                node_type=detect_node_type(G, node_id),
            ))
        session.bulk_save_objects(nodes_data)
        session.commit()
        print(f"[OK] 写入 {len(nodes_data)} 个路网节点")

        # 写入边
        edges_data = []
        for u, v, data in G.edges(data=True):
            # 提取几何
            geom_wkt = ""
            if "geometry" in data:
                geom_wkt = data["geometry"].wkt
            else:
                u_data = G.nodes[u]
                v_data = G.nodes[v]
                line = LineString([(u_data["x"], u_data["y"]),
                                   (v_data["x"], v_data["y"])])
                geom_wkt = line.wkt

            # 提取道路名称（可能是列表）
            name = data.get("name", "")
            if isinstance(name, list):
                name = "/".join(str(n) for n in name)

            # 提取限速
            max_speed = data.get("maxspeed", 0)
            if isinstance(max_speed, list):
                max_speed = max_speed[0]
            if isinstance(max_speed, str):
                try:
                    max_speed = float(max_speed.replace("km/h", "").strip())
                except ValueError:
                    max_speed = 0

            # 提取 highway 类型
            highway = data.get("highway", "")
            if isinstance(highway, list):
                highway = "/".join(str(h) for h in highway)

            edges_data.append(RoadEdge(
                source_node_id=int(u),
                target_node_id=int(v),
                length=data.get("length", 0),
                name=str(name)[:255],
                highway_type=str(highway)[:50],
                max_speed=float(max_speed) if max_speed else 0,
                congestion=1.0,
                oneway=bool(data.get("oneway", False)),
                geometry=geom_wkt,
            ))
        session.bulk_save_objects(edges_data)
        session.commit()
        print(f"[OK] 写入 {len(edges_data)} 条路网边")
    finally:
        session.close()


def export_graphml(G):
    """导出 GraphML 文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, "beijing_walk.graphml")
    ox.save_graphml(G, filepath)
    print(f"[OK] 已导出 {filepath}")


def main():
    G = crawl_walk_network()
    save_to_mysql(G)
    export_graphml(G)
    print("[OK] 路网爬取完成")


if __name__ == "__main__":
    main()
