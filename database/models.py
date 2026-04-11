"""SQLAlchemy ORM 模型定义"""

from sqlalchemy import (
    Column, BigInteger, Integer, Float, String, Boolean, Text,
    ForeignKey, Index, LargeBinary, DateTime
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class RoadNode(Base):
    """路网节点"""
    __tablename__ = "road_nodes"

    id = Column(BigInteger, primary_key=True, comment="OSM node ID")
    lat = Column(Float(precision=32), nullable=False, comment="纬度")
    lng = Column(Float(precision=32), nullable=False, comment="经度")
    node_type = Column(
        String(20), default="普通",
        comment="节点类型：交叉口/普通"
    )

    __table_args__ = (
        Index("idx_road_nodes_latlng", "lat", "lng"),
    )


class RoadEdge(Base):
    """路网边"""
    __tablename__ = "road_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_node_id = Column(
        BigInteger, ForeignKey("road_nodes.id"), nullable=False,
        comment="起始节点 OSM ID"
    )
    target_node_id = Column(
        BigInteger, ForeignKey("road_nodes.id"), nullable=False,
        comment="终止节点 OSM ID"
    )
    length = Column(Float, nullable=False, comment="边长度（米）")
    name = Column(String(255), default="", comment="道路名称")
    highway_type = Column(String(50), default="", comment="道路类型")
    max_speed = Column(Float, default=0, comment="最高限速 km/h")
    congestion = Column(Float, default=1.0, comment="拥挤度系数，默认1.0")
    oneway = Column(Boolean, default=False, comment="是否单行道")
    geometry = Column(Text, default="", comment="WKT LineString 几何")

    source_node = relationship("RoadNode", foreign_keys=[source_node_id])
    target_node = relationship("RoadNode", foreign_keys=[target_node_id])

    __table_args__ = (
        Index("idx_road_edges_source", "source_node_id"),
        Index("idx_road_edges_target", "target_node_id"),
    )


class POI(Base):
    """兴趣点"""
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, autoincrement=True)
    osm_id = Column(BigInteger, nullable=True, comment="OSM ID")
    name = Column(String(255), default="", comment="名称")
    category = Column(
        String(50), default="",
        comment="主类别：景点/餐厅/超市/卫生间/便利店等"
    )
    sub_category = Column(String(50), default="", comment="子类别")
    lat = Column(Float(precision=32), nullable=False, comment="纬度")
    lng = Column(Float(precision=32), nullable=False, comment="经度")
    snapped_node_id = Column(
        BigInteger, ForeignKey("road_nodes.id"), nullable=True,
        comment="吸附到的最近路网节点"
    )
    snap_distance = Column(Float, default=0, comment="吸附距离（米）")
    address = Column(String(500), default="", comment="地址")
    phone = Column(String(50), default="", comment="电话")
    opening_hours = Column(String(255), default="", comment="营业时间")
    rating = Column(Float, default=0, comment="评分")
    heat = Column(Float, default=0, comment="热度")
    has_indoor = Column(Boolean, default=False, comment="是否有室内地图")
    tags_json = Column(Text, default="{}", comment="原始 OSM tags JSON")

    snapped_node = relationship("RoadNode", foreign_keys=[snapped_node_id])

    __table_args__ = (
        Index("idx_pois_category", "category"),
        Index("idx_pois_latlng", "lat", "lng"),
        Index("idx_pois_snapped", "snapped_node_id"),
    )


class Building(Base):
    """建筑物"""
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    osm_id = Column(BigInteger, nullable=True, comment="OSM ID")
    name = Column(String(255), default="", comment="建筑名称")
    building_type = Column(String(50), default="", comment="建筑类型")
    lat = Column(Float(precision=32), nullable=False, comment="质心纬度")
    lng = Column(Float(precision=32), nullable=False, comment="质心经度")
    snapped_node_id = Column(
        BigInteger, ForeignKey("road_nodes.id"), nullable=True,
        comment="吸附到的最近路网节点"
    )
    address = Column(String(500), default="", comment="地址")
    floors = Column(Integer, default=0, comment="楼层数")
    geometry_wkt = Column(Text, default="", comment="WKT Polygon 几何")

    snapped_node = relationship("RoadNode", foreign_keys=[snapped_node_id])

    __table_args__ = (
        Index("idx_buildings_latlng", "lat", "lng"),
        Index("idx_buildings_snapped", "snapped_node_id"),
    )


class IndoorMap(Base):
    """室内地图（预留）"""
    __tablename__ = "indoor_maps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(
        Integer, ForeignKey("buildings.id"), nullable=False,
        comment="所属建筑 ID"
    )
    floor = Column(Integer, nullable=False, comment="楼层")
    map_image_url = Column(String(500), default="", comment="地图图片 URL")
    nodes_json = Column(Text, default="[]", comment="室内节点 JSON")
    edges_json = Column(Text, default="[]", comment="室内边 JSON")

    building = relationship("Building", foreign_keys=[building_id])

    __table_args__ = (
        Index("idx_indoor_maps_building", "building_id"),
    )


class Diary(Base):
    """旅游日记"""
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="标题（B+树索引，精确查找）")
    author = Column(String(100), default="匿名", comment="作者")
    destination = Column(String(255), default="", comment="目的地名称")
    content_compressed = Column(LargeBinary, nullable=False, comment="zlib压缩后的正文")
    rating = Column(Float, default=0.0, comment="评分 0-5")
    created_at = Column(DateTime, default=datetime.utcnow, comment="发布时间")

    __table_args__ = (
        Index("idx_diaries_title", "title"),
        Index("idx_diaries_destination", "destination"),
    )
