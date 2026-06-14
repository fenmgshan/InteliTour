"""景点推荐 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.attraction import (
    AttractionItem,
    AttractionListRequest,
    AttractionSearchRequest,
)
from backend.services import attraction_service
from backend.utils.coords import to_wgs84, convert_dict_latlng

router = APIRouter(prefix="/api/attraction", tags=["attraction"])


@router.post("/list", response_model=list[AttractionItem], summary="景点列表（分类+排序）")
def list_attractions(req: AttractionListRequest):
    try:
        # GCJ-02（高德）→ WGS-84（OSM 路网）
        wgs_lat, wgs_lng = to_wgs84(req.origin_lat, req.origin_lng)
        results = attraction_service.list_attractions(
            wgs_lat, wgs_lng, req.sub_category, req.sort_by, req.limit,
        )
        # WGS-84 → GCJ-02，使 POI 位置与高德地图底图对齐
        for item in results:
            convert_dict_latlng(item, "gcj02")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=list[AttractionItem], summary="按名称搜索景点")
def search_attractions(req: AttractionSearchRequest):
    try:
        # GCJ-02（高德）→ WGS-84（OSM 路网）
        wgs_lat, wgs_lng = to_wgs84(req.origin_lat, req.origin_lng)
        results = attraction_service.search_attractions(
            wgs_lat, wgs_lng, req.q, req.limit,
        )
        # WGS-84 → GCJ-02，使 POI 位置与高德地图底图对齐
        for item in results:
            convert_dict_latlng(item, "gcj02")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
