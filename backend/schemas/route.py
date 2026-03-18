"""Pydantic 请求/响应模型

定义路线规划与坐标吸附 API 的数据结构。
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ── 通用坐标 ──────────────────────────────────────────────

class LatLng(BaseModel):
    lat: float = Field(..., description="纬度")
    lng: float = Field(..., description="经度")


# ── 坐标吸附 ──────────────────────────────────────────────

class SnapRequest(BaseModel):
    lat: float = Field(..., description="待吸附纬度")
    lng: float = Field(..., description="待吸附经度")


class SnapResponse(BaseModel):
    node_id: int = Field(..., description="吸附到的路网节点 ID")
    lat: float = Field(..., description="节点纬度")
    lng: float = Field(..., description="节点经度")
    distance: float = Field(..., description="吸附距离（米）")


# ── 两点最短路径 ──────────────────────────────────────────

class ShortestPathRequest(BaseModel):
    origin: LatLng = Field(..., description="起点坐标")
    destination: LatLng = Field(..., description="终点坐标")
    strategy: str = Field(
        "distance",
        description="权重策略: distance | time | bike | ebike",
    )


class ShortestPathResponse(BaseModel):
    path: List[LatLng] = Field(..., description="路径坐标序列")
    total_distance: float = Field(..., description="总距离（米）")
    total_time: float = Field(..., description="预估总耗时（秒）")
    strategy: str = Field(..., description="使用的权重策略")


# ── 多点 TSP ──────────────────────────────────────────────

class TSPRequest(BaseModel):
    origin: LatLng = Field(..., description="起点坐标")
    waypoints: List[LatLng] = Field(..., description="途经点坐标列表（最多 15 个）")
    strategy: str = Field(
        "distance",
        description="权重策略: distance | time | bike | ebike",
    )
    round_trip: bool = Field(False, description="是否返回起点")


class TSPSegment(BaseModel):
    from_index: int = Field(..., description="起始途经点索引（-1 表示起点）")
    to_index: int = Field(..., description="到达途经点索引（-1 表示起点）")
    path: List[LatLng] = Field(..., description="该段路径坐标")
    distance: float = Field(..., description="该段距离（米）")
    time: float = Field(..., description="该段耗时（秒）")


class TSPResponse(BaseModel):
    ordered_waypoints: List[int] = Field(
        ..., description="途经点的最优访问顺序（输入列表的索引）"
    )
    path: List[LatLng] = Field(..., description="完整路径坐标序列")
    segments: List[TSPSegment] = Field(..., description="各段路径详情")
    total_distance: float = Field(..., description="总距离（米）")
    total_time: float = Field(..., description="预估总耗时（秒）")
