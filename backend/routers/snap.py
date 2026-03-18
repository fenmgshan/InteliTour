"""坐标吸附 API"""

from fastapi import APIRouter, HTTPException

from backend.schemas.route import SnapRequest, SnapResponse
from backend.services.snap_service import get_snap_service

router = APIRouter(prefix="/api", tags=["snap"])


@router.post("/snap", response_model=SnapResponse, summary="坐标吸附到最近路网节点")
def snap_point(req: SnapRequest):
    try:
        service = get_snap_service()
        node_id, node_lat, node_lng, dist = service.snap_point(req.lat, req.lng)
        return SnapResponse(
            node_id=int(node_id),
            lat=node_lat,
            lng=node_lng,
            distance=round(dist, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
