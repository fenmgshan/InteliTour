"""Pydantic 周边设施请求/响应模型"""

from pydantic import BaseModel, Field


class NearbyRequest(BaseModel):
    origin_lat: float = Field(..., description="起点纬度")
    origin_lng: float = Field(..., description="起点经度")
    category: str = Field(..., description="设施类别，如 toilet / supermarket / restaurant")
    max_dist: float = Field(1000.0, gt=0, le=5000, description="最大路网距离（米）")
    limit: int = Field(20, ge=1, le=100, description="最多返回数量")


class NearbyItem(BaseModel):
    id: int
    name: str
    category: str
    sub_category: str
    lat: float
    lng: float
    address: str
    distance: float = Field(..., description="实际路网距离（米）")
