"""周边设施查询 API 路由"""

from fastapi import APIRouter, HTTPException

from backend.schemas.nearby import NearbyRequest, NearbyItem
from backend.services import nearby_service

router = APIRouter(prefix="/api/nearby", tags=["nearby"])


@router.post("", response_model=list[NearbyItem], summary="周边设施查询（有界 Dijkstra）")
def find_nearby(req: NearbyRequest):
    try:
        return nearby_service.find_nearby(
            req.origin_lat, req.origin_lng,
            req.category, req.max_dist, req.limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
