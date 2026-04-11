"""Pydantic 美食推荐请求/响应模型"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    id: int
    name: str
    category: str
    sub_category: str
    lat: float
    lng: float
    address: str
    rating: float
    heat: float
    distance: float = Field(..., description="到起点的路网距离（米）")
    score: float = Field(..., description="综合推荐分")


class FoodRecommendRequest(BaseModel):
    origin_lat: float = Field(..., description="起点纬度")
    origin_lng: float = Field(..., description="起点经度")
    cuisine: str = Field("", description="菜系/子类别过滤，空字符串表示不过滤")
    n: int = Field(10, ge=1, le=50, description="返回数量")


class FoodSearchRequest(BaseModel):
    q: str = Field(..., min_length=1, description="搜索词（支持错别字容错）")
    origin_lat: Optional[float] = Field(None, description="起点纬度（用于距离排序）")
    origin_lng: Optional[float] = Field(None, description="起点经度")
    max_edit_distance: int = Field(2, ge=0, le=4, description="Levenshtein 最大编辑距离")
    n: int = Field(10, ge=1, le=50, description="返回数量")
