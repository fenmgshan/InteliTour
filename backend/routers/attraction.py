"""景点推荐 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.attraction import (
    AttractionItem,
    AttractionListRequest,
    AttractionSearchRequest,
)
from backend.services import attraction_service

router = APIRouter(prefix="/api/attraction", tags=["attraction"])


@router.post("/list", response_model=list[AttractionItem], summary="景点列表（分类+排序）")
def list_attractions(req: AttractionListRequest):
    try:
        return attraction_service.list_attractions(
            req.origin_lat, req.origin_lng,
            req.sub_category, req.sort_by, req.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[AttractionItem], summary="按名称搜索景点")
def search_attractions(req: AttractionSearchRequest):
    try:
        return attraction_service.search_attractions(
            req.origin_lat, req.origin_lng,
            req.q, req.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
