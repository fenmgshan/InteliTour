"""Pydantic 景点推荐请求/响应模型"""

from pydantic import BaseModel, Field


class AttractionItem(BaseModel):
    id: int = Field(..., description="景点 POI ID")
    name: str = Field(..., description="景点名称")
    category: str = Field(..., description="主类别")
    sub_category: str = Field(..., description="OSM 子类别")
    lat: float = Field(..., description="纬度")
    lng: float = Field(..., description="经度")
    address: str = Field(..., description="地址")
    rating: float = Field(..., description="评分")
    heat: float = Field(..., description="热度")
    distance: float = Field(..., description="到起点的路网距离（米）")


class AttractionListRequest(BaseModel):
    origin_lat: float = Field(..., description="起点纬度")
    origin_lng: float = Field(..., description="起点经度")
    sub_category: str = Field("", description="子类别过滤，空=全部")
    sort_by: str = Field("heat", description="排序方式：heat | distance")
    limit: int = Field(20, ge=1, le=100, description="返回数量")


class AttractionSearchRequest(BaseModel):
    origin_lat: float = Field(..., description="起点纬度")
    origin_lng: float = Field(..., description="起点经度")
    q: str = Field(..., description="名称搜索关键词")
    limit: int = Field(20, ge=1, le=100, description="返回数量")
