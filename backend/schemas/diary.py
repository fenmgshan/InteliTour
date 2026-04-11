"""Pydantic 日记请求/响应模型"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DiaryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="标题")
    author: str = Field("匿名", max_length=100, description="作者")
    destination: str = Field("", max_length=255, description="目的地")
    content: str = Field(..., min_length=1, description="正文（富文本/纯文本）")
    rating: float = Field(0.0, ge=0.0, le=5.0, description="评分 0-5")


class DiaryResponse(BaseModel):
    id: int
    title: str
    author: str
    destination: str
    content: str = Field(..., description="解压后的正文")
    rating: float
    heat: float = Field(0.0, description="浏览热度（来自 Redis）")
    created_at: datetime

    class Config:
        from_attributes = True


class DiaryBrief(BaseModel):
    """列表/推荐场景用，不含正文"""
    id: int
    title: str
    author: str
    destination: str
    rating: float
    heat: float
    created_at: datetime

    class Config:
        from_attributes = True


class DiarySearchRequest(BaseModel):
    mode: str = Field(
        ...,
        description="搜索模式: title（精确）| destination（目的地）| fulltext（全文）",
    )
    q: str = Field(..., min_length=1, description="搜索关键词")
