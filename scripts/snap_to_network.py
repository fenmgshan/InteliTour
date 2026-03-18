"""POI 吸附到最近路网节点预处理

使用 KDTree 将 pois 和 buildings 表中每条记录
吸附到最近的路网节点，更新 snapped_node_id 和 snap_distance。

提供 SnapService 类作为后端 API 可复用接口。
"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from scipy.spatial import KDTree
from database.config import get_session
from database.models import RoadNode, POI, Building


# 地球半径（米）
EARTH_RADIUS = 6371000


def haversine(lat1, lng1, lat2, lng2):
    """计算两点间的 Haversine 距离（米）"""
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(a))


class SnapService:
    """路网节点吸附服务

    用法:
        service = SnapService()
        node_id, node_lat, node_lng, distance = service.snap_point(39.9, 116.4)
    """

    def __init__(self):
        self._node_ids = []
        self._coords = []
        self._tree = None
        self._load_nodes()

    def _load_nodes(self):
        """从数据库加载路网节点并构建 KDTree"""
        session = get_session()
        try:
            nodes = session.query(RoadNode.id, RoadNode.lat, RoadNode.lng).all()
            if not nodes:
                raise RuntimeError("road_nodes 表为空，请先运行 crawl_road_network.py")
            self._node_ids = [n.id for n in nodes]
            self._coords = [(n.lat, n.lng) for n in nodes]
            self._tree = KDTree(np.array(self._coords))
            print(f"[SnapService] 加载 {len(nodes)} 个路网节点")
        finally:
            session.close()

    def snap_point(self, lat, lng):
        """将坐标吸附到最近路网节点

        Returns:
            (node_id, node_lat, node_lng, distance_meters)
        """
        _, idx = self._tree.query([lat, lng])
        node_id = self._node_ids[idx]
        node_lat, node_lng = self._coords[idx]
        dist = haversine(lat, lng, node_lat, node_lng)
        return node_id, node_lat, node_lng, dist


def snap_all_pois(service):
    """吸附所有 POI 到最近路网节点"""
    session = get_session()
    try:
        pois = session.query(POI).all()
        count = 0
        for poi in pois:
            node_id, _, _, dist = service.snap_point(poi.lat, poi.lng)
            poi.snapped_node_id = node_id
            poi.snap_distance = round(dist, 2)
            count += 1
        session.commit()
        print(f"[OK] 吸附 {count} 条 POI")
    finally:
        session.close()


def snap_all_buildings(service):
    """吸附所有建筑物到最近路网节点"""
    session = get_session()
    try:
        buildings = session.query(Building).all()
        count = 0
        for b in buildings:
            node_id, _, _, dist = service.snap_point(b.lat, b.lng)
            b.snapped_node_id = node_id
            count += 1
        session.commit()
        print(f"[OK] 吸附 {count} 条建筑物")
    finally:
        session.close()


def main():
    service = SnapService()
    snap_all_pois(service)
    snap_all_buildings(service)
    print("[OK] 吸附预处理完成")


if __name__ == "__main__":
    main()
