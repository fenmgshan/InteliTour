"""周边设施查询 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.nearby import NearbyRequest, NearbyItem
from backend.services import nearby_service
from backend.utils.coords import to_wgs84, convert_dict_latlng

router = APIRouter(prefix="/api/nearby", tags=["nearby"])


@router.post("", response_model=list[NearbyItem], summary="周边设施查询（有界 Dijkstra）")
def find_nearby(req: NearbyRequest):
    try:
        # GCJ-02（高德）→ WGS-84（OSM 路网）
        wgs_lat, wgs_lng = to_wgs84(req.origin_lat, req.origin_lng)
        results = nearby_service.find_nearby(
            wgs_lat, wgs_lng, req.category, req.max_dist, req.limit,
        )
        # WGS-84 → GCJ-02，使 POI 位置与高德地图底图对齐
        for item in results:
            convert_dict_latlng(item, "gcj02")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
